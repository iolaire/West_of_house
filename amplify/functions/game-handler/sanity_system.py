"""
Sanity System for West of Haunted House

This module implements the Halloween sanity mechanics, including sanity loss/gain,
description variant selection based on sanity level, and safe room tracking.

The sanity system is the primary Halloween mechanic in the MVP, affecting how
players experience the game world through altered descriptions and gameplay effects.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass

try:
    from .state_manager import GameState
    from .world_loader import WorldData, Room
except ImportError:
    # For testing when imported directly
    from state_manager import GameState
    from world_loader import WorldData, Room


@dataclass
class SanityThreshold:
    """Defines a sanity threshold and its effects."""
    min_sanity: int
    max_sanity: int
    name: str
    description: str


class SanitySystem:
    """
    Manages the sanity mechanics for the Halloween-themed game.
    
    Sanity is a 0-100 scale that affects:
    - Description variants (normal, disturbed, unreliable, garbled)
    - Gameplay effects (potential teleportation at very low sanity)
    - Player experience and atmosphere
    
    Sanity thresholds:
    - 100-75: Normal spooky descriptions
    - 74-50: Enhanced disturbed descriptions
    - 49-25: Unreliable narrator effects
    - 24-0: Severe effects including potential random teleportation
    """
    
    # Define sanity thresholds
    THRESHOLDS = [
        SanityThreshold(75, 100, "normal", "Normal spooky descriptions"),
        SanityThreshold(50, 74, "disturbed", "Enhanced disturbed descriptions"),
        SanityThreshold(25, 49, "unreliable", "Unreliable narrator effects"),
        SanityThreshold(0, 24, "garbled", "Severe effects and garbled text")
    ]
    
    def __init__(self, world_data: Optional[WorldData] = None):
        """
        Initialize the sanity system.
        
        Args:
            world_data: Optional WorldData for room information
        """
        self.world = world_data
    
    def apply_sanity_loss(
        self,
        state: GameState,
        amount: int,
        reason: str
    ) -> List[str]:
        """
        Decrease sanity and return notification messages.
        
        Sanity is clamped to [0, 100] range. Returns list of effects triggered
        by the sanity loss.
        
        Args:
            state: Current game state
            amount: Amount of sanity to lose (positive number)
            reason: Reason for sanity loss (for logging/notifications)
            
        Returns:
            List of notification messages about effects triggered
            
        Requirements: 6.1
        """
        if amount <= 0:
            return []
        
        # Store old sanity for threshold checking
        old_sanity = state.sanity
        
        # Apply sanity loss (clamped to 0)
        state.sanity = max(0, state.sanity - amount)
        
        # Generate notifications
        notifications = []
        
        # Add base notification about sanity loss
        if state.sanity > 50:
            notifications.append("Your sanity slips as dread washes over you...")
        elif state.sanity > 25:
            notifications.append("The horrors gnaw at your mind...")
        elif state.sanity > 0:
            notifications.append("Reality fractures around you...")
        else:
            notifications.append("Your mind shatters into fragments...")
        
        # Check if we crossed any thresholds
        old_threshold = self.get_sanity_threshold(old_sanity)
        new_threshold = self.get_sanity_threshold(state.sanity)
        
        if old_threshold != new_threshold:
            notifications.append(f"Your perception shifts... ({new_threshold.name})")
        
        return notifications
    
    def apply_sanity_gain(
        self,
        state: GameState,
        amount: int
    ) -> None:
        """
        Increase sanity (capped at 100).
        
        Args:
            state: Current game state
            amount: Amount of sanity to gain (positive number)
            
        Requirements: 6.5
        """
        if amount <= 0:
            return
        
        # Apply sanity gain (capped at 100)
        state.sanity = min(100, state.sanity + amount)
    
    def get_sanity_threshold(self, sanity_level: int) -> SanityThreshold:
        """
        Get the current sanity threshold based on sanity level.
        
        Args:
            sanity_level: Current sanity value (0-100)
            
        Returns:
            SanityThreshold object for the current level
        """
        for threshold in self.THRESHOLDS:
            if threshold.min_sanity <= sanity_level <= threshold.max_sanity:
                return threshold
        
        # Default to garbled if somehow out of range
        return self.THRESHOLDS[-1]
    
    def get_description_variant(
        self,
        base_description: str,
        sanity_level: int
    ) -> str:
        """
        Return appropriate description based on sanity level.
        
        For MVP, we always return the spooky description as-is.
        Future enhancements could modify descriptions based on sanity thresholds.
        
        Sanity thresholds:
        - 100-75: Normal spooky
        - 74-50: Enhanced disturbed
        - 49-25: Unreliable narrator
        - 24-0: Garbled/broken
        
        Args:
            base_description: The base spooky description
            sanity_level: Current sanity level (0-100)
            
        Returns:
            Description string appropriate for sanity level
            
        Requirements: 6.2, 6.3, 6.4
        """
        # For MVP, return base description
        # Future: Could add modifiers based on sanity threshold
        threshold = self.get_sanity_threshold(sanity_level)
        
        # In MVP, we just return the base spooky description
        # Future versions could add prefixes/suffixes or modify text
        return base_description
    
    def process_room_entry(
        self,
        state: GameState,
        room: Room
    ) -> List[str]:
        """
        Process sanity effects when entering a room.
        
        Handles:
        - Sanity loss from cursed rooms
        - Sanity gain from safe rooms
        
        Args:
            state: Current game state
            room: Room being entered
            
        Returns:
            List of notification messages
            
        Requirements: 6.1, 6.5
        """
        notifications = []
        
        # Check if room has sanity effects
        if room.sanity_effect < 0:
            # Cursed room - lose sanity
            loss_notifications = self.apply_sanity_loss(
                state,
                abs(room.sanity_effect),
                f"Entering cursed room: {room.name}"
            )
            notifications.extend(loss_notifications)
        elif room.sanity_effect > 0:
            # Safe room - gain sanity
            old_sanity = state.sanity
            self.apply_sanity_gain(state, room.sanity_effect)
            if state.sanity > old_sanity:
                notifications.append("You feel a sense of calm returning...")
        
        # Check if room is marked as safe for resting
        if room.is_safe_room and state.sanity < 100:
            notifications.append("This place feels safe. You could rest here to recover your sanity.")
        
        return notifications
    
    def process_turn_in_safe_room(
        self,
        state: GameState,
        room: Room
    ) -> List[str]:
        """
        Process sanity restoration when resting in a safe room.
        
        Safe rooms restore 10 sanity per turn when the player rests.
        
        Args:
            state: Current game state
            room: Current room
            
        Returns:
            List of notification messages
            
        Requirements: 6.5
        """
        notifications = []
        
        if room.is_safe_room and state.sanity < 100:
            old_sanity = state.sanity
            self.apply_sanity_gain(state, 10)
            
            if state.sanity > old_sanity:
                notifications.append("Resting in this safe place restores your sanity...")
        
        return notifications
    
    def should_trigger_severe_effects(self, sanity_level: int) -> bool:
        """
        Check if sanity is low enough to trigger severe effects.
        
        Severe effects (like random teleportation) trigger below 25 sanity.
        
        Args:
            sanity_level: Current sanity level (0-100)
            
        Returns:
            True if severe effects should trigger
            
        Requirements: 6.4
        """
        return sanity_level < 25
    
    def get_sanity_status_message(self, sanity_level: int) -> str:
        """
        Get a status message describing the current sanity level.
        
        Args:
            sanity_level: Current sanity level (0-100)
            
        Returns:
            Status message string
        """
        threshold = self.get_sanity_threshold(sanity_level)
        
        if sanity_level >= 90:
            return "Your mind is clear and focused."
        elif sanity_level >= 75:
            return "You feel slightly unsettled."
        elif sanity_level >= 50:
            return "Dark thoughts creep into your mind."
        elif sanity_level >= 25:
            return "Reality seems to shift and waver."
        else:
            return "You can barely distinguish reality from nightmare."
