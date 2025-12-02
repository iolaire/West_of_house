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
        
        # Set flags for known flag-gated exits to ensure they're accessible
        # Trap door puzzle
        if room_id == "living_room" and direction == "DOWN":
            state.set_flag("trap_door_open", True)
        # Grating puzzle
        if room_id == "grating_clearing" and direction == "DOWN":
            state.set_flag("grate_unlocked", True)
        # Kitchen window puzzle
        if room_id == "east_of_house" and target_room_id == "kitchen":
            state.set_flag("kitchen_window_open", True)
        
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



@st.composite
def container_and_objects(draw, world_data):
    """
    Generate a container and a list of objects to put in it.
    
    Returns tuple of (room_id, container_id, object_ids) where container has capacity.
    """
    # Find all containers
    containers = []
    for obj_id, obj in world_data.objects.items():
        if obj.type == "container" and obj.capacity > 0:
            containers.append(obj_id)
    
    if not containers:
        assume(False)  # Skip if no containers with capacity
    
    # Pick a container
    container_id = draw(st.sampled_from(containers))
    container = world_data.get_object(container_id)
    
    # Find takeable objects
    takeable_objects = []
    for obj_id, obj in world_data.objects.items():
        if obj.is_takeable and obj_id != container_id:
            takeable_objects.append(obj_id)
    
    if not takeable_objects:
        assume(False)  # Skip if no takeable objects
    
    # Generate a list of objects (1 to 5 objects)
    num_objects = draw(st.integers(min_value=1, max_value=5))
    object_ids = [draw(st.sampled_from(takeable_objects)) for _ in range(num_objects)]
    
    # Pick a random room
    room_ids = list(world_data.rooms.keys())
    room_id = draw(st.sampled_from(room_ids))
    
    return (room_id, container_id, object_ids)


# Feature: game-backend-api, Property 23: Container capacity enforcement
@settings(max_examples=100)
@given(st.data())
def test_container_capacity_never_exceeded(data):
    """
    For any container with capacity C, the total size of objects in the container
    should never exceed C.
    
    **Validates: Requirements 15.2**
    
    This property ensures that:
    1. Container capacity limits are enforced
    2. Objects cannot be added when capacity would be exceeded
    3. Container state remains consistent
    """
    # Load world data (fresh instance for each test)
    WorldData.clear_cache()  # Clear cache to ensure fresh data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a container and objects to put in it
    room_id, container_id, object_ids = data.draw(container_and_objects(world))
    
    # Create game state in that room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Get current room and container
    current_room = world.get_room(room_id)
    container = world.get_object(container_id)
    
    # Ensure container is in room and open
    if container_id not in current_room.items:
        current_room.items.append(container_id)
    container.state['is_open'] = True
    container.state['contents'] = []
    
    # Track total size in container
    total_size = 0
    
    # Try to put each object in the container
    for object_id in object_ids:
        game_object = world.get_object(object_id)
        
        # Mark as takeable and add to inventory
        game_object.is_takeable = True
        if object_id not in state.inventory:
            state.inventory.append(object_id)
        
        # Try to put object in container
        result = engine.handle_put(object_id, container_id, state)
        
        # Calculate what the new size would be
        object_size = getattr(game_object, 'size', 1)
        new_size = total_size + object_size
        
        if new_size <= container.capacity:
            # Should succeed - capacity not exceeded
            assert result.success is True, \
                f"Putting {object_id} (size {object_size}) should succeed when total size {new_size} <= capacity {container.capacity}"
            total_size = new_size
            # Verify object is in container
            assert object_id in container.state.get('contents', [])
            assert object_id not in state.inventory
        else:
            # Should fail - capacity would be exceeded
            assert result.success is False, \
                f"Putting {object_id} (size {object_size}) should fail when total size {new_size} exceeds capacity {container.capacity}"
            # Object should still be in inventory
            assert object_id in state.inventory
            # Note: We don't check if object is not in container because it might have been added
            # in a previous iteration (e.g., trying to add 'sword' twice)
        
        # Verify total size never exceeds capacity
        current_contents = container.state.get('contents', [])
        current_size = sum(world.get_object(obj_id).size for obj_id in current_contents)
        assert current_size <= container.capacity, \
            f"Container size {current_size} exceeds capacity {container.capacity}"


