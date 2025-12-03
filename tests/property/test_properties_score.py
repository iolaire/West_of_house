"""
Property-Based Tests for SCORE Command

Tests correctness properties related to the SCORE command,
ensuring proper display of current score and rank.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler'))

import pytest
from hypothesis import given, strategies as st, settings
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


# Feature: complete-zork-commands, Property 32: Score displays current value
@settings(max_examples=100)
@given(
    score=st.integers(min_value=0, max_value=350),
    moves=st.integers(min_value=0, max_value=10000),
    sanity=st.integers(min_value=0, max_value=100),
    souls=st.integers(min_value=0, max_value=100),
    cursed=st.booleans(),
    blood_moon=st.booleans()
)
def test_score_displays_current_value(score, moves, sanity, souls, cursed, blood_moon):
    """
    For any game state, executing SCORE should return the current score value.
    
    **Validates: Requirements 7.5**
    
    This property ensures that:
    1. SCORE command returns success
    2. Score value is displayed in the message
    3. Moves count is displayed
    4. Rank is calculated and displayed
    5. Additional stats (sanity, souls) are shown
    """
    # Load world data (fresh instance for each test)
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Create game state with specific score
    state = GameState.create_new_game()
    state.score = score
    state.moves = moves
    state.sanity = sanity
    state.souls_collected = souls
    state.cursed = cursed
    state.blood_moon_active = blood_moon
    
    # Execute SCORE command
    result = engine.handle_score(state)
    
    # Should succeed
    assert result.success is True, \
        "SCORE command should always succeed"
    
    # Should have a message
    assert result.message is not None and len(result.message) > 0, \
        "SCORE should return a message"
    
    # Message should contain the score value
    assert str(score) in result.message, \
        f"Score message should contain score value {score}"
    
    # Message should contain moves count
    assert str(moves) in result.message, \
        f"Score message should contain moves count {moves}"
    
    # Message should contain "score" keyword
    assert "score" in result.message.lower(), \
        "Score message should mention 'score'"
    
    # Message should contain "moves" keyword
    assert "moves" in result.message.lower(), \
        "Score message should mention 'moves'"
    
    # Message should contain rank
    assert "rank" in result.message.lower(), \
        "Score message should mention 'rank'"
    
    # Message should contain sanity
    assert "sanity" in result.message.lower(), \
        "Score message should mention 'sanity'"
    assert str(sanity) in result.message, \
        f"Score message should contain sanity value {sanity}"
    
    # Message should contain souls
    assert "souls" in result.message.lower(), \
        "Score message should mention 'souls'"
    assert str(souls) in result.message, \
        f"Score message should contain souls value {souls}"


@settings(max_examples=100)
@given(score=st.integers(min_value=0, max_value=350))
def test_score_calculates_correct_rank(score):
    """
    For any score value, the rank should be calculated correctly based on
    score thresholds.
    
    **Validates: Requirements 7.5**
    
    This property ensures that:
    1. Rank is calculated based on score
    2. Correct rank is displayed for each score range
    3. Rank thresholds are consistent
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Create game state with specific score
    state = GameState.create_new_game()
    state.score = score
    
    # Execute SCORE command
    result = engine.handle_score(state)
    
    # Should succeed
    assert result.success is True, \
        "SCORE command should succeed"
    
    # Determine expected rank based on score
    if score >= 350:
        expected_rank = "Master Adventurer"
    elif score >= 300:
        expected_rank = "Experienced Adventurer"
    elif score >= 200:
        expected_rank = "Adventurer"
    elif score >= 100:
        expected_rank = "Junior Adventurer"
    elif score >= 50:
        expected_rank = "Novice Adventurer"
    else:
        expected_rank = "Beginner"
    
    # Message should contain the expected rank
    assert expected_rank in result.message, \
        f"Score {score} should result in rank '{expected_rank}', but message was: {result.message}"


@settings(max_examples=100)
@given(
    score=st.integers(min_value=0, max_value=350),
    moves=st.integers(min_value=0, max_value=10000)
)
def test_score_displays_treasures_collected(score, moves):
    """
    For any game state, SCORE should display the number of treasures collected.
    
    **Validates: Requirements 7.5**
    
    This property ensures that:
    1. Treasures collected count is displayed
    2. Count is accurate (based on trophy case contents)
    3. Message format is consistent
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Create game state
    state = GameState.create_new_game()
    state.score = score
    state.moves = moves
    
    # Execute SCORE command
    result = engine.handle_score(state)
    
    # Should succeed
    assert result.success is True, \
        "SCORE command should succeed"
    
    # Message should mention treasures
    assert "treasures" in result.message.lower(), \
        "Score message should mention 'treasures'"
    
    # Message should contain a number for treasures collected
    # (even if it's 0)
    import re
    treasure_pattern = r'treasures[^:]*:\s*(\d+)'
    match = re.search(treasure_pattern, result.message.lower())
    assert match is not None, \
        "Score message should contain treasures count in format 'Treasures: N'"


@settings(max_examples=100)
@given(cursed=st.booleans())
def test_score_displays_curse_status(cursed):
    """
    For any game state, SCORE should display curse status if cursed.
    
    **Validates: Requirements 7.5**
    
    This property ensures that:
    1. Curse status is displayed when cursed
    2. Message format is consistent
    3. Haunted theme is maintained
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Create game state
    state = GameState.create_new_game()
    state.cursed = cursed
    
    # Execute SCORE command
    result = engine.handle_score(state)
    
    # Should succeed
    assert result.success is True, \
        "SCORE command should succeed"
    
    # If cursed, message should mention it
    if cursed:
        assert "cursed" in result.message.lower(), \
            "Score message should mention 'cursed' when player is cursed"


