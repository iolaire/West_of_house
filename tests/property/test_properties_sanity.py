"""
Property-Based Tests for Sanity System

Tests correctness properties related to the Halloween sanity mechanics,
including sanity bounds, threshold effects, and description variants.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler'))

import pytest
from hypothesis import given, strategies as st, settings
from state_manager import GameState
from sanity_system import SanitySystem
from world_loader import Room


# Feature: game-backend-api, Property 10: Sanity bounds
@settings(max_examples=100)
@given(
    initial_sanity=st.integers(min_value=0, max_value=100),
    sanity_changes=st.lists(
        st.integers(min_value=-50, max_value=50),
        min_size=1,
        max_size=20
    )
)
def test_sanity_bounds(initial_sanity, sanity_changes):
    """
    For any sequence of sanity changes, sanity should always stay in [0, 100].
    
    **Validates: Requirements 6.1, 6.5**
    
    This property ensures that sanity is properly clamped to valid range
    regardless of how many loss or gain operations are applied.
    """
    # Create game state with initial sanity
    state = GameState.create_new_game()
    state.sanity = initial_sanity
    
    # Create sanity system
    sanity_system = SanitySystem()
    
    # Apply sequence of sanity changes
    for change in sanity_changes:
        if change > 0:
            # Sanity gain
            sanity_system.apply_sanity_gain(state, change)
        else:
            # Sanity loss
            sanity_system.apply_sanity_loss(state, abs(change), "test")
        
        # Verify sanity is always in valid range
        assert 0 <= state.sanity <= 100, \
            f"Sanity {state.sanity} out of bounds after change {change}"


# Feature: game-backend-api, Property 10: Sanity bounds (edge cases)
@settings(max_examples=100)
@given(
    initial_sanity=st.integers(min_value=0, max_value=100),
    large_loss=st.integers(min_value=100, max_value=1000),
    large_gain=st.integers(min_value=100, max_value=1000)
)
def test_sanity_bounds_extreme_values(initial_sanity, large_loss, large_gain):
    """
    For any sanity value, applying extreme loss or gain should clamp to [0, 100].
    
    **Validates: Requirements 6.1, 6.5**
    
    Tests that even very large sanity changes are properly bounded.
    """
    state = GameState.create_new_game()
    state.sanity = initial_sanity
    sanity_system = SanitySystem()
    
    # Apply large loss
    sanity_system.apply_sanity_loss(state, large_loss, "extreme test")
    assert 0 <= state.sanity <= 100
    assert state.sanity == 0  # Should be clamped to 0
    
    # Apply large gain
    sanity_system.apply_sanity_gain(state, large_gain)
    assert 0 <= state.sanity <= 100
    assert state.sanity == 100  # Should be clamped to 100


# Additional property: Sanity loss always decreases or maintains sanity
@settings(max_examples=100)
@given(
    initial_sanity=st.integers(min_value=0, max_value=100),
    loss_amount=st.integers(min_value=1, max_value=50)
)
def test_sanity_loss_decreases(initial_sanity, loss_amount):
    """
    For any sanity value, applying sanity loss should never increase sanity.
    
    **Validates: Requirements 6.1**
    """
    state = GameState.create_new_game()
    state.sanity = initial_sanity
    sanity_system = SanitySystem()
    
    old_sanity = state.sanity
    sanity_system.apply_sanity_loss(state, loss_amount, "test")
    
    # Sanity should decrease or stay at 0
    assert state.sanity <= old_sanity


# Additional property: Sanity gain always increases or maintains sanity
@settings(max_examples=100)
@given(
    initial_sanity=st.integers(min_value=0, max_value=100),
    gain_amount=st.integers(min_value=1, max_value=50)
)
def test_sanity_gain_increases(initial_sanity, gain_amount):
    """
    For any sanity value, applying sanity gain should never decrease sanity.
    
    **Validates: Requirements 6.5**
    """
    state = GameState.create_new_game()
    state.sanity = initial_sanity
    sanity_system = SanitySystem()
    
    old_sanity = state.sanity
    sanity_system.apply_sanity_gain(state, gain_amount)
    
    # Sanity should increase or stay at 100
    assert state.sanity >= old_sanity


# Additional property: Zero changes have no effect
@settings(max_examples=100)
@given(initial_sanity=st.integers(min_value=0, max_value=100))
def test_zero_sanity_changes_no_effect(initial_sanity):
    """
    For any sanity value, applying zero loss or gain should not change sanity.
    
    **Validates: Requirements 6.1, 6.5**
    """
    state = GameState.create_new_game()
    state.sanity = initial_sanity
    sanity_system = SanitySystem()
    
    # Apply zero loss
    sanity_system.apply_sanity_loss(state, 0, "test")
    assert state.sanity == initial_sanity
    
    # Apply zero gain
    sanity_system.apply_sanity_gain(state, 0)
    assert state.sanity == initial_sanity


# Additional property: Negative amounts are handled gracefully
@settings(max_examples=100)
@given(
    initial_sanity=st.integers(min_value=0, max_value=100),
    negative_amount=st.integers(min_value=-100, max_value=-1)
)
def test_negative_amounts_handled(initial_sanity, negative_amount):
    """
    For any sanity value, applying negative amounts should not cause errors.
    
    **Validates: Requirements 6.1, 6.5**
    """
    state = GameState.create_new_game()
    state.sanity = initial_sanity
    sanity_system = SanitySystem()
    
    # Negative loss should have no effect
    sanity_system.apply_sanity_loss(state, negative_amount, "test")
    assert state.sanity == initial_sanity
    
    # Negative gain should have no effect
    sanity_system.apply_sanity_gain(state, negative_amount)
    assert state.sanity == initial_sanity



# Feature: game-backend-api, Property 11: Sanity threshold effects
@settings(max_examples=100)
@given(sanity_level=st.integers(min_value=0, max_value=100))
def test_sanity_threshold_effects(sanity_level):
    """
    For any sanity level, the correct threshold should be returned.
    
    **Validates: Requirements 6.2, 6.3, 6.4**
    
    Sanity thresholds:
    - 100-75: Normal spooky descriptions
    - 74-50: Enhanced disturbed descriptions
    - 49-25: Unreliable narrator effects
    - 24-0: Severe effects including potential random teleportation
    """
    sanity_system = SanitySystem()
    threshold = sanity_system.get_sanity_threshold(sanity_level)
    
    # Verify threshold is within expected range
    assert threshold.min_sanity <= sanity_level <= threshold.max_sanity
    
    # Verify correct threshold name based on sanity level
    if 75 <= sanity_level <= 100:
        assert threshold.name == "normal"
        assert threshold.min_sanity == 75
        assert threshold.max_sanity == 100
    elif 50 <= sanity_level <= 74:
        assert threshold.name == "disturbed"
        assert threshold.min_sanity == 50
        assert threshold.max_sanity == 74
    elif 25 <= sanity_level <= 49:
        assert threshold.name == "unreliable"
        assert threshold.min_sanity == 25
        assert threshold.max_sanity == 49
    elif 0 <= sanity_level <= 24:
        assert threshold.name == "garbled"
        assert threshold.min_sanity == 0
        assert threshold.max_sanity == 24


# Additional property: Threshold transitions are consistent
@settings(max_examples=100)
@given(
    initial_sanity=st.integers(min_value=76, max_value=100),
    loss_amount=st.integers(min_value=1, max_value=100)
)
def test_threshold_transitions(initial_sanity, loss_amount):
    """
    For any sanity loss that crosses thresholds, the new threshold should be correct.
    
    **Validates: Requirements 6.2, 6.3, 6.4**
    """
    state = GameState.create_new_game()
    state.sanity = initial_sanity
    sanity_system = SanitySystem()
    
    # Get initial threshold
    old_threshold = sanity_system.get_sanity_threshold(state.sanity)
    
    # Apply sanity loss
    sanity_system.apply_sanity_loss(state, loss_amount, "test")
    
    # Get new threshold
    new_threshold = sanity_system.get_sanity_threshold(state.sanity)
    
    # Verify new threshold is correct for new sanity level
    assert new_threshold.min_sanity <= state.sanity <= new_threshold.max_sanity


# Additional property: Severe effects trigger at correct threshold
@settings(max_examples=100)
@given(sanity_level=st.integers(min_value=0, max_value=100))
def test_severe_effects_threshold(sanity_level):
    """
    For any sanity level, severe effects should trigger only below 25.
    
    **Validates: Requirements 6.4**
    """
    sanity_system = SanitySystem()
    should_trigger = sanity_system.should_trigger_severe_effects(sanity_level)
    
    if sanity_level < 25:
        assert should_trigger is True
    else:
        assert should_trigger is False


# Additional property: Description variants are returned
@settings(max_examples=100)
@given(
    sanity_level=st.integers(min_value=0, max_value=100),
    description=st.text(min_size=10, max_size=200)
)
def test_description_variant_returned(sanity_level, description):
    """
    For any sanity level and description, a description variant should be returned.
    
    **Validates: Requirements 6.2, 6.3, 6.4**
    
    In MVP, this returns the base description, but the function should always
    return a valid string.
    """
    sanity_system = SanitySystem()
    variant = sanity_system.get_description_variant(description, sanity_level)
    
    # Should return a string
    assert isinstance(variant, str)
    
    # Should not be empty if input wasn't empty
    if description:
        assert variant
    
    # In MVP, should return the base description
    assert variant == description