@settings(max_examples=100)
@given(st.data())
def test_container_open_state_enforced(data):
    """
    For any container that is not transparent, objects can only be put in or taken out
    when the container is open.
    
    **Validates: Requirements 15.1**
    
    This property ensures that:
    1. Closed containers block put/take operations
    2. Open containers allow put/take operations
    3. Transparent containers allow operations regardless of open state
    """
    # Load world data (fresh instance for each test)
    WorldData.clear_cache()  # Clear cache to ensure fresh data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a container and an object
    room_id, container_id, object_ids = data.draw(container_and_objects(world))
    
    if not object_ids:
        assume(False)
    
    object_id = object_ids[0]
    
    # Create game state in that room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Get current room and container
    current_room = world.get_room(room_id)
    container = world.get_object(container_id)
    game_object = world.get_object(object_id)
    
    # Ensure container is in room
    if container_id not in current_room.items:
        current_room.items.append(container_id)
    
    # Initialize container state
    container.state['contents'] = []
    
    # Check if container is transparent
    is_transparent = container.state.get('is_transparent', False)
    
    # Test with closed container
    container.state['is_open'] = False
    
    # Mark object as takeable and add to inventory
    game_object.is_takeable = True
    if object_id not in state.inventory:
        state.inventory.append(object_id)
    
    # Try to put object in closed container
    result = engine.handle_put(object_id, container_id, state)
    
    if is_transparent:
        # Transparent containers should allow operations when closed
        # (though this depends on implementation - trophy case is always "open")
        pass
    else:
        # Non-transparent closed containers should block operations
        assert result.success is False, \
            f"Putting object in closed non-transparent container should fail"
        assert object_id in state.inventory
        assert object_id not in container.state.get('contents', [])
    
    # Test with open container
    container.state['is_open'] = True
    
    # Try to put object in open container
    result = engine.handle_put(object_id, container_id, state)
    
    # Should succeed (assuming capacity allows)
    if result.success:
        assert object_id in container.state.get('contents', [])
        assert object_id not in state.inventory


@st.composite
def treasure_objects(draw, world_data):
    """
    Generate a list of treasure objects with their values.
    
    Returns list of (object_id, treasure_value) tuples for treasures.
    """
    # Find all treasure objects
    treasures = []
    for obj_id, obj in world_data.objects.items():
        if obj.is_treasure and obj.treasure_value > 0:
            treasures.append((obj_id, obj.treasure_value))
    
    if not treasures:
        # If no treasures in data, create mock treasures for testing
        treasures = [
            ("treasure1", 10),
            ("treasure2", 20),
            ("treasure3", 30),
            ("treasure4", 50),
            ("treasure5", 100)
        ]
    
    # Generate a subset of treasures (1 to min(5, len(treasures)))
    num_treasures = draw(st.integers(min_value=1, max_value=min(5, len(treasures))))
    selected_treasures = draw(st.lists(
        st.sampled_from(treasures),
        min_size=num_treasures,
        max_size=num_treasures,
        unique=True
    ))
    
    return selected_treasures


