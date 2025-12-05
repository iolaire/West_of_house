"""
Property-Based Tests for BOARD and DISEMBARK Commands

Tests correctness properties related to the BOARD and DISEMBARK commands,
ensuring round-trip consistency and proper state updates.
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
def vehicle_scenario(draw, world_data):
    """
    Generate a valid room with a vehicle object.
    
    Creates a test vehicle and places it in a random room.
    Returns tuple of (room_id, vehicle_id, vehicle_object).
    """
    # Get all room IDs
    room_ids = list(world_data.rooms.keys())
    room_id = draw(st.sampled_from(room_ids))
    
    # Generate vehicle properties
    vehicle_names = ["boat", "basket", "raft", "canoe", "carriage"]
    vehicle_id = draw(st.sampled_from(vehicle_names))
    
    # Create a vehicle object
    vehicle = GameObject(
        id=vehicle_id,
        name=vehicle_id,
        name_spooky=f"ghostly {vehicle_id}",
        type="vehicle",
        is_takeable=False,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={"is_vehicle": True, "requires_water": False},
        interactions=[]
    )
    
    return (room_id, vehicle_id, vehicle)


@st.composite
def water_vehicle_scenario(draw, world_data):
    """
    Generate a room with water and a water-requiring vehicle.
    
    Returns tuple of (room_id, vehicle_id, vehicle_object).
    """
    # Get all room IDs
    room_ids = list(world_data.rooms.keys())
    room_id = draw(st.sampled_from(room_ids))
    
    # Generate water vehicle
    vehicle_names = ["boat", "raft", "canoe"]
    vehicle_id = draw(st.sampled_from(vehicle_names))
    
    # Create a water vehicle
    vehicle = GameObject(
        id=vehicle_id,
        name=vehicle_id,
        name_spooky=f"ghostly {vehicle_id}",
        type="vehicle",
        is_takeable=False,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={"is_vehicle": True, "requires_water": True},
        interactions=[]
    )
    
    return (room_id, vehicle_id, vehicle)


# Feature: complete-zork-commands, Property 3: Board/Disembark inverse operations
@settings(max_examples=100)
@given(st.data())
def test_board_disembark_round_trip(data):
    """
    For any vehicle object, boarding then immediately disembarking should
    return the player to the original location (round-trip property).
    
    **Validates: Requirements 2.3, 2.4**
    
    This property ensures that:
    1. BOARD places player in vehicle
    2. DISEMBARK removes player from vehicle
    3. Round-trip preserves vehicle state consistency
    4. Game state is updated correctly
    """
    # Load world data (fresh instance for each test)
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid vehicle scenario
    room_id, vehicle_id, vehicle = data.draw(vehicle_scenario(world))
    
    # Add vehicle to world data
    world.objects[vehicle_id] = vehicle
    
    # Create game state in the room with the vehicle
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add vehicle to room
    room = world.get_room(room_id)
    if vehicle_id not in room.items:
        room.items.append(vehicle_id)
    
    # Original state: not in any vehicle
    original_vehicle = state.current_vehicle
    assert original_vehicle is None, "Should start with no vehicle"
    
    # Board the vehicle
    board_result = engine.handle_board(vehicle_id, state)
    
    # Board should succeed
    assert board_result.success is True, \
        f"Boarding {vehicle_id} should succeed"
    
    # Should now be in the vehicle
    assert state.current_vehicle == vehicle_id, \
        f"current_vehicle should be {vehicle_id}, got {state.current_vehicle}"
    
    # Board result should not change room
    assert board_result.room_changed is False, \
        "room_changed should be False after boarding"
    
    # Disembark from the vehicle
    disembark_result = engine.handle_disembark(None, state)
    
    # Disembark should succeed
    assert disembark_result.success is True, \
        f"Disembarking from {vehicle_id} should succeed"
    
    # Should be back to original state (not in vehicle)
    assert state.current_vehicle == original_vehicle, \
        f"Round-trip should return to original vehicle state (None), got {state.current_vehicle}"
    
    # Disembark result should not change room
    assert disembark_result.room_changed is False, \
        "room_changed should be False after disembarking"
    
    # Both operations should return messages
    assert board_result.message is not None and len(board_result.message) > 0, \
        "Board result should contain a message"
    assert disembark_result.message is not None and len(disembark_result.message) > 0, \
        "Disembark result should contain a message"
    
    # Messages should mention the vehicle
    assert vehicle_id in board_result.message.lower(), \
        f"Board message should mention {vehicle_id}"
    assert vehicle_id in disembark_result.message.lower(), \
        f"Disembark message should mention {vehicle_id}"


@settings(max_examples=100)
@given(st.data())
def test_board_disembark_specific_vehicle_round_trip(data):
    """
    For any vehicle, boarding then disembarking with specific vehicle name
    should return to original state.
    
    **Validates: Requirements 2.3, 2.4**
    
    This property ensures that disembarking with a specific vehicle name works correctly.
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid vehicle scenario
    room_id, vehicle_id, vehicle = data.draw(vehicle_scenario(world))
    
    # Add vehicle to world data
    world.objects[vehicle_id] = vehicle
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add vehicle to room
    room = world.get_room(room_id)
    if vehicle_id not in room.items:
        room.items.append(vehicle_id)
    
    # Original state
    original_vehicle = state.current_vehicle
    assert original_vehicle is None
    
    # Board
    board_result = engine.handle_board(vehicle_id, state)
    assert board_result.success is True
    assert state.current_vehicle == vehicle_id
    
    # Disembark with specific vehicle name
    disembark_result = engine.handle_disembark(vehicle_id, state)
    assert disembark_result.success is True
    assert state.current_vehicle == original_vehicle


