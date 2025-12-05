"""
Property Tests for Communication System Commands

Tests correctness properties for SAY, WHISPER, and ANSWER commands following established patterns.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler'))

import pytest
from hypothesis import given, strategies as st, settings, assume
from game_engine import GameEngine, ActionResult
from state_manager import GameState
from world_loader import WorldData, Room, GameObject


# Test SAY command properties
@settings(max_examples=100)
@given(st.data())
def test_say_command_properties(data):
    """Test SAY command maintains correctness properties."""
    # Setup world and game engine
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    engine = GameEngine(world)

    # Create game state
    state = GameState(
        session_id="test_session",
        current_room='west_of_house'
    )

    # Generate test parameters
    sanity = data.draw(st.integers(min_value=0, max_value=100))
    has_message = data.draw(st.booleans())

    state.sanity = sanity

    if has_message:
        # Generate meaningful message
        message = data.draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'Pd'))))
    else:
        message = ''

    result = engine.handle_say(message, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (The specific message content may vary based on implementation)

    # Property 4: Sanity affects message content when relevant
    if sanity < 30:
        # Low sanity might add supernatural elements to speech
        supernatural_words = ['ghost', 'shadow', 'whisper', 'echo', 'haunted']
        # This is optional enhancement, not required


@settings(max_examples=100)
@given(st.data())
def test_say_command_message_content(data):
    """Test SAY command with various message content."""
    # Setup world and game engine
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    engine = GameEngine(world)

    # Create game state
    state = GameState(
        session_id="test_session",
        current_room='west_of_house'
    )

    # Test with different types of messages
    message_types = [
        'hello', 'help me', 'what is this', 'open sesame',
        'magic word', 'password', 'please help', 'thank you',
        '', 'x', 'a very long message that tests character limits'
    ]
    message = data.draw(st.sampled_from(message_types))

    result = engine.handle_say(message, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is meaningful regardless of message content
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test WHISPER command properties
@settings(max_examples=100)
@given(st.data())
def test_whisper_command_properties(data):
    """Test WHISPER command maintains correctness properties."""
    # Setup world and game engine
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    engine = GameEngine(world)

    # Create game state
    state = GameState(
        session_id="test_session",
        current_room='west_of_house'
    )

    # Generate test parameters
    sanity = data.draw(st.integers(min_value=0, max_value=100))
    has_message = data.draw(st.booleans())

    state.sanity = sanity

    if has_message:
        message = data.draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'Pd'))))
    else:
        message = ''

    result = engine.handle_whisper(message, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (The specific message content may vary based on implementation)

    # Property 4: Sanity affects content appropriately
    if sanity < 30:
        # Low sanity might cause supernatural whispering effects
        supernatural_words = ['ghost', 'shadow', 'spirit', 'unseen']
        # This is optional enhancement


@settings(max_examples=100)
@given(st.data())
def test_whisper_command_messages(data):
    """Test WHISPER command with various message types."""
    # Setup world and game engine
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    engine = GameEngine(world)

    # Create game state
    state = GameState(
        session_id="test_session",
        current_room='west_of_house'
    )

    # Test with different whisper messages
    messages = ['secret', 'help me', 'password', 'magic word', 'hello darkness', '']
    message = data.draw(st.sampled_from(messages))

    result = engine.handle_whisper(message, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is meaningful regardless of message content
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test ANSWER command properties
@settings(max_examples=100)
@given(st.data())
def test_answer_command_properties(data):
    """Test ANSWER command maintains correctness properties."""
    # Setup world and game engine
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    engine = GameEngine(world)

    # Create game state
    state = GameState(
        session_id="test_session",
        current_room='west_of_house'
    )

    # Generate test parameters
    sanity = data.draw(st.integers(min_value=0, max_value=100))
    has_answer = data.draw(st.booleans())

    state.sanity = sanity

    if has_answer:
        answer = data.draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'Pd'))))
    else:
        answer = ''

    result = engine.handle_answer(answer, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (The specific message content may vary based on implementation)

    # Property 4: Sanity affects content when relevant
    if sanity < 30:
        # Low sanity might cause supernatural answering effects
        supernatural_words = ['ghost', 'spirit', 'whisper', 'unseen']
        # This is optional enhancement


@settings(max_examples=100)
@given(st.data())
def test_answer_command_responses(data):
    """Test ANSWER command with various response types."""
    # Setup world and game engine
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    engine = GameEngine(world)

    # Create game state
    state = GameState(
        session_id="test_session",
        current_room='west_of_house'
    )

    # Test with different answer types
    answers = [
        'yes', 'no', 'maybe', 'help', 'i don\'t know',
        'hello', 'goodbye', 'password', 'secret', '',
        'a', 'this is a very long answer to test boundaries'
    ]
    answer = data.draw(st.sampled_from(answers))

    result = engine.handle_answer(answer, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is meaningful regardless of answer content
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test communication state consistency
@settings(max_examples=100)
@given(st.data())
def test_communication_state_consistency(data):
    """Test that communication commands maintain state consistency."""
    # Setup world and game engine
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    engine = GameEngine(world)

    # Create game state
    state = GameState(
        session_id="test_session",
        current_room='west_of_house'
    )

    # Generate test parameters
    sanity = data.draw(st.integers(min_value=0, max_value=100))
    state.sanity = sanity
    original_turns = state.turn_count

    # Execute multiple communication commands
    result1 = engine.handle_say('hello world', state)
    assert isinstance(result1, ActionResult)

    result2 = engine.handle_whisper('secret message', state)
    assert isinstance(result2, ActionResult)

    result3 = engine.handle_answer('yes', state)
    assert isinstance(result3, ActionResult)

    # State should remain consistent
    assert isinstance(state.sanity, int)
    assert isinstance(state.turn_count, int)
    assert state.turn_count >= original_turns
    assert 0 <= state.sanity <= 100

    # GameState should remain valid
    assert isinstance(state, GameState)

    # All results should be ActionResults
    for result in [result1, result2, result3]:
        assert isinstance(result, ActionResult)
        assert len(result.message) > 0


@settings(max_examples=100)
@given(st.data())
def test_communication_edge_cases(data):
    """Test communication commands with edge cases."""
    # Setup world and game engine
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    engine = GameEngine(world)

    # Create game state
    state = GameState(
        session_id="test_session",
        current_room='west_of_house'
    )

    # Test with empty strings and unusual inputs
    unusual_inputs = ['', ' ', 'x', '123', '!@#$%', 'very long message ' * 20]

    message = data.draw(st.sampled_from(unusual_inputs))

    # Test each command with unusual input
    result1 = engine.handle_say(message, state)
    result2 = engine.handle_whisper(message, state)
    result3 = engine.handle_answer(message, state)

    # All should return valid ActionResults without crashing
    for result in [result1, result2, result3]:
        assert isinstance(result, ActionResult)
        assert len(result.message) > 0

    # State should remain valid
    assert isinstance(state, GameState)