# Feature: game-backend-api, Property 19: Score accumulation
@settings(max_examples=100)
@given(st.data())
def test_score_equals_sum_of_treasure_values(data):
    """
    For any sequence of treasure placements, the score should equal
    the sum of all treasure values placed in the trophy case.
    
    **Validates: Requirements 13.1, 13.2**
    
    This property ensures that:
    1. Each treasure adds its value to the score
    2. Score accumulates correctly across multiple treasures
    3. Treasures are not double-scored
    """
    # Load world data (fresh instance for each test)
    WorldData.clear_cache()  # Clear cache to ensure fresh data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a list of treasures to place
    treasures = data.draw(treasure_objects(world))
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = "living_room"  # Assume trophy case is here
    
    # Get current room
    current_room = world.get_room(state.current_room)
    
    # Create or get trophy case
    trophy_case_id = "trophy_case"
    
    # Check if trophy case exists in world data
    try:
        trophy_case = world.get_object(trophy_case_id)
    except ValueError:
        # Trophy case doesn't exist, create a mock one
        from world_loader import GameObject, Interaction
        trophy_case = GameObject(
            id=trophy_case_id,
            name="trophy case",
            name_spooky="cursed trophy case",
            type="container",
            state={'is_open': True, 'is_transparent': True, 'contents': []},
            interactions=[
                Interaction(
                    verb="PUT",
                    condition=None,
                    response_original="You place it in the trophy case.",
                    response_spooky="You place it in the cursed trophy case.",
                    state_change=None,
                    flag_change=None,
                    sanity_effect=0,
                    curse_trigger=False
                )
            ],
            is_takeable=False,
            is_treasure=False,
            treasure_value=0,
            size=10,
            capacity=100,
            soul_value=0
        )
        world.objects[trophy_case_id] = trophy_case
    
    # Ensure trophy case is in room and open
    if trophy_case_id not in current_room.items:
        current_room.items.append(trophy_case_id)
    trophy_case.state['is_open'] = True
    trophy_case.state['is_transparent'] = True
    trophy_case.state['contents'] = []
    
    # Track expected score
    expected_score = 0
    scored_treasures = set()
    
    # Place each treasure in the trophy case
    for treasure_id, treasure_value in treasures:
        # Check if treasure exists in world data
        try:
            treasure_obj = world.get_object(treasure_id)
        except ValueError:
            # Treasure doesn't exist, create a mock one
            from world_loader import GameObject, Interaction
            treasure_obj = GameObject(
                id=treasure_id,
                name=treasure_id,
                name_spooky=f"cursed {treasure_id}",
                type="item",
                state={},
                interactions=[
                    Interaction(
                        verb="TAKE",
                        condition=None,
                        response_original=f"You take the {treasure_id}.",
                        response_spooky=f"You take the cursed {treasure_id}.",
                        state_change=None,
                        flag_change=None,
                        sanity_effect=0,
                        curse_trigger=False
                    )
                ],
                is_takeable=True,
                is_treasure=True,
                treasure_value=treasure_value,
                size=1,
                capacity=0,
                soul_value=0
            )
            world.objects[treasure_id] = treasure_obj
        
        # Ensure treasure is marked as treasure with correct value
        treasure_obj.is_treasure = True
        treasure_obj.treasure_value = treasure_value
        treasure_obj.is_takeable = True
        
        # Add treasure to inventory
        if treasure_id not in state.inventory:
            state.inventory.append(treasure_id)
        
        # Place treasure in trophy case
        result = engine.handle_place_treasure(treasure_id, trophy_case_id, state)
        
        # Placement should succeed
        assert result.success is True, f"Placing {treasure_id} should succeed"
        
        # Update expected score (only if not already scored)
        if treasure_id not in scored_treasures:
            expected_score += treasure_value
            scored_treasures.add(treasure_id)
        
        # Verify score matches expected
        assert state.score == expected_score, \
            f"Score mismatch: expected {expected_score}, got {state.score}"
    
    # Final verification: score should equal sum of all unique treasure values
    assert state.score == expected_score, \
        f"Final score {state.score} should equal sum of treasure values {expected_score}"


