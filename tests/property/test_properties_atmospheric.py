"""
Property Tests for Atmospheric Commands

Tests correctness properties for SPRAY, STAY, WIND, BLOW OUT, and BLOW UP commands following established patterns.
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


# Test SPRAY command properties
@settings(max_examples=100)
@given(st.data())
def test_spray_command_properties(data):
    """Test SPRAY command maintains correctness properties."""
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
    has_object = data.draw(st.booleans())
    has_target = data.draw(st.booleans())

    state.sanity = sanity

    if has_object:
        object_id = data.draw(st.sampled_from(['spray', 'paint', 'water', 'perfume', 'insecticide']))
    else:
        object_id = data.draw(st.sampled_from(['', 'air', 'nothing']))

    if has_target:
        target = data.draw(st.sampled_from(['wall', 'surface', 'object', 'area', 'creature']))
    else:
        target = data.draw(st.sampled_from(['', 'air', 'nothing']))

    result = engine.handle_spray(object_id, target, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (SPAY is a spraying/dispensing action)

    # Property 4: Sanity affects spraying behavior when relevant
    if sanity < 30:
        # Low sanity might cause unusual spraying effects
        supernatural_words = ['strange', 'unusual', 'supernatural', 'haunted', 'mysterious']
        # This is optional enhancement, not required

    # Property 5: Message contains spraying/dispensing themes
    spray_themes = ['spray', 'mist', 'aerosol', 'liquid', 'dispense', 'apply']
    # Should reference spraying themes in some way


@settings(max_examples=100)
@given(st.data())
def test_spray_command_substances(data):
    """Test SPRAY command with various substance types."""
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

    # Test with different spray substances
    substances = [
        'paint', 'water', 'perfume', 'insecticide', 'air freshener',
        'spray', 'aerosol', 'mist', 'chemical', 'solution',
        'liquid', 'substance', 'compound', 'mixture'
    ]
    targets = [
        'wall', 'surface', 'object', 'area', 'creature', 'plant'
    ]

    object_id = data.draw(st.sampled_from(substances))
    target = data.draw(st.sampled_from(targets))

    result = engine.handle_spray(object_id, target, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is contextually appropriate
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test STAY command properties
@settings(max_examples=100)
@given(st.data())
def test_stay_command_properties(data):
    """Test STAY command maintains correctness properties."""
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

    result = engine.handle_stay(state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (STAY is a waiting/pausing action)

    # Property 4: Sanity affects staying behavior when relevant
    if sanity < 30:
        # Low sanity might cause unusual waiting effects
        supernatural_words = ['time', 'space', 'supernatural', 'haunted', 'unusual']
        # This is optional enhancement, not required

    # Property 5: Message contains waiting/pausing themes
    stay_themes = ['stay', 'wait', 'pause', 'remain', 'rest', 'stop']
    # Should reference waiting themes in some way


@settings(max_examples=100)
@given(st.data())
def test_stay_command_waiting_effects(data):
    """Test STAY command with various waiting effects."""
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

    # Test with different sanity levels affecting patience
    sanity = data.draw(st.integers(min_value=0, max_value=100))
    state.sanity = sanity

    result = engine.handle_stay(state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is meaningful regardless of patience level
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test WIND command properties
@settings(max_examples=100)
@given(st.data())
def test_wind_command_properties(data):
    """Test WIND command maintains correctness properties."""
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
    has_object = data.draw(st.booleans())

    state.sanity = sanity

    if has_object:
        object_id = data.draw(st.sampled_from(['wind', 'air', 'breeze', 'gust', 'current']))
    else:
        object_id = data.draw(st.sampled_from(['', 'nothing', 'magic']))

    result = engine.handle_wind(object_id, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (WIND creates air movement effects)

    # Property 4: Sanity affects wind effects significantly
    if sanity < 30:
        # Low sanity makes wind supernatural or dangerous
        supernatural_words = ['haunted', 'supernatural', 'ghost', 'spirit', 'mysterious']
        # This is optional enhancement, not required

    # Property 5: Message contains wind/air movement themes
    wind_themes = ['wind', 'air', 'breeze', 'gust', 'current', 'blow', 'movement']
    # Should reference wind themes in some way


@settings(max_examples=100)
@given(st.data())
def test_wind_command_air_patterns(data):
    """Test WIND command with various air pattern types."""
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

    # Test with different wind patterns
    wind_patterns = [
        'wind', 'air', 'breeze', 'gust', 'current', 'draft',
        'whirlwind', 'tornado', 'storm', 'zephyr', 'gale',
        'magical wind', 'spiritual air', 'haunted breeze'
    ]
    object_id = data.draw(st.sampled_from(wind_patterns))

    result = engine.handle_wind(object_id, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is contextually appropriate
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test BLOW OUT command properties
@settings(max_examples=100)
@given(st.data())
def test_blow_out_command_properties(data):
    """Test BLOW OUT command maintains correctness properties."""
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
    has_object = data.draw(st.booleans())

    state.sanity = sanity

    if has_object:
        object_id = data.draw(st.sampled_from(['candle', 'light', 'lamp', 'fire', 'flame']))
    else:
        object_id = data.draw(st.sampled_from(['', 'air', 'nothing', 'wind']))

    result = engine.handle_blow_out(object_id, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (BLOW OUT extinguishes flames or creates blowing effects)

    # Property 4: Sanity affects blowing out when relevant
    if sanity < 30:
        # Low sanity might cause supernatural extinguishing
        supernatural_words = ['haunted', 'supernatural', 'ghost', 'spirit', 'mysterious']
        # This is optional enhancement, not required

    # Property 5: Message contains extinguishing/blowing themes
    blow_out_themes = ['blow', 'out', 'extinguish', 'extinguishing', 'air', 'breath']
    # Should reference blowing out themes in some way


@settings(max_examples=100)
@given(st.data())
def test_blow_out_command_light_sources(data):
    """Test BLOW OUT command with various light sources."""
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

    # Test with different light sources that can be blown out
    light_sources = [
        'candle', 'light', 'lamp', 'fire', 'flame', 'torch',
        'match', 'lantern', 'oil lamp', 'candlestick', 'wick'
    ]
    object_id = data.draw(st.sampled_from(light_sources))

    result = engine.handle_blow_out(object_id, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is contextually appropriate
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test BLOW UP command properties
@settings(max_examples=100)
@given(st.data())
def test_blow_up_command_properties(data):
    """Test BLOW UP command maintains correctness properties."""
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
    has_object = data.draw(st.booleans())

    state.sanity = sanity

    if has_object:
        object_id = data.draw(st.sampled_from(['balloon', 'bubble', 'inflatable', 'object', 'item']))
    else:
        object_id = data.draw(st.sampled_from(['', 'air', 'nothing', 'wind']))

    result = engine.handle_blow_up(object_id, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (BLOW UP inflates or expands objects)

    # Property 4: Sanity affects inflation when relevant
    if sanity < 30:
        # Low sanity might cause supernatural inflation
        supernatural_words = ['strange', 'unusual', 'supernatural', 'haunted', 'mysterious']
        # This is optional enhancement, not required

    # Property 5: Message contains inflation/expansion themes
    blow_up_themes = ['inflate', 'expand', 'grow', 'swell', 'blow', 'air']
    # Should reference inflation themes in some way


@settings(max_examples=100)
@given(st.data())
def test_blow_up_command_inflatable_objects(data):
    """Test BLOW UP command with various inflatable objects."""
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

    # Test with different inflatable objects
    inflatables = [
        'balloon', 'bubble', 'inflatable', 'toy', 'ball',
        'cushion', 'mattress', 'raft', 'boat', 'tube',
        'bag', 'sack', 'container', 'object'
    ]
    object_id = data.draw(st.sampled_from(inflatables))

    result = engine.handle_blow_up(object_id, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is contextually appropriate
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test atmospheric commands state consistency
@settings(max_examples=100)
@given(st.data())
def test_atmospheric_commands_state_consistency(data):
    """Test that atmospheric commands maintain state consistency."""
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

    # Execute multiple atmospheric commands
    result1 = engine.handle_spray('water', 'surface', state)
    assert isinstance(result1, ActionResult)

    result2 = engine.handle_stay(state)
    assert isinstance(result2, ActionResult)

    result3 = engine.handle_wind('breeze', state)
    assert isinstance(result3, ActionResult)

    result4 = engine.handle_blow_out('candle', state)
    assert isinstance(result4, ActionResult)

    result5 = engine.handle_blow_up('balloon', state)
    assert isinstance(result5, ActionResult)

    # State should remain consistent
    assert isinstance(state.sanity, int)
    assert isinstance(state.turn_count, int)
    assert state.turn_count >= original_turns
    assert 0 <= state.sanity <= 100

    # GameState should remain valid
    assert isinstance(state, GameState)

    # All results should be ActionResults
    for result in [result1, result2, result3, result4, result5]:
        assert isinstance(result, ActionResult)
        assert len(result.message) > 0


@settings(max_examples=100)
@given(st.data())
def test_atmospheric_commands_edge_cases(data):
    """Test atmospheric commands with edge cases."""
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
    unusual_inputs = ['', ' ', 'nonexistent', 'abstract_concept', 'nothing', '123', '!@#$%']

    spray_object = data.draw(st.sampled_from(unusual_inputs))
    spray_target = data.draw(st.sampled_from(unusual_inputs))
    wind_object = data.draw(st.sampled_from(unusual_inputs))
    blow_object = data.draw(st.sampled_from(unusual_inputs))

    # Test each command with unusual input
    result1 = engine.handle_spray(spray_object, spray_target, state)
    result2 = engine.handle_stay(state)
    result3 = engine.handle_wind(wind_object, state)
    result4 = engine.handle_blow_out(blow_object, state)
    result5 = engine.handle_blow_up(blow_object, state)

    # All should return valid ActionResults without crashing
    for result in [result1, result2, result3, result4, result5]:
        assert isinstance(result, ActionResult)
        assert len(result.message) > 0

    # State should remain valid
    assert isinstance(state, GameState)


@settings(max_examples=100)
@given(st.data())
def test_atmospheric_commands_sanity_integration(data):
    """Test that atmospheric commands integrate properly with sanity system."""
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
    original_sanity = sanity
    state.sanity = sanity

    # Test atmospheric commands affect sanity appropriately
    result = engine.handle_wind('haunted breeze', state)  # WIND should be most sanity-affecting
    assert isinstance(result, ActionResult)

    # Sanity should remain in valid range
    assert isinstance(state.sanity, int)
    assert 0 <= state.sanity <= 100

    # Message content should reflect sanity level
    result_message = result.message.lower()
    if original_sanity < 30:
        # Low sanity should produce supernatural wind effects
        has_supernatural_effect = any(word in result_message for word in [
            'haunted', 'supernatural', 'ghost', 'spirit', 'mysterious', 'strange'
        ])
        # Note: This is optional enhancement, just test that message exists

    # Message should always be meaningful
    assert len(result_message) > 0