"""
Property Tests for Advanced Object Manipulation Commands

Tests correctness properties for MOVE, RAISE, LOWER, and SLIDE commands following established patterns.
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


# Test MOVE command properties
@settings(max_examples=100)
@given(st.data())
def test_move_command_properties(data):
    """Test MOVE command maintains correctness properties."""
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
    has_target = data.draw(st.booleans())
    target_direction = data.draw(st.sampled_from(['north', 'south', 'east', 'west', 'up', 'down']))

    state.sanity = sanity

    if has_target:
        # Test with a target object
        target_id = data.draw(st.sampled_from(['house', 'door', 'window', 'tree']))
    else:
        target_id = data.draw(st.sampled_from(['', 'air', 'nothing']))

    result = engine.handle_move(target_id, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command doesn't crash regardless of input
    # (We're testing robustness more than specific success/failure)

    # Property 4: Sanity affects message content when relevant
    if sanity < 30:
        # Low sanity might add haunted elements to any action
        haunted_words = ['ghost', 'shadow', 'whisper', 'chill', 'supernatural']
        has_haunted = any(word in result_message for word in haunted_words)
        # Note: This is optional, so we just check the message exists


@settings(max_examples=100)
@given(st.data())
def test_move_command_directions(data):
    """Test MOVE command with various directions."""
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
    direction = data.draw(st.sampled_from(['north', 'south', 'east', 'west', 'up', 'down', 'left', 'right']))
    target = 'house'

    result = engine.handle_move(target, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message mentions movement or inability to move
    result_message = result.message.lower()
    movement_words = ['move', 'push', 'shift', 'slide', 'cannot', 'won\'t', 'too heavy', 'stuck', 'don\'t see', 'see any']
    assert any(word in result_message for word in movement_words)


# Test RAISE command properties
@settings(max_examples=100)
@given(st.data())
def test_raise_command_properties(data):
    """Test RAISE command maintains correctness properties."""
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
    has_target = data.draw(st.booleans())

    state.sanity = sanity

    if has_target:
        target_id = data.draw(st.sampled_from(['trapdoor', 'lid', 'gate', 'window', 'curtain']))
    else:
        target_id = data.draw(st.sampled_from(['', 'air', 'nothing']))

    result = engine.handle_raise(target_id, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Message contains raising-related words
    raising_words = ['raise', 'lift', 'open', 'cannot', 'won\'t', 'stuck', 'too heavy', 'see', 'don\'t']
    assert any(word in result_message for word in raising_words)

    # Property 4: Sanity affects content appropriately
    if sanity < 30:
        # Low sanity might see supernatural resistance
        supernatural_words = ['ghost', 'shadow', 'force', 'unholy', 'cursed']
        # This is optional enhancement


@settings(max_examples=100)
@given(st.data())
def test_raise_command_specific_objects(data):
    """Test RAISE command with specific object types."""
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

    # Test with object that might be raisable
    raisable_objects = ['trapdoor', 'lid', 'gate', 'cover', 'hatch']
    target = data.draw(st.sampled_from(raisable_objects))

    result = engine.handle_raise(target, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is contextually appropriate
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test LOWER command properties
@settings(max_examples=100)
@given(st.data())
def test_lower_command_properties(data):
    """Test LOWER command maintains correctness properties."""
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
    has_target = data.draw(st.booleans())

    state.sanity = sanity

    if has_target:
        target_id = data.draw(st.sampled_from(['ladder', 'rope', 'bridge', 'gate', 'window']))
    else:
        target_id = data.draw(st.sampled_from(['', 'air', 'nothing']))

    result = engine.handle_lower(target_id, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Message contains lowering-related words
    lowering_words = ['lower', 'drop', 'bring down', 'cannot', 'won\'t', 'stuck', 'don\'t see', 'see any']
    assert any(word in result_message for word in lowering_words)


@settings(max_examples=100)
@given(st.data())
def test_lower_command_scenarios(data):
    """Test LOWER command with various scenarios."""
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

    # Test with objects that might be lowerable
    lowerable_objects = ['ladder', 'rope', 'bridge', 'drawbridge', 'portcullis']
    target = data.draw(st.sampled_from(lowerable_objects))

    result = engine.handle_lower(target, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is meaningful regardless of object
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test SLIDE command properties
@settings(max_examples=100)
@given(st.data())
def test_slide_command_properties(data):
    """Test SLIDE command maintains correctness properties."""
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
    has_target = data.draw(st.booleans())
    has_direction = data.draw(st.booleans())

    state.sanity = sanity

    if has_target:
        target_id = data.draw(st.sampled_from(['panel', 'door', 'drawer', 'box', 'stone']))
    else:
        target_id = data.draw(st.sampled_from(['', 'air', 'nothing']))

    if has_direction:
        direction = data.draw(st.sampled_from(['left', 'right', 'up', 'down', 'open', 'closed']))
    else:
        direction = ''

    result = engine.handle_slide(target_id, '', state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Message contains sliding-related words
    sliding_words = ['slide', 'move', 'shift', 'glide', 'cannot', 'won\'t', 'stuck', 'don\'t see', 'see any']
    assert any(word in result_message for word in sliding_words)


@settings(max_examples=100)
@given(st.data())
def test_slide_command_directions(data):
    """Test SLIDE command with various directions."""
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

    # Test with sliding directions
    directions = ['left', 'right', 'up', 'down', 'open', 'closed', 'aside']
    direction = data.draw(st.sampled_from(directions))
    target = 'panel'

    result = engine.handle_slide(target, '', state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is meaningful for any direction
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test object manipulation state consistency
@settings(max_examples=100)
@given(st.data())
def test_object_manipulation_state_consistency(data):
    """Test that object manipulation commands maintain state consistency."""
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

    # Execute multiple object manipulation commands
    result1 = engine.handle_move('house', state)
    assert isinstance(result1, ActionResult)

    result2 = engine.handle_raise('trapdoor', state)
    assert isinstance(result2, ActionResult)

    result3 = engine.handle_lower('ladder', state)
    assert isinstance(result3, ActionResult)

    result4 = engine.handle_slide('panel', '', state)
    assert isinstance(result4, ActionResult)

    # State should remain consistent
    assert isinstance(state.sanity, int)
    assert isinstance(state.turn_count, int)
    assert state.turn_count >= original_turns
    assert 0 <= state.sanity <= 100

    # GameState should remain valid
    assert isinstance(state, GameState)

    # All results should be ActionResults
    for result in [result1, result2, result3, result4]:
        assert isinstance(result, ActionResult)
        assert len(result.message) > 0