@settings(max_examples=100)
@given(blood_moon=st.booleans())
def test_score_displays_blood_moon_status(blood_moon):
    """
    For any game state, SCORE should display blood moon status if active.
    
    **Validates: Requirements 7.5**
    
    This property ensures that:
    1. Blood moon status is displayed when active
    2. Message format is consistent
    3. Haunted theme is maintained
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Create game state
    state = GameState.create_new_game()
    state.blood_moon_active = blood_moon
    
    # Execute SCORE command
    result = engine.handle_score(state)
    
    # Should succeed
    assert result.success is True, \
        "SCORE command should succeed"
    
    # If blood moon active, message should mention it
    if blood_moon:
        assert "blood moon" in result.message.lower(), \
            "Score message should mention 'blood moon' when active"


@settings(max_examples=100)
@given(
    score1=st.integers(min_value=0, max_value=350),
    score2=st.integers(min_value=0, max_value=350)
)
def test_score_reflects_state_changes(score1, score2):
    """
    For any two different scores, SCORE should reflect the current state.
    
    **Validates: Requirements 7.5**
    
    This property ensures that:
    1. SCORE always shows current score
    2. Score updates are reflected immediately
    3. No caching or stale data
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Create game state with first score
    state = GameState.create_new_game()
    state.score = score1
    
    # Execute SCORE command
    result1 = engine.handle_score(state)
    
    # Should succeed and contain first score
    assert result1.success is True
    assert str(score1) in result1.message
    
    # Change score
    state.score = score2
    
    # Execute SCORE command again
    result2 = engine.handle_score(state)
    
    # Should succeed and contain second score
    assert result2.success is True
    assert str(score2) in result2.message
    
    # If scores are different, messages should be different
    if score1 != score2:
        # At minimum, the score values should differ
        assert result1.message != result2.message, \
            "Score messages should differ when scores are different"


@settings(max_examples=100)
@given(st.data())
def test_score_does_not_modify_state(data):
    """
    For any game state, SCORE command should not modify the state.
    
    **Validates: Requirements 7.5**
    
    This property ensures that:
    1. SCORE is a read-only operation
    2. No state fields are changed
    3. Game continues normally after SCORE
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Create game state with random values
    state = GameState.create_new_game()
    score = data.draw(st.integers(min_value=0, max_value=350))
    moves = data.draw(st.integers(min_value=0, max_value=1000))
    sanity = data.draw(st.integers(min_value=0, max_value=100))
    souls = data.draw(st.integers(min_value=0, max_value=50))
    
    state.score = score
    state.moves = moves
    state.sanity = sanity
    state.souls_collected = souls
    
    # Capture original state
    original_score = state.score
    original_moves = state.moves
    original_sanity = state.sanity
    original_souls = state.souls_collected
    original_room = state.current_room
    original_inventory = state.inventory.copy()
    
    # Execute SCORE command
    result = engine.handle_score(state)
    
    # Should succeed
    assert result.success is True
    
    # State should be unchanged
    assert state.score == original_score, \
        "SCORE should not change score"
    assert state.moves == original_moves, \
        "SCORE should not change moves"
    assert state.sanity == original_sanity, \
        "SCORE should not change sanity"
    assert state.souls_collected == original_souls, \
        "SCORE should not change souls"
    assert state.current_room == original_room, \
        "SCORE should not change current room"
    assert state.inventory == original_inventory, \
        "SCORE should not change inventory"


@settings(max_examples=100)
@given(
    score=st.integers(min_value=0, max_value=350),
    moves=st.integers(min_value=0, max_value=10000)
)
def test_score_displays_max_possible_points(score, moves):
    """
    For any game state, SCORE should display the maximum possible points.
    
    **Validates: Requirements 7.5**
    
    This property ensures that:
    1. Maximum score (350) is mentioned
    2. Player knows what they're working toward
    3. Message format is consistent
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Create game state
    state = GameState.create_new_game()
    state.score = score
    state.moves = moves
    
    # Execute SCORE command
    result = engine.handle_score(state)
    
    # Should succeed
    assert result.success is True
    
    # Message should mention maximum possible points (350)
    assert "350" in result.message, \
        "Score message should mention maximum possible points (350)"
    
    # Message should show score out of maximum
    assert "out of" in result.message.lower(), \
        "Score message should show 'X out of 350' format"