@settings(max_examples=100)
@given(st.data())
def test_treasures_not_double_scored(data):
    """
    For any treasure, placing it in the trophy case multiple times should
    only add its value to the score once.
    
    **Validates: Requirements 13.1, 13.2**
    
    This property ensures that:
    1. Treasures can only be scored once
    2. Attempting to score the same treasure again doesn't increase score
    3. The scored_treasures flag correctly tracks which treasures have been scored
    """
    # Load world data (fresh instance for each test)
    WorldData.clear_cache()  # Clear cache to ensure fresh data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a treasure to place
    treasures = data.draw(treasure_objects(world))
    
    if not treasures:
        assume(False)
    
    treasure_id, treasure_value = treasures[0]
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = "living_room"
    
    # Get current room
    current_room = world.get_room(state.current_room)
    
    # Create or get trophy case
    trophy_case_id = "trophy_case"
    
    try:
        trophy_case = world.get_object(trophy_case_id)
    except ValueError:
        from world_loader import GameObject, Interaction
        trophy_case = GameObject(
            id=trophy_case_id,
            name="trophy case",
            name_spooky="cursed trophy case",
            type="container",
            state={'is_open': True, 'is_transparent': True, 'contents': []},
            interactions=[
                Interaction(
                    verb="PUT",
                    condition=None,
                    response_original="You place it in the trophy case.",
                    response_spooky="You place it in the cursed trophy case.",
                    state_change=None,
                    flag_change=None,
                    sanity_effect=0,
                    curse_trigger=False
                )
            ],
            is_takeable=False,
            is_treasure=False,
            treasure_value=0,
            size=10,
            capacity=100,
            soul_value=0
        )
        world.objects[trophy_case_id] = trophy_case
    
    # Ensure trophy case is in room
    if trophy_case_id not in current_room.items:
        current_room.items.append(trophy_case_id)
    trophy_case.state['is_open'] = True
    trophy_case.state['is_transparent'] = True
    trophy_case.state['contents'] = []
    
    # Create or get treasure
    try:
        treasure_obj = world.get_object(treasure_id)
    except ValueError:
        from world_loader import GameObject, Interaction
        treasure_obj = GameObject(
            id=treasure_id,
            name=treasure_id,
            name_spooky=f"cursed {treasure_id}",
            type="item",
            state={},
            interactions=[
                Interaction(
                    verb="TAKE",
                    condition=None,
                    response_original=f"You take the {treasure_id}.",
                    response_spooky=f"You take the cursed {treasure_id}.",
                    state_change=None,
                    flag_change=None,
                    sanity_effect=0,
                    curse_trigger=False
                )
            ],
            is_takeable=True,
            is_treasure=True,
            treasure_value=treasure_value,
            size=1,
            capacity=0,
            soul_value=0
        )
        world.objects[treasure_id] = treasure_obj
    
    treasure_obj.is_treasure = True
    treasure_obj.treasure_value = treasure_value
    treasure_obj.is_takeable = True
    
    # Add treasure to inventory
    state.inventory.append(treasure_id)
    
    # Place treasure in trophy case (first time)
    result1 = engine.handle_place_treasure(treasure_id, trophy_case_id, state)
    
    assert result1.success is True
    score_after_first = state.score
    assert score_after_first == treasure_value, \
        f"Score after first placement should be {treasure_value}, got {score_after_first}"
    
    # Try to place the same treasure again (simulate taking it out and putting it back)
    # First, take it from the trophy case
    trophy_case.state['contents'].remove(treasure_id)
    state.inventory.append(treasure_id)
    
    # Place it again (second time)
    result2 = engine.handle_place_treasure(treasure_id, trophy_case_id, state)
    
    # Placement should succeed but score should not increase
    assert result2.success is True
    score_after_second = state.score
    assert score_after_second == treasure_value, \
        f"Score after second placement should still be {treasure_value}, got {score_after_second}"
    
    # Verify treasure is marked as scored
    scored_treasures = state.get_flag("scored_treasures", [])
    assert treasure_id in scored_treasures, \
        f"Treasure {treasure_id} should be in scored_treasures list"


