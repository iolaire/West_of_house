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
    
    def handle_enter(
        self,
        object_id: Optional[str],
        state: GameState
    ) -> ActionResult:
        """
        Handle entering objects (vehicles, buildings, passages).
        
        Supports entering specific objects or using the IN direction to enter
        the current location. Validates entry points exist and updates player
        location appropriately.
        
        Args:
            object_id: The object to enter (optional, defaults to IN direction)
            state: Current game state
            
        Returns:
            ActionResult with success status, message, and room information
            
        Requirements: 2.2
        """
        try:
            # If no object specified, try to move IN
            if not object_id:
                return self.handle_movement("IN", state)
            
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory
            
            if not object_in_room and not object_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {object_id} here.",
                    room_changed=False
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Check if object is enterable
            is_enterable = game_object.state.get('is_enterable', False)
            
            if not is_enterable:
                return ActionResult(
                    success=False,
                    message=f"You can't enter the {object_id}.",
                    room_changed=False
                )
            
            # Check if object has an entry destination
            entry_destination = game_object.state.get('entry_destination', None)
            
            if not entry_destination:
                return ActionResult(
                    success=False,
                    message=f"There's nowhere to go inside the {object_id}.",
                    room_changed=False
                )
            
            # Check if entry requires any conditions
            entry_condition = game_object.state.get('entry_condition', None)
            if entry_condition:
                # Check if condition flag is met
                condition_met = state.get_flag(entry_condition, False)
                if not condition_met:
                    return ActionResult(
                        success=False,
                        message=f"You can't enter the {object_id} right now.",
                        room_changed=False
                    )
            
            # Get target room to validate it exists
            target_room = self.world.get_room(entry_destination)
            
            # Move player to new room
            state.move_to_room(entry_destination)
            
            # Check if room is lit
            is_lit = self.is_room_lit(entry_destination, state)
            
            # Get room description
            if not is_lit:
                description = self.get_darkness_description(entry_destination)
            else:
                description = self.world.get_room_description(entry_destination, state.sanity)
            
            # Apply room effects
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
            
            # Apply lamp battery drain
            lamp_notifications = self.apply_lamp_battery_drain(state)
            notifications.extend(lamp_notifications)
            
            # Create success message with haunted theme
            enter_message = f"You enter the {object_id}, crossing into its shadowy interior."
            full_message = f"{enter_message}\n\n{description}"
            
            return ActionResult(
                success=True,
                message=full_message,
                room_changed=True,
                new_room=entry_destination,
                state_changes={
                    'current_room': entry_destination,
                    'moves': state.moves,
                    'turn_count': state.turn_count,
                    'sanity': state.sanity
                },
                notifications=notifications,
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            # Room or object not found
            return ActionResult(
                success=False,
                message=f"An error occurred: {str(e)}",
                room_changed=False
            )
        except Exception as e:
            # Unexpected error
            return ActionResult(
                success=False,
                message="Something went wrong while entering.",
                room_changed=False
            )
    
    def handle_exit(
        self,
        object_id: Optional[str],
        state: GameState
    ) -> ActionResult:
        """
        Handle exiting current location or object.
        
        Supports exiting specific objects or using the OUT direction to exit
        the current location. Validates exit points exist and updates player
        location appropriately.
        
        Args:
            object_id: The object to exit from (optional, defaults to OUT direction)
            state: Current game state
            
        Returns:
            ActionResult with success status, message, and room information
            
        Requirements: 2.2
        """
        try:
            # If no object specified, try to move OUT
            if not object_id:
                return self.handle_movement("OUT", state)
            
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if we're currently inside the specified object
            # This would require tracking what object the player is "in"
            # For now, we'll treat EXIT as equivalent to moving OUT
            
            # Check if object exists in current room
            if object_id not in current_room.items:
                return ActionResult(
                    success=False,
                    message=f"You're not in the {object_id}.",
                    room_changed=False
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Check if object has an exit destination
            exit_destination = game_object.state.get('exit_destination', None)
            
            if not exit_destination:
                # No specific exit destination, try OUT direction
                return self.handle_movement("OUT", state)
            
            # Get target room to validate it exists
            target_room = self.world.get_room(exit_destination)
            
            # Move player to new room
            state.move_to_room(exit_destination)
            
            # Check if room is lit
            is_lit = self.is_room_lit(exit_destination, state)
            
            # Get room description
            if not is_lit:
                description = self.get_darkness_description(exit_destination)
            else:
                description = self.world.get_room_description(exit_destination, state.sanity)
            
            # Apply room effects
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
            
            # Apply lamp battery drain
            lamp_notifications = self.apply_lamp_battery_drain(state)
            notifications.extend(lamp_notifications)
            
            # Create success message with haunted theme
            exit_message = f"You exit the {object_id}, emerging back into the open."
            full_message = f"{exit_message}\n\n{description}"
            
            return ActionResult(
                success=True,
                message=full_message,
                room_changed=True,
                new_room=exit_destination,
                state_changes={
                    'current_room': exit_destination,
                    'moves': state.moves,
                    'turn_count': state.turn_count,
                    'sanity': state.sanity
                },
                notifications=notifications,
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            # Room or object not found
            return ActionResult(
                success=False,
                message=f"An error occurred: {str(e)}",
                room_changed=False
            )
        except Exception as e:
            # Unexpected error
            return ActionResult(
                success=False,
                message="Something went wrong while exiting.",
                room_changed=False
            )
    
    def handle_board(
        self,
        vehicle_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle boarding vehicles (boat, basket, etc.).
        
        Validates that the vehicle is present and accessible, then places
        the player inside the vehicle. Tracks the current vehicle in game state.
        
        Args:
            vehicle_id: The vehicle to board
            state: Current game state
            
        Returns:
            ActionResult with success status, message, and state updates
            
        Requirements: 2.3
        """
        try:
            # Check if already in a vehicle
            if state.current_vehicle:
                return ActionResult(
                    success=False,
                    message=f"You're already in the {state.current_vehicle}. You need to disembark first.",
                    room_changed=False
                )
            
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if vehicle is in current room or inventory
            vehicle_in_room = vehicle_id in current_room.items
            vehicle_in_inventory = vehicle_id in state.inventory
            
            if not vehicle_in_room and not vehicle_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {vehicle_id} here.",
                    room_changed=False
                )
            
            # Get vehicle object
            vehicle = self.world.get_object(vehicle_id)
            
            # Check if object is actually a vehicle
            is_vehicle = vehicle.state.get('is_vehicle', False)
            
            if not is_vehicle:
                return ActionResult(
                    success=False,
                    message=f"You can't board the {vehicle_id}.",
                    room_changed=False
                )
            
            # Check if vehicle requires specific conditions
            requires_water = vehicle.state.get('requires_water', False)
            if requires_water:
                # Check if current room has water
                room_has_water = current_room.state.get('has_water', False)
                if not room_has_water:
                    return ActionResult(
                        success=False,
                        message=f"The {vehicle_id} can't be used here. It needs water.",
                        room_changed=False
                    )
            
            # Board the vehicle
            state.current_vehicle = vehicle_id
            
            # Create success message with haunted theme
            board_message = f"You climb into the {vehicle_id}, settling into its cold, unwelcoming interior."
            
            return ActionResult(
                success=True,
                message=board_message,
                room_changed=False,
                state_changes={
                    'current_vehicle': state.current_vehicle
                }
            )
            
        except ValueError as e:
            # Vehicle not found
            return ActionResult(
                success=False,
                message=f"You don't see any {vehicle_id} here.",
                room_changed=False
            )
        except Exception as e:
            # Unexpected error
            return ActionResult(
                success=False,
                message="Something went wrong while boarding.",
                room_changed=False
            )
    
    def handle_disembark(
        self,
        vehicle_id: Optional[str],
        state: GameState
    ) -> ActionResult:
        """
        Handle disembarking from vehicles.
        
        Removes the player from the current vehicle. If vehicle_id is specified,
        validates that the player is in that specific vehicle.
        
        Args:
            vehicle_id: The vehicle to disembark from (optional, defaults to current vehicle)
            state: Current game state
            
        Returns:
            ActionResult with success status, message, and state updates
            
        Requirements: 2.4
        """
        try:
            # Check if player is in a vehicle
            if not state.current_vehicle:
                return ActionResult(
                    success=False,
                    message="You're not in any vehicle.",
                    room_changed=False
                )
            
            # If specific vehicle specified, validate it matches current vehicle
            if vehicle_id and vehicle_id != state.current_vehicle:
                return ActionResult(
                    success=False,
                    message=f"You're not in the {vehicle_id}. You're in the {state.current_vehicle}.",
                    room_changed=False
                )
            
            # Get the vehicle name for the message
            vehicle_name = state.current_vehicle
            
            # Disembark from vehicle
            state.current_vehicle = None
            
            # Create success message with haunted theme
            disembark_message = f"You climb out of the {vehicle_name}, your feet finding solid ground once more."
            
            return ActionResult(
                success=True,
                message=disembark_message,
                room_changed=False,
                state_changes={
                    'current_vehicle': state.current_vehicle
                }
            )
            
        except Exception as e:
            # Unexpected error
            return ActionResult(
                success=False,
                message="Something went wrong while disembarking.",
                room_changed=False
            )
    
    def handle_climb(
        self,
        direction: str,
        object_id: Optional[str],
        state: GameState
    ) -> ActionResult:
        """
        Handle climbing up or down with climbable objects.
        
        Validates that the object is climbable, checks for valid exits in the
        specified direction, and moves the player to the connected room.
        
        Args:
            direction: The direction to climb (UP or DOWN)
            object_id: The object to climb (optional, can be implicit from room)
            state: Current game state
            
        Returns:
            ActionResult with success status, message, and room information
            
        Requirements: 2.1
        """
        try:
            # Validate direction is UP or DOWN
            if direction not in ["UP", "DOWN"]:
                return ActionResult(
                    success=False,
                    message="You can only climb up or down.",
                    room_changed=False
                )
            
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if the room has an exit in the specified direction
            if direction not in current_room.exits:
                return ActionResult(
                    success=False,
                    message=f"There's nothing to climb {direction.lower()} here.",
                    room_changed=False
                )
            
            # If an object is specified, validate it exists and is climbable
            if object_id:
                # Check if object is in current room
                if object_id not in current_room.items:
                    # Check if it's mentioned in the room description (scenery)
                    try:
                        game_object = self.world.get_object(object_id)
                        # Object exists but not in room
                        return ActionResult(
                            success=False,
                            message=f"You don't see any {object_id} here.",
                            room_changed=False
                        )
                    except ValueError:
                        # Object doesn't exist at all
                        return ActionResult(
                            success=False,
                            message=f"You don't see any {object_id} here.",
                            room_changed=False
                        )
                
                # Get object and check if it's climbable
                game_object = self.world.get_object(object_id)
                is_climbable = game_object.state.get('is_climbable', False)
                
                if not is_climbable:
                    return ActionResult(
                        success=False,
                        message=f"You can't climb the {object_id}.",
                        room_changed=False
                    )
            
            # Get target room ID
            target_room_id = current_room.exits[direction]
            
            # Check if exit is conditional on flags
            if current_room.flags_required:
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
            
            # Check if room is lit (for dark rooms)
            is_lit = self.is_room_lit(target_room_id, state)
            
            # Get room description based on lighting and sanity level
            if not is_lit:
                description = self.get_darkness_description(target_room_id)
            else:
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
            
            # Apply lamp battery drain
            lamp_notifications = self.apply_lamp_battery_drain(state)
            notifications.extend(lamp_notifications)
            
            # Create success message with haunted theme
            climb_message = f"You climb {direction.lower()}, your hands gripping cold surfaces."
            full_message = f"{climb_message}\n\n{description}"
            
            return ActionResult(
                success=True,
                message=full_message,
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
                message="Something went wrong while climbing.",
                room_changed=False
            )
    
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
            
            # Puzzle-specific movement checks
            # Puzzle 2: Kitchen window entry
            if state.current_room == "east_of_house" and target_room_id == "kitchen":
                kitchen_window_open = state.get_flag("kitchen_window_open", False)
                if not kitchen_window_open:
                    return ActionResult(
                        success=False,
                        message="The window is not open wide enough to enter. You need to open it first.",
                        room_changed=False
                    )
            
            # Puzzle 1: Trap door to cellar
            if state.current_room == "living_room" and target_room_id == "cellar" and direction == "DOWN":
                trap_door_open = state.get_flag("trap_door_open", False)
                if not trap_door_open:
                    return ActionResult(
                        success=False,
                        message="The trap door is closed. You need to open it first.",
                        room_changed=False
                    )
            
            # Puzzle 3: Grating to underground (if grating exists)
            if state.current_room == "grating_clearing" and direction == "DOWN":
                grate_unlocked = state.get_flag("grate_unlocked", False)
                if not grate_unlocked:
                    return ActionResult(
                        success=False,
                        message="The grating is locked. You need to unlock it first.",
                        room_changed=False
                    )
            
            # Get target room to validate it exists
            target_room = self.world.get_room(target_room_id)
            
            # Move player to new room
            state.move_to_room(target_room_id)
            
            # Check if room is lit (for dark rooms)
            is_lit = self.is_room_lit(target_room_id, state)
            
            # Get room description based on lighting and sanity level
            if not is_lit:
                description = self.get_darkness_description(target_room_id)
            else:
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
            
            # Apply lamp battery drain
            lamp_notifications = self.apply_lamp_battery_drain(state)
            notifications.extend(lamp_notifications)
            
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
    
    def handle_take(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle taking an object from the current room.
        
        Validates that object is takeable, adds to inventory, removes from room.
        
        Args:
            object_id: The object identifier to take
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 4.2, 4.3, 5.2, 5.3
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if object is in current room
            if object_id not in current_room.items:
                # Check if already in inventory
                if object_id in state.inventory:
                    return ActionResult(
                        success=False,
                        message="You already have that."
                    )
                return ActionResult(
                    success=False,
                    message=f"You don't see any {object_id} here."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Check if object is takeable
            if not game_object.is_takeable:
                # Look for TAKE interaction with custom message
                for interaction in game_object.interactions:
                    if interaction.verb == "TAKE":
                        return ActionResult(
                            success=False,
                            message=interaction.response_spooky
                        )
                # Default message for non-takeable objects
                return ActionResult(
                    success=False,
                    message="You can't take that."
                )
            
            # Find TAKE interaction for response message
            take_message = "Taken."
            sanity_change = 0
            notifications = []
            
            for interaction in game_object.interactions:
                if interaction.verb == "TAKE":
                    # Check conditions if any
                    if interaction.condition:
                        conditions_met = True
                        for key, required_value in interaction.condition.items():
                            if game_object.state.get(key) != required_value:
                                conditions_met = False
                                break
                        if not conditions_met:
                            continue
                    
                    take_message = interaction.response_spooky
                    sanity_change = interaction.sanity_effect
                    
                    # Apply state changes to object
                    if interaction.state_change:
                        for key, value in interaction.state_change.items():
                            game_object.state[key] = value
                    
                    # Apply flag changes to game state
                    if interaction.flag_change:
                        for flag_name, flag_value in interaction.flag_change.items():
                            state.set_flag(flag_name, flag_value)
                    
                    break
            
            # Add to inventory
            state.add_to_inventory(object_id)
            
            # Remove from room
            current_room.items.remove(object_id)
            
            # Apply sanity effects
            if sanity_change != 0:
                state.sanity = max(0, min(100, state.sanity + sanity_change))
                if sanity_change < 0:
                    notifications.append("Touching it fills you with dread...")
            
            return ActionResult(
                success=True,
                message=take_message,
                inventory_changed=True,
                state_changes={
                    'inventory': state.inventory,
                    'sanity': state.sanity
                },
                notifications=notifications,
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while taking that."
            )
    
    def handle_drop(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle dropping an object from inventory into the current room.
        
        Removes from inventory and adds to current room.
        
        Args:
            object_id: The object identifier to drop
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 4.2, 4.3, 5.2, 5.3
        """
        try:
            # Check if object is in inventory
            if object_id not in state.inventory:
                return ActionResult(
                    success=False,
                    message="You don't have that."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Find DROP interaction for response message
            drop_message = "Dropped."
            sanity_change = 0
            notifications = []
            
            for interaction in game_object.interactions:
                if interaction.verb == "DROP":
                    # Check conditions if any
                    if interaction.condition:
                        conditions_met = True
                        for key, required_value in interaction.condition.items():
                            if game_object.state.get(key) != required_value:
                                conditions_met = False
                                break
                        if not conditions_met:
                            continue
                    
                    drop_message = interaction.response_spooky
                    sanity_change = interaction.sanity_effect
                    
                    # Apply state changes to object
                    if interaction.state_change:
                        for key, value in interaction.state_change.items():
                            game_object.state[key] = value
                    
                    # Apply flag changes to game state
                    if interaction.flag_change:
                        for flag_name, flag_value in interaction.flag_change.items():
                            state.set_flag(flag_name, flag_value)
                    
                    break
            
            # Remove from inventory
            state.remove_from_inventory(object_id)
            
            # Add to current room
            current_room = self.world.get_room(state.current_room)
            current_room.items.append(object_id)
            
            # Apply sanity effects
            if sanity_change != 0:
                state.sanity = max(0, min(100, state.sanity + sanity_change))
            
            return ActionResult(
                success=True,
                message=drop_message,
                inventory_changed=True,
                state_changes={
                    'inventory': state.inventory,
                    'sanity': state.sanity
                },
                notifications=notifications,
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message="You don't have that."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while dropping that."
            )
    
    def handle_object_interaction(
        self,
        verb: str,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle generic object interactions (OPEN, CLOSE, READ, MOVE).
        
        Checks prerequisites and conditions, updates object state,
        and updates game flags when appropriate.
        
        Args:
            verb: The interaction verb (OPEN, CLOSE, READ, MOVE)
            object_id: The object identifier to interact with
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 4.4, 4.5, 18.1, 18.2, 18.3
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory
            
            if not object_in_room and not object_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {object_id} here."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Find matching interaction
            matching_interaction = None
            for interaction in game_object.interactions:
                if interaction.verb == verb:
                    # Check if interaction has conditions
                    if interaction.condition:
                        # Check if all conditions are met
                        conditions_met = True
                        for key, required_value in interaction.condition.items():
                            current_value = game_object.state.get(key, None)
                            if current_value != required_value:
                                conditions_met = False
                                break
                        if not conditions_met:
                            continue
                    matching_interaction = interaction
                    break
            
            if not matching_interaction:
                # No matching interaction found
                return ActionResult(
                    success=False,
                    message=f"You can't {verb.lower()} that."
                )
            
            # Get response message (always use spooky)
            message = matching_interaction.response_spooky
            
            # Apply state changes to object
            if matching_interaction.state_change:
                for key, value in matching_interaction.state_change.items():
                    game_object.state[key] = value
            
            # Apply flag changes to game state
            if matching_interaction.flag_change:
                for flag_name, flag_value in matching_interaction.flag_change.items():
                    state.set_flag(flag_name, flag_value)
            
            # Handle puzzle-specific logic
            notifications = []
            
            # Puzzle 1: Moving rug reveals trap door
            if object_id == "rug" and verb == "MOVE":
                if game_object.state.get("is_moved", False):
                    # Rug has been moved, make trap door visible
                    state.set_flag("rug_moved", True)
                    try:
                        trap_door = self.world.get_object("trap_door")
                        trap_door.state["is_visible"] = True
                        notifications.append("The trap door is now visible!")
                    except ValueError:
                        pass  # Trap door object doesn't exist
            
            # Puzzle 2: Opening kitchen window allows entry
            if object_id == "kitchen_window" and verb == "OPEN":
                if game_object.state.get("is_open", False):
                    state.set_flag("kitchen_window_open", True)
                    notifications.append("You can now enter through the window.")
            
            # Puzzle 3: Opening trap door (requires rug to be moved first)
            if object_id == "trap_door" and verb == "OPEN":
                rug_moved = state.get_flag("rug_moved", False)
                if not rug_moved:
                    return ActionResult(
                        success=False,
                        message="You don't see any trap door here."
                    )
                if game_object.state.get("is_open", False):
                    state.set_flag("trap_door_open", True)
                    notifications.append("The way to the cellar is now open.")
            
            # Apply sanity effects
            sanity_change = matching_interaction.sanity_effect
            
            if sanity_change != 0:
                state.sanity = max(0, min(100, state.sanity + sanity_change))
                if sanity_change < 0:
                    notifications.append("The experience disturbs you...")
            
            # Check for curse trigger
            if matching_interaction.curse_trigger:
                state.cursed = True
                notifications.append("You feel a dark curse take hold...")
            
            return ActionResult(
                success=True,
                message=message,
                state_changes={
                    'sanity': state.sanity,
                    'cursed': state.cursed,
                    'flags': state.flags
                },
                notifications=notifications,
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong with that action."
            )
    
    def handle_examine(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle examining an object in the current room or inventory.
        
        Returns spooky descriptions based on sanity level.
        Handles both scenery and takeable objects.
        
        Args:
            object_id: The object identifier to examine
            state: Current game state
            
        Returns:
            ActionResult with examination description
            
        Requirements: 4.1
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory
            
            if not object_in_room and not object_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {object_id} here."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Find EXAMINE interaction
            examine_interaction = None
            for interaction in game_object.interactions:
                if interaction.verb == "EXAMINE":
                    # Check if interaction has conditions
                    if interaction.condition:
                        # Check if all conditions are met
                        conditions_met = True
                        for key, required_value in interaction.condition.items():
                            if game_object.state.get(key) != required_value:
                                conditions_met = False
                                break
                        if not conditions_met:
                            continue
                    examine_interaction = interaction
                    break
            
            if not examine_interaction:
                # No examine interaction defined, provide default description
                display_name = game_object.name_spooky if game_object.name_spooky else game_object.name
                return ActionResult(
                    success=True,
                    message=f"You see {display_name}. Nothing particularly interesting."
                )
            
            # Return spooky description (always use spooky per requirements 19.5, 20.1, 20.2)
            description = examine_interaction.response_spooky
            
            # Apply sanity effects if any
            sanity_change = examine_interaction.sanity_effect
            notifications = []
            
            if sanity_change != 0:
                state.sanity = max(0, min(100, state.sanity + sanity_change))
                if sanity_change < 0:
                    notifications.append("The sight disturbs you deeply...")
            
            return ActionResult(
                success=True,
                message=description,
                state_changes={'sanity': state.sanity} if sanity_change != 0 else {},
                notifications=notifications,
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while examining that."
            )
    
    def handle_put(
        self,
        object_id: str,
        container_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle putting an object into a container.
        
        Validates capacity limits and container state.
        
        Args:
            object_id: The object to put in the container
            container_id: The container to put the object in
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 15.1, 15.2, 15.3
        """
        try:
            # Check if object is in inventory
            if object_id not in state.inventory:
                return ActionResult(
                    success=False,
                    message="You don't have that."
                )
            
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if container is in current room or inventory
            container_in_room = container_id in current_room.items
            container_in_inventory = container_id in state.inventory
            
            if not container_in_room and not container_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {container_id} here."
                )
            
            # Get container object
            container = self.world.get_object(container_id)
            
            # Check if object is actually a container
            if container.type != "container":
                return ActionResult(
                    success=False,
                    message="That's not a container."
                )
            
            # Check if container is open (unless it's transparent)
            is_transparent = container.state.get('is_transparent', False)
            is_open = container.state.get('is_open', False)
            
            if not is_open and not is_transparent:
                return ActionResult(
                    success=False,
                    message="The container is closed."
                )
            
            # Get object to put
            game_object = self.world.get_object(object_id)
            
            # Check container capacity
            if container.capacity > 0:
                # Calculate current contents size
                contents = container.state.get('contents', [])
                current_size = 0
                for obj_id in contents:
                    try:
                        obj = self.world.get_object(obj_id)
                        current_size += getattr(obj, 'size', 1)
                    except:
                        current_size += 1
                
                # Get size of object being added
                object_size = getattr(game_object, 'size', 1)
                
                # Check if adding this object would exceed capacity
                if current_size + object_size > container.capacity:
                    return ActionResult(
                        success=False,
                        message="The container is full."
                    )
            
            # Find PUT interaction for response message
            put_message = "Done."
            sanity_change = 0
            notifications = []
            
            for interaction in container.interactions:
                if interaction.verb == "PUT":
                    put_message = interaction.response_spooky
                    sanity_change = interaction.sanity_effect
                    
                    # Apply state changes to container
                    if interaction.state_change:
                        for key, value in interaction.state_change.items():
                            container.state[key] = value
                    
                    # Apply flag changes to game state
                    if interaction.flag_change:
                        for flag_name, flag_value in interaction.flag_change.items():
                            state.set_flag(flag_name, flag_value)
                    
                    break
            
            # Remove from inventory
            state.remove_from_inventory(object_id)
            
            # Add to container contents
            if 'contents' not in container.state:
                container.state['contents'] = []
            container.state['contents'].append(object_id)
            
            # Apply sanity effects
            if sanity_change != 0:
                state.sanity = max(0, min(100, state.sanity + sanity_change))
            
            return ActionResult(
                success=True,
                message=put_message,
                inventory_changed=True,
                state_changes={
                    'inventory': state.inventory,
                    'sanity': state.sanity
                },
                notifications=notifications,
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {container_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while putting that."
            )
    
    def handle_take_from_container(
        self,
        object_id: str,
        container_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle taking an object from a container.
        
        Removes object from container and adds to inventory.
        
        Args:
            object_id: The object to take from the container
            container_id: The container to take the object from
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 15.3
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if container is in current room or inventory
            container_in_room = container_id in current_room.items
            container_in_inventory = container_id in state.inventory
            
            if not container_in_room and not container_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {container_id} here."
                )
            
            # Get container object
            container = self.world.get_object(container_id)
            
            # Check if object is actually a container
            if container.type != "container":
                return ActionResult(
                    success=False,
                    message="That's not a container."
                )
            
            # Check if container is open or transparent
            is_transparent = container.state.get('is_transparent', False)
            is_open = container.state.get('is_open', False)
            
            if not is_open and not is_transparent:
                return ActionResult(
                    success=False,
                    message="The container is closed."
                )
            
            # Check if object is in container
            contents = container.state.get('contents', [])
            if object_id not in contents:
                return ActionResult(
                    success=False,
                    message=f"There's no {object_id} in the {container_id}."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Check if object is takeable
            if not game_object.is_takeable:
                return ActionResult(
                    success=False,
                    message="You can't take that."
                )
            
            # Find TAKE interaction for response message
            take_message = "Taken."
            sanity_change = 0
            notifications = []
            
            for interaction in game_object.interactions:
                if interaction.verb == "TAKE":
                    take_message = interaction.response_spooky
                    sanity_change = interaction.sanity_effect
                    
                    # Apply state changes to object
                    if interaction.state_change:
                        for key, value in interaction.state_change.items():
                            game_object.state[key] = value
                    
                    # Apply flag changes to game state
                    if interaction.flag_change:
                        for flag_name, flag_value in interaction.flag_change.items():
                            state.set_flag(flag_name, flag_value)
                    
                    break
            
            # Remove from container
            container.state['contents'].remove(object_id)
            
            # Add to inventory
            state.add_to_inventory(object_id)
            
            # Apply sanity effects
            if sanity_change != 0:
                state.sanity = max(0, min(100, state.sanity + sanity_change))
                if sanity_change < 0:
                    notifications.append("Touching it fills you with dread...")
            
            return ActionResult(
                success=True,
                message=take_message,
                inventory_changed=True,
                state_changes={
                    'inventory': state.inventory,
                    'sanity': state.sanity
                },
                notifications=notifications,
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {container_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while taking that."
            )
    
    def handle_examine_container(
        self,
        container_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle examining a container to see its contents.
        
        Lists all contained objects if container is open or transparent.
        
        Args:
            container_id: The container to examine
            state: Current game state
            
        Returns:
            ActionResult with container description and contents
            
        Requirements: 15.4
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if container is in current room or inventory
            container_in_room = container_id in current_room.items
            container_in_inventory = container_id in state.inventory
            
            if not container_in_room and not container_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {container_id} here."
                )
            
            # Get container object
            container = self.world.get_object(container_id)
            
            # Get base description from EXAMINE interaction
            base_description = ""
            sanity_change = 0
            
            for interaction in container.interactions:
                if interaction.verb == "EXAMINE":
                    base_description = interaction.response_spooky
                    sanity_change = interaction.sanity_effect
                    break
            
            # Check if container is open or transparent
            is_transparent = container.state.get('is_transparent', False)
            is_open = container.state.get('is_open', False)
            
            # Build description with contents if visible
            if is_open or is_transparent:
                contents = container.state.get('contents', [])
                if contents:
                    contents_names = []
                    for obj_id in contents:
                        obj = self.world.get_object(obj_id)
                        display_name = obj.name_spooky if obj.name_spooky else obj.name
                        contents_names.append(display_name)
                    
                    contents_list = ", ".join(contents_names)
                    description = f"{base_description}\n\nInside you see: {contents_list}"
                else:
                    description = f"{base_description}\n\nThe container is empty."
            else:
                description = base_description
            
            # Apply sanity effects
            notifications = []
            if sanity_change != 0:
                state.sanity = max(0, min(100, state.sanity + sanity_change))
                if sanity_change < 0:
                    notifications.append("The sight disturbs you deeply...")
            
            return ActionResult(
                success=True,
                message=description,
                state_changes={'sanity': state.sanity} if sanity_change != 0 else {},
                notifications=notifications,
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {container_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while examining that."
            )
    
    def handle_lamp_on(
        self,
        state: GameState
    ) -> ActionResult:
        """
        Handle turning the lamp on.
        
        Checks if lamp is in inventory and has battery remaining.
        
        Args:
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 14.1
        """
        try:
            # Check if lamp is in inventory
            if "lamp" not in state.inventory:
                return ActionResult(
                    success=False,
                    message="You don't have the lamp."
                )
            
            # Check if lamp is already on
            lamp_on = state.get_flag("lamp_on", False)
            if lamp_on:
                return ActionResult(
                    success=False,
                    message="The lamp is already on."
                )
            
            # Check if lamp has battery
            if state.lamp_battery <= 0:
                return ActionResult(
                    success=False,
                    message="The lamp has no power left. It won't turn on."
                )
            
            # Turn lamp on
            state.set_flag("lamp_on", True)
            
            return ActionResult(
                success=True,
                message="The lamp is now on, casting eerie shadows around you.",
                state_changes={
                    'flags': state.flags
                }
            )
            
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong with the lamp."
            )
    
    def handle_lamp_off(
        self,
        state: GameState
    ) -> ActionResult:
        """
        Handle turning the lamp off.
        
        Args:
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 14.1
        """
        try:
            # Check if lamp is in inventory
            if "lamp" not in state.inventory:
                return ActionResult(
                    success=False,
                    message="You don't have the lamp."
                )
            
            # Check if lamp is already off
            lamp_on = state.get_flag("lamp_on", False)
            if not lamp_on:
                return ActionResult(
                    success=False,
                    message="The lamp is already off."
                )
            
            # Turn lamp off
            state.set_flag("lamp_on", False)
            
            return ActionResult(
                success=True,
                message="The lamp is now off. Darkness surrounds you.",
                state_changes={
                    'flags': state.flags
                }
            )
            
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong with the lamp."
            )
    
    def apply_lamp_battery_drain(
        self,
        state: GameState
    ) -> List[str]:
        """
        Apply lamp battery drain for the current turn.
        
        Drains battery by 1 per turn when lamp is on (2 if cursed).
        Automatically turns off lamp when battery reaches 0.
        
        Args:
            state: Current game state
            
        Returns:
            List of notification messages
            
        Requirements: 14.2, 14.3
        """
        notifications = []
        
        # Check if lamp is on
        lamp_on = state.get_flag("lamp_on", False)
        if not lamp_on:
            return notifications
        
        # Check if lamp is in inventory
        if "lamp" not in state.inventory:
            return notifications
        
        # Calculate drain amount (2x if cursed)
        drain_amount = 2 if state.cursed else 1
        
        # Drain battery
        state.lamp_battery = max(0, state.lamp_battery - drain_amount)
        
        # Check for low battery warnings
        if state.lamp_battery == 10:
            notifications.append("The lamp is growing dim. It won't last much longer.")
        elif state.lamp_battery == 5:
            notifications.append("The lamp flickers ominously. It's nearly dead.")
        
        # Auto-shutoff at 0 battery
        if state.lamp_battery == 0:
            state.set_flag("lamp_on", False)
            notifications.append("The lamp has gone out. You are in darkness.")
        
        return notifications
    
    def get_darkness_description(
        self,
        room_id: str
    ) -> str:
        """
        Get darkness description for a dark room without light.
        
        Args:
            room_id: The room identifier
            
        Returns:
            Darkness description string
            
        Requirements: 14.1
        """
        return ("It is pitch black. You are likely to be eaten by a grue. "
                "The darkness presses in around you, and you can hear strange "
                "sounds echoing from unseen corners.")
    
    def is_room_lit(
        self,
        room_id: str,
        state: GameState
    ) -> bool:
        """
        Check if a room is lit (either not dark, or player has light source).
        
        Args:
            room_id: The room identifier
            state: Current game state
            
        Returns:
            True if room is lit, False if in darkness
            
        Requirements: 14.1
        """
        try:
            room = self.world.get_room(room_id)
            
            # If room is not dark, it's always lit
            if not room.is_dark:
                return True
            
            # Check if player has lamp and it's on
            lamp_on = state.get_flag("lamp_on", False)
            has_lamp = "lamp" in state.inventory
            
            return has_lamp and lamp_on
            
        except ValueError:
            # Room not found, assume lit
            return True
    
    def handle_lock(
        self,
        object_id: str,
        key_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle locking an object with a key.
        
        Validates that the object is lockable, the key is appropriate,
        and updates the object's lock state.
        
        Args:
            object_id: The object to lock
            key_id: The key to use for locking
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 3.3
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory
            
            if not object_in_room and not object_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {object_id} here."
                )
            
            # Check if key is in inventory
            if key_id not in state.inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't have the {key_id}."
                )
            
            # Get object and key data
            game_object = self.world.get_object(object_id)
            key_object = self.world.get_object(key_id)
            
            # Check if object is lockable
            is_lockable = game_object.state.get('is_lockable', False)
            
            if not is_lockable:
                return ActionResult(
                    success=False,
                    message=f"The {object_id} cannot be locked."
                )
            
            # Check if object is already locked
            is_locked = game_object.state.get('is_locked', False)
            
            if is_locked:
                return ActionResult(
                    success=False,
                    message=f"The {object_id} is already locked."
                )
            
            # Check if key matches the lock
            required_key = game_object.state.get('required_key', None)
            
            if required_key and required_key != key_id:
                return ActionResult(
                    success=False,
                    message=f"The {key_id} doesn't fit the lock."
                )
            
            # Lock the object
            game_object.state['is_locked'] = True
            
            # Create success message with haunted theme
            lock_message = f"You lock the {object_id} with the {key_id}. A cold click echoes in the darkness."
            
            # Apply any flag changes
            notifications = []
            if object_id == "grate":
                state.set_flag("grate_locked", True)
                state.set_flag("grate_unlocked", False)
            
            return ActionResult(
                success=True,
                message=lock_message,
                state_changes={
                    'flags': state.flags
                },
                notifications=notifications
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while locking that."
            )
    
    def handle_unlock(
        self,
        object_id: str,
        key_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle unlocking an object with a key.
        
        Validates that the object is lockable, the key is appropriate,
        and updates the object's lock state.
        
        Args:
            object_id: The object to unlock
            key_id: The key to use for unlocking
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 3.3
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory
            
            if not object_in_room and not object_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {object_id} here."
                )
            
            # Check if key is in inventory
            if key_id not in state.inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't have the {key_id}."
                )
            
            # Get object and key data
            game_object = self.world.get_object(object_id)
            key_object = self.world.get_object(key_id)
            
            # Check if object is lockable
            is_lockable = game_object.state.get('is_lockable', False)
            
            if not is_lockable:
                return ActionResult(
                    success=False,
                    message=f"The {object_id} cannot be unlocked."
                )
            
            # Check if object is already unlocked
            is_locked = game_object.state.get('is_locked', False)
            
            if not is_locked:
                return ActionResult(
                    success=False,
                    message=f"The {object_id} is already unlocked."
                )
            
            # Check if key matches the lock
            required_key = game_object.state.get('required_key', None)
            
            if required_key and required_key != key_id:
                return ActionResult(
                    success=False,
                    message=f"The {key_id} doesn't fit the lock."
                )
            
            # Unlock the object
            game_object.state['is_locked'] = False
            
            # Create success message with haunted theme
            unlock_message = f"You unlock the {object_id} with the {key_id}. The mechanism groans as it releases."
            
            # Apply any flag changes
            notifications = []
            if object_id == "grate":
                state.set_flag("grate_unlocked", True)
                state.set_flag("grate_locked", False)
            
            return ActionResult(
                success=True,
                message=unlock_message,
                state_changes={
                    'flags': state.flags
                },
                notifications=notifications
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while unlocking that."
            )
    
    def handle_turn(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle turning turnable objects (dials, valves, etc.).
        
        Validates that the object is turnable, updates rotation/activation state,
        and triggers any associated effects.
        
        Args:
            object_id: The object to turn
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 3.4
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory
            
            if not object_in_room and not object_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {object_id} here."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Check if object is turnable
            is_turnable = game_object.state.get('is_turnable', False)
            
            if not is_turnable:
                return ActionResult(
                    success=False,
                    message=f"You can't turn the {object_id}."
                )
            
            # Get current rotation state
            current_rotation = game_object.state.get('rotation', 0)
            max_rotation = game_object.state.get('max_rotation', 360)
            rotation_increment = game_object.state.get('rotation_increment', 90)
            
            # Update rotation
            new_rotation = (current_rotation + rotation_increment) % max_rotation
            game_object.state['rotation'] = new_rotation
            
            # Check if turning activates something
            is_activated = game_object.state.get('is_activated', False)
            activation_rotation = game_object.state.get('activation_rotation', None)
            
            notifications = []
            
            if activation_rotation is not None:
                if new_rotation == activation_rotation:
                    game_object.state['is_activated'] = True
                    notifications.append(f"The {object_id} clicks into place!")
                else:
                    game_object.state['is_activated'] = False
            
            # Apply any flag changes based on activation
            if game_object.state.get('is_activated', False):
                activation_flag = game_object.state.get('activation_flag', None)
                if activation_flag:
                    state.set_flag(activation_flag, True)
            
            # Create success message with haunted theme
            turn_message = f"You turn the {object_id}. It rotates with an eerie creak."
            
            # Add rotation description if available
            rotation_descriptions = game_object.state.get('rotation_descriptions', {})
            if str(new_rotation) in rotation_descriptions:
                turn_message += f" {rotation_descriptions[str(new_rotation)]}"
            
            return ActionResult(
                success=True,
                message=turn_message,
                state_changes={
                    'flags': state.flags
                },
                notifications=notifications
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while turning that."
            )
    
    def handle_push(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle pushing moveable objects.
        
        Validates that the object is moveable, updates location or position,
        and triggers any associated effects (revealing items, etc.).
        
        Args:
            object_id: The object to push
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 3.5
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if object is in current room
            if object_id not in current_room.items:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {object_id} here."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Check if object is moveable
            is_moveable = game_object.state.get('is_moveable', False)
            
            if not is_moveable:
                return ActionResult(
                    success=False,
                    message=f"The {object_id} won't budge."
                )
            
            # Check if already pushed
            is_pushed = game_object.state.get('is_pushed', False)
            
            if is_pushed:
                return ActionResult(
                    success=False,
                    message=f"The {object_id} has already been pushed as far as it will go."
                )
            
            # Push the object
            game_object.state['is_pushed'] = True
            
            # Check for revealed items
            notifications = []
            reveals_items = game_object.state.get('reveals_items', [])
            
            if reveals_items:
                for item_id in reveals_items:
                    if item_id not in current_room.items:
                        current_room.items.append(item_id)
                        try:
                            revealed_obj = self.world.get_object(item_id)
                            notifications.append(f"Pushing the {object_id} reveals {revealed_obj.name_spooky}!")
                        except ValueError:
                            notifications.append(f"Pushing the {object_id} reveals something hidden!")
            
            # Apply any flag changes
            push_flag = game_object.state.get('push_flag', None)
            if push_flag:
                state.set_flag(push_flag, True)
            
            # Create success message with haunted theme
            push_message = f"You push the {object_id}. It slides across the floor with a grinding sound."
            
            # Add custom push message if available
            custom_message = game_object.state.get('push_message', None)
            if custom_message:
                push_message = custom_message
            
            return ActionResult(
                success=True,
                message=push_message,
                state_changes={
                    'flags': state.flags
                },
                notifications=notifications
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while pushing that."
            )
    
    def handle_pull(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle pulling moveable objects.
        
        Validates that the object is moveable, updates location or position,
        and triggers any associated effects (revealing items, etc.).
        
        Args:
            object_id: The object to pull
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 3.5
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if object is in current room
            if object_id not in current_room.items:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {object_id} here."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Check if object is moveable
            is_moveable = game_object.state.get('is_moveable', False)
            
            if not is_moveable:
                return ActionResult(
                    success=False,
                    message=f"The {object_id} won't budge."
                )
            
            # Check if already pulled
            is_pulled = game_object.state.get('is_pulled', False)
            
            if is_pulled:
                return ActionResult(
                    success=False,
                    message=f"The {object_id} has already been pulled as far as it will go."
                )
            
            # Pull the object
            game_object.state['is_pulled'] = True
            
            # Check for revealed items
            notifications = []
            reveals_items = game_object.state.get('reveals_items', [])
            
            if reveals_items:
                for item_id in reveals_items:
                    if item_id not in current_room.items:
                        current_room.items.append(item_id)
                        try:
                            revealed_obj = self.world.get_object(item_id)
                            notifications.append(f"Pulling the {object_id} reveals {revealed_obj.name_spooky}!")
                        except ValueError:
                            notifications.append(f"Pulling the {object_id} reveals something hidden!")
            
            # Apply any flag changes
            pull_flag = game_object.state.get('pull_flag', None)
            if pull_flag:
                state.set_flag(pull_flag, True)
            
            # Create success message with haunted theme
            pull_message = f"You pull the {object_id}. It drags toward you with a scraping sound."
            
            # Add custom pull message if available
            custom_message = game_object.state.get('pull_message', None)
            if custom_message:
                pull_message = custom_message
            
            return ActionResult(
                success=True,
                message=pull_message,
                state_changes={
                    'flags': state.flags
                },
                notifications=notifications
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while pulling that."
            )
    
    def handle_tie(
        self,
        object_id: str,
        target_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle tying rope-like objects to targets.
        
        Validates that the object is rope-like, the target is valid,
        and tracks the tied state in object properties.
        
        Args:
            object_id: The rope-like object to tie
            target_id: The target to tie the rope to
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 3.6
        """
        try:
            # Check if rope object is in inventory
            if object_id not in state.inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't have the {object_id}."
                )
            
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if target is in current room or inventory
            target_in_room = target_id in current_room.items
            target_in_inventory = target_id in state.inventory
            
            if not target_in_room and not target_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {target_id} here."
                )
            
            # Get rope and target objects
            rope_object = self.world.get_object(object_id)
            target_object = self.world.get_object(target_id)
            
            # Check if object is rope-like
            is_rope = rope_object.state.get('is_rope', False)
            can_tie = rope_object.state.get('can_tie', False)
            
            if not is_rope or not can_tie:
                return ActionResult(
                    success=False,
                    message=f"You can't tie the {object_id}."
                )
            
            # Check if rope is already tied
            is_tied = rope_object.state.get('is_tied', False)
            
            if is_tied:
                tied_to = rope_object.state.get('tied_to', 'something')
                return ActionResult(
                    success=False,
                    message=f"The {object_id} is already tied to {tied_to}."
                )
            
            # Check if target is valid for tying
            tie_targets = rope_object.state.get('tie_targets', [])
            
            if tie_targets and target_id not in tie_targets:
                return ActionResult(
                    success=False,
                    message=f"You can't tie the {object_id} to the {target_id}."
                )
            
            # Check if target can be tied to
            can_be_tied_to = target_object.state.get('can_be_tied_to', True)
            
            if not can_be_tied_to:
                return ActionResult(
                    success=False,
                    message=f"You can't tie anything to the {target_id}."
                )
            
            # Tie the rope to the target
            rope_object.state['is_tied'] = True
            rope_object.state['tied_to'] = target_id
            
            # Update target object to track what's tied to it
            if 'tied_objects' not in target_object.state:
                target_object.state['tied_objects'] = []
            target_object.state['tied_objects'].append(object_id)
            
            # Apply any flag changes
            notifications = []
            tie_flag = rope_object.state.get('tie_flag', None)
            if tie_flag:
                state.set_flag(tie_flag, True)
            
            # Create success message with haunted theme
            tie_message = f"You tie the {object_id} to the {target_id}. The knot holds fast, though your fingers tremble."
            
            # Add custom tie message if available
            custom_message = rope_object.state.get('tie_message', None)
            if custom_message:
                tie_message = custom_message
            
            return ActionResult(
                success=True,
                message=tie_message,
                state_changes={
                    'flags': state.flags
                },
                notifications=notifications
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {target_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while tying that."
            )
    
    def handle_untie(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle untying previously tied objects.
        
        Validates that the object is tied and updates the tied state.
        
        Args:
            object_id: The rope-like object to untie
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 3.6
        """
        try:
            # Check if rope object is in inventory or current room
            current_room = self.world.get_room(state.current_room)
            
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory
            
            if not object_in_room and not object_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {object_id} here."
                )
            
            # Get rope object
            rope_object = self.world.get_object(object_id)
            
            # Check if object is rope-like
            is_rope = rope_object.state.get('is_rope', False)
            
            if not is_rope:
                return ActionResult(
                    success=False,
                    message=f"You can't untie the {object_id}."
                )
            
            # Check if rope is tied
            is_tied = rope_object.state.get('is_tied', False)
            
            if not is_tied:
                return ActionResult(
                    success=False,
                    message=f"The {object_id} is not tied to anything."
                )
            
            # Get what it's tied to
            tied_to = rope_object.state.get('tied_to', None)
            
            # Untie the rope
            rope_object.state['is_tied'] = False
            rope_object.state['tied_to'] = None
            
            # Update target object to remove this rope from tied objects
            if tied_to:
                try:
                    target_object = self.world.get_object(tied_to)
                    tied_objects = target_object.state.get('tied_objects', [])
                    if object_id in tied_objects:
                        tied_objects.remove(object_id)
                        target_object.state['tied_objects'] = tied_objects
                except ValueError:
                    # Target object doesn't exist, that's okay
                    pass
            
            # Apply any flag changes
            notifications = []
            untie_flag = rope_object.state.get('untie_flag', None)
            if untie_flag:
                state.set_flag(untie_flag, True)
            
            # Clear tie flag if it was set
            tie_flag = rope_object.state.get('tie_flag', None)
            if tie_flag:
                state.set_flag(tie_flag, False)
            
            # Create success message with haunted theme
            untie_message = f"You untie the {object_id}. The knot comes loose with an eerie whisper."
            
            # Add custom untie message if available
            custom_message = rope_object.state.get('untie_message', None)
            if custom_message:
                untie_message = custom_message
            
            return ActionResult(
                success=True,
                message=untie_message,
                state_changes={
                    'flags': state.flags
                },
                notifications=notifications
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while untying that."
            )
    
    def handle_fill(
        self,
        container_id: str,
        source_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle filling containers from liquid sources.
        
        Validates that the container can hold liquids, the source has liquid,
        and tracks liquid contents in container state. Validates container capacity.
        
        Args:
            container_id: The container to fill
            source_id: The liquid source to fill from
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 3.7
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if container is in inventory or current room
            container_in_room = container_id in current_room.items
            container_in_inventory = container_id in state.inventory
            
            if not container_in_room and not container_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't have the {container_id}."
                )
            
            # Check if source is in current room or inventory
            source_in_room = source_id in current_room.items
            source_in_inventory = source_id in state.inventory
            
            if not source_in_room and not source_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {source_id} here."
                )
            
            # Get container and source objects
            container_object = self.world.get_object(container_id)
            source_object = self.world.get_object(source_id)
            
            # Check if container can hold liquids
            can_hold_liquid = container_object.state.get('can_hold_liquid', False)
            
            if not can_hold_liquid:
                return ActionResult(
                    success=False,
                    message=f"You can't fill the {container_id} with liquid."
                )
            
            # Check if source has liquid
            has_liquid = source_object.state.get('has_liquid', False)
            is_liquid_source = source_object.state.get('is_liquid_source', False)
            
            if not has_liquid and not is_liquid_source:
                return ActionResult(
                    success=False,
                    message=f"The {source_id} has no liquid to fill from."
                )
            
            # Check if container is already full
            is_full = container_object.state.get('is_full', False)
            liquid_level = container_object.state.get('liquid_level', 0)
            max_capacity = container_object.state.get('liquid_capacity', 100)
            
            if is_full or liquid_level >= max_capacity:
                return ActionResult(
                    success=False,
                    message=f"The {container_id} is already full."
                )
            
            # Get liquid type from source
            liquid_type = source_object.state.get('liquid_type', 'water')
            
            # Fill the container
            container_object.state['is_full'] = True
            container_object.state['liquid_level'] = max_capacity
            container_object.state['liquid_type'] = liquid_type
            container_object.state['is_empty'] = False
            
            # Apply any flag changes
            notifications = []
            fill_flag = container_object.state.get('fill_flag', None)
            if fill_flag:
                state.set_flag(fill_flag, True)
            
            # Create success message with haunted theme
            fill_message = f"You fill the {container_id} with {liquid_type} from the {source_id}. The liquid swirls with an unnatural darkness."
            
            # Add custom fill message if available
            custom_message = container_object.state.get('fill_message', None)
            if custom_message:
                fill_message = custom_message
            
            return ActionResult(
                success=True,
                message=fill_message,
                state_changes={
                    'flags': state.flags
                },
                notifications=notifications
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {source_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while filling that."
            )
    
    def handle_pour(
        self,
        container_id: str,
        target_id: Optional[str],
        state: GameState
    ) -> ActionResult:
        """
        Handle pouring liquids from containers.
        
        Validates that the container has liquid, empties the container,
        and handles liquid evaporation/spillage. Can pour into another container
        or onto the ground.
        
        Args:
            container_id: The container to pour from
            target_id: The target to pour into (optional, defaults to ground)
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 3.8
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if container is in inventory or current room
            container_in_room = container_id in current_room.items
            container_in_inventory = container_id in state.inventory
            
            if not container_in_room and not container_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't have the {container_id}."
                )
            
            # Get container object
            container_object = self.world.get_object(container_id)
            
            # Check if container can hold liquids
            can_hold_liquid = container_object.state.get('can_hold_liquid', False)
            
            if not can_hold_liquid:
                return ActionResult(
                    success=False,
                    message=f"The {container_id} doesn't contain any liquid."
                )
            
            # Check if container has liquid
            is_empty = container_object.state.get('is_empty', True)
            liquid_level = container_object.state.get('liquid_level', 0)
            
            if is_empty or liquid_level <= 0:
                return ActionResult(
                    success=False,
                    message=f"The {container_id} is empty."
                )
            
            # Get liquid type
            liquid_type = container_object.state.get('liquid_type', 'liquid')
            
            # Handle pouring into another container
            if target_id:
                # Check if target is in current room or inventory
                target_in_room = target_id in current_room.items
                target_in_inventory = target_id in state.inventory
                
                if not target_in_room and not target_in_inventory:
                    return ActionResult(
                        success=False,
                        message=f"You don't see any {target_id} here."
                    )
                
                # Get target object
                target_object = self.world.get_object(target_id)
                
                # Check if target can hold liquids
                target_can_hold_liquid = target_object.state.get('can_hold_liquid', False)
                
                if not target_can_hold_liquid:
                    # Pouring onto an object that can't hold liquid
                    pour_message = f"You pour the {liquid_type} onto the {target_id}. It spills away into the shadows."
                else:
                    # Check if target is full
                    target_is_full = target_object.state.get('is_full', False)
                    target_liquid_level = target_object.state.get('liquid_level', 0)
                    target_max_capacity = target_object.state.get('liquid_capacity', 100)
                    
                    if target_is_full or target_liquid_level >= target_max_capacity:
                        return ActionResult(
                            success=False,
                            message=f"The {target_id} is already full."
                        )
                    
                    # Pour into target container
                    target_object.state['is_full'] = True
                    target_object.state['liquid_level'] = target_max_capacity
                    target_object.state['liquid_type'] = liquid_type
                    target_object.state['is_empty'] = False
                    
                    pour_message = f"You pour the {liquid_type} from the {container_id} into the {target_id}."
            else:
                # Pouring onto the ground
                pour_message = f"You pour the {liquid_type} onto the ground. It seeps away into the darkness."
            
            # Empty the container
            container_object.state['is_full'] = False
            container_object.state['liquid_level'] = 0
            container_object.state['liquid_type'] = None
            container_object.state['is_empty'] = True
            
            # Apply any flag changes
            notifications = []
            pour_flag = container_object.state.get('pour_flag', None)
            if pour_flag:
                state.set_flag(pour_flag, True)
            
            # Add custom pour message if available
            custom_message = container_object.state.get('pour_message', None)
            if custom_message:
                pour_message = custom_message
            
            return ActionResult(
                success=True,
                message=pour_message,
                state_changes={
                    'flags': state.flags
                },
                notifications=notifications
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {target_id if target_id else container_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while pouring that."
            )
    
    def handle_look_under(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle looking under objects.
        
        Reveals hidden items or information under objects. Returns "nothing there"
        message if appropriate. Uses haunted theme descriptions.
        
        Args:
            object_id: The object to look under
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 4.2
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory
            
            if not object_in_room and not object_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {object_id} here."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Check if object has something hidden under it
            hidden_under = game_object.state.get('hidden_under', None)
            reveals_under = game_object.state.get('reveals_under', [])
            under_description = game_object.state.get('under_description', None)
            
            notifications = []
            sanity_change = 0
            
            # If there are items to reveal
            if reveals_under:
                for item_id in reveals_under:
                    if item_id not in current_room.items:
                        current_room.items.append(item_id)
                        try:
                            revealed_obj = self.world.get_object(item_id)
                            notifications.append(f"You discover {revealed_obj.name_spooky} hidden beneath!")
                        except ValueError:
                            notifications.append(f"You discover something hidden beneath!")
                
                # Mark as revealed so it doesn't happen again
                game_object.state['reveals_under'] = []
                
                message = f"You look under the {object_id}."
                if under_description:
                    message = under_description
                
                return ActionResult(
                    success=True,
                    message=message,
                    notifications=notifications,
                    sanity_change=sanity_change
                )
            
            # If there's a custom description
            if under_description:
                return ActionResult(
                    success=True,
                    message=under_description,
                    sanity_change=sanity_change
                )
            
            # If there's hidden information
            if hidden_under:
                return ActionResult(
                    success=True,
                    message=hidden_under,
                    sanity_change=sanity_change
                )
            
            # Default: nothing there
            default_messages = [
                f"You peer beneath the {object_id}. Nothing but shadows and dust.",
                f"There's nothing under the {object_id} but darkness.",
                f"You find nothing of interest beneath the {object_id}.",
                f"The space under the {object_id} is empty, save for cobwebs."
            ]
            
            # Use a consistent message based on object_id hash for consistency
            message_idx = hash(object_id) % len(default_messages)
            
            return ActionResult(
                success=True,
                message=default_messages[message_idx],
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while looking under that."
            )
    
    def handle_look_inside(
        self,
        container_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle looking inside containers.
        
        Lists all container contents if container is open or transparent.
        Handles open/closed and transparent states. Formats contents list clearly.
        
        Args:
            container_id: The container to look inside
            state: Current game state
            
        Returns:
            ActionResult with container contents description
            
        Requirements: 4.3
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if container is in current room or inventory
            container_in_room = container_id in current_room.items
            container_in_inventory = container_id in state.inventory
            
            if not container_in_room and not container_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {container_id} here."
                )
            
            # Get container object
            container = self.world.get_object(container_id)
            
            # Check if object is actually a container
            if container.type != "container":
                return ActionResult(
                    success=False,
                    message=f"You can't look inside the {container_id}."
                )
            
            # Check if container is open or transparent
            is_transparent = container.state.get('is_transparent', False)
            is_open = container.state.get('is_open', False)
            
            if not is_open and not is_transparent:
                return ActionResult(
                    success=False,
                    message=f"The {container_id} is closed. You can't see inside."
                )
            
            # Get contents
            contents = container.state.get('contents', [])
            
            if not contents:
                return ActionResult(
                    success=True,
                    message=f"The {container_id} is empty. Nothing but shadows within."
                )
            
            # Build contents list
            contents_names = []
            for obj_id in contents:
                try:
                    obj = self.world.get_object(obj_id)
                    display_name = obj.name_spooky if obj.name_spooky else obj.name
                    contents_names.append(display_name)
                except ValueError:
                    # Object doesn't exist, skip it
                    continue
            
            if not contents_names:
                return ActionResult(
                    success=True,
                    message=f"The {container_id} appears empty."
                )
            
            # Format contents list
            if len(contents_names) == 1:
                contents_str = contents_names[0]
            elif len(contents_names) == 2:
                contents_str = f"{contents_names[0]} and {contents_names[1]}"
            else:
                contents_str = ", ".join(contents_names[:-1]) + f", and {contents_names[-1]}"
            
            message = f"Inside the {container_id}, you see: {contents_str}."
            
            return ActionResult(
                success=True,
                message=message
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {container_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while looking inside that."
            )
    
    def handle_look_behind(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle looking behind objects.
        
        Reveals hidden items or information behind objects. Returns "nothing there"
        message if appropriate. Uses haunted theme descriptions.
        
        Args:
            object_id: The object to look behind
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 4.2
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory
            
            if not object_in_room and not object_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {object_id} here."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Check if object has something hidden behind it
            hidden_behind = game_object.state.get('hidden_behind', None)
            reveals_behind = game_object.state.get('reveals_behind', [])
            behind_description = game_object.state.get('behind_description', None)
            
            notifications = []
            sanity_change = 0
            
            # If there are items to reveal
            if reveals_behind:
                for item_id in reveals_behind:
                    if item_id not in current_room.items:
                        current_room.items.append(item_id)
                        try:
                            revealed_obj = self.world.get_object(item_id)
                            notifications.append(f"You discover {revealed_obj.name_spooky} concealed behind it!")
                        except ValueError:
                            notifications.append(f"You discover something concealed behind it!")
                
                # Mark as revealed so it doesn't happen again
                game_object.state['reveals_behind'] = []
                
                message = f"You look behind the {object_id}."
                if behind_description:
                    message = behind_description
                
                return ActionResult(
                    success=True,
                    message=message,
                    notifications=notifications,
                    sanity_change=sanity_change
                )
            
            # If there's a custom description
            if behind_description:
                return ActionResult(
                    success=True,
                    message=behind_description,
                    sanity_change=sanity_change
                )
            
            # If there's hidden information
            if hidden_behind:
                return ActionResult(
                    success=True,
                    message=hidden_behind,
                    sanity_change=sanity_change
                )
            
            # Default: nothing there
            default_messages = [
                f"You peer behind the {object_id}. Nothing but empty space.",
                f"There's nothing behind the {object_id} but cold air.",
                f"You find nothing of interest behind the {object_id}.",
                f"The space behind the {object_id} is empty and foreboding."
            ]
            
            # Use a consistent message based on object_id hash for consistency
            message_idx = hash(object_id) % len(default_messages)
            
            return ActionResult(
                success=True,
                message=default_messages[message_idx],
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while looking behind that."
            )
    
    def handle_search(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle searching objects and locations.
        
        Reveals hidden details or items through thorough searching. Returns
        appropriate "found" or "nothing" messages. Uses thematic descriptions.
        
        Args:
            object_id: The object to search
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 4.4
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory
            
            if not object_in_room and not object_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {object_id} here."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Check if object has searchable properties
            search_reveals = game_object.state.get('search_reveals', [])
            search_description = game_object.state.get('search_description', None)
            hidden_details = game_object.state.get('hidden_details', None)
            
            notifications = []
            sanity_change = 0
            
            # If there are items to reveal through searching
            if search_reveals:
                for item_id in search_reveals:
                    if item_id not in current_room.items:
                        current_room.items.append(item_id)
                        try:
                            revealed_obj = self.world.get_object(item_id)
                            notifications.append(f"Your search reveals {revealed_obj.name_spooky}!")
                        except ValueError:
                            notifications.append(f"Your search reveals something hidden!")
                
                # Mark as searched so it doesn't happen again
                game_object.state['search_reveals'] = []
                
                message = f"You search the {object_id} thoroughly."
                if search_description:
                    message = search_description
                
                return ActionResult(
                    success=True,
                    message=message,
                    notifications=notifications,
                    sanity_change=sanity_change
                )
            
            # If there's a custom search description
            if search_description:
                return ActionResult(
                    success=True,
                    message=search_description,
                    sanity_change=sanity_change
                )
            
            # If there are hidden details to discover
            if hidden_details:
                return ActionResult(
                    success=True,
                    message=hidden_details,
                    sanity_change=sanity_change
                )
            
            # Default: nothing found
            default_messages = [
                f"You search the {object_id} carefully but find nothing of interest.",
                f"Your thorough search of the {object_id} reveals nothing unusual.",
                f"Despite your careful examination, the {object_id} yields no secrets.",
                f"You find nothing hidden in or on the {object_id}.",
                f"The {object_id} holds no hidden surprises, only shadows and dust."
            ]
            
            # Use a consistent message based on object_id hash for consistency
            message_idx = hash(object_id) % len(default_messages)
            
            return ActionResult(
                success=True,
                message=default_messages[message_idx],
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while searching."
            )
    
    def handle_read(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle reading readable objects (books, signs, notes).
        
        Supports reading readable objects and displays their text content.
        Returns "nothing to read" if the object is not readable.
        
        Args:
            object_id: The object to read
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 4.5
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory
            
            if not object_in_room and not object_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {object_id} here."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Check if object has a READ interaction
            read_interaction = None
            for interaction in game_object.interactions:
                if interaction.verb == "READ":
                    # Check if interaction has conditions
                    if interaction.condition:
                        # Check if all conditions are met
                        conditions_met = True
                        for key, required_value in interaction.condition.items():
                            current_value = game_object.state.get(key, None)
                            if current_value != required_value:
                                conditions_met = False
                                break
                        if not conditions_met:
                            continue
                    read_interaction = interaction
                    break
            
            if not read_interaction:
                # No READ interaction defined - object is not readable
                return ActionResult(
                    success=False,
                    message=f"There's nothing to read on the {object_id}."
                )
            
            # Get the text content (always use spooky version)
            text_content = read_interaction.response_spooky
            
            # Apply state changes to object if any
            if read_interaction.state_change:
                for key, value in read_interaction.state_change.items():
                    game_object.state[key] = value
            
            # Apply flag changes to game state if any
            if read_interaction.flag_change:
                for flag_name, flag_value in read_interaction.flag_change.items():
                    state.set_flag(flag_name, flag_value)
            
            # Apply sanity effects if any
            sanity_change = read_interaction.sanity_effect
            notifications = []
            
            if sanity_change != 0:
                state.sanity = max(0, min(100, state.sanity + sanity_change))
                if sanity_change < 0:
                    notifications.append("The words disturb you deeply...")
                elif sanity_change > 0:
                    notifications.append("The text brings a strange comfort...")
            
            return ActionResult(
                success=True,
                message=text_content,
                state_changes={
                    'sanity': state.sanity
                } if sanity_change != 0 else {},
                notifications=notifications,
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while reading."
            )
    
    def handle_listen(
        self,
        object_id: Optional[str],
        state: GameState
    ) -> ActionResult:
        """
        Handle listening to objects and rooms.
        
        Supports listening to specific objects or the current room. Returns
        audible information or silence message. Uses atmospheric descriptions.
        
        Args:
            object_id: The object to listen to (optional, defaults to room)
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 4.6
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # If no object specified, listen to the room
            if not object_id:
                # Check if room has audio_description (rooms don't have state dict, so we'd need to add it as a property)
                # For now, rooms don't have audio descriptions, so we'll use default messages
                audio_description = None
                
                if audio_description:
                    return ActionResult(
                        success=True,
                        message=audio_description
                    )
                
                # Default room listening messages based on sanity
                if state.sanity < 30:
                    default_messages = [
                        "You hear whispers in the darkness, speaking words you cannot understand...",
                        "The silence is broken by distant screams that echo through your mind.",
                        "Phantom footsteps circle around you, growing closer with each passing moment.",
                        "You hear the sound of something breathing, heavy and labored, just out of sight."
                    ]
                elif state.sanity < 60:
                    default_messages = [
                        "You hear unsettling creaks and groans from the old structure.",
                        "The wind howls mournfully through unseen cracks and crevices.",
                        "Faint scratching sounds emanate from within the walls.",
                        "You hear distant sounds that might be voices... or something else."
                    ]
                else:
                    default_messages = [
                        "You hear nothing unusual, just the ambient sounds of this eerie place.",
                        "The silence is oppressive, broken only by your own breathing.",
                        "You hear the faint creaking of old wood settling.",
                        "Nothing but an eerie quiet fills your ears."
                    ]
                
                # Use a consistent message based on room hash for consistency
                message_idx = hash(state.current_room) % len(default_messages)
                
                return ActionResult(
                    success=True,
                    message=default_messages[message_idx]
                )
            
            # Listening to a specific object
            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory
            
            if not object_in_room and not object_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {object_id} here."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Check if object has audio_description property
            audio_description = game_object.state.get('audio_description', None)
            
            if audio_description:
                # Apply sanity effects if any
                sanity_change = game_object.state.get('listen_sanity_effect', 0)
                notifications = []
                
                if sanity_change != 0:
                    state.sanity = max(0, min(100, state.sanity + sanity_change))
                    if sanity_change < 0:
                        notifications.append("The sounds disturb you deeply...")
                    elif sanity_change > 0:
                        notifications.append("The sounds bring a strange comfort...")
                
                return ActionResult(
                    success=True,
                    message=audio_description,
                    state_changes={
                        'sanity': state.sanity
                    } if sanity_change != 0 else {},
                    notifications=notifications,
                    sanity_change=sanity_change
                )
            
            # Check if object has a LISTEN interaction
            listen_interaction = None
            for interaction in game_object.interactions:
                if interaction.verb == "LISTEN":
                    # Check if interaction has conditions
                    if interaction.condition:
                        # Check if all conditions are met
                        conditions_met = True
                        for key, required_value in interaction.condition.items():
                            current_value = game_object.state.get(key, None)
                            if current_value != required_value:
                                conditions_met = False
                                break
                        if not conditions_met:
                            continue
                    listen_interaction = interaction
                    break
            
            if listen_interaction:
                # Get the audio information (always use spooky version)
                audio_info = listen_interaction.response_spooky
                
                # Apply state changes to object if any
                if listen_interaction.state_change:
                    for key, value in listen_interaction.state_change.items():
                        game_object.state[key] = value
                
                # Apply flag changes to game state if any
                if listen_interaction.flag_change:
                    for flag_name, flag_value in listen_interaction.flag_change.items():
                        state.set_flag(flag_name, flag_value)
                
                # Apply sanity effects if any
                sanity_change = listen_interaction.sanity_effect
                notifications = []
                
                if sanity_change != 0:
                    state.sanity = max(0, min(100, state.sanity + sanity_change))
                    if sanity_change < 0:
                        notifications.append("The sounds disturb you deeply...")
                    elif sanity_change > 0:
                        notifications.append("The sounds bring a strange comfort...")
                
                return ActionResult(
                    success=True,
                    message=audio_info,
                    state_changes={
                        'sanity': state.sanity
                    } if sanity_change != 0 else {},
                    notifications=notifications,
                    sanity_change=sanity_change
                )
            
            # Default: nothing to hear
            default_messages = [
                f"You listen carefully to the {object_id}, but hear nothing unusual.",
                f"The {object_id} is silent, revealing no audible secrets.",
                f"You press your ear close to the {object_id}, but it makes no sound.",
                f"The {object_id} offers no sounds, only an eerie silence.",
                f"Listening to the {object_id} yields nothing but the ambient sounds of this place."
            ]
            
            # Use a consistent message based on object_id hash for consistency
            message_idx = hash(object_id) % len(default_messages)
            
            return ActionResult(
                success=True,
                message=default_messages[message_idx]
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while listening."
            )
    
    def handle_smell(
        self,
        object_id: Optional[str],
        state: GameState
    ) -> ActionResult:
        """
        Handle smelling objects and rooms.
        
        Supports smelling specific objects or the current room. Returns
        olfactory information or neutral message. Uses thematic descriptions.
        
        Args:
            object_id: The object to smell (optional, defaults to room)
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 4.7
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # If no object specified, smell the room
            if not object_id:
                # Check if room has smell_description (rooms don't have state dict, so we'd need to add it as a property)
                # For now, rooms don't have smell descriptions, so we'll use default messages
                smell_description = None
                
                if smell_description:
                    return ActionResult(
                        success=True,
                        message=smell_description
                    )
                
                # Default room smelling messages based on sanity
                if state.sanity < 30:
                    default_messages = [
                        "The air reeks of decay and something far worse—a smell that shouldn't exist in this world.",
                        "You smell burning flesh and sulfur, though you see no fire.",
                        "The stench of rotting meat fills your nostrils, making you gag.",
                        "An overwhelming smell of blood and death permeates the air, thick and cloying."
                    ]
                elif state.sanity < 60:
                    default_messages = [
                        "The air smells musty and old, with an underlying hint of something unpleasant.",
                        "You detect the scent of mold and dampness, mixed with something you can't quite identify.",
                        "A faint smell of decay lingers in the air, barely noticeable but persistent.",
                        "The air carries an earthy, stale odor that makes you slightly uncomfortable."
                    ]
                else:
                    default_messages = [
                        "The air smells stale and dusty, as if this place has been closed for years.",
                        "You smell nothing unusual, just the musty scent of an old building.",
                        "The air is thick with dust and the smell of aged wood.",
                        "A faint smell of mildew and old stone fills your nostrils."
                    ]
                
                # Use a consistent message based on room hash for consistency
                message_idx = hash(state.current_room) % len(default_messages)
                
                return ActionResult(
                    success=True,
                    message=default_messages[message_idx]
                )
            
            # Smelling a specific object
            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory
            
            if not object_in_room and not object_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {object_id} here."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Check if object has smell_description property
            smell_description = game_object.state.get('smell_description', None)
            
            if smell_description:
                # Apply sanity effects if any
                sanity_change = game_object.state.get('smell_sanity_effect', 0)
                notifications = []
                
                if sanity_change != 0:
                    state.sanity = max(0, min(100, state.sanity + sanity_change))
                    if sanity_change < 0:
                        notifications.append("The smell disturbs you deeply...")
                    elif sanity_change > 0:
                        notifications.append("The smell brings a strange comfort...")
                
                return ActionResult(
                    success=True,
                    message=smell_description,
                    state_changes={
                        'sanity': state.sanity
                    } if sanity_change != 0 else {},
                    notifications=notifications,
                    sanity_change=sanity_change
                )
            
            # Check if object has a SMELL interaction
            smell_interaction = None
            for interaction in game_object.interactions:
                if interaction.verb == "SMELL":
                    # Check if interaction has conditions
                    if interaction.condition:
                        # Check if all conditions are met
                        conditions_met = True
                        for key, required_value in interaction.condition.items():
                            current_value = game_object.state.get(key, None)
                            if current_value != required_value:
                                conditions_met = False
                                break
                        if not conditions_met:
                            continue
                    smell_interaction = interaction
                    break
            
            if smell_interaction:
                # Get the olfactory information (always use spooky version)
                smell_info = smell_interaction.response_spooky
                
                # Apply state changes to object if any
                if smell_interaction.state_change:
                    for key, value in smell_interaction.state_change.items():
                        game_object.state[key] = value
                
                # Apply flag changes to game state if any
                if smell_interaction.flag_change:
                    for flag_name, flag_value in smell_interaction.flag_change.items():
                        state.set_flag(flag_name, flag_value)
                
                # Apply sanity effects if any
                sanity_change = smell_interaction.sanity_effect
                notifications = []
                
                if sanity_change != 0:
                    state.sanity = max(0, min(100, state.sanity + sanity_change))
                    if sanity_change < 0:
                        notifications.append("The smell disturbs you deeply...")
                    elif sanity_change > 0:
                        notifications.append("The smell brings a strange comfort...")
                
                return ActionResult(
                    success=True,
                    message=smell_info,
                    state_changes={
                        'sanity': state.sanity
                    } if sanity_change != 0 else {},
                    notifications=notifications,
                    sanity_change=sanity_change
                )
            
            # Default: nothing to smell
            default_messages = [
                f"You smell the {object_id}, but detect nothing unusual.",
                f"The {object_id} has no particular scent.",
                f"You sniff the {object_id}, but it smells unremarkable.",
                f"The {object_id} offers no distinctive odor.",
                f"Smelling the {object_id} reveals nothing but the ambient scents of this place."
            ]
            
            # Use a consistent message based on object_id hash for consistency
            message_idx = hash(object_id) % len(default_messages)
            
            return ActionResult(
                success=True,
                message=default_messages[message_idx]
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while smelling."
            )
    
    def handle_burn(
        self,
        object_id: str,
        fire_source_id: Optional[str],
        state: GameState
    ) -> ActionResult:
        """
        Handle burning a flammable object with a fire source.
        
        Args:
            object_id: The object to burn
            fire_source_id: The fire source (lamp, matches, etc.) - optional
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 6.1
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if object exists and is accessible
            if object_id not in current_room.items and object_id not in state.inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {object_id} here."
                )
            
            # Get the object
            game_object = self.world.get_object(object_id)
            
            # Check if object is flammable
            if not game_object.state.get('is_flammable', False):
                return ActionResult(
                    success=False,
                    message=f"The {object_id} won't burn."
                )
            
            # If fire source specified, validate it
            if fire_source_id:
                # Check if fire source is in inventory or room
                if fire_source_id not in state.inventory and fire_source_id not in current_room.items:
                    return ActionResult(
                        success=False,
                        message=f"You don't have any {fire_source_id}."
                    )
                
                # Get fire source object
                fire_source = self.world.get_object(fire_source_id)
                
                # Check if it's actually a fire source
                if not fire_source.state.get('is_fire_source', False):
                    return ActionResult(
                        success=False,
                        message=f"You can't burn things with the {fire_source_id}."
                    )
                
                # Check if fire source is lit (for lamp)
                if fire_source_id == "lamp" and not state.get_flag("lamp_on", False):
                    return ActionResult(
                        success=False,
                        message="The lamp isn't lit."
                    )
            
            # Burn the object
            notifications = []
            
            # Remove object from room or inventory
            if object_id in current_room.items:
                current_room.items.remove(object_id)
            if object_id in state.inventory:
                state.remove_from_inventory(object_id)
            
            # Mark object as burned
            game_object.state['is_burned'] = True
            game_object.state['is_destroyed'] = True
            
            # Get burn message
            burn_message = f"The {object_id} catches fire and burns to ashes, leaving nothing but a faint smell of smoke and decay."
            
            # Check for BURN interaction with custom message
            for interaction in game_object.interactions:
                if interaction.verb == "BURN":
                    burn_message = interaction.response_spooky
                    
                    # Apply state changes
                    if interaction.state_change:
                        for key, value in interaction.state_change.items():
                            game_object.state[key] = value
                    
                    # Apply flag changes
                    if interaction.flag_change:
                        for flag_name, flag_value in interaction.flag_change.items():
                            state.set_flag(flag_name, flag_value)
                    
                    # Apply sanity effects
                    if interaction.sanity_effect != 0:
                        state.sanity = max(0, min(100, state.sanity + interaction.sanity_effect))
                        if interaction.sanity_effect < 0:
                            notifications.append("The flames dance with an unnatural hunger...")
                    
                    break
            
            return ActionResult(
                success=True,
                message=burn_message,
                inventory_changed=(object_id in state.inventory),
                state_changes={'sanity': state.sanity} if notifications else {},
                notifications=notifications
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while burning that."
            )
    
    def handle_place_treasure(
        self,
        object_id: str,
        container_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle placing a treasure in the trophy case for scoring.
        
        Updates score based on treasure value, tracks which treasures have been scored,
        and prevents double-scoring the same treasure.
        
        Args:
            object_id: The treasure object to place
            container_id: The container (should be trophy case)
            state: Current game state
            
        Returns:
            ActionResult with success status, message, and score update
            
        Requirements: 13.1, 13.2
        """
        try:
            # First, use the standard put handler to place the object
            put_result = self.handle_put(object_id, container_id, state)
            
            if not put_result.success:
                return put_result
            
            # Get the object to check if it's a treasure
            game_object = self.world.get_object(object_id)
            
            # Check if this is a treasure
            if not game_object.is_treasure:
                # Not a treasure, just return the put result
                return put_result
            
            # Check if this treasure has already been scored
            scored_treasures = state.get_flag("scored_treasures", [])
            if not isinstance(scored_treasures, list):
                scored_treasures = []
            
            if object_id in scored_treasures:
                # Already scored, don't add points again
                return ActionResult(
                    success=True,
                    message=f"{put_result.message} (Already scored)",
                    inventory_changed=True,
                    state_changes=put_result.state_changes,
                    notifications=put_result.notifications
                )
            
            # Add treasure value to score
            treasure_value = game_object.treasure_value
            state.score += treasure_value
            
            # Mark treasure as scored
            scored_treasures.append(object_id)
            state.set_flag("scored_treasures", scored_treasures)
            
            # Create notifications
            notifications = list(put_result.notifications)
            notifications.append(f"You have scored {treasure_value} points!")
            
            # Check for win condition
            if state.score >= 350:
                state.set_flag("won_flag", True)
                notifications.append("Congratulations! You have achieved victory!")
            
            return ActionResult(
                success=True,
                message=put_result.message,
                inventory_changed=True,
                state_changes={
                    **put_result.state_changes,
                    'score': state.score,
                    'flags': state.flags
                },
                notifications=notifications
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {container_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while placing that treasure."
            )
    
    def check_win_condition(
        self,
        state: GameState
    ) -> bool:
        """
        Check if the win condition has been met.
        
        Win condition: score reaches 350 points.
        
        Args:
            state: Current game state
            
        Returns:
            True if win condition met, False otherwise
            
        Requirements: 13.4, 13.5
        """
        return state.score >= 350
    
    def handle_attack(
        self,
        target_id: str,
        weapon_id: Optional[str],
        state: GameState
    ) -> ActionResult:
        """
        Handle attacking creatures with weapons.
        
        Supports attacking creatures with weapons, implements basic combat
        resolution, and updates creature and player states. Returns combat
        descriptions with haunted theme.
        
        Args:
            target_id: The creature to attack
            weapon_id: The weapon to use (optional, can use bare hands)
            state: Current game state
            
        Returns:
            ActionResult with success status, message, and state updates
            
        Requirements: 5.1
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if target is in current room
            if target_id not in current_room.items:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {target_id} here."
                )
            
            # Get target object
            target = self.world.get_object(target_id)
            
            # Check if target is a creature
            is_creature = target.state.get('is_creature', False)
            
            if not is_creature:
                return ActionResult(
                    success=False,
                    message=f"You can't attack the {target_id}."
                )
            
            # Check if weapon is specified and in inventory
            weapon = None
            weapon_damage = 1  # Base damage for bare hands
            weapon_name = "your bare hands"
            
            if weapon_id:
                if weapon_id not in state.inventory:
                    return ActionResult(
                        success=False,
                        message=f"You don't have the {weapon_id}."
                    )
                
                weapon = self.world.get_object(weapon_id)
                
                # Check if object is actually a weapon
                is_weapon = weapon.state.get('is_weapon', False)
                
                if not is_weapon:
                    return ActionResult(
                        success=False,
                        message=f"The {weapon_id} is not a weapon."
                    )
                
                weapon_damage = weapon.state.get('damage', 5)
                weapon_name = weapon.name_spooky if weapon.name_spooky else weapon.name
            
            # Get creature health
            creature_health = target.state.get('health', 10)
            creature_strength = target.state.get('strength', 5)
            creature_name = target.name_spooky if target.name_spooky else target.name
            
            # Calculate damage dealt to creature
            damage_dealt = weapon_damage
            
            # Apply damage to creature
            new_health = creature_health - damage_dealt
            target.state['health'] = max(0, new_health)
            
            notifications = []
            sanity_change = -2  # Attacking is disturbing
            
            # Check if creature is dead
            if new_health <= 0:
                # Creature is dead
                target.state['is_alive'] = False
                target.state['is_dead'] = True
                
                # Remove creature from room
                current_room.items.remove(target_id)
                
                # Check if creature drops items
                drops_items = target.state.get('drops_items', [])
                for item_id in drops_items:
                    if item_id not in current_room.items:
                        current_room.items.append(item_id)
                
                # Apply sanity effects
                state.sanity = max(0, min(100, state.sanity + sanity_change))
                notifications.append("The violence weighs on your mind...")
                
                # Create death message
                death_message = target.state.get('death_message', 
                    f"The {creature_name} collapses in a heap, its life force extinguished.")
                
                attack_message = f"You strike the {creature_name} with {weapon_name}!\n\n{death_message}"
                
                # Check for victory flag
                victory_flag = target.state.get('victory_flag', None)
                if victory_flag:
                    state.set_flag(victory_flag, True)
                    notifications.append("You have overcome a great challenge!")
                
                return ActionResult(
                    success=True,
                    message=attack_message,
                    state_changes={
                        'sanity': state.sanity,
                        'flags': state.flags
                    },
                    notifications=notifications,
                    sanity_change=sanity_change
                )
            
            # Creature is still alive, it counterattacks
            player_damage = creature_strength
            
            # Check if player has armor
            armor_reduction = 0
            for item_id in state.inventory:
                try:
                    item = self.world.get_object(item_id)
                    if item.state.get('is_armor', False):
                        armor_reduction += item.state.get('armor_value', 0)
                except ValueError:
                    pass
            
            actual_damage = max(1, player_damage - armor_reduction)
            
            # Apply damage to player (tracked via sanity for now)
            state.sanity = max(0, state.sanity - actual_damage)
            sanity_change -= actual_damage
            
            # Create combat message
            attack_message = f"You strike the {creature_name} with {weapon_name}, dealing {damage_dealt} damage!\n\n"
            attack_message += f"The {creature_name} retaliates, striking you for {actual_damage} damage!"
            
            notifications.append(f"The {creature_name} has {new_health} health remaining.")
            
            # Check if player died
            if state.sanity <= 0:
                state.set_flag("player_dead", True)
                notifications.append("You have been slain! The darkness claims you...")
            
            return ActionResult(
                success=True,
                message=attack_message,
                state_changes={
                    'sanity': state.sanity,
                    'flags': state.flags
                },
                notifications=notifications,
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {target_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong during combat."
            )
    
    def handle_throw(
        self,
        object_id: str,
        target_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle throwing objects at targets.
        
        Validates object is in inventory, moves object to target location,
        and applies any throw effects (damage, activation). Returns thematic
        descriptions.
        
        Args:
            object_id: The object to throw
            target_id: The target to throw at
            state: Current game state
            
        Returns:
            ActionResult with success status, message, and state updates
            
        Requirements: 5.2
        """
        try:
            # Check if object is in inventory
            if object_id not in state.inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't have the {object_id}."
                )
            
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if target is in current room
            if target_id not in current_room.items:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {target_id} here."
                )
            
            # Get object and target
            game_object = self.world.get_object(object_id)
            target = self.world.get_object(target_id)
            
            # Check if object is throwable
            is_throwable = game_object.state.get('is_throwable', True)  # Most objects can be thrown
            
            if not is_throwable:
                return ActionResult(
                    success=False,
                    message=f"You can't throw the {object_id}."
                )
            
            # Remove from inventory
            state.remove_from_inventory(object_id)
            
            # Add to current room (object lands here)
            current_room.items.append(object_id)
            
            notifications = []
            sanity_change = 0
            
            # Check if throwing at a creature
            is_creature = target.state.get('is_creature', False)
            
            if is_creature:
                # Calculate throw damage
                throw_damage = game_object.state.get('throw_damage', 2)
                
                # Apply damage to creature
                creature_health = target.state.get('health', 10)
                new_health = creature_health - throw_damage
                target.state['health'] = max(0, new_health)
                
                creature_name = target.name_spooky if target.name_spooky else target.name
                object_name = game_object.name_spooky if game_object.name_spooky else game_object.name
                
                # Check if creature is dead
                if new_health <= 0:
                    target.state['is_alive'] = False
                    target.state['is_dead'] = True
                    current_room.items.remove(target_id)
                    
                    # Check if creature drops items
                    drops_items = target.state.get('drops_items', [])
                    for item_id in drops_items:
                        if item_id not in current_room.items:
                            current_room.items.append(item_id)
                    
                    throw_message = f"You hurl the {object_name} at the {creature_name}!\n\n"
                    throw_message += f"The {creature_name} is struck down and collapses!"
                    
                    sanity_change = -2
                    notifications.append("The violence disturbs you...")
                else:
                    throw_message = f"You hurl the {object_name} at the {creature_name}!\n\n"
                    throw_message += f"The {creature_name} is hit for {throw_damage} damage!"
                    notifications.append(f"The {creature_name} has {new_health} health remaining.")
            else:
                # Throwing at non-creature
                object_name = game_object.name_spooky if game_object.name_spooky else game_object.name
                target_name = target.name_spooky if target.name_spooky else target.name
                
                throw_message = f"You throw the {object_name} at the {target_name}. It bounces off harmlessly."
                
                # Check for special throw effects
                throw_effect = game_object.state.get('throw_effect', None)
                if throw_effect:
                    # Apply custom throw effect
                    if throw_effect == 'break':
                        game_object.state['is_broken'] = True
                        throw_message += f"\n\nThe {object_name} shatters on impact!"
                    elif throw_effect == 'activate':
                        target.state['is_activated'] = True
                        throw_message += f"\n\nThe impact activates the {target_name}!"
            
            # Apply sanity effects
            if sanity_change != 0:
                state.sanity = max(0, min(100, state.sanity + sanity_change))
            
            return ActionResult(
                success=True,
                message=throw_message,
                inventory_changed=True,
                state_changes={
                    'inventory': state.inventory,
                    'sanity': state.sanity
                },
                notifications=notifications,
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {target_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while throwing."
            )
    
    def handle_give(
        self,
        object_id: str,
        npc_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle giving objects to NPCs.
        
        Validates object is in inventory, transfers object to NPC possession,
        and triggers NPC reactions if defined. Returns appropriate messages.
        
        Args:
            object_id: The object to give
            npc_id: The NPC to give the object to
            state: Current game state
            
        Returns:
            ActionResult with success status, message, and state updates
            
        Requirements: 5.3
        """
        try:
            # Check if object is in inventory
            if object_id not in state.inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't have the {object_id}."
                )
            
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if NPC is in current room
            if npc_id not in current_room.items:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {npc_id} here."
                )
            
            # Get object and NPC
            game_object = self.world.get_object(object_id)
            npc = self.world.get_object(npc_id)
            
            # Check if target is an NPC
            is_npc = npc.state.get('is_npc', False)
            is_creature = npc.state.get('is_creature', False)
            
            if not is_npc and not is_creature:
                return ActionResult(
                    success=False,
                    message=f"You can't give things to the {npc_id}."
                )
            
            # Remove from player inventory
            state.remove_from_inventory(object_id)
            
            # Add to NPC's inventory
            if 'inventory' not in npc.state:
                npc.state['inventory'] = []
            npc.state['inventory'].append(object_id)
            
            notifications = []
            sanity_change = 0
            
            # Check for NPC reactions to this specific object
            reactions = npc.state.get('gift_reactions', {})
            
            object_name = game_object.name_spooky if game_object.name_spooky else game_object.name
            npc_name = npc.name_spooky if npc.name_spooky else npc.name
            
            if object_id in reactions:
                # NPC has a specific reaction to this object
                reaction = reactions[object_id]
                give_message = f"You give the {object_name} to the {npc_name}.\n\n{reaction['message']}"
                
                # Apply reaction effects
                if 'flag_change' in reaction:
                    for flag_name, flag_value in reaction['flag_change'].items():
                        state.set_flag(flag_name, flag_value)
                
                if 'sanity_effect' in reaction:
                    sanity_change = reaction['sanity_effect']
                
                if 'gives_item' in reaction:
                    # NPC gives something in return
                    return_item = reaction['gives_item']
                    state.add_to_inventory(return_item)
                    try:
                        return_obj = self.world.get_object(return_item)
                        return_name = return_obj.name_spooky if return_obj.name_spooky else return_obj.name
                        notifications.append(f"The {npc_name} gives you {return_name} in return!")
                    except ValueError:
                        notifications.append(f"The {npc_name} gives you something in return!")
                
                if 'npc_leaves' in reaction and reaction['npc_leaves']:
                    # NPC leaves the room
                    current_room.items.remove(npc_id)
                    notifications.append(f"The {npc_name} departs, satisfied.")
            else:
                # Default reaction
                default_reaction = npc.state.get('default_gift_reaction', 
                    f"The {npc_name} accepts the {object_name} with a cold, unreadable expression.")
                give_message = f"You give the {object_name} to the {npc_name}.\n\n{default_reaction}"
            
            # Apply sanity effects
            if sanity_change != 0:
                state.sanity = max(0, min(100, state.sanity + sanity_change))
            
            return ActionResult(
                success=True,
                message=give_message,
                inventory_changed=True,
                state_changes={
                    'inventory': state.inventory,
                    'sanity': state.sanity,
                    'flags': state.flags
                },
                notifications=notifications,
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {npc_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while giving that."
            )
    
    def handle_tell(
        self,
        npc_id: str,
        message: Optional[str],
        state: GameState
    ) -> ActionResult:
        """
        Handle dialogue with NPCs (TELL and ASK commands).
        
        Supports dialogue with NPCs, returns NPC responses, and tracks
        conversation state if needed. Uses thematic dialogue.
        
        Args:
            npc_id: The NPC to talk to
            message: The message or topic (optional)
            state: Current game state
            
        Returns:
            ActionResult with success status and dialogue response
            
        Requirements: 5.4
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if NPC is in current room
            if npc_id not in current_room.items:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {npc_id} here."
                )
            
            # Get NPC
            npc = self.world.get_object(npc_id)
            
            # Check if target is an NPC or creature
            is_npc = npc.state.get('is_npc', False)
            is_creature = npc.state.get('is_creature', False)
            
            if not is_npc and not is_creature:
                return ActionResult(
                    success=False,
                    message=f"The {npc_id} doesn't respond to your words."
                )
            
            npc_name = npc.name_spooky if npc.name_spooky else npc.name
            
            # Check if NPC has dialogue responses
            dialogue_responses = npc.state.get('dialogue_responses', {})
            
            if message and message.lower() in dialogue_responses:
                # NPC has a specific response to this topic
                response = dialogue_responses[message.lower()]
                
                # Check if response has conditions
                if isinstance(response, dict):
                    # Complex response with conditions
                    if 'condition_flag' in response:
                        condition_met = state.get_flag(response['condition_flag'], False)
                        if condition_met:
                            dialogue_message = response.get('response_if_true', response.get('response', ''))
                        else:
                            dialogue_message = response.get('response_if_false', response.get('response', ''))
                    else:
                        dialogue_message = response.get('response', '')
                    
                    # Apply any flag changes
                    if 'flag_change' in response:
                        for flag_name, flag_value in response['flag_change'].items():
                            state.set_flag(flag_name, flag_value)
                else:
                    # Simple string response
                    dialogue_message = response
            else:
                # Default response
                default_response = npc.state.get('default_dialogue', 
                    f"The {npc_name} stares at you with hollow eyes but says nothing.")
                dialogue_message = default_response
            
            # Track conversation state
            if 'conversation_count' not in npc.state:
                npc.state['conversation_count'] = 0
            npc.state['conversation_count'] += 1
            
            return ActionResult(
                success=True,
                message=dialogue_message,
                state_changes={
                    'flags': state.flags
                }
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {npc_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong during conversation."
            )
    
    def handle_wake(
        self,
        creature_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle waking sleeping creatures.
        
        Supports waking sleeping creatures, changes creature state from
        sleeping to awake, and triggers wake-up reactions. Returns
        appropriate messages.
        
        Args:
            creature_id: The creature to wake
            state: Current game state
            
        Returns:
            ActionResult with success status, message, and state updates
            
        Requirements: 5.5
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if creature is in current room
            if creature_id not in current_room.items:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {creature_id} here."
                )
            
            # Get creature
            creature = self.world.get_object(creature_id)
            
            # Check if target is a creature or NPC
            is_creature = creature.state.get('is_creature', False)
            is_npc = creature.state.get('is_npc', False)
            
            if not is_creature and not is_npc:
                return ActionResult(
                    success=False,
                    message=f"You can't wake the {creature_id}."
                )
            
            # Check if creature is sleeping
            is_sleeping = creature.state.get('is_sleeping', False)
            
            if not is_sleeping:
                creature_name = creature.name_spooky if creature.name_spooky else creature.name
                return ActionResult(
                    success=False,
                    message=f"The {creature_name} is not sleeping."
                )
            
            # Wake the creature
            creature.state['is_sleeping'] = False
            creature.state['is_awake'] = True
            
            notifications = []
            sanity_change = 0
            
            creature_name = creature.name_spooky if creature.name_spooky else creature.name
            
            # Check for wake-up reaction
            wake_reaction = creature.state.get('wake_reaction', None)
            
            if wake_reaction:
                wake_message = f"You wake the {creature_name}.\n\n{wake_reaction}"
                
                # Check if waking triggers hostility
                becomes_hostile = creature.state.get('hostile_when_woken', False)
                if becomes_hostile:
                    creature.state['is_hostile'] = True
                    notifications.append(f"The {creature_name} looks angry at being disturbed!")
                    sanity_change = -3
            else:
                # Default wake message
                wake_message = f"You wake the {creature_name}. It stirs and opens its eyes, regarding you with an unsettling gaze."
            
            # Apply any flag changes
            wake_flag = creature.state.get('wake_flag', None)
            if wake_flag:
                state.set_flag(wake_flag, True)
            
            # Apply sanity effects
            if sanity_change != 0:
                state.sanity = max(0, min(100, state.sanity + sanity_change))
                notifications.append("The encounter disturbs you...")
            
            return ActionResult(
                success=True,
                message=wake_message,
                state_changes={
                    'sanity': state.sanity,
                    'flags': state.flags
                },
                notifications=notifications,
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {creature_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong while waking that."
            )
    
    def handle_kiss(
        self,
        npc_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle kissing NPCs.
        
        Supports kissing NPCs and returns humorous or thematic responses.
        No state changes (just flavor).
        
        Args:
            npc_id: The NPC to kiss
            state: Current game state
            
        Returns:
            ActionResult with success status and response message
            
        Requirements: 5.6
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if NPC is in current room
            if npc_id not in current_room.items:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {npc_id} here."
                )
            
            # Get NPC
            npc = self.world.get_object(npc_id)
            
            # Check if target is an NPC or creature
            is_npc = npc.state.get('is_npc', False)
            is_creature = npc.state.get('is_creature', False)
            
            if not is_npc and not is_creature:
                return ActionResult(
                    success=False,
                    message=f"Kissing the {npc_id} seems like a bad idea."
                )
            
            npc_name = npc.name_spooky if npc.name_spooky else npc.name
            
            # Check for custom kiss response
            kiss_response = npc.state.get('kiss_response', None)
            
            if kiss_response:
                kiss_message = kiss_response
            else:
                # Default humorous/thematic responses
                default_responses = [
                    f"You kiss the {npc_name}. Its cold, lifeless lips send a shiver down your spine.",
                    f"The {npc_name} recoils from your advance, looking deeply offended.",
                    f"You lean in to kiss the {npc_name}, but it vanishes in a puff of smoke before you can make contact.",
                    f"The {npc_name} accepts your kiss with an eerie smile that makes your blood run cold.",
                    f"You kiss the {npc_name}. Nothing happens, but you feel foolish.",
                    f"The {npc_name} turns its head away. Perhaps romance is not in the cards today.",
                    f"Your lips meet the {npc_name}'s cold flesh. You immediately regret this decision."
                ]
                
                # Use a consistent response based on npc_id hash
                response_idx = hash(npc_id) % len(default_responses)
                kiss_message = default_responses[response_idx]
            
            return ActionResult(
                success=True,
                message=kiss_message
            )
            
        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {npc_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something went wrong during that awkward moment."
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
        # Handle climb commands
        if command.verb == "CLIMB" and command.direction:
            return self.handle_climb(command.direction, command.object, state)
        
        # Handle enter commands
        if command.verb == "ENTER":
            return self.handle_enter(command.object, state)
        
        # Handle exit commands
        if command.verb == "EXIT":
            return self.handle_exit(command.object, state)
        
        # Handle board commands
        if command.verb == "BOARD" and command.object:
            return self.handle_board(command.object, state)
        
        # Handle disembark commands (also GET OUT)
        if command.verb in ["DISEMBARK", "GET_OUT"]:
            return self.handle_disembark(command.object, state)
        
        # Handle movement commands
        if command.verb == "GO" and command.direction:
            return self.handle_movement(command.direction, state)
        
        # Handle examine commands
        if command.verb == "EXAMINE" and command.object:
            # Check if examining a container
            try:
                obj = self.world.get_object(command.object)
                if obj.type == "container":
                    return self.handle_examine_container(command.object, state)
            except ValueError:
                pass
            return self.handle_examine(command.object, state)
        
        # Handle take commands
        if command.verb == "TAKE" and command.object:
            # Check if taking from a container (format: "take object from container")
            if command.preposition == "FROM" and command.target:
                return self.handle_take_from_container(command.object, command.target, state)
            return self.handle_take(command.object, state)
        
        # Handle drop commands
        if command.verb == "DROP" and command.object:
            return self.handle_drop(command.object, state)
        
        # Handle put commands (format: "put object in container")
        if command.verb == "PUT" and command.object and command.target:
            # Check if target is trophy case for treasure scoring
            if command.target == "trophy_case":
                return self.handle_place_treasure(command.object, command.target, state)
            return self.handle_put(command.object, command.target, state)
        
        # Handle lock commands (format: "lock object with key")
        if command.verb == "LOCK" and command.object:
            if not command.target:
                return ActionResult(
                    success=False,
                    message=f"What do you want to lock the {command.object} with?"
                )
            return self.handle_lock(command.object, command.target, state)
        
        # Handle unlock commands (format: "unlock object with key")
        if command.verb == "UNLOCK" and command.object:
            if not command.target:
                return ActionResult(
                    success=False,
                    message=f"What do you want to unlock the {command.object} with?"
                )
            return self.handle_unlock(command.object, command.target, state)
        
        # Handle turn commands
        if command.verb == "TURN" and command.object:
            return self.handle_turn(command.object, state)
        
        # Handle push commands
        if command.verb == "PUSH" and command.object:
            return self.handle_push(command.object, state)
        
        # Handle pull commands
        if command.verb == "PULL" and command.object:
            return self.handle_pull(command.object, state)
        
        # Handle tie commands (format: "tie object to target")
        if command.verb == "TIE" and command.object:
            if not command.target:
                return ActionResult(
                    success=False,
                    message=f"What do you want to tie the {command.object} to?"
                )
            return self.handle_tie(command.object, command.target, state)
        
        # Handle untie commands
        if command.verb == "UNTIE" and command.object:
            return self.handle_untie(command.object, state)
        
        # Handle fill commands (format: "fill object from source")
        if command.verb == "FILL" and command.object:
            if not command.target:
                return ActionResult(
                    success=False,
                    message=f"What do you want to fill the {command.object} from?"
                )
            return self.handle_fill(command.object, command.target, state)
        
        # Handle pour commands (format: "pour object" or "pour object into target")
        if command.verb == "POUR" and command.object:
            # Target is optional for pour (can pour onto ground)
            return self.handle_pour(command.object, command.target, state)
        
        # Handle read commands
        if command.verb == "READ" and command.object:
            return self.handle_read(command.object, state)
        
        # Handle object interaction commands (OPEN, CLOSE, MOVE)
        if command.verb in ["OPEN", "CLOSE", "MOVE"] and command.object:
            return self.handle_object_interaction(command.verb, command.object, state)
        
        # Handle lamp commands (LIGHT, TURN ON)
        if command.verb in ["LIGHT", "TURN_ON"] and command.object == "lamp":
            return self.handle_lamp_on(state)
        
        # Handle lamp off commands (EXTINGUISH, TURN OFF)
        if command.verb in ["EXTINGUISH", "TURN_OFF"] and command.object == "lamp":
            return self.handle_lamp_off(state)
        
        # Handle look under commands
        if command.verb == "LOOK_UNDER" and command.object:
            return self.handle_look_under(command.object, state)
        
        # Handle look behind commands
        if command.verb == "LOOK_BEHIND" and command.object:
            return self.handle_look_behind(command.object, state)
        
        # Handle look inside commands
        if command.verb == "LOOK_INSIDE" and command.object:
            return self.handle_look_inside(command.object, state)
        
        # Handle search commands
        if command.verb == "SEARCH" and command.object:
            return self.handle_search(command.object, state)
        
        # Handle listen commands (can listen to object or room)
        if command.verb == "LISTEN":
            return self.handle_listen(command.object, state)
        
        # Handle smell commands (can smell object or room)
        if command.verb == "SMELL":
            return self.handle_smell(command.object, state)
        
        # Handle burn commands (format: "burn object" or "burn object with fire_source")
        if command.verb == "BURN" and command.object:
            # Target is the fire source (if specified with WITH preposition)
            return self.handle_burn(command.object, command.target, state)
        
        # Handle attack commands (format: "attack creature" or "attack creature with weapon")
        if command.verb in ["ATTACK", "KILL"] and command.object:
            # Target is the weapon (if specified with WITH preposition)
            return self.handle_attack(command.object, command.target, state)
        
        # Handle throw commands (format: "throw object at target")
        if command.verb == "THROW" and command.object:
            if not command.target:
                return ActionResult(
                    success=False,
                    message=f"What do you want to throw the {command.object} at?"
                )
            return self.handle_throw(command.object, command.target, state)
        
        # Handle give commands (format: "give object to npc")
        if command.verb == "GIVE" and command.object:
            if not command.target:
                return ActionResult(
                    success=False,
                    message=f"Who do you want to give the {command.object} to?"
                )
            return self.handle_give(command.object, command.target, state)
        
        # Handle tell/ask commands (format: "tell npc about topic" or "ask npc about topic")
        if command.verb in ["TELL", "ASK"] and command.object:
            # Target is the topic (optional)
            return self.handle_tell(command.object, command.target, state)
        
        # Handle wake commands
        if command.verb == "WAKE" and command.object:
            return self.handle_wake(command.object, state)
        
        # Handle kiss commands
        if command.verb == "KISS" and command.object:
            return self.handle_kiss(command.object, state)
        
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
