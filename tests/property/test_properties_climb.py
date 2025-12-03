"""
Property-Based Tests for CLIMB Command

Tests correctness properties related to the CLIMB command,
ensuring movement consistency and proper state updates.
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
def valid_climb_scenario(draw, world_data):
    """
    Generate a valid room ID and climb direction (UP or DOWN) where the exit exists.
    
    Returns tuple of (room_id, direction, target_room_id) where the climb is valid.
    """
    # Get all room IDs
    room_ids = list(world_data.rooms.keys())
    
    # Pick a random room
    room_id = draw(st.sampled_from(room_ids))
    room = world_data.get_room(room_id)
    
    # Check if room has UP or DOWN exits
    climbable_directions = []
    if 'UP' in room.exits:
        climbable_directions.append('UP')
    if 'DOWN' in room.exits:
        climbable_directions.append('DOWN')
    
    # If room has climbable exits, pick one
    if climbable_directions:
        direction = draw(st.sampled_from(climbable_directions))
        target_room_id = room.exits[direction]
        return (room_id, direction, target_room_id)
    else:
        # Room has no climbable exits, skip this example
        assume(False)


@st.composite
def invalid_climb_scenario(draw, world_data):
    """
    Generate a room ID and an invalid climb direction (UP or DOWN that doesn't exist).
    
    Returns tuple of (room_id, invalid_direction).
    """
    # Get all room IDs
    room_ids = list(world_data.rooms.keys())
    
    # Pick a random room
    room_id = draw(st.sampled_from(room_ids))
    room = world_data.get_room(room_id)
    
    # Find directions that are NOT exits from this room
    invalid_directions = []
    if 'UP' not in room.exits:
        invalid_directions.append('UP')
    if 'DOWN' not in room.exits:
        invalid_directions.append('DOWN')
    
    # If there are invalid climb directions, pick one
    if invalid_directions:
        invalid_direction = draw(st.sampled_from(invalid_directions))
        return (room_id, invalid_direction)
    else:
        # This room has both UP and DOWN exits (unlikely), skip this example
        assume(False)


# Feature: complete-zork-commands, Property 1: Climb movement consistency
@settings(max_examples=100)
@given(st.data())
def test_climb_movement_consistency(data):
    """
    For any climbable object and valid direction (UP/DOWN), executing CLIMB should
    result in the player moving to the connected room in that direction.
    
    **Validates: Requirements 2.1**
    
    This property ensures that:
    1. Valid climb commands succeed
    2. Player moves to the correct target room
    3. Game state is updated correctly (room changed, counters incremented)
    4. Room description is returned
    """
    # Load world data (fresh instance for each test)
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid climb scenario
    room_id, direction, target_room_id = data.draw(valid_climb_scenario(world))
    
    # Create game state in the starting room
    state = GameState.create_new_game()
    state.current_room = room_id
    initial_moves = state.moves
    initial_turns = state.turn_count
    
    # Attempt climb
    result = engine.handle_climb(direction, None, state)
    
    # Climb should succeed
    assert result.success is True, \
        f"Climbing {direction} from {room_id} should succeed"
    
    # Room should have changed
    assert result.room_changed is True, \
        f"room_changed should be True after successful climb"
    
    # New room should be the target room
    assert result.new_room == target_room_id, \
        f"new_room should be {target_room_id}, got {result.new_room}"
    
    # Current room in state should be updated
    assert state.current_room == target_room_id, \
        f"current_room should be {target_room_id}, got {state.current_room}"
    
    # Target room should be in visited rooms
    assert target_room_id in state.rooms_visited, \
        f"Target room {target_room_id} should be in rooms_visited"
    
    # Counters should increment
    assert state.moves == initial_moves + 1, \
        f"moves should increment from {initial_moves} to {initial_moves + 1}, got {state.moves}"
    assert state.turn_count == initial_turns + 1, \
        f"turn_count should increment from {initial_turns} to {initial_turns + 1}, got {state.turn_count}"
    
    # Result should contain a description
    assert result.message is not None, \
        "Result message should not be None"
    assert len(result.message) > 0, \
        "Result message should not be empty"
    
    # Message should contain climb-related text
    assert "climb" in result.message.lower(), \
        "Result message should mention climbing"


@settings(max_examples=100)
@given(st.data())
def test_climb_fails_for_invalid_directions(data):
    """
    For any room and invalid climb direction, climb should fail and state should be unchanged.
    
    **Validates: Requirements 2.1**
    
    This property ensures that:
    1. Invalid climb directions are properly rejected
    2. Game state remains unchanged on failed climb
    3. Appropriate error messages are returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get an invalid climb scenario
    room_id, invalid_direction = data.draw(invalid_climb_scenario(world))
    
    # Create game state in the starting room
    state = GameState.create_new_game()
    state.current_room = room_id
    initial_room = state.current_room
    initial_moves = state.moves
    initial_turns = state.turn_count
    
    # Attempt climb in invalid direction
    result = engine.handle_climb(invalid_direction, None, state)
    
    # Climb should fail
    assert result.success is False, \
        f"Climbing {invalid_direction} from {room_id} should fail when no exit exists"
    
    # Room should not have changed
    assert result.room_changed is False, \
        "room_changed should be False after failed climb"
    
    # New room should be None
    assert result.new_room is None, \
        "new_room should be None after failed climb"
    
    # State should be unchanged
    assert state.current_room == initial_room, \
        f"current_room should remain {initial_room}, got {state.current_room}"
    assert state.moves == initial_moves, \
        f"moves should remain {initial_moves}, got {state.moves}"
    assert state.turn_count == initial_turns, \
        f"turn_count should remain {initial_turns}, got {state.turn_count}"
    
    # Error message should be returned
    assert result.message is not None, \
        "Result message should not be None"
    assert len(result.message) > 0, \
        "Result message should not be empty"


@settings(max_examples=100)
@given(st.data())
def test_climb_rejects_non_up_down_directions(data):
    """
    For any direction that is not UP or DOWN, climb should fail.
    
    **Validates: Requirements 2.1**
    
    This property ensures that:
    1. Only UP and DOWN are valid climb directions
    2. Other directions (NORTH, SOUTH, EAST, WEST, etc.) are rejected
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get all room IDs
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    # Pick a non-climb direction
    invalid_directions = ["NORTH", "SOUTH", "EAST", "WEST", "IN", "OUT", 
                          "NORTHEAST", "NORTHWEST", "SOUTHEAST", "SOUTHWEST"]
    invalid_direction = data.draw(st.sampled_from(invalid_directions))
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    initial_room = state.current_room
    
    # Attempt climb with invalid direction
    result = engine.handle_climb(invalid_direction, None, state)
    
    # Climb should fail
    assert result.success is False, \
        f"Climbing {invalid_direction} should fail (only UP/DOWN allowed)"
    
    # State should be unchanged
    assert state.current_room == initial_room, \
        "current_room should remain unchanged"
    
    # Error message should indicate direction restriction
    assert "up or down" in result.message.lower(), \
        "Error message should indicate only UP or DOWN are valid"


@settings(max_examples=100)
@given(st.data())
def test_climb_round_trip_returns_to_origin(data):
    """
    For any room with both UP and DOWN exits that connect to each other,
    climbing up then down (or down then up) should return to the original room.
    
    **Validates: Requirements 2.1**
    
    This property ensures that:
    1. Climb operations are reversible
    2. Round-trip climbing preserves location consistency
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Find rooms that have both UP and DOWN exits
    room_ids = list(world.rooms.keys())
    rooms_with_both = []
    
    for room_id in room_ids:
        room = world.get_room(room_id)
        if 'UP' in room.exits and 'DOWN' in room.exits:
            # Check if UP and DOWN are inverses
            up_room_id = room.exits['UP']
            up_room = world.get_room(up_room_id)
            if 'DOWN' in up_room.exits and up_room.exits['DOWN'] == room_id:
                rooms_with_both.append(room_id)
    
    # Skip if no rooms with round-trip climbing
    if not rooms_with_both:
        assume(False)
    
    # Pick a room with round-trip climbing
    room_id = data.draw(st.sampled_from(rooms_with_both))
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    original_room = room_id
    
    # Climb up
    result_up = engine.handle_climb('UP', None, state)
    assert result_up.success is True, "Climbing UP should succeed"
    
    intermediate_room = state.current_room
    assert intermediate_room != original_room, "Should have moved to a different room"
    
    # Climb back down
    result_down = engine.handle_climb('DOWN', None, state)
    assert result_down.success is True, "Climbing DOWN should succeed"
    
    # Should be back at original room
    assert state.current_room == original_room, \
        f"Round-trip climb should return to original room {original_room}, got {state.current_room}"
