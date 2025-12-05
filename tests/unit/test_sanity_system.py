"""
Unit Tests for Sanity System

Tests the Halloween sanity mechanics including sanity loss/gain,
threshold detection, and room effects.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler'))

import pytest
from state_manager import GameState
from sanity_system import SanitySystem, SanityThreshold
from world_loader import Room


class TestSanityLoss:
    """Tests for sanity loss functionality."""
    
    def test_sanity_loss_from_cursed_room(self):
        """
        Test sanity loss when entering a cursed room.
        
        **Validates: Requirements 6.1**
        """
        state = GameState.create_new_game()
        state.sanity = 100
        sanity_system = SanitySystem()
        
        # Create a cursed room with -10 sanity effect
        cursed_room = Room(
            id="cursed_chamber",
            name="Cursed Chamber",
            description_original="A dark chamber",
            description_spooky="A chamber filled with malevolent energy",
            exits={},
            items=[],
            sanity_effect=-10,
            is_cursed_room=True
        )
        
        # Process room entry
        notifications = sanity_system.process_room_entry(state, cursed_room)
        
        # Verify sanity decreased
        assert state.sanity == 90
        assert len(notifications) > 0
        assert any("sanity" in n.lower() or "dread" in n.lower() for n in notifications)
    
    def test_sanity_loss_basic(self):
        """
        Test basic sanity loss functionality.
        
        **Validates: Requirements 6.1**
        """
        state = GameState.create_new_game()
        state.sanity = 80
        sanity_system = SanitySystem()
        
        notifications = sanity_system.apply_sanity_loss(state, 20, "test")
        
        assert state.sanity == 60
        assert len(notifications) > 0
    
    def test_sanity_loss_clamped_at_zero(self):
        """
        Test that sanity loss is clamped at 0.
        
        **Validates: Requirements 6.1**
        """
        state = GameState.create_new_game()
        state.sanity = 30
        sanity_system = SanitySystem()
        
        # Try to lose more sanity than available
        sanity_system.apply_sanity_loss(state, 50, "test")
        
        assert state.sanity == 0
    
    def test_sanity_loss_threshold_notification(self):
        """
        Test that crossing sanity thresholds generates notifications.
        
        **Validates: Requirements 6.2, 6.3, 6.4**
        """
        state = GameState.create_new_game()
        state.sanity = 76  # Just above disturbed threshold
        sanity_system = SanitySystem()
        
        # Cross into disturbed threshold
        notifications = sanity_system.apply_sanity_loss(state, 2, "test")
        
        assert state.sanity == 74
        # Should get notification about threshold change
        assert any("perception" in n.lower() or "disturbed" in n.lower() for n in notifications)


class TestSanityGain:
    """Tests for sanity gain functionality."""
    
    def test_sanity_gain_in_safe_room(self):
        """
        Test sanity gain when resting in a safe room.
        
        **Validates: Requirements 6.5**
        """
        state = GameState.create_new_game()
        state.sanity = 50
        sanity_system = SanitySystem()
        
        # Create a safe room
        safe_room = Room(
            id="sanctuary",
            name="Sanctuary",
            description_original="A peaceful room",
            description_spooky="A room where the darkness seems less oppressive",
            exits={},
            items=[],
            is_safe_room=True
        )
        
        # Process turn in safe room
        notifications = sanity_system.process_turn_in_safe_room(state, safe_room)
        
        # Verify sanity increased
        assert state.sanity == 60
        assert len(notifications) > 0
        assert any("safe" in n.lower() or "sanity" in n.lower() for n in notifications)
    
    def test_sanity_gain_basic(self):
        """
        Test basic sanity gain functionality.
        
        **Validates: Requirements 6.5**
        """
        state = GameState.create_new_game()
        state.sanity = 50
        sanity_system = SanitySystem()
        
        sanity_system.apply_sanity_gain(state, 20)
        
        assert state.sanity == 70
    
    def test_sanity_gain_clamped_at_100(self):
        """
        Test that sanity gain is clamped at 100.
        
        **Validates: Requirements 6.5**
        """
        state = GameState.create_new_game()
        state.sanity = 90
        sanity_system = SanitySystem()
        
        # Try to gain more sanity than maximum
        sanity_system.apply_sanity_gain(state, 20)
        
        assert state.sanity == 100
    
    def test_sanity_gain_no_effect_at_max(self):
        """
        Test that sanity gain has no effect when already at maximum.
        
        **Validates: Requirements 6.5**
        """
        state = GameState.create_new_game()
        state.sanity = 100
        sanity_system = SanitySystem()
        
        sanity_system.apply_sanity_gain(state, 10)
        
        assert state.sanity == 100


class TestSanityThresholds:
    """Tests for sanity threshold detection."""
    
    def test_normal_threshold(self):
        """
        Test detection of normal sanity threshold (75-100).
        
        **Validates: Requirements 6.2**
        """
        sanity_system = SanitySystem()
        
        # Test various values in normal range
        for sanity in [75, 80, 90, 100]:
            threshold = sanity_system.get_sanity_threshold(sanity)
            assert threshold.name == "normal"
            assert threshold.min_sanity == 75
            assert threshold.max_sanity == 100
    
    def test_disturbed_threshold(self):
        """
        Test detection of disturbed sanity threshold (50-74).
        
        **Validates: Requirements 6.2, 6.3**
        """
        sanity_system = SanitySystem()
        
        # Test various values in disturbed range
        for sanity in [50, 60, 70, 74]:
            threshold = sanity_system.get_sanity_threshold(sanity)
            assert threshold.name == "disturbed"
            assert threshold.min_sanity == 50
            assert threshold.max_sanity == 74
    
    def test_unreliable_threshold(self):
        """
        Test detection of unreliable narrator threshold (25-49).
        
        **Validates: Requirements 6.3, 6.4**
        """
        sanity_system = SanitySystem()
        
        # Test various values in unreliable range
        for sanity in [25, 30, 40, 49]:
            threshold = sanity_system.get_sanity_threshold(sanity)
            assert threshold.name == "unreliable"
            assert threshold.min_sanity == 25
            assert threshold.max_sanity == 49
    
    def test_garbled_threshold(self):
        """
        Test detection of garbled/severe threshold (0-24).
        
        **Validates: Requirements 6.4**
        """
        sanity_system = SanitySystem()
        
        # Test various values in garbled range
        for sanity in [0, 10, 20, 24]:
            threshold = sanity_system.get_sanity_threshold(sanity)
            assert threshold.name == "garbled"
            assert threshold.min_sanity == 0
            assert threshold.max_sanity == 24
    
    def test_threshold_boundaries(self):
        """
        Test sanity threshold boundaries are correct.
        
        **Validates: Requirements 6.2, 6.3, 6.4**
        """
        sanity_system = SanitySystem()
        
        # Test boundary values
        assert sanity_system.get_sanity_threshold(75).name == "normal"
        assert sanity_system.get_sanity_threshold(74).name == "disturbed"
        assert sanity_system.get_sanity_threshold(50).name == "disturbed"
        assert sanity_system.get_sanity_threshold(49).name == "unreliable"
        assert sanity_system.get_sanity_threshold(25).name == "unreliable"
        assert sanity_system.get_sanity_threshold(24).name == "garbled"


class TestDescriptionVariants:
    """Tests for description variant selection."""
    
    def test_description_variant_at_different_sanity_levels(self):
        """
        Test description variants at different sanity levels.
        
        **Validates: Requirements 6.2, 6.3, 6.4**
        """
        sanity_system = SanitySystem()
        base_description = "A dark and foreboding chamber"
        
        # Test at different sanity levels
        for sanity in [100, 75, 50, 25, 0]:
            variant = sanity_system.get_description_variant(base_description, sanity)
            
            # Should return a string
            assert isinstance(variant, str)
            
            # In MVP, should return base description
            assert variant == base_description
    
    def test_description_variant_returns_string(self):
        """
        Test that description variant always returns a string.
        
        **Validates: Requirements 6.2, 6.3, 6.4**
        """
        sanity_system = SanitySystem()
        
        variant = sanity_system.get_description_variant("Test description", 50)
        assert isinstance(variant, str)


class TestRoomEffects:
    """Tests for room-based sanity effects."""
    
    def test_cursed_room_entry(self):
        """
        Test entering a cursed room decreases sanity.
        
        **Validates: Requirements 6.1**
        """
        state = GameState.create_new_game()
        state.sanity = 100
        sanity_system = SanitySystem()
        
        cursed_room = Room(
            id="cursed",
            name="Cursed Room",
            description_original="Dark",
            description_spooky="Very dark",
            exits={},
            items=[],
            sanity_effect=-15,
            is_cursed_room=True
        )
        
        notifications = sanity_system.process_room_entry(state, cursed_room)
        
        assert state.sanity == 85
        assert len(notifications) > 0
    
    def test_safe_room_entry(self):
        """
        Test entering a safe room provides notification.
        
        **Validates: Requirements 6.5**
        """
        state = GameState.create_new_game()
        state.sanity = 80
        sanity_system = SanitySystem()
        
        safe_room = Room(
            id="safe",
            name="Safe Room",
            description_original="Peaceful",
            description_spooky="Less oppressive",
            exits={},
            items=[],
            is_safe_room=True
        )
        
        notifications = sanity_system.process_room_entry(state, safe_room)
        
        # Should get notification about safe room
        assert any("safe" in n.lower() for n in notifications)
    
    def test_neutral_room_no_effect(self):
        """
        Test that neutral rooms don't affect sanity.
        
        **Validates: Requirements 6.1, 6.5**
        """
        state = GameState.create_new_game()
        state.sanity = 75
        sanity_system = SanitySystem()
        
        neutral_room = Room(
            id="neutral",
            name="Neutral Room",
            description_original="Normal",
            description_spooky="Spooky but neutral",
            exits={},
            items=[],
            sanity_effect=0
        )
        
        notifications = sanity_system.process_room_entry(state, neutral_room)
        
        # Sanity should not change
        assert state.sanity == 75


class TestSevereEffects:
    """Tests for severe sanity effects."""
    
    def test_severe_effects_trigger_below_25(self):
        """
        Test that severe effects trigger below 25 sanity.
        
        **Validates: Requirements 6.4**
        """
        sanity_system = SanitySystem()
        
        # Should trigger below 25
        assert sanity_system.should_trigger_severe_effects(24) is True
        assert sanity_system.should_trigger_severe_effects(10) is True
        assert sanity_system.should_trigger_severe_effects(0) is True
        
        # Should not trigger at or above 25
        assert sanity_system.should_trigger_severe_effects(25) is False
        assert sanity_system.should_trigger_severe_effects(50) is False
        assert sanity_system.should_trigger_severe_effects(100) is False


class TestSanityStatusMessages:
    """Tests for sanity status messages."""
    
    def test_status_messages_at_different_levels(self):
        """
        Test that appropriate status messages are returned at different sanity levels.
        
        **Validates: Requirements 6.2, 6.3, 6.4**
        """
        sanity_system = SanitySystem()
        
        # Test various sanity levels
        message_100 = sanity_system.get_sanity_status_message(100)
        message_80 = sanity_system.get_sanity_status_message(80)
        message_60 = sanity_system.get_sanity_status_message(60)
        message_40 = sanity_system.get_sanity_status_message(40)
        message_10 = sanity_system.get_sanity_status_message(10)
        
        # All should return strings
        assert isinstance(message_100, str)
        assert isinstance(message_80, str)
        assert isinstance(message_60, str)
        assert isinstance(message_40, str)
        assert isinstance(message_10, str)
        
        # Messages should be different at different levels
        assert message_100 != message_10
        
        # Low sanity should have more severe messages
        assert len(message_10) > 0
