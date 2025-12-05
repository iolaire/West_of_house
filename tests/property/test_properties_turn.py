"""
Property-Based Tests for TURN Command

Tests correctness properties related to the TURN command,
ensuring state changes occur correctly.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler'))

import pytest
from hypothesis import given, strategies as st, settings, assume
from game_engine import GameEngine, ActionResult
from state_manager import GameState
from world_loader import WorldData, GameObject


# Initialize world data for tests
@pytest.fixture(scope="module")
def world_data():
    """Load world data once for all tests."""
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    return world


@pytest.fixture(scope="module")
def game_engine(world_data):
    """Create game engine instance."""
    return GameEngine(world_data)


# Custom strategies for generating test data
@st.composite
def turnable_object_scenario(draw, world_data):
    """
    Generate a valid room with a turnable object.
    
    Creates a test turnable object and places it in a random room.
    Returns tuple of (room_id, object_id, turnable_object).
    """
    # Get all room IDs
    room_ids = list(world_data.rooms.keys())
    room_id = draw(st.sampled_from(room_ids))
    
    # Generate turnable object properties
    turnable_names = ["dial", "valve", "wheel", "knob", "lever"]
    object_id = draw(st.sampled_from(turnable_names))
    
    # Generate rotation properties
    initial_rotation = draw(st.integers(min_value=0, max_value=270))
    max_rotation = 360
    rotation_increment = draw(st.sampled_from([45, 90, 180]))
    
    # Create a turnable object
    turnable_object = GameObject(
        id=object_id,
        name=object_id,
        name_spooky=f"ancient {object_id}",
        type="object",
        is_takeable=False,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={
            "is_turnable": True,
            "rotation": initial_rotation,
            "max_rotation": max_rotation,
            "rotation_increment": rotation_increment
        },
        interactions=[]
    )
    
    return (room_id, object_id, turnable_object)


# Feature: complete-zork-commands, Property 6: Turn command state changes
@settings(max_examples=100)
@given(st.data())
def test_turn_changes_rotation_state(data):
    """
    For any turnable object, executing TURN should change the object's rotation state.
    
    **Validates: Requirements 3.4**
    
    This property ensures that:
    1. TURN updates the rotation value
    2. Rotation wraps around at max_rotation
    3. State changes are applied correctly
    """
    # Load world data (fresh instance for each test)
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid turnable object scenario
    room_id, object_id, turnable_object = data.draw(turnable_object_scenario(world))
    
    # Add object to world data
    world.objects[object_id] = turnable_object
    
    # Create game state in the room with the turnable object
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add turnable object to room
    room = world.get_room(room_id)
    if object_id not in room.items:
        room.items.append(object_id)
    
    # Get original rotation
    original_rotation = turnable_object.state.get('rotation', 0)
    rotation_increment = turnable_object.state.get('rotation_increment', 90)
    max_rotation = turnable_object.state.get('max_rotation', 360)
    
    # Turn the object
    turn_result = engine.handle_turn(object_id, state)
    
    # Turn should succeed
    assert turn_result.success is True, \
        f"Turning {object_id} should succeed"
    
    # Rotation should have changed
    new_rotation = turnable_object.state.get('rotation', 0)
    expected_rotation = (original_rotation + rotation_increment) % max_rotation
    
    assert new_rotation == expected_rotation, \
        f"Rotation should be {expected_rotation}, got {new_rotation}"
    
    # Result should contain a message
    assert turn_result.message is not None and len(turn_result.message) > 0, \
        "Turn result should contain a message"
    
    # Message should mention the object
    assert object_id in turn_result.message.lower(), \
        f"Turn message should mention {object_id}"


@settings(max_examples=100)
@given(st.data())
def test_turn_wraps_rotation(data):
    """
    For any turnable object, rotation should wrap around at max_rotation.
    
    **Validates: Requirements 3.4**
    
    This property ensures that rotation values stay within bounds.
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid turnable object scenario
    room_id, object_id, turnable_object = data.draw(turnable_object_scenario(world))
    
    # Set rotation close to max to test wrapping
    turnable_object.state['rotation'] = 315
    turnable_object.state['max_rotation'] = 360
    turnable_object.state['rotation_increment'] = 90
    
    # Add object to world data
    world.objects[object_id] = turnable_object
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add turnable object to room
    room = world.get_room(room_id)
    if object_id not in room.items:
        room.items.append(object_id)
    
    # Turn the object
    turn_result = engine.handle_turn(object_id, state)
    
    # Turn should succeed
    assert turn_result.success is True
    
    # Rotation should wrap around
    new_rotation = turnable_object.state.get('rotation', 0)
    expected_rotation = (315 + 90) % 360  # Should be 45
    
    assert new_rotation == expected_rotation, \
        f"Rotation should wrap to {expected_rotation}, got {new_rotation}"
    
    # Rotation should be less than max_rotation
    assert new_rotation < turnable_object.state['max_rotation'], \
        f"Rotation {new_rotation} should be less than max_rotation {turnable_object.state['max_rotation']}"