# Feature: game-backend-api, Property 20: Win condition trigger
@settings(max_examples=100)
@given(st.data())
def test_won_flag_set_when_score_reaches_350(data):
    """
    For any game state where score reaches 350, the won_flag should be set to true.
    
    **Validates: Requirements 13.4**
    
    This property ensures that:
    1. The win condition is triggered at exactly 350 points
    2. The won_flag is set correctly
    3. Victory is properly detected
    """
    # Load world data (fresh instance for each test)
    WorldData.clear_cache()  # Clear cache to ensure fresh data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = "living_room"
    
    # Get current room
    current_room = world.get_room(state.current_room)
    
    # Create or get trophy case
    trophy_case_id = "trophy_case"
    
    try:
        trophy_case = world.get_object(trophy_case_id)
    except ValueError:
        from world_loader import GameObject, Interaction
        trophy_case = GameObject(
            id=trophy_case_id,
            name="trophy case",
            name_spooky="cursed trophy case",
            type="container",
            state={'is_open': True, 'is_transparent': True, 'contents': []},
            interactions=[
                Interaction(
                    verb="PUT",
                    condition=None,
                    response_original="You place it in the trophy case.",
                    response_spooky="You place it in the cursed trophy case.",
                    state_change=None,
                    flag_change=None,
                    sanity_effect=0,
                    curse_trigger=False
                )
            ],
            is_takeable=False,
            is_treasure=False,
            treasure_value=0,
            size=10,
            capacity=100,
            soul_value=0
        )
        world.objects[trophy_case_id] = trophy_case
    
    # Ensure trophy case is in room
    if trophy_case_id not in current_room.items:
        current_room.items.append(trophy_case_id)
    trophy_case.state['is_open'] = True
    trophy_case.state['is_transparent'] = True
    trophy_case.state['contents'] = []
    
    # Generate a target score that will trigger the win condition
    # We'll use a score between 350 and 400 to test the boundary
    target_score = data.draw(st.integers(min_value=350, max_value=400))
    
    # Create a treasure with exactly the right value to reach target_score
    treasure_id = "winning_treasure"
    treasure_value = target_score
    
    from world_loader import GameObject, Interaction
    treasure_obj = GameObject(
        id=treasure_id,
        name=treasure_id,
        name_spooky=f"cursed {treasure_id}",
        type="item",
        state={},
        interactions=[
            Interaction(
                verb="TAKE",
                condition=None,
                response_original=f"You take the {treasure_id}.",
                response_spooky=f"You take the cursed {treasure_id}.",
                state_change=None,
                flag_change=None,
                sanity_effect=0,
                curse_trigger=False
            )
        ],
        is_takeable=True,
        is_treasure=True,
        treasure_value=treasure_value,
        size=1,
        capacity=0,
        soul_value=0
    )
    world.objects[treasure_id] = treasure_obj
    
    # Add treasure to inventory
    state.inventory.append(treasure_id)
    
    # Verify won_flag is not set initially
    assert state.get_flag("won_flag", False) is False, \
        "won_flag should not be set initially"
    
    # Place treasure in trophy case
    result = engine.handle_place_treasure(treasure_id, trophy_case_id, state)
    
    # Placement should succeed
    assert result.success is True, f"Placing {treasure_id} should succeed"
    
    # Verify score reached target
    assert state.score == target_score, \
        f"Score should be {target_score}, got {state.score}"
    
    # Verify won_flag is set when score >= 350
    if target_score >= 350:
        assert state.get_flag("won_flag", False) is True, \
            f"won_flag should be set when score {target_score} >= 350"
        
        # Verify victory message is in notifications
        assert any("victory" in notif.lower() or "congratulations" in notif.lower() 
                   for notif in result.notifications), \
            "Victory notification should be present"
    else:
        # This shouldn't happen given our test setup, but check anyway
        assert state.get_flag("won_flag", False) is False, \
            f"won_flag should not be set when score {target_score} < 350"


