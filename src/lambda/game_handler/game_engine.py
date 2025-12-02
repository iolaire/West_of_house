"""
Game Engine for West of Haunted House

Core game logic for processing commands and managing game state.
Handles movement, object interactions, and game mechanics.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

try:
    from .state_manager import GameState
    from .world_loader import WorldData, Room
    from .command_parser import ParsedCommand
except ImportError:
    # For testing when imported directly
    from state_manager import GameState
    from world_loader import WorldData, Room
    from command_parser import ParsedCommand


@dataclass
class ActionResult:
    """Result of executing a game action."""
    success: bool
    message: str
    room_changed: bool = False
    new_room: Optional[str] = None
    inventory_changed: bool = False
    state_changes: Dict[str, Any] = field(default_factory=dict)
    notifications: List[str] = field(default_factory=list)
    sanity_change: int = 0
    souls_awarded: int = 0


class GameEngine:
    """
    Core game engine that processes commands and manages game state.
    
    Handles:
    - Room navigation with exit validation
    - Conditional exits based on flags
    - Room descriptions based on sanity level
    - State updates and turn progression
    """
    
    def __init__(self, world_data: WorldData):
        """
        Initialize the game engine with world data.
        
        Args:
            world_data: Loaded world data containing rooms, objects, and flags
        """
        self.world = world_data
    
    def handle_movement(
        self,
        direction: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle player movement between rooms.
        
        Validates exits against room data, checks conditional exits based on flags,
        updates current_room in state, and returns appropriate room descriptions.
        
        Args:
            direction: The direction to move (NORTH, SOUTH, EAST, WEST, UP, DOWN, IN, OUT)
            state: Current game state
            
        Returns:
            ActionResult with success status, message, and room information
            
        Requirements: 3.1, 3.2, 3.4, 3.5
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Validate direction exists in room exits
            if direction not in current_room.exits:
                return ActionResult(
                    success=False,
                    message=f"You cannot go {direction.lower()} from here. The way is blocked.",
                    room_changed=False
                )
            
            # Get target room ID
            target_room_id = current_room.exits[direction]
            
            # Check if exit is conditional on flags
            if current_room.flags_required:
                # Check if this exit requires specific flags
                # For now, we check if any flags are required for the room
                # More sophisticated flag checking can be added later
                for flag_name, required_value in current_room.flags_required.items():
                    current_value = state.get_flag(flag_name, False)
                    if current_value != required_value:
                        return ActionResult(
                            success=False,
                            message="The way is blocked. You need to do something first.",
                            room_changed=False
                        )
            
            # Get target room to validate it exists
            target_room = self.world.get_room(target_room_id)
            
            # Move player to new room
            state.move_to_room(target_room_id)
            
            # Get room description based on sanity level
            description = self.world.get_room_description(target_room_id, state.sanity)
            
            # Apply room effects (sanity changes)
            sanity_change = 0
            notifications = []
            
            if target_room.sanity_effect != 0:
                sanity_change = target_room.sanity_effect
                state.sanity = max(0, min(100, state.sanity + sanity_change))
                
                if sanity_change < 0:
                    notifications.append("Your sanity slips as dread washes over you...")
                elif sanity_change > 0:
                    notifications.append("You feel a sense of calm returning...")
            
            # Increment turn counter
            state.increment_turn()
            
            return ActionResult(
                success=True,
                message=description,
                room_changed=True,
                new_room=target_room_id,
                state_changes={
                    'current_room': target_room_id,
                    'moves': state.moves,
                    'turn_count': state.turn_count,
                    'sanity': state.sanity
                },
                notifications=notifications,
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            # Room not found or other validation error
            return ActionResult(
                success=False,
                message=f"An error occurred: {str(e)}",
                room_changed=False
            )
        except Exception as e:
            # Unexpected error
            return ActionResult(
                success=False,
                message="Something went wrong. Please try again.",
                room_changed=False
            )
    
    def execute_command(
        self,
        command: ParsedCommand,
        state: GameState
    ) -> ActionResult:
        """
        Execute a parsed command and update game state.
        
        Routes commands to appropriate handlers based on verb type.
        
        Args:
            command: Parsed command from CommandParser
            state: Current game state
            
        Returns:
            ActionResult with outcome of command execution
        """
        # Handle movement commands
        if command.verb == "GO" and command.direction:
            return self.handle_movement(command.direction, state)
        
        # Handle unknown commands
        if command.verb == "UNKNOWN":
            return ActionResult(
                success=False,
                message="I don't understand that command. Try 'go north', 'take lamp', or 'inventory'."
            )
        
        # Placeholder for other command types (to be implemented in future tasks)
        return ActionResult(
            success=False,
            message=f"The {command.verb} command is not yet implemented."
        )
