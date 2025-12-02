"""
Property-Based Tests for Game Engine

Tests correctness properties related to game engine mechanics,
including movement, object interactions, and command processing.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler'))

import pytest
from hypothesis import given, strategies as st, settings, assume
from game_engine import GameEngine, ActionResult
from state_manager import GameState
from world_loader import WorldData
from command_parser import CommandParser, ParsedCommand


# Initialize world data for tests
@pytest.fixture(scope="module")
def world_data():
    """Load world data once for all tests."""
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    return world


@pytest.fixture(scope="module")
def game_engine(world_data):
    """Create game engine instance."""
    return GameEngine(world_data)


# Custom strategies for generating test data
@st.composite
def valid_room_and_direction(draw, world_data):
    """
    Generate a valid room ID and a direction from that room.
    
    Returns tuple of (room_id, direction, target_room_id) where the exit exists.
    """
    # Get all room IDs
    room_ids = list(world_data.rooms.keys())
    
    # Pick a random room
    room_id = draw(st.sampled_from(room_ids))
    room = world_data.get_room(room_id)
    
    # If room has exits, pick one
    if room.exits:
        direction = draw(st.sampled_from(list(room.exits.keys())))
        target_room_id = room.exits[direction]
        return (room_id, direction, target_room_id)
    else:
        # Room has no exits, return None for direction
        return (room_id, None, None)


@st.composite
def invalid_room_and_direction(draw, world_data):
    """
    Generate a room ID and an invalid direction (one that doesn't exist as an exit).
    
    Returns tuple of (room_id, invalid_direction).
    """
    # Get all room IDs
    room_ids = list(world_data.rooms.keys())
    
    # Pick a random room
    room_id = draw(st.sampled_from(room_ids))
    room = world_data.get_room(room_id)
    
    # All possible directions
    all_directions = ["NORTH", "SOUTH", "EAST", "WEST", "UP", "DOWN", "IN", "OUT",
                      "NORTHEAST", "NORTHWEST", "SOUTHEAST", "SOUTHWEST", "NE", "NW", "SE", "SW"]
    
    # Find directions that are NOT exits from this room
    invalid_directions = [d for d in all_directions if d not in room.exits]
    
    # If there are invalid directions, pick one
    if invalid_directions:
        invalid_direction = draw(st.sampled_from(invalid_directions))
        return (room_id, invalid_direction)
    else:
        # This room has all directions as exits (unlikely), skip this example
        assume(False)


# Feature: game-backend-api, Property 6: Movement validation
@settings(max_examples=100)
@given(st.data())
def test_movement_succeeds_only_for_valid_exits(data):
    """
    For any room and direction, movement should succeed if and only if
    the room has an exit in that direction (and any required flags are set).
    
    **Validates: Requirements 3.1, 3.4, 3.5**
    
    This property ensures that:
    1. Valid exits allow movement
    2. Invalid directions are blocked
    3. Movement updates the game state correctly
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Test valid movement
    room_id, direction, target_room_id = data.draw(valid_room_and_direction(world))
    
    if direction is not None:
        # Create game state in the starting room
        state = GameState.create_new_game()
        state.current_room = room_id
        
        # Attempt movement
        result = engine.handle_movement(direction, state)
        
        # Movement should succeed
        assert result.success is True, f"Movement from {room_id} in direction {direction} should succeed"
        assert result.room_changed is True
        assert result.new_room == target_room_id
        assert state.current_room == target_room_id
        
        # State should be updated
        assert target_room_id in state.rooms_visited
        assert state.moves > 0
        assert state.turn_count > 0


@settings(max_examples=100)
@given(st.data())
def test_movement_fails_for_invalid_exits(data):
    """
    For any room and invalid direction, movement should fail and state should be unchanged.
    
    **Validates: Requirements 3.1, 3.4, 3.5**
    
    This property ensures that:
    1. Invalid directions are properly rejected
    2. Game state remains unchanged on failed movement
    3. Appropriate error messages are returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Test invalid movement
    room_id, invalid_direction = data.draw(invalid_room_and_direction(world))
    
    # Create game state in the starting room
    state = GameState.create_new_game()
    state.current_room = room_id
    initial_room = state.current_room
    initial_moves = state.moves
    initial_turns = state.turn_count
    
    # Attempt movement in invalid direction
    result = engine.handle_movement(invalid_direction, state)
    
    # Movement should fail
    assert result.success is False, f"Movement from {room_id} in invalid direction {invalid_direction} should fail"
    assert result.room_changed is False
    assert result.new_room is None
    
    # State should be unchanged
    assert state.current_room == initial_room
    assert state.moves == initial_moves
    assert state.turn_count == initial_turns


@settings(max_examples=100)
@given(st.data())
def test_movement_updates_rooms_visited(data):
    """
    For any valid movement, the target room should be added to rooms_visited.
    
    **Validates: Requirements 3.2**
    
    This property ensures that room visitation tracking works correctly.
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get valid movement
    room_id, direction, target_room_id = data.draw(valid_room_and_direction(world))
    
    if direction is not None:
        # Create game state
        state = GameState.create_new_game()
        state.current_room = room_id
        initial_visited = state.rooms_visited.copy()
        
        # Perform movement
        result = engine.handle_movement(direction, state)
        
        if result.success:
            # Target room should be in visited set
            assert target_room_id in state.rooms_visited
            
            # Visited set should have grown (unless room was already visited)
            assert len(state.rooms_visited) >= len(initial_visited)


@settings(max_examples=100)
@given(st.data())
def test_movement_returns_room_description(data):
    """
    For any valid movement, the result should include the target room's description.
    
    **Validates: Requirements 3.3**
    
    This property ensures that players receive appropriate feedback after movement.
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get valid movement
    room_id, direction, target_room_id = data.draw(valid_room_and_direction(world))
    
    if direction is not None:
        # Create game state
        state = GameState.create_new_game()
        state.current_room = room_id
        
        # Perform movement
        result = engine.handle_movement(direction, state)
        
        if result.success:
            # Result should contain a description
            assert result.message is not None
            assert len(result.message) > 0
            
            # Description should be the spooky variant
            expected_description = world.get_room_description(target_room_id, state.sanity)
            assert result.message == expected_description


@settings(max_examples=100)
@given(st.data())
def test_movement_increments_counters(data):
    """
    For any valid movement, turn_count and moves should increment.
    
    **Validates: Requirements 3.2**
    
    This property ensures that game progression tracking works correctly.
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get valid movement
    room_id, direction, target_room_id = data.draw(valid_room_and_direction(world))
    
    if direction is not None:
        # Create game state
        state = GameState.create_new_game()
        state.current_room = room_id
        initial_moves = state.moves
        initial_turns = state.turn_count
        
        # Perform movement
        result = engine.handle_movement(direction, state)
        
        if result.success:
            # Counters should increment
            assert state.moves == initial_moves + 1
            assert state.turn_count == initial_turns + 1


@st.composite
def takeable_object_in_room(draw, world_data):
    """
    Generate a room ID and a takeable object that exists in that room.
    
    Returns tuple of (room_id, object_id) where object is takeable and in room.
    """
    # Find all takeable objects (either marked is_takeable or has TAKE interaction with state_change)
    takeable_objects = []
    for obj_id, obj in world_data.objects.items():
        if obj.is_takeable:
            takeable_objects.append(obj_id)
        else:
            # Check if object has a TAKE interaction that changes state (indicating it can be taken)
            for interaction in obj.interactions:
                if interaction.verb == "TAKE" and interaction.state_change:
                    takeable_objects.append(obj_id)
                    break
    
    if not takeable_objects:
        assume(False)  # Skip if no takeable objects
    
    # Pick a takeable object
    object_id = draw(st.sampled_from(takeable_objects))
    
    # Pick a random room to place the object in
    room_ids = list(world_data.rooms.keys())
    room_id = draw(st.sampled_from(room_ids))
    
    return (room_id, object_id)


# Feature: game-backend-api, Property 7: Object conservation (take/drop)
@settings(max_examples=100)
@given(st.data())
def test_take_then_drop_returns_object_to_room(data):
    """
    For any game state, taking an object from a room and then dropping it
    should result in the object being back in the room and not in inventory.
    
    **Validates: Requirements 4.2, 4.3**
    
    This property ensures that:
    1. Take operation removes object from room and adds to inventory
    2. Drop operation removes object from inventory and adds to room
    3. The round-trip preserves object location
    """
    # Load world data (fresh instance for each test)
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a takeable object in a room
    room_id, object_id = data.draw(takeable_object_in_room(world))
    
    # Create game state in that room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Get current room and object
    current_room = world.get_room(room_id)
    game_object = world.get_object(object_id)
    
    # Mark object as takeable for this test
    game_object.is_takeable = True
    
    # Ensure object is in room initially
    if object_id not in current_room.items:
        current_room.items.append(object_id)
    
    # Verify initial state
    assert object_id in current_room.items, "Object should be in room initially"
    assert object_id not in state.inventory, "Object should not be in inventory initially"
    
    # Take the object
    take_result = engine.handle_take(object_id, state)
    
    # Take should succeed
    assert take_result.success is True, f"Taking {object_id} should succeed"
    
    # Object should now be in inventory and not in room
    assert object_id in state.inventory, "Object should be in inventory after taking"
    assert object_id not in current_room.items, "Object should not be in room after taking"
    
    # Drop the object
    drop_result = engine.handle_drop(object_id, state)
    
    # Drop should succeed
    assert drop_result.success is True, f"Dropping {object_id} should succeed"
    
    # Object should be back in room and not in inventory (round trip complete)
    assert object_id not in state.inventory, "Object should not be in inventory after dropping"
    assert object_id in current_room.items, "Object should be back in room after dropping"


# Feature: game-backend-api, Property 8: Inventory tracking
@settings(max_examples=100)
@given(st.data())
def test_inventory_reflects_take_drop_operations(data):
    """
    For any sequence of take and drop operations, the inventory should contain
    exactly the objects that were taken minus the objects that were dropped.
    
    **Validates: Requirements 5.1, 5.5**
    
    This property ensures that:
    1. Inventory accurately tracks all take operations
    2. Inventory accurately reflects all drop operations
    3. Inventory state is consistent after any sequence of operations
    """
    # Load world data (fresh instance for each test)
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Create game state
    state = GameState.create_new_game()
    
    # Get list of all objects
    all_objects = list(world.objects.keys())
    
    # Generate a sequence of take/drop operations (3-10 operations)
    num_operations = data.draw(st.integers(min_value=3, max_value=10))
    
    # Track what should be in inventory
    expected_inventory = set()
    
    # Get current room
    current_room = world.get_room(state.current_room)
    
    for _ in range(num_operations):
        # Decide whether to take or drop
        operation = data.draw(st.sampled_from(['take', 'drop']))
        
        if operation == 'take':
            # Pick an object to take
            object_id = data.draw(st.sampled_from(all_objects))
            game_object = world.get_object(object_id)
            
            # Mark as takeable and place in room
            game_object.is_takeable = True
            if object_id not in current_room.items:
                current_room.items.append(object_id)
            
            # Take the object
            result = engine.handle_take(object_id, state)
            
            if result.success:
                # Update expected inventory
                expected_inventory.add(object_id)
        
        elif operation == 'drop':
            # Can only drop if we have something in inventory
            if state.inventory:
                # Pick an object from inventory to drop
                object_id = data.draw(st.sampled_from(state.inventory))
                
                # Drop the object
                result = engine.handle_drop(object_id, state)
                
                if result.success:
                    # Update expected inventory
                    expected_inventory.discard(object_id)
    
    # Verify final inventory matches expected
    actual_inventory = set(state.inventory)
    assert actual_inventory == expected_inventory, \
        f"Inventory mismatch: expected {expected_inventory}, got {actual_inventory}"
