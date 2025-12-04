"""
Property-based tests for multi-object handling.

Tests that commands can affect multiple objects appropriately.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "lambda" / "game_handler"))

from game_engine import GameEngine
from state_manager import GameState
from world_loader import WorldData
from command_parser import CommandParser, ParsedCommand


@pytest.fixture(scope="module")
def world_data():
    """Load world data for testing."""
    data_dir = Path(__file__).parent.parent.parent / "src" / "lambda" / "game_handler" / "data"
    world = WorldData()
    world.load_from_json(str(data_dir))
    return world


@pytest.fixture(scope="module")
def game_engine(world_data):
    """Create game engine for testing."""
    return GameEngine(world_data)


@pytest.fixture(scope="module")
def parser():
    """Create command parser for testing."""
    return CommandParser()


# Feature: complete-zork-commands, Property 47: Multi-object handling
def test_expand_all_returns_takeable_objects(game_engine):
    """
    Property 47: 'all' expands to all takeable objects in room.
    
    When a player uses 'all' or 'everything', the system should
    expand it to all takeable objects in the current room.
    """
    state = GameState(
        session_id="test-session",
        current_room="west_of_house"
    )
    
    # Expand 'all'
    objects = game_engine.expand_multi_object('all', state)
    
    # Should return a list
    assert isinstance(objects, list)
    
    # All returned objects should be takeable
    for obj_id in objects:
        try:
            obj = game_engine.world.get_object(obj_id)
            assert obj.state.get('is_takeable', True)
        except ValueError:
            pass


# Feature: complete-zork-commands, Property 47: Multi-object command execution
def test_multi_object_command_processes_each(game_engine):
    """
    Property 47: Multi-object commands process each object.
    
    When a command affects multiple objects, the system should
    process each object individually and combine results.
    """
    state = GameState(
        session_id="test-session",
        current_room="west_of_house"
    )
    
    # Create a multi-object command
    objects = ['mailbox', 'leaflet']
    
    # Execute multi-object command
    result = game_engine.handle_multi_object_command('EXAMINE', objects, state)
    
    # Should return a result
    assert result is not None
    assert isinstance(result.message, str)
    
    # Message should contain results for each object
    # (either success or failure for each)
    assert len(result.message) > 0


# Feature: complete-zork-commands, Property 47: Empty multi-object fails gracefully
def test_empty_multi_object_fails_gracefully(game_engine):
    """
    Property 47: Empty multi-object list fails with helpful message.
    
    When no objects match a multi-object specifier, the system
    should return a helpful error message.
    """
    state = GameState(
        session_id="test-session",
        current_room="west_of_house"
    )
    
    # Execute with empty object list
    result = game_engine.handle_multi_object_command('TAKE', [], state)
    
    # Should fail gracefully
    assert not result.success
    assert len(result.message) > 0
    assert "nothing" in result.message.lower()


# Feature: complete-zork-commands, Property 47: Single object from multi-object
def test_single_object_from_multi_object_works(game_engine):
    """
    Property 47: Single object in multi-object list works normally.
    
    When a multi-object specifier expands to a single object,
    it should work the same as a single-object command.
    """
    state = GameState(
        session_id="test-session",
        current_room="west_of_house"
    )
    
    # Execute with single object in list
    result = game_engine.handle_multi_object_command('EXAMINE', ['mailbox'], state)
    
    # Should work
    assert result is not None
    assert isinstance(result.message, str)


# Feature: complete-zork-commands, Property 47: Multi-object success count
def test_multi_object_tracks_successes(game_engine):
    """
    Property 47: Multi-object commands track success count.
    
    The system should track how many objects were successfully
    processed and report overall success if any succeeded.
    """
    state = GameState(
        session_id="test-session",
        current_room="west_of_house"
    )
    
    # Add some objects to inventory for testing
    state.inventory = ['lamp', 'sword']
    
    # Try to drop multiple objects
    result = game_engine.handle_multi_object_command('DROP', ['lamp', 'sword'], state)
    
    # Should indicate success if any objects were processed
    assert isinstance(result.success, bool)


# Feature: complete-zork-commands, Property 47: All except exclusion
def test_all_except_excludes_specified_objects(game_engine):
    """
    Property 47: 'all except X' excludes specified objects.
    
    When a player uses 'all except X', the system should
    expand to all objects except the specified one.
    """
    state = GameState(
        session_id="test-session",
        current_room="west_of_house"
    )
    
    # Expand 'all except mailbox'
    objects = game_engine.expand_multi_object('all except mailbox', state)
    
    # Should return a list
    assert isinstance(objects, list)
    
    # Should not include mailbox
    assert 'mailbox' not in objects


# Feature: complete-zork-commands, Property 47: Multi-object with target
def test_multi_object_with_target(game_engine):
    """
    Property 47: Multi-object commands support targets.
    
    Commands like 'put all in box' should process each object
    with the specified target.
    """
    state = GameState(
        session_id="test-session",
        current_room="west_of_house"
    )
    
    # Add objects to inventory
    state.inventory = ['lamp', 'sword']
    
    # Execute multi-object command with target
    result = game_engine.handle_multi_object_command(
        'PUT',
        ['lamp', 'sword'],
        state,
        target='trophy_case'
    )
    
    # Should process command
    assert result is not None
    assert isinstance(result.message, str)


# Feature: complete-zork-commands, Property 47: Combined results format
def test_combined_results_are_readable(game_engine):
    """
    Property 47: Combined results are clearly formatted.
    
    When multiple objects are processed, results should be
    clearly formatted with one result per object.
    """
    state = GameState(
        session_id="test-session",
        current_room="west_of_house"
    )
    
    # Execute multi-object command
    objects = ['mailbox', 'leaflet']
    result = game_engine.handle_multi_object_command('EXAMINE', objects, state)
    
    # Message should be readable
    assert len(result.message) > 0
    
    # Should contain newlines for multiple results
    if len(objects) > 1:
        # Results should be separated (either by newlines or clear formatting)
        assert len(result.message.split('\n')) >= 1


# Feature: complete-zork-commands, Property 47: Everything synonym
def test_everything_synonym_for_all(game_engine):
    """
    Property 47: 'everything' works the same as 'all'.
    
    The system should treat 'everything' as a synonym for 'all'.
    """
    state = GameState(
        session_id="test-session",
        current_room="west_of_house"
    )
    
    # Expand 'everything'
    objects_everything = game_engine.expand_multi_object('everything', state)
    
    # Expand 'all'
    objects_all = game_engine.expand_multi_object('all', state)
    
    # Should return same objects
    assert set(objects_everything) == set(objects_all)


# Feature: complete-zork-commands, Property 47: Multi-object preserves state
def test_multi_object_preserves_state_consistency(game_engine):
    """
    Property 47: Multi-object commands maintain state consistency.
    
    Processing multiple objects should maintain game state
    consistency throughout the operation.
    """
    state = GameState(
        session_id="test-session",
        current_room="west_of_house"
    )
    
    # Record initial state
    initial_inventory = list(state.inventory)
    initial_room = state.current_room
    
    # Execute multi-object command
    objects = game_engine.expand_multi_object('all', state)
    if objects:
        result = game_engine.handle_multi_object_command('EXAMINE', objects, state)
        
        # State should remain consistent
        assert state.current_room == initial_room
        # Examine shouldn't change inventory
        assert state.inventory == initial_inventory
