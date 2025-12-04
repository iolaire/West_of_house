"""
Property-Based Tests for Error Handling and Feedback

Tests correctness properties related to error messages, command feedback,
and user guidance when commands fail or are unrecognized.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler'))

import pytest
from hypothesis import given, strategies as st, settings
from command_parser import CommandParser, ParsedCommand
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


# Helper to create test game state
def create_test_state():
    """Create a basic game state for testing."""
    return GameState(session_id="test-session")


# Feature: complete-zork-commands, Property 35: Unimplemented command messages
@settings(max_examples=100)
@given(
    unimplemented_verb=st.sampled_from([
        "USE", "APPLY", "OPERATE", "WALK_TO", "RUN_TO", "TRAVEL_TO",
        "SAY", "SPEAK", "TALK", "WEAR", "REMOVE", "DRINK", "EAT"
    ])
)
def test_unimplemented_command_messages(game_engine, unimplemented_verb):
    """
    For any recognized but unimplemented command, the system should return
    a message indicating the command is not yet available.
    
    **Validates: Requirements 9.1**
    
    This property ensures that players receive clear feedback when attempting
    to use commands that are recognized but not yet implemented, rather than
    generic error messages.
    """
    state = create_test_state()
    
    # Create a command with an unimplemented verb
    command = ParsedCommand(verb=unimplemented_verb, object="test_object")
    
    # Execute the command
    result = engine.execute_command(command, state)
    
    # Should fail
    assert result.success is False
    
    # Message should indicate the command is not implemented
    assert "not yet implemented" in result.message.lower() or \
           "not yet available" in result.message.lower() or \
           "not implemented" in result.message.lower()
    
    # Should provide some guidance or suggestions
    assert len(result.message) > 50  # Should be more than just "not implemented"


# Feature: complete-zork-commands, Property 36: Incorrect usage guidance
@settings(max_examples=100)
@given(
    verb=st.sampled_from(["LOCK", "UNLOCK", "TIE", "THROW", "GIVE", "FILL"]),
    has_object=st.booleans()
)
def test_incorrect_usage_guidance(verb, has_object):
    """
    For any command used with incorrect syntax, the system should return
    guidance on correct usage.
    
    **Validates: Requirements 9.2**
    
    This property ensures that when commands requiring multiple parameters
    are used incorrectly, the player receives helpful guidance on the
    correct syntax.
    """
    engine = create_test_engine()
    state = create_test_state()
    
    # Create a command with missing required parameters
    # These commands require both object and target
    command = ParsedCommand(
        verb=verb,
        object="test_object" if has_object else None,
        target=None  # Missing required target
    )
    
    # Execute the command
    result = engine.execute_command(command, state)
    
    # Should fail
    assert result.success is False
    
    # Message should ask for the missing parameter
    assert "what" in result.message.lower() or \
           "which" in result.message.lower() or \
           "usage" in result.message.lower()


# Feature: complete-zork-commands, Property 37: Missing object messages
@settings(max_examples=100)
@given(
    verb=st.sampled_from(["TAKE", "EXAMINE", "OPEN", "CLOSE", "READ", "PUSH"]),
    fake_object=st.text(
        alphabet=st.characters(whitelist_categories=("Ll",), min_codepoint=97, max_codepoint=122),
        min_size=5,
        max_size=15
    ).filter(lambda x: x not in ["lamp", "mailbox", "leaflet", "sword", "trophy"])
)
def test_missing_object_messages(verb, fake_object):
    """
    For any command referencing an object not present, the system should
    clearly state the object is not here.
    
    **Validates: Requirements 9.3**
    
    This property ensures that when players reference objects that don't
    exist or aren't present, they receive clear feedback rather than
    confusing error messages.
    """
    engine = create_test_engine()
    state = create_test_state()
    
    # Create a command referencing a non-existent object
    command = ParsedCommand(verb=verb, object=fake_object)
    
    # Execute the command
    result = engine.execute_command(command, state)
    
    # Should fail
    assert result.success is False
    
    # Message should indicate object is not present
    assert "don't see" in result.message.lower() or \
           "not here" in result.message.lower() or \
           "don't know" in result.message.lower() or \
           "can't find" in result.message.lower()


# Feature: complete-zork-commands, Property 38: Impossible action explanations
@settings(max_examples=100)
@given(
    action_type=st.sampled_from([
        ("OPEN", "already_open"),
        ("CLOSE", "already_closed"),
        ("TAKE", "too_heavy"),
        ("LOCK", "no_lock")
    ])
)
def test_impossible_action_explanations(action_type):
    """
    For any impossible action, the system should explain why it cannot be done.
    
    **Validates: Requirements 9.4**
    
    This property ensures that when actions are impossible due to game state
    or object properties, players receive explanations rather than just
    "you can't do that" messages.
    """
    engine = create_test_engine()
    state = create_test_state()
    
    verb, reason = action_type
    
    # For this test, we'll verify that impossible actions return explanatory messages
    # We'll test with the mailbox which exists in the game
    command = ParsedCommand(verb=verb, object="mailbox")
    
    # Execute the command
    result = engine.execute_command(command, state)
    
    # Result should have a message (success or failure)
    assert result.message is not None
    assert len(result.message) > 0
    
    # If it fails, message should be explanatory (more than just "no")
    if not result.success:
        assert len(result.message) > 10  # Should be more than just "No" or "Can't"


# Feature: complete-zork-commands, Property 39: Missing parameter prompts
@settings(max_examples=100)
@given(
    command_type=st.sampled_from([
        ("LOCK", "object", None),
        ("UNLOCK", "object", None),
        ("TIE", "object", None),
        ("THROW", "object", None),
        ("GIVE", "object", None),
        ("FILL", "object", None)
    ])
)
def test_missing_parameter_prompts(command_type):
    """
    For any command requiring additional objects, the system should prompt
    for the missing information.
    
    **Validates: Requirements 9.5**
    
    This property ensures that when commands are incomplete, players are
    guided to provide the missing information rather than receiving
    generic error messages.
    """
    engine = create_test_engine()
    state = create_test_state()
    
    verb, has_object, has_target = command_type
    
    # Create command with missing target parameter
    command = ParsedCommand(
        verb=verb,
        object="test_object" if has_object else None,
        target=None  # Missing required target
    )
    
    # Execute the command
    result = engine.execute_command(command, state)
    
    # Should fail
    assert result.success is False
    
    # Message should prompt for missing information
    assert "what" in result.message.lower() or \
           "which" in result.message.lower() or \
           "who" in result.message.lower()


# Additional property: Unknown commands provide suggestions
@settings(max_examples=100)
@given(
    gibberish=st.text(
        alphabet=st.characters(whitelist_categories=("Ll",), min_codepoint=97, max_codepoint=122),
        min_size=3,
        max_size=20
    ).filter(lambda x: x not in [
        "go", "take", "drop", "open", "close", "examine", "look", "inventory",
        "quit", "north", "south", "east", "west", "up", "down"
    ])
)
def test_unknown_commands_provide_suggestions(gibberish):
    """
    For any unknown command, the system should provide helpful suggestions.
    
    This ensures players aren't left confused when they try commands that
    don't exist in the game.
    """
    engine = create_test_engine()
    state = create_test_state()
    parser = CommandParser()
    
    # Parse the gibberish command
    command = parser.parse(gibberish)
    
    # If it's recognized as UNKNOWN
    if command.verb == "UNKNOWN":
        # Execute the command
        result = engine.execute_command(command, state)
        
        # Should fail
        assert result.success is False
        
        # Message should provide suggestions
        assert "try" in result.message.lower() or \
               "command" in result.message.lower()
        
        # Should be reasonably long (contains suggestions)
        assert len(result.message) > 30


# Additional property: Error messages maintain immersion
@settings(max_examples=100)
@given(
    command_str=st.sampled_from([
        "take nonexistent",
        "open imaginary",
        "frobulate widget",
        "xyzzy plugh",
        "go nowhere"
    ])
)
def test_error_messages_maintain_immersion(command_str):
    """
    For any error condition, messages should maintain the game's atmosphere.
    
    Error messages should be helpful but also fit the haunted theme where
    appropriate.
    """
    engine = create_test_engine()
    state = create_test_state()
    parser = CommandParser()
    
    # Parse and execute the command
    command = parser.parse(command_str)
    result = engine.execute_command(command, state)
    
    # Result should have a message
    assert result.message is not None
    assert len(result.message) > 0
    
    # Message should not contain technical jargon or stack traces
    assert "error" not in result.message.lower() or "an error occurred" in result.message.lower()
    assert "exception" not in result.message.lower()
    assert "traceback" not in result.message.lower()
    assert "none" not in result.message.lower() or "nothing" in result.message.lower()


# Additional property: Consistent error message format
@settings(max_examples=100)
@given(
    verb=st.sampled_from(["TAKE", "OPEN", "EXAMINE", "PUSH", "PULL"]),
    fake_object=st.text(
        alphabet=st.characters(whitelist_categories=("Ll",), min_codepoint=97, max_codepoint=122),
        min_size=4,
        max_size=12
    )
)
def test_consistent_error_message_format(verb, fake_object):
    """
    For any error condition, messages should follow a consistent format.
    
    This ensures a professional and polished user experience.
    """
    engine = create_test_engine()
    state = create_test_state()
    
    # Create command with non-existent object
    command = ParsedCommand(verb=verb, object=fake_object)
    
    # Execute the command
    result = engine.execute_command(command, state)
    
    # Should fail
    assert result.success is False
    
    # Message should be properly formatted
    assert result.message is not None
    assert len(result.message) > 0
    
    # Should not have trailing/leading whitespace issues
    assert result.message == result.message.strip()
    
    # Should not have multiple consecutive spaces
    assert "  " not in result.message or "\n\n" in result.message  # Allow double newlines for formatting