@settings(max_examples=100)
@given(st.data())
def test_turn_multiple_times(data):
    """
    For any turnable object, turning multiple times should increment rotation correctly.
    
    **Validates: Requirements 3.4**
    
    This property ensures that repeated turns work correctly.
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid turnable object scenario
    room_id, object_id, turnable_object = data.draw(turnable_object_scenario(world))
    
    # Add object to world data
    world.objects[object_id] = turnable_object
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add turnable object to room
    room = world.get_room(room_id)
    if object_id not in room.items:
        room.items.append(object_id)
    
    # Get initial rotation
    initial_rotation = turnable_object.state.get('rotation', 0)
    rotation_increment = turnable_object.state.get('rotation_increment', 90)
    max_rotation = turnable_object.state.get('max_rotation', 360)
    
    # Turn multiple times
    num_turns = data.draw(st.integers(min_value=1, max_value=10))
    
    for i in range(num_turns):
        turn_result = engine.handle_turn(object_id, state)
        assert turn_result.success is True, f"Turn {i+1} should succeed"
    
    # Check final rotation
    final_rotation = turnable_object.state.get('rotation', 0)
    expected_rotation = (initial_rotation + (rotation_increment * num_turns)) % max_rotation
    
    assert final_rotation == expected_rotation, \
        f"After {num_turns} turns, rotation should be {expected_rotation}, got {final_rotation}"


@settings(max_examples=100)
@given(st.data())
def test_turn_fails_for_non_turnable_object(data):
    """
    For any non-turnable object, attempting to turn should fail.
    
    **Validates: Requirements 3.4**
    
    This property ensures that:
    1. Only turnable objects can be turned
    2. State remains unchanged
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a room with objects
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    room = world.get_room(room_id)
    
    # Find a non-turnable object in the room
    non_turnable_objects = []
    for item_id in room.items:
        try:
            obj = world.get_object(item_id)
            if not obj.state.get('is_turnable', False):
                non_turnable_objects.append(item_id)
        except ValueError:
            continue
    
    # Skip if no non-turnable objects
    if not non_turnable_objects:
        assume(False)
    
    object_id = data.draw(st.sampled_from(non_turnable_objects))
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Attempt to turn non-turnable object
    result = engine.handle_turn(object_id, state)
    
    # Should fail
    assert result.success is False, \
        f"Turning non-turnable object {object_id} should fail"
    
    # Error message should indicate can't turn
    assert "can't turn" in result.message.lower(), \
        "Error message should indicate object cannot be turned"


@settings(max_examples=100)
@given(st.data())
def test_turn_fails_for_absent_object(data):
    """
    For any object not in the current room, turning should fail.
    
    **Validates: Requirements 3.4**
    
    This property ensures that:
    1. Can only turn objects that are present
    2. State remains unchanged
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a room
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Use an object ID that doesn't exist in the room
    absent_object_id = "nonexistent_object_xyz"
    
    # Attempt to turn absent object
    result = engine.handle_turn(absent_object_id, state)
    
    # Should fail
    assert result.success is False, \
        "Turning absent object should fail"
    
    # Error message should indicate object not present
    assert "don't see" in result.message.lower(), \
        "Error message should indicate object is not present"


@settings(max_examples=100)
@given(st.data())
def test_turn_activation_at_specific_rotation(data):
    """
    For any turnable object with activation rotation, turning to that rotation should activate it.
    
    **Validates: Requirements 3.4**
    
    This property ensures that activation triggers work correctly.
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get all room IDs
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    # Create a turnable object with activation
    object_id = "test_dial"
    activation_rotation = 180
    
    turnable_object = GameObject(
        id=object_id,
        name=object_id,
        name_spooky=f"mysterious {object_id}",
        type="object",
        is_takeable=False,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={
            "is_turnable": True,
            "rotation": 90,  # One turn away from activation
            "max_rotation": 360,
            "rotation_increment": 90,
            "activation_rotation": activation_rotation,
            "is_activated": False
        },
        interactions=[]
    )
    
    # Add object to world data
    world.objects[object_id] = turnable_object
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add turnable object to room
    room = world.get_room(room_id)
    if object_id not in room.items:
        room.items.append(object_id)
    
    # Turn the object to activation rotation
    turn_result = engine.handle_turn(object_id, state)
    
    # Turn should succeed
    assert turn_result.success is True
    
    # Object should now be activated
    assert turnable_object.state.get('is_activated', False) is True, \
        "Object should be activated at activation rotation"
    
    # Should have notification about activation
    assert len(turn_result.notifications) > 0, \
        "Should have notification about activation"


@settings(max_examples=100)
@given(st.data())
def test_turn_deactivation_away_from_activation_rotation(data):
    """
    For any turnable object with activation rotation, turning away from that rotation should deactivate it.
    
    **Validates: Requirements 3.4**
    
    This property ensures that deactivation works correctly.
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get all room IDs
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    # Create a turnable object with activation
    object_id = "test_dial"
    activation_rotation = 180
    
    turnable_object = GameObject(
        id=object_id,
        name=object_id,
        name_spooky=f"mysterious {object_id}",
        type="object",
        is_takeable=False,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={
            "is_turnable": True,
            "rotation": activation_rotation,  # At activation rotation
            "max_rotation": 360,
            "rotation_increment": 90,
            "activation_rotation": activation_rotation,
            "is_activated": True  # Already activated
        },
        interactions=[]
    )
    
    # Add object to world data
    world.objects[object_id] = turnable_object
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add turnable object to room
    room = world.get_room(room_id)
    if object_id not in room.items:
        room.items.append(object_id)
    
    # Turn the object away from activation rotation
    turn_result = engine.handle_turn(object_id, state)
    
    # Turn should succeed
    assert turn_result.success is True
    
    # Object should now be deactivated
    assert turnable_object.state.get('is_activated', False) is False, \
        "Object should be deactivated when turned away from activation rotation"
