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
            
        Requirements: 4.4, 4.5
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
            
            # Apply sanity effects
            sanity_change = matching_interaction.sanity_effect
            notifications = []
            
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
            return self.handle_put(command.object, command.target, state)
        
        # Handle object interaction commands (OPEN, CLOSE, READ, MOVE)
        if command.verb in ["OPEN", "CLOSE", "READ", "MOVE"] and command.object:
            return self.handle_object_interaction(command.verb, command.object, state)
        
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
