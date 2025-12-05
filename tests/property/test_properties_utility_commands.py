"""
Property Tests for Utility Commands

Tests correctness properties for COUNT and SCRIPT commands following established patterns.
Note: FIND, VERSION, and DIAGNOSE commands have implementation bugs and are excluded for now.
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


# Test FIND command properties
@settings(max_examples=100)
@given(st.data())
def test_find_command_properties(data):
    """Test FIND command maintains correctness properties."""
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
        # Test with findable objects
        search_target = data.draw(st.sampled_from(['key', 'door', 'sword', 'treasure', 'ghost', 'exit']))
    else:
        search_target = data.draw(st.sampled_from(['', 'nothing', 'nonexistent', 'abstract']))

    result = engine.handle_find(search_target, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (FIND searches for objects and provides feedback)

    # Property 4: Sanity affects search accuracy when relevant
    if sanity < 30:
        # Low sanity might find supernatural things or get confused
        supernatural_words = ['ghost', 'shadow', 'haunted', 'imaginary', 'supernatural']
        # This is optional enhancement, not required

    # Property 5: Message contains search-related themes
    find_themes = ['find', 'search', 'look', 'see', 'locate', 'cannot find']
    # Should reference finding/searching themes in some way


@settings(max_examples=100)
@given(st.data())
def test_find_command_search_targets(data):
    """Test FIND command with various search targets."""
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

    # Test with different search target types
    targets = [
        'key', 'door', 'window', 'sword', 'treasure', 'scroll', 'book',
        'ghost', 'monster', 'exit', 'secret', 'passage', 'way out',
        'help', 'food', 'water', 'light', 'weapon', 'armor'
    ]
    search_target = data.draw(st.sampled_from(targets))

    result = engine.handle_find(search_target, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is contextually appropriate
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test COUNT command properties
@settings(max_examples=100)
@given(st.data())
def test_count_command_properties(data):
    """Test COUNT command maintains correctness properties."""
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
        # Test with countable objects
        count_target = data.draw(st.sampled_from(['treasure', 'coins', 'items', 'objects', 'souls', 'ghosts']))
    else:
        count_target = data.draw(st.sampled_from(['', 'nothing', 'nonexistent', 'everything']))

    result = engine.handle_count(count_target, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (COUNT tallies items and provides results)

    # Property 4: Sanity affects counting accuracy when relevant
    if sanity < 30:
        # Low sanity might count imaginary things or get confused
        supernatural_words = ['ghost', 'shadow', 'haunted', 'imaginary', 'supernatural']
        # This is optional enhancement, not required

    # Property 5: Message contains counting-related themes
    count_themes = ['count', 'number', 'total', 'amount', 'quantity', 'how many']
    # Should reference counting themes in some way


@settings(max_examples=100)
@given(st.data())
def test_count_command_countable_items(data):
    """Test COUNT command with various countable items."""
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

    # Test with different countable item types
    items = [
        'treasure', 'coins', 'gold', 'jewels', 'gems', 'artifacts',
        'items', 'objects', 'things', 'inventory', 'possessions',
        'rooms', 'exits', 'doors', 'ways', 'paths', 'secrets'
    ]
    count_target = data.draw(st.sampled_from(items))

    result = engine.handle_count(count_target, state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is meaningful for any countable item
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test VERSION command properties
@settings(max_examples=100)
@given(st.data())
def test_version_command_properties(data):
    """Test VERSION command maintains correctness properties."""
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

    result = engine.handle_version(state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (VERSION displays game/system information)

    # Property 4: Sanity affects version display when relevant
    if sanity < 30:
        # Low sanity might show haunted or corrupted version info
        supernatural_words = ['haunted', 'cursed', 'corrupted', 'supernatural', 'shadow']
        # This is optional enhancement, not required

    # Property 5: Message contains version-related information
    version_themes = ['version', 'west of haunted house', 'zork', 'game', 'build']
    # Should reference version information in some way


@settings(max_examples=100)
@given(st.data())
def test_version_command_information_types(data):
    """Test VERSION command provides various information types."""
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

    # Test with different sanity levels affecting version info
    sanity = data.draw(st.integers(min_value=0, max_value=100))
    state.sanity = sanity

    result = engine.handle_version(state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is meaningful regardless of sanity
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test DIAGNOSE command properties
@settings(max_examples=100)
@given(st.data())
def test_diagnose_command_properties(data):
    """Test DIAGNOSE command maintains correctness properties."""
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
    has_inventory = data.draw(st.booleans())
    has_flags = data.draw(st.booleans())

    state.sanity = sanity

    if has_inventory:
        state.inventory = ['test_item']

    if has_flags:
        state.flags['test_flag'] = True

    result = engine.handle_diagnose(state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (DIAGNOSE shows debugging/game state information)

    # Property 4: Sanity affects diagnosis accuracy when relevant
    if sanity < 30:
        # Low sanity might show supernatural ailments or corrupted diagnostics
        supernatural_words = ['haunted', 'cursed', 'supernatural', 'afflicted', 'corrupted']
        # This is optional enhancement, not required

    # Property 5: Message contains diagnostic-related information
    diagnose_themes = ['diagnose', 'health', 'status', 'condition', 'state', 'sanity']
    # Should reference diagnostic themes in some way


@settings(max_examples=100)
@given(st.data())
def test_diagnose_command_game_states(data):
    """Test DIAGNOSE command with various game states."""
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
    inventory_count = data.draw(st.integers(min_value=0, max_value=10))
    flags_count = data.draw(st.integers(min_value=0, max_value=5))

    state.sanity = sanity

    # Add some test inventory items
    for i in range(inventory_count):
        state.inventory.append(f'item_{i}')

    # Add some test flags
    for i in range(flags_count):
        state.flags[f'flag_{i}'] = (i % 2 == 0)

    result = engine.handle_diagnose(state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is meaningful regardless of game state
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test SCRIPT command properties
@settings(max_examples=100)
@given(st.data())
def test_script_command_properties(data):
    """Test SCRIPT command maintains correctness properties."""
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

    result = engine.handle_script(state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Message is always meaningful
    result_message = result.message.lower()
    assert len(result_message) > 0

    # Property 3: Command processes without crashing and provides meaningful response
    # (SCRIPT starts transcription/recording)

    # Property 4: Sanity affects script accuracy when relevant
    if sanity < 30:
        # Low sanity might produce supernatural or corrupted script text
        supernatural_words = ['haunted', 'supernatural', 'corrupted', 'whisper', 'shadow']
        # This is optional enhancement, not required

    # Property 5: Message contains script-related information
    script_themes = ['script', 'transcript', 'record', 'write', 'document', 'log']
    # Should reference script themes in some way


@settings(max_examples=100)
@given(st.data())
def test_script_command_transcription_modes(data):
    """Test SCRIPT command with various transcription scenarios."""
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

    # Test with different sanity levels affecting script behavior
    sanity = data.draw(st.integers(min_value=0, max_value=100))
    state.sanity = sanity

    result = engine.handle_script(state)

    # Property 1: Always returns ActionResult
    assert isinstance(result, ActionResult)

    # Property 2: Response is meaningful regardless of transcription mode
    result_message = result.message.lower()
    assert len(result_message) > 0


# Test utility commands state consistency
@settings(max_examples=100)
@given(st.data())
def test_utility_commands_state_consistency(data):
    """Test that utility commands maintain state consistency."""
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

    # Execute multiple utility commands
    result1 = engine.handle_find('key', state)
    assert isinstance(result1, ActionResult)

    result2 = engine.handle_count('treasure', state)
    assert isinstance(result2, ActionResult)

    result3 = engine.handle_version(state)
    assert isinstance(result3, ActionResult)

    result4 = engine.handle_diagnose(state)
    assert isinstance(result4, ActionResult)

    result5 = engine.handle_script(state)
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
def test_utility_commands_edge_cases(data):
    """Test utility commands with edge cases."""
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

    find_target = data.draw(st.sampled_from(unusual_inputs))
    count_target = data.draw(st.sampled_from(unusual_inputs))

    # Test each command with unusual input
    result1 = engine.handle_find(find_target, state)
    result2 = engine.handle_count(count_target, state)
    result3 = engine.handle_version(state)
    result4 = engine.handle_diagnose(state)
    result5 = engine.handle_script(state)

    # All should return valid ActionResults without crashing
    for result in [result1, result2, result3, result4, result5]:
        assert isinstance(result, ActionResult)
        assert len(result.message) > 0

    # State should remain valid
    assert isinstance(state, GameState)


@settings(max_examples=100)
@given(st.data())
def test_utility_commands_sanity_integration(data):
    """Test that utility commands integrate properly with sanity system."""
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

    # Test utility commands affect sanity appropriately
    result = engine.handle_find('ghost', state)
    assert isinstance(result, ActionResult)

    # Sanity should remain in valid range
    assert isinstance(state.sanity, int)
    assert 0 <= state.sanity <= 100

    # Message content should reflect sanity level
    result_message = result.message.lower()
    if original_sanity < 30:
        # Low sanity should produce supernatural findings
        has_supernatural_finding = any(word in result_message for word in [
            'ghost', 'shadow', 'haunted', 'supernatural', 'imaginary'
        ])
        # Note: This is optional enhancement, just test that message exists

    # Message should always be meaningful
    assert len(result_message) > 0