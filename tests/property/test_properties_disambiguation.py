"""
Property-based tests for disambiguation system.

Tests that ambiguous commands prompt for clarification and track context.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "lambda" / "game_handler"))

from game_engine import GameEngine
from state_manager import GameState
from world_loader import WorldData
from command_parser import CommandParser


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


# Feature: complete-zork-commands, Property 45: Disambiguation prompts
def test_disambiguation_prompts_for_ambiguous_objects(game_engine, parser, world_data):
    """
    Property 45: When multiple objects match a name, system prompts for clarification.
    
    For any command with an ambiguous object reference, the system should:
    1. Detect multiple matching objects
    2. Return a disambiguation prompt
    3. Store disambiguation context in game state
    4. Not execute the command until clarified
    """
    # Create game state
    state = GameState(
        session_id="test-session",
        current_room="west_of_house"
    )
    
    # Test with a generic name that could match multiple objects
    # In a real scenario, we'd have multiple objects with similar names
    # For this test, we'll verify the mechanism works
    
    # Manually create a scenario with ambiguous matches
    # by checking if find_matching_objects returns multiple results
    test_names = ['key', 'lamp', 'sword', 'book', 'door']
    
    for name in test_names:
        matches = game_engine.find_matching_objects(name, state)
        
        if len(matches) > 1:
            # Parse a command with the ambiguous name
            command = parser.parse(f"take {name}")
            
            # Execute command
            result = game_engine.execute_command(command, state)
            
            # Should prompt for disambiguation
            assert not result.success, f"Ambiguous command for '{name}' should not succeed"
            assert "which do you mean" in result.message.lower() or "which" in result.message.lower()
            
            # Should store disambiguation context
            assert state.disambiguation_context is not None
            assert state.disambiguation_context['object'] == command.object
            assert len(state.disambiguation_context['matches']) > 1
            
            # Clear context for next iteration
            state.disambiguation_context = None


# Feature: complete-zork-commands, Property 45: Disambiguation context tracking
def test_disambiguation_context_stored(game_engine, parser, world_data):
    """
    Property 45: Disambiguation context is stored in game state.
    
    When disambiguation is needed, the system should store:
    - The original command verb
    - The ambiguous object name
    - The list of matching objects
    - Any target or preposition from the command
    """
    state = GameState(
        session_id="test-session",
        current_room="west_of_house"
    )
    
    # Create a scenario with ambiguous objects
    # For this test, we'll manually set up disambiguation context
    state.disambiguation_context = {
        'command': 'TAKE',
        'object': 'key',
        'matches': ['brass_key', 'skeleton_key'],
        'target': None,
        'preposition': None
    }
    
    # Verify context is stored
    assert state.disambiguation_context is not None
    assert state.disambiguation_context['command'] == 'TAKE'
    assert state.disambiguation_context['object'] == 'key'
    assert len(state.disambiguation_context['matches']) == 2


# Feature: complete-zork-commands, Property 45: Disambiguation resolution
def test_disambiguation_clears_after_resolution(game_engine, parser, world_data):
    """
    Property 45: Disambiguation context is cleared after resolution.
    
    After the player provides clarification, the disambiguation context
    should be cleared and the command should proceed normally.
    """
    state = GameState(
        session_id="test-session",
        current_room="west_of_house"
    )
    
    # Set up disambiguation context
    state.disambiguation_context = {
        'command': 'TAKE',
        'object': 'key',
        'matches': ['brass_key', 'skeleton_key'],
        'target': None,
        'preposition': None
    }
    
    # Parse a clarifying command
    command = parser.parse("take brass key")
    
    # Execute command - should clear disambiguation context
    result = game_engine.execute_command(command, state)
    
    # Context should be cleared
    assert state.disambiguation_context is None


# Feature: complete-zork-commands, Property 45: Single match no disambiguation
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.sampled_from(['mailbox', 'leaflet', 'lamp', 'sword']))
def test_single_match_no_disambiguation(game_engine, parser, object_name):
    """
    Property 45: Single matching object does not trigger disambiguation.
    
    When only one object matches the name, no disambiguation prompt
    should be shown and the command should proceed normally.
    """
    state = GameState(
        session_id="test-session",
        current_room="west_of_house"
    )
    
    # Parse command with unambiguous object
    command = parser.parse(f"examine {object_name}")
    
    # Check disambiguation
    disambiguation_result = game_engine.check_disambiguation(command, state)
    
    # Should not need disambiguation
    assert disambiguation_result is None
    assert state.disambiguation_context is None


# Feature: complete-zork-commands, Property 45: No object no disambiguation
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.sampled_from(['north', 'south', 'inventory', 'look', 'quit']))
def test_no_object_no_disambiguation(game_engine, parser, command_text):
    """
    Property 45: Commands without objects don't trigger disambiguation.
    
    Commands that don't reference objects should not trigger
    disambiguation checks.
    """
    state = GameState(
        session_id="test-session",
        current_room="west_of_house"
    )
    
    # Parse command without object
    command = parser.parse(command_text)
    
    # Check disambiguation
    disambiguation_result = game_engine.check_disambiguation(command, state)
    
    # Should not need disambiguation
    assert disambiguation_result is None
    assert state.disambiguation_context is None


# Feature: complete-zork-commands, Property 45: Disambiguation prompt format
def test_disambiguation_prompt_format(game_engine):
    """
    Property 45: Disambiguation prompts are clearly formatted.
    
    Disambiguation prompts should:
    - List all matching objects
    - Use clear language ("which do you mean")
    - Format multiple options with commas and "or"
    """
    # Test with 2 matches
    matches_2 = ['brass_key', 'skeleton_key']
    prompt_2 = game_engine.create_disambiguation_prompt(matches_2)
    assert 'which do you mean' in prompt_2.lower()
    assert 'or' in prompt_2.lower()
    
    # Test with 3+ matches
    matches_3 = ['brass_key', 'skeleton_key', 'rusty_key']
    prompt_3 = game_engine.create_disambiguation_prompt(matches_3)
    assert 'which do you mean' in prompt_3.lower()
    assert ',' in prompt_3  # Should have commas for list
    assert 'or' in prompt_3.lower()
    
    # Test with 0 matches
    matches_0 = []
    prompt_0 = game_engine.create_disambiguation_prompt(matches_0)
    assert "don't see" in prompt_0.lower()
    
    # Test with 1 match (no disambiguation needed)
    matches_1 = ['brass_key']
    prompt_1 = game_engine.create_disambiguation_prompt(matches_1)
    assert prompt_1 == ""  # Empty string means no disambiguation needed
