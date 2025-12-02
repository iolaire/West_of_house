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
