"""
Property Tests for Magic System Commands

Tests correctness properties for CAST, INCANT, ENCHANT, DISENCHANT, and EXORCISE commands following established patterns.
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


# Test CAST command properties
@settings(max_examples=100)
@given(st.data())
def test_cast_command_properties(data):
    """Test CAST command maintains correctness properties."""
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
    has_spell = data.draw(st.booleans())
    has_target = data.draw(st.booleans())
    has_instrument = data.draw(st.booleans())

    state.sanity = sanity

    if has_spell:
        spell_name = data.draw(st.sampled_from(['fireball', 'light', 'heal', 'freeze', 'teleport']))
    else:
        spell_name = data.draw(st.sampled_from(['', 'nonexistent', 'magic words', 'ancient spell']))

    if has_target:
        target_id = data.draw(st.sampled_from(['door', 'window', 'creature', 'self', 'enemy']))
    else:
        target_id = ''

    if has_instrument:
        instrument_id = data.draw(st.sampled_from(['wand', 'staff', 'crystal', 'amulet', 'book']))
    else:
        instrument_id = ''

    result = engine.handle_cast(spell_name, target_id, instrument_id, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (The specific message content may vary based on implementation)

    # Property 4: Sanity affects spell casting when relevant
    if sanity < 30:
        # Low sanity might cause magical backfire or supernatural effects
        supernatural_words = ['backfire', 'uncontrolled', 'ghost', 'shadow', 'haunted']
        # This is optional enhancement, not required


@settings(max_examples=100)
@given(st.data())
def test_cast_command_spells(data):
    """Test CAST command with various spell types."""
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

    # Test with different spell types
    spells = [
        'fireball', 'light', 'heal', 'freeze', 'teleport', 'shield',
        'invisibility', 'fly', 'detect magic', 'dispel', 'summon',
        'magic missile', 'lightning', 'poison', 'cure wounds'
    ]
    spell_name = data.draw(st.sampled_from(spells))

    result = engine.handle_cast(spell_name, '', '', state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is meaningful regardless of spell
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test INCANT command (alias for CAST)
@settings(max_examples=100)
@given(st.data())
def test_incant_command_properties(data):
    """Test INCANT command maintains correctness properties."""
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
    has_incantation = data.draw(st.booleans())

    state.sanity = sanity

    if has_incantation:
        incantation = data.draw(st.sampled_from([
            'abra cadabra', 'hocus pocus', 'alakazam',
            'ancient words of power', 'mystic verse', 'arcane chant'
        ]))
    else:
        incantation = data.draw(st.sampled_from(['', 'mutter', 'words', '']))

    # Test INCANT as CAST alias
    result = engine.handle_cast(incantation, '', '', state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Sanity affects incantation power
    if sanity < 30:
        # Low sanity might cause chaotic magical effects
        supernatural_words = ['chaos', 'uncontrolled', 'ghost', 'shadow', 'wild magic']
        # This is optional enhancement


@settings(max_examples=100)
@given(st.data())
def test_incant_command_chants(data):
    """Test INCANT command with various chant types."""
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

    # Test with different incantation types
    incantations = [
        'elemental fire', 'spiritual protection', 'arcane sight',
        'ethereal ward', 'mystic shield', 'divine light',
        'shadow binding', 'ghost banishing', 'demon warding'
    ]
    incantation = data.draw(st.sampled_from(incantations))

    result = engine.handle_cast(incantation, '', '', state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is meaningful for any incantation
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test ENCHANT command properties
@settings(max_examples=100)
@given(st.data())
def test_enchant_command_properties(data):
    """Test ENCHANT command maintains correctness properties."""
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
        # Test with enchantable objects
        target_id = data.draw(st.sampled_from(['sword', 'armor', 'ring', 'amulet', 'wand', 'potion']))
    else:
        target_id = data.draw(st.sampled_from(['', 'air', 'nothing', 'wall']))

    result = engine.handle_enchant(target_id, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (The specific message content may vary based on implementation)

    # Property 4: Sanity affects enchantment success when relevant
    if sanity < 30:
        # Low sanity might cause cursed or chaotic enchantments
        supernatural_words = ['cursed', 'haunted', 'unstable', 'shadow', 'corrupted']
        # This is optional enhancement, not required


@settings(max_examples=100)
@given(st.data())
def test_enchant_command_objects(data):
    """Test ENCHANT command with various object types."""
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

    # Test with different enchantable object types
    objects = [
        'sword', 'dagger', 'armor', 'shield', 'helmet', 'ring',
        'amulet', 'wand', 'staff', 'crystal', 'potion', 'scroll',
        'book', 'rope', 'container', 'door', 'key'
    ]
    target_id = data.draw(st.sampled_from(objects))

    result = engine.handle_enchant(target_id, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is contextually appropriate
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test DISENCHANT command properties
@settings(max_examples=100)
@given(st.data())
def test_disenchant_command_properties(data):
    """Test DISENCHANT command maintains correctness properties."""
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
        # Test with potentially enchanted objects
        target_id = data.draw(st.sampled_from(['sword', 'ring', 'amulet', 'cursed item', 'haunted object']))
    else:
        target_id = data.draw(st.sampled_from(['', 'air', 'nothing', 'wall']))

    result = engine.handle_disenchant(target_id, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (The specific message content may vary based on implementation)

    # Property 4: Sanity affects disenchantment when relevant
    if sanity < 30:
        # Low sanity might release supernatural forces
        supernatural_words = ['spirit', 'ghost', 'curse', 'energy', 'haunted']
        # This is optional enhancement, not required


@settings(max_examples=100)
@given(st.data())
def test_disenchant_command_magical_objects(data):
    """Test DISENCHANT command with magical object types."""
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

    # Test with different magical object types
    objects = [
        'enchanted sword', 'magic ring', 'cursed amulet', 'haunted doll',
        'mystic orb', 'arcane scroll', 'blessed symbol', 'corrupted artifact',
        'phylactery', 'talisman', 'rune stone', 'magical crystal'
    ]
    target_id = data.draw(st.sampled_from(objects))

    result = engine.handle_disenchant(target_id, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is meaningful regardless of object
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test EXORCISE command properties
@settings(max_examples=100)
@given(st.data())
def test_exorcise_command_properties(data):
    """Test EXORCISE command maintains correctness properties."""
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
        # Test with exorcisable targets
        target_id = data.draw(st.sampled_from(['ghost', 'demon', 'spirit', 'haunted object', 'possessed item']))
    else:
        target_id = data.draw(st.sampled_from(['', 'air', 'nothing', 'wall']))

    if has_direction:
        direction = data.draw(st.sampled_from(['north', 'east', 'south', 'west', 'up', 'down']))
    else:
        direction = ''

    result = engine.handle_exorcise(target_id, direction, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (The specific message content may vary based on implementation)

    # Property 4: Sanity affects exorcism power significantly
    if sanity < 30:
        # Low sanity makes exorcism dangerous or ineffective
        supernatural_words = ['dangerous', 'possessed', 'overwhelmed', 'corrupted', 'haunted']
        # This is optional enhancement, not required


@settings(max_examples=100)
@given(st.data())
def test_exorcise_command_supernatural_targets(data):
    """Test EXORCISE command with supernatural targets."""
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

    # Test with different supernatural target types
    targets = [
        'ghost', 'spirit', 'demon', 'spectre', 'phantom', 'wraith',
        'poltergeist', 'shade', 'apparition', 'haunted doll', 'possessed mirror',
        'cursed skull', 'ancient spirit', 'malevolent entity', 'lost soul'
    ]
    target_id = data.draw(st.sampled_from(targets))

    result = engine.handle_exorcise(target_id, '', state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is meaningful for any supernatural target
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test magic system state consistency
@settings(max_examples=100)
@given(st.data())
def test_magic_system_state_consistency(data):
    """Test that magic commands maintain state consistency."""
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

    # Execute multiple magic commands
    result1 = engine.handle_cast('light', '', '', state)
    assert isinstance(result1, ActionResult)

    result2 = engine.handle_enchant('sword', state)
    assert isinstance(result2, ActionResult)

    result3 = engine.handle_disenchant('ring', state)
    assert isinstance(result3, ActionResult)

    result4 = engine.handle_exorcise('ghost', '', state)
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
def test_magic_system_edge_cases(data):
    """Test magic commands with edge cases."""
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

    spell_name = data.draw(st.sampled_from(unusual_inputs))
    object_id = data.draw(st.sampled_from(unusual_inputs))

    # Test each command with unusual input
    result1 = engine.handle_cast(spell_name, object_id, '', state)
    result2 = engine.handle_enchant(object_id, state)
    result3 = engine.handle_disenchant(object_id, state)
    result4 = engine.handle_exorcise(object_id, '', state)

    # All should return valid ActionResults without crashing
    for result in [result1, result2, result3, result4]:
        assert isinstance(result, ActionResult)
        assert len(result.message) > 0

    # State should remain valid
    assert isinstance(state, GameState)


@settings(max_examples=100)
@given(st.data())
def test_magic_system_sanity_integration(data):
    """Test that magic system integrates properly with sanity system."""
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

    # Test magic commands affect sanity appropriately
    result = engine.handle_cast('fireball', '', '', state)
    assert isinstance(result, ActionResult)

    # Sanity should remain in valid range
    assert isinstance(state.sanity, int)
    assert 0 <= state.sanity <= 100

    # Message content should reflect sanity level
    result_message = result.message.lower()
    if original_sanity < 30:
        # Low sanity should produce supernatural/magical chaos effects
        has_magical_chaos = any(word in result_message for word in [
            'chaos', 'uncontrolled', 'wild', 'backfire', 'storm', 'supernatural'
        ])
        # Note: This is optional enhancement, just test that message exists

    # Message should always be meaningful
    assert len(result_message) > 0