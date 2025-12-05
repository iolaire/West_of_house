"""
Property-Based Tests for ENTER and EXIT Commands

Tests correctness properties related to the ENTER and EXIT commands,
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
from world_loader import WorldData


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
def valid_enter_exit_scenario(draw, world_data):
    """
    Generate a valid room with IN/OUT exits that form a round-trip.
    
    Returns tuple of (room_id, entry_room_id) where:
    - room_id has an IN exit to entry_room_id
    - entry_room_id has an OUT exit back to room_id
    - No flag requirements block the entrance
    """
    # Get all room IDs
    room_ids = list(world_data.rooms.keys())
    
    # Find rooms with IN exits
    rooms_with_in = []
    for room_id in room_ids:
        room = world_data.get_room(room_id)
        if 'IN' in room.exits:
            entry_room_id = room.exits['IN']
            
            # Skip east_of_house -> kitchen (requires kitchen_window_open flag)
            if room_id == 'east_of_house' and entry_room_id == 'kitchen':
                continue
            
            # Check if the entry room has an OUT exit back
            try:
                entry_room = world_data.get_room(entry_room_id)
                if 'OUT' in entry_room.exits and entry_room.exits['OUT'] == room_id:
                    rooms_with_in.append((room_id, entry_room_id))
            except ValueError:
                # Entry room doesn't exist, skip
                continue
    
    # If we found rooms with round-trip IN/OUT, pick one
    if rooms_with_in:
        return draw(st.sampled_from(rooms_with_in))
    else:
        # No rooms with round-trip IN/OUT, skip this example
        assume(False)


@st.composite
def enterable_object_scenario(draw, world_data):
    """
    Generate a room with an enterable object that has entry and exit destinations.
    
    Returns tuple of (room_id, object_id, entry_destination, exit_destination).
    """
    # Get all room IDs
    room_ids = list(world_data.rooms.keys())
    
    # Find rooms with enterable objects
    valid_scenarios = []
    for room_id in room_ids:
        room = world_data.get_room(room_id)
        for item_id in room.items:
            try:
                obj = world_data.get_object(item_id)
                if obj.state.get('is_enterable', False):
                    entry_dest = obj.state.get('entry_destination')
                    exit_dest = obj.state.get('exit_destination')
                    if entry_dest and exit_dest:
                        # Verify destinations exist
                        try:
                            world_data.get_room(entry_dest)
                            world_data.get_room(exit_dest)
                            valid_scenarios.append((room_id, item_id, entry_dest, exit_dest))
                        except ValueError:
                            continue
            except ValueError:
                continue
    
    # If we found enterable objects, pick one
    if valid_scenarios:
        return draw(st.sampled_from(valid_scenarios))
    else:
        # No enterable objects found, skip this example
        assume(False)


# Feature: complete-zork-commands, Property 2: Enter/Exit inverse operations
@settings(max_examples=100)
@given(st.data())
def test_enter_exit_round_trip_with_in_out(data):
    """
    For any room with an entrance, entering then immediately exiting should
    return the player to the original room (round-trip property).
    
    **Validates: Requirements 2.2**
    
    This property ensures that:
    1. ENTER (using IN direction) moves player to entry room
    2. EXIT (using OUT direction) returns player to original room
    3. Round-trip preserves location consistency
    4. Game state is updated correctly
    """
    # Load world data (fresh instance for each test)
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid enter/exit scenario
    room_id, entry_room_id = data.draw(valid_enter_exit_scenario(world))
    
    # Create game state in the starting room
    state = GameState.create_new_game()
    state.current_room = room_id
    original_room = room_id
    
    # Enter (using IN direction - no object specified)
    enter_result = engine.handle_enter(None, state)
    
    # Enter should succeed
    assert enter_result.success is True, \
        f"Entering from {room_id} should succeed"
    
    # Should have moved to entry room
    assert enter_result.room_changed is True, \
        "room_changed should be True after entering"
    assert enter_result.new_room == entry_room_id, \
        f"new_room should be {entry_room_id}, got {enter_result.new_room}"
    assert state.current_room == entry_room_id, \
        f"current_room should be {entry_room_id}, got {state.current_room}"
    
    # Exit (using OUT direction - no object specified)
    exit_result = engine.handle_exit(None, state)
    
    # Exit should succeed
    assert exit_result.success is True, \
        f"Exiting from {entry_room_id} should succeed"
    
    # Should have returned to original room (round-trip complete)
    assert exit_result.room_changed is True, \
        "room_changed should be True after exiting"
    assert exit_result.new_room == original_room, \
        f"new_room should be {original_room}, got {exit_result.new_room}"
    assert state.current_room == original_room, \
        f"Round-trip should return to original room {original_room}, got {state.current_room}"
    
    # Both rooms should be in visited rooms
    assert original_room in state.rooms_visited, \
        f"Original room {original_room} should be in rooms_visited"
    assert entry_room_id in state.rooms_visited, \
        f"Entry room {entry_room_id} should be in rooms_visited"


# Note: test_enter_exit_round_trip_with_object is commented out because
# there are currently no enterable objects (vehicles, buildings) in the world data.
# This test should be re-enabled when enterable objects are added to the game.
#
# @settings(max_examples=100)
# @given(st.data())
# def test_enter_exit_round_trip_with_object(data):
#     """
#     For any enterable object, entering the object then exiting should
#     return the player to the original room (round-trip property).
#     
#     **Validates: Requirements 2.2**
#     
#     This property ensures that:
#     1. ENTER with object moves player to entry destination
#     2. EXIT returns player to exit destination (original room)
#     3. Round-trip preserves location consistency
#     4. Works with vehicles, buildings, and other enterable objects
#     """
#     pass