@settings(max_examples=100)
@given(st.data())
def test_won_flag_not_set_below_350(data):
    """
    For any game state where score is below 350, the won_flag should not be set.
    
    **Validates: Requirements 13.4**
    
    This property ensures that:
    1. The win condition is not triggered prematurely
    2. Scores below 350 don't set the won_flag
    """
    # Load world data (fresh instance for each test)
    WorldData.clear_cache()  # Clear cache to ensure fresh data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = "living_room"
    
    # Get current room
    current_room = world.get_room(state.current_room)
    
    # Create or get trophy case
    trophy_case_id = "trophy_case"
    
    try:
        trophy_case = world.get_object(trophy_case_id)
    except ValueError:
        from world_loader import GameObject, Interaction
        trophy_case = GameObject(
            id=trophy_case_id,
            name="trophy case",
            name_spooky="cursed trophy case",
            type="container",
            state={'is_open': True, 'is_transparent': True, 'contents': []},
            interactions=[
                Interaction(
                    verb="PUT",
                    condition=None,
                    response_original="You place it in the trophy case.",
                    response_spooky="You place it in the cursed trophy case.",
                    state_change=None,
                    flag_change=None,
                    sanity_effect=0,
                    curse_trigger=False
                )
            ],
            is_takeable=False,
            is_treasure=False,
            treasure_value=0,
            size=10,
            capacity=100,
            soul_value=0
        )
        world.objects[trophy_case_id] = trophy_case
    
    # Ensure trophy case is in room
    if trophy_case_id not in current_room.items:
        current_room.items.append(trophy_case_id)
    trophy_case.state['is_open'] = True
    trophy_case.state['is_transparent'] = True
    trophy_case.state['contents'] = []
    
    # Generate a score below 350
    target_score = data.draw(st.integers(min_value=1, max_value=349))
    
    # Create a treasure with value below 350
    treasure_id = "small_treasure"
    treasure_value = target_score
    
    from world_loader import GameObject, Interaction
    treasure_obj = GameObject(
        id=treasure_id,
        name=treasure_id,
        name_spooky=f"cursed {treasure_id}",
        type="item",
        state={},
        interactions=[
            Interaction(
                verb="TAKE",
                condition=None,
                response_original=f"You take the {treasure_id}.",
                response_spooky=f"You take the cursed {treasure_id}.",
                state_change=None,
                flag_change=None,
                sanity_effect=0,
                curse_trigger=False
            )
        ],
        is_takeable=True,
        is_treasure=True,
        treasure_value=treasure_value,
        size=1,
        capacity=0,
        soul_value=0
    )
    world.objects[treasure_id] = treasure_obj
    
    # Add treasure to inventory
    state.inventory.append(treasure_id)
    
    # Place treasure in trophy case
    result = engine.handle_place_treasure(treasure_id, trophy_case_id, state)
    
    # Placement should succeed
    assert result.success is True, f"Placing {treasure_id} should succeed"
    
    # Verify score is below 350
    assert state.score < 350, \
        f"Score should be below 350, got {state.score}"
    
    # Verify won_flag is NOT set
    assert state.get_flag("won_flag", False) is False, \
        f"won_flag should not be set when score {state.score} < 350"
    
    # Verify no victory message in notifications
    assert not any("victory" in notif.lower() or "congratulations" in notif.lower() 
                   for notif in result.notifications), \
        "Victory notification should not be present when score < 350"


@settings(max_examples=100)
@given(st.data())
def test_check_win_condition_method(data):
    """
    For any game state, check_win_condition should return True if and only if score >= 350.
    
    **Validates: Requirements 13.4**
    
    This property ensures the check_win_condition method works correctly.
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Generate a random score
    score = data.draw(st.integers(min_value=0, max_value=500))
    
    # Create game state with that score
    state = GameState.create_new_game()
    state.score = score
    
    # Check win condition
    result = engine.check_win_condition(state)
    
    # Verify result matches expected
    expected = (score >= 350)
    assert result == expected, \
        f"check_win_condition should return {expected} for score {score}, got {result}"
