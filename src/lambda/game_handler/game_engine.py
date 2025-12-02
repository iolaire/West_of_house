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
        
        # Handle object interaction commands (OPEN, CLOSE, READ, MOVE)
        if command.verb in ["OPEN", "CLOSE", "READ", "MOVE"] and command.object:
            return self.handle_object_interaction(command.verb, command.object, state)
        
        # Handle lamp commands (LIGHT, TURN ON)
        if command.verb in ["LIGHT", "TURN_ON"] and command.object == "lamp":
            return self.handle_lamp_on(state)
        
        # Handle lamp off commands (EXTINGUISH, TURN OFF)
        if command.verb in ["EXTINGUISH", "TURN_OFF"] and command.object == "lamp":
            return self.handle_lamp_off(state)
        
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