@settings(max_examples=100)
@given(st.data())
def test_enter_increments_counters(data):
    """
    For any valid enter operation, turn_count and moves should increment.
    
    **Validates: Requirements 2.2**
    
    This property ensures that game progression tracking works correctly.
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid enter/exit scenario
    room_id, entry_room_id = data.draw(valid_enter_exit_scenario(world))
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    initial_moves = state.moves
    initial_turns = state.turn_count
    
    # Enter
    result = engine.handle_enter(None, state)
    
    if result.success:
        # Counters should increment
        assert state.moves == initial_moves + 1, \
            f"moves should increment from {initial_moves} to {initial_moves + 1}, got {state.moves}"
        assert state.turn_count == initial_turns + 1, \
            f"turn_count should increment from {initial_turns} to {initial_turns + 1}, got {state.turn_count}"


@settings(max_examples=100)
@given(st.data())
def test_exit_increments_counters(data):
    """
    For any valid exit operation, turn_count and moves should increment.
    
    **Validates: Requirements 2.2**
    
    This property ensures that game progression tracking works correctly.
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid enter/exit scenario
    room_id, entry_room_id = data.draw(valid_enter_exit_scenario(world))
    
    # Create game state in entry room (so we can exit)
    state = GameState.create_new_game()
    state.current_room = entry_room_id
    initial_moves = state.moves
    initial_turns = state.turn_count
    
    # Exit
    result = engine.handle_exit(None, state)
    
    if result.success:
        # Counters should increment
        assert state.moves == initial_moves + 1, \
            f"moves should increment from {initial_moves} to {initial_moves + 1}, got {state.moves}"
        assert state.turn_count == initial_turns + 1, \
            f"turn_count should increment from {initial_turns} to {initial_turns + 1}, got {state.turn_count}"


@settings(max_examples=100)
@given(st.data())
def test_enter_returns_description(data):
    """
    For any valid enter operation, the result should include a room description.
    
    **Validates: Requirements 2.2**
    
    This property ensures that players receive appropriate feedback after entering.
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid enter/exit scenario
    room_id, entry_room_id = data.draw(valid_enter_exit_scenario(world))
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Enter
    result = engine.handle_enter(None, state)
    
    if result.success:
        # Result should contain a description
        assert result.message is not None, \
            "Result message should not be None"
        assert len(result.message) > 0, \
            "Result message should not be empty"
        
        # Message should contain enter-related text
        assert "enter" in result.message.lower(), \
            "Result message should mention entering"


@settings(max_examples=100)
@given(st.data())
def test_exit_returns_description(data):
    """
    For any valid exit operation, the result should include a room description.
    
    **Validates: Requirements 2.2**
    
    This property ensures that players receive appropriate feedback after exiting.
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid enter/exit scenario
    room_id, entry_room_id = data.draw(valid_enter_exit_scenario(world))
    
    # Create game state in entry room (so we can exit)
    state = GameState.create_new_game()
    state.current_room = entry_room_id
    
    # Exit
    result = engine.handle_exit(None, state)
    
    if result.success:
        # Result should contain a description
        assert result.message is not None, \
            "Result message should not be None"
        assert len(result.message) > 0, \
            "Result message should not be empty"
        
        # Message should contain exit-related text or room description
        # The implementation returns "exit message + room description"
        # so we just verify there's a meaningful message
        assert len(result.message) > 20, \
            "Result message should contain substantial content"