@settings(max_examples=100)
@given(st.data())
def test_board_fails_when_already_in_vehicle(data):
    """
    For any vehicle, attempting to board while already in a vehicle should fail.
    
    **Validates: Requirements 2.3**
    
    This property ensures that:
    1. Cannot board a second vehicle while in first vehicle
    2. State remains unchanged on failed board
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get two vehicle scenarios
    room_id, vehicle1_id, vehicle1 = data.draw(vehicle_scenario(world))
    _, vehicle2_id, vehicle2 = data.draw(vehicle_scenario(world))
    
    # Ensure different vehicles
    assume(vehicle1_id != vehicle2_id)
    
    # Add vehicles to world data
    world.objects[vehicle1_id] = vehicle1
    world.objects[vehicle2_id] = vehicle2
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add both vehicles to room
    room = world.get_room(room_id)
    if vehicle1_id not in room.items:
        room.items.append(vehicle1_id)
    if vehicle2_id not in room.items:
        room.items.append(vehicle2_id)
    
    # Board first vehicle
    board_result1 = engine.handle_board(vehicle1_id, state)
    assert board_result1.success is True
    assert state.current_vehicle == vehicle1_id
    
    # Attempt to board second vehicle
    board_result2 = engine.handle_board(vehicle2_id, state)
    
    # Should fail
    assert board_result2.success is False, \
        "Boarding second vehicle while in first should fail"
    
    # State should remain unchanged
    assert state.current_vehicle == vehicle1_id, \
        f"current_vehicle should remain {vehicle1_id}, got {state.current_vehicle}"
    
    # Error message should indicate already in vehicle
    assert "already in" in board_result2.message.lower(), \
        "Error message should indicate already in a vehicle"


@settings(max_examples=100)
@given(st.data())
def test_disembark_fails_when_not_in_vehicle(data):
    """
    For any state where player is not in a vehicle, disembark should fail.
    
    **Validates: Requirements 2.4**
    
    This property ensures that:
    1. Cannot disembark when not in a vehicle
    2. State remains unchanged
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get all room IDs
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    # Create game state not in any vehicle
    state = GameState.create_new_game()
    state.current_room = room_id
    state.current_vehicle = None
    
    # Attempt to disembark
    result = engine.handle_disembark(None, state)
    
    # Should fail
    assert result.success is False, \
        "Disembarking when not in vehicle should fail"
    
    # State should remain unchanged
    assert state.current_vehicle is None, \
        "current_vehicle should remain None"
    
    # Error message should indicate not in vehicle
    assert "not in any vehicle" in result.message.lower(), \
        "Error message should indicate not in any vehicle"


@settings(max_examples=100)
@given(st.data())
def test_disembark_fails_for_wrong_vehicle(data):
    """
    For any vehicle, attempting to disembark from a different vehicle should fail.
    
    **Validates: Requirements 2.4**
    
    This property ensures that:
    1. Cannot disembark from vehicle you're not in
    2. State remains unchanged
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get two different vehicle names
    vehicle_names = ["boat", "basket", "raft", "canoe", "carriage"]
    vehicle1_id = data.draw(st.sampled_from(vehicle_names))
    vehicle2_id = data.draw(st.sampled_from(vehicle_names))
    
    # Ensure different vehicles
    assume(vehicle1_id != vehicle2_id)
    
    # Get a room
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    # Create game state in vehicle1
    state = GameState.create_new_game()
    state.current_room = room_id
    state.current_vehicle = vehicle1_id
    
    # Attempt to disembark from vehicle2
    result = engine.handle_disembark(vehicle2_id, state)
    
    # Should fail
    assert result.success is False, \
        f"Disembarking from {vehicle2_id} when in {vehicle1_id} should fail"
    
    # State should remain unchanged
    assert state.current_vehicle == vehicle1_id, \
        f"current_vehicle should remain {vehicle1_id}, got {state.current_vehicle}"
    
    # Error message should indicate wrong vehicle
    assert "not in the" in result.message.lower(), \
        "Error message should indicate not in the specified vehicle"


@settings(max_examples=100)
@given(st.data())
def test_board_fails_for_non_vehicle_object(data):
    """
    For any non-vehicle object, attempting to board should fail.
    
    **Validates: Requirements 2.3**
    
    This property ensures that:
    1. Only objects marked as vehicles can be boarded
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
    
    # Find a non-vehicle object in the room
    non_vehicle_objects = []
    for item_id in room.items:
        try:
            obj = world.get_object(item_id)
            if not obj.state.get('is_vehicle', False):
                non_vehicle_objects.append(item_id)
        except ValueError:
            continue
    
    # Skip if no non-vehicle objects
    if not non_vehicle_objects:
        assume(False)
    
    object_id = data.draw(st.sampled_from(non_vehicle_objects))
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    original_vehicle = state.current_vehicle
    
    # Attempt to board non-vehicle object
    result = engine.handle_board(object_id, state)
    
    # Should fail
    assert result.success is False, \
        f"Boarding non-vehicle object {object_id} should fail"
    
    # State should remain unchanged
    assert state.current_vehicle == original_vehicle, \
        "current_vehicle should remain unchanged"
    
    # Error message should indicate can't board
    assert "can't board" in result.message.lower(), \
        "Error message should indicate object cannot be boarded"


