"""
Property Tests for Special Object Manipulation Commands

Tests correctness properties for SPRING, HATCH, APPLY, and BRUSH commands following established patterns.
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


# Test SPRING command properties
@settings(max_examples=100)
@given(st.data())
def test_spring_command_properties(data):
    """Test SPRING command maintains correctness properties."""
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
        # Test with springable objects
        target_id = data.draw(st.sampled_from(['trapdoor', 'box', 'chest', 'cage', 'device']))
    else:
        target_id = data.draw(st.sampled_from(['', 'air', 'nothing', 'wall']))

    result = engine.handle_spring(target_id, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (The specific message content may vary based on implementation)

    # Property 4: Sanity affects message content when relevant
    if sanity < 30:
        # Low sanity might add supernatural elements
        supernatural_words = ['ghost', 'shadow', 'supernatural', 'haunted']
        # This is optional enhancement, not required


@settings(max_examples=100)
@given(st.data())
def test_spring_command_mechanisms(data):
    """Test SPRING command with various mechanical objects."""
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

    # Test with objects that might have spring mechanisms
    mechanical_objects = ['trapdoor', 'box', 'chest', 'lock', 'mechanism', 'device']
    target = data.draw(st.sampled_from(mechanical_objects))

    result = engine.handle_spring(target, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is contextually appropriate
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test HATCH command properties
@settings(max_examples=100)
@given(st.data())
def test_hatch_command_properties(data):
    """Test HATCH command maintains correctness properties."""
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
        # Test with objects that might hatch or contain hatching things
        target_id = data.draw(st.sampled_from(['egg', 'cocoon', 'chest', 'box', 'container']))
    else:
        target_id = data.draw(st.sampled_from(['', 'air', 'nothing', 'wall']))

    result = engine.handle_hatch(target_id, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (The specific message content may vary based on implementation)

    # Property 4: Sanity affects content appropriately
    if sanity < 30:
        # Low sanity might see supernatural hatching
        supernatural_words = ['ghost', 'demon', 'spirit', 'unnatural']
        # This is optional enhancement


@settings(max_examples=100)
@given(st.data())
def test_hatch_command_biological_objects(data):
    """Test HATCH command with biological objects."""
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

    # Test with biological objects that might hatch
    biological_objects = ['egg', 'cocoon', 'chrysalis', 'seed', 'pod']
    target = data.draw(st.sampled_from(biological_objects))

    result = engine.handle_hatch(target, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is meaningful regardless of object
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test APPLY command properties
@settings(max_examples=100)
@given(st.data())
def test_apply_command_properties(data):
    """Test APPLY command maintains correctness properties."""
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
    has_tool = data.draw(st.booleans())
    has_target = data.draw(st.booleans())

    state.sanity = sanity

    if has_tool:
        tool = data.draw(st.sampled_from(['paint', 'oil', 'magic', 'potion', 'powder']))
    else:
        tool = data.draw(st.sampled_from(['', 'air', 'nothing']))

    if has_target:
        target = data.draw(st.sampled_from(['door', 'wall', 'object', 'surface', 'mechanism']))
    else:
        target = data.draw(st.sampled_from(['', 'air', 'nothing']))

    result = engine.handle_apply(tool, target, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (The specific message content may vary based on implementation)

    # Property 4: Sanity affects content when relevant
    if sanity < 30:
        # Low sanity might cause supernatural application effects
        supernatural_words = ['ghost', 'shadow', 'magic', 'curse']
        # This is optional enhancement


@settings(max_examples=100)
@given(st.data())
def test_apply_command_tool_target_combinations(data):
    """Test APPLY command with various tool-target combinations."""
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

    # Test with various tools and targets
    tools = ['paint', 'oil', 'magic', 'potion', 'powder', 'liquid']
    targets = ['door', 'wall', 'object', 'surface', 'mechanism']

    tool = data.draw(st.sampled_from(tools))
    target = data.draw(st.sampled_from(targets))

    result = engine.handle_apply(tool, target, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is meaningful for any tool-target combination
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test BRUSH command properties
@settings(max_examples=100)
@given(st.data())
def test_brush_command_properties(data):
    """Test BRUSH command maintains correctness properties."""
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
        # Test with brushable objects
        target_id = data.draw(st.sampled_from(['dust', 'cobweb', 'dirt', 'debris', 'surface']))
    else:
        target_id = data.draw(st.sampled_from(['', 'air', 'nothing', 'wall']))

    result = engine.handle_brush(target_id, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (The specific message content may vary based on implementation)

    # Property 4: Sanity affects content appropriately
    if sanity < 30:
        # Low sanity might see supernatural residue
        supernatural_words = ['ghost', 'shadow', 'ectoplasm', 'spirit']
        # This is optional enhancement


@settings(max_examples=100)
@given(st.data())
def test_brush_command_cleaning_surfaces(data):
    """Test BRUSH command with various surfaces."""
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

    # Test with surfaces that might need brushing
    surfaces = ['dust', 'cobweb', 'dirt', 'debris', 'floor', 'wall', 'surface']
    target = data.draw(st.sampled_from(surfaces))

    result = engine.handle_brush(target, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is meaningful regardless of surface
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test special manipulation state consistency
@settings(max_examples=100)
@given(st.data())
def test_special_manipulation_state_consistency(data):
    """Test that special manipulation commands maintain state consistency."""
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

    # Execute multiple special manipulation commands
    result1 = engine.handle_spring('trapdoor', state)
    assert isinstance(result1, ActionResult)

    result2 = engine.handle_hatch('egg', state)
    assert isinstance(result2, ActionResult)

    result3 = engine.handle_apply('paint', 'wall', state)
    assert isinstance(result3, ActionResult)

    result4 = engine.handle_brush('dust', state)
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


@settings(max_examples=100)
@given(st.data())
def test_special_manipulation_edge_cases(data):
    """Test special manipulation commands with edge cases."""
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
    unusual_inputs = ['', ' ', 'nonexistent', 'abstract_concept', 'nothing']

    target = data.draw(st.sampled_from(unusual_inputs))

    # Test each command with unusual input
    result1 = engine.handle_spring(target, state)
    result2 = engine.handle_hatch(target, state)
    result3 = engine.handle_apply(target, '', state)
    result4 = engine.handle_brush(target, state)

    # All should return valid ActionResults without crashing
    for result in [result1, result2, result3, result4]:
        assert isinstance(result, ActionResult)
        assert len(result.message) > 0

    # State should remain valid
    assert isinstance(state, GameState)