@settings(max_examples=100)
@given(st.data())
def test_board_fails_for_absent_vehicle(data):
    """
    For any vehicle not in the current room, boarding should fail.
    
    **Validates: Requirements 2.3**
    
    This property ensures that:
    1. Can only board vehicles that are present
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
    original_vehicle = state.current_vehicle
    
    # Use a vehicle ID that doesn't exist in the room
    absent_vehicle_id = "nonexistent_vehicle_xyz"
    
    # Attempt to board absent vehicle
    result = engine.handle_board(absent_vehicle_id, state)
    
    # Should fail
    assert result.success is False, \
        "Boarding absent vehicle should fail"
    
    # State should remain unchanged
    assert state.current_vehicle == original_vehicle, \
        "current_vehicle should remain unchanged"
    
    # Error message should indicate vehicle not present
    assert "don't see" in result.message.lower(), \
        "Error message should indicate vehicle is not present"


@settings(max_examples=100)
@given(st.data())
def test_board_state_unchanged_on_failure(data):
    """
    For any failed board operation, game state should remain unchanged.
    
    **Validates: Requirements 2.3**
    
    This property ensures that:
    1. Failed board operations don't modify state
    2. current_vehicle remains None
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
    original_vehicle = state.current_vehicle
    original_room = state.current_room
    
    # Attempt to board a non-existent vehicle
    result = engine.handle_board("nonexistent_vehicle", state)
    
    # Should fail
    assert result.success is False, \
        "Boarding non-existent vehicle should fail"
    
    # State should remain unchanged
    assert state.current_vehicle == original_vehicle, \
        "current_vehicle should remain unchanged"
    assert state.current_room == original_room, \
        "current_room should remain unchanged"
    
    # Error message should be returned
    assert result.message is not None and len(result.message) > 0, \
        "Error message should be returned"


@settings(max_examples=100)
@given(st.data())
def test_board_returns_message(data):
    """
    For any successful board operation, a message should be returned.
    
    **Validates: Requirements 2.3**
    
    This property ensures that players receive appropriate feedback after boarding.
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid vehicle scenario
    room_id, vehicle_id, vehicle = data.draw(vehicle_scenario(world))
    
    # Add vehicle to world data
    world.objects[vehicle_id] = vehicle
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add vehicle to room
    room = world.get_room(room_id)
    if vehicle_id not in room.items:
        room.items.append(vehicle_id)
    
    # Board
    result = engine.handle_board(vehicle_id, state)
    
    if result.success:
        # Result should contain a message
        assert result.message is not None, \
            "Result message should not be None"
        assert len(result.message) > 0, \
            "Result message should not be empty"
        
        # Message should mention the vehicle
        assert vehicle_id in result.message.lower(), \
            f"Result message should mention {vehicle_id}"


@settings(max_examples=100)
@given(st.data())
def test_disembark_returns_message(data):
    """
    For any successful disembark operation, a message should be returned.
    
    **Validates: Requirements 2.4**
    
    This property ensures that players receive appropriate feedback after disembarking.
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid vehicle scenario
    room_id, vehicle_id, vehicle = data.draw(vehicle_scenario(world))
    
    # Add vehicle to world data
    world.objects[vehicle_id] = vehicle
    
    # Create game state in vehicle
    state = GameState.create_new_game()
    state.current_room = room_id
    state.current_vehicle = vehicle_id
    
    # Disembark
    result = engine.handle_disembark(None, state)
    
    if result.success:
        # Result should contain a message
        assert result.message is not None, \
            "Result message should not be None"
        assert len(result.message) > 0, \
            "Result message should not be empty"
        
        # Message should mention the vehicle
        assert vehicle_id in result.message.lower(), \
            f"Result message should mention {vehicle_id}"
