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
    
    def resolve_object_name(self, name: str, state: GameState) -> Optional[str]:
        """
        Resolve a flexible object name to an object ID.
        
        Searches in current room and inventory for objects matching the name.
        
        Args:
            name: The name to resolve (e.g., "parchment", "cursed", "leaflet")
            state: Current game state
            
        Returns:
            Object ID if found, None otherwise
        """
        try:
            current_room = self.world.get_room(state.current_room)
            # Include global items in available objects
            available_objects = list(current_room.items) + list(state.inventory) + list(current_room.global_items)
            
            # Add objects from open containers in room, inventory, and global items
            for container_id in list(current_room.items) + list(state.inventory) + list(current_room.global_items):
                try:
                    container = self.world.get_object(container_id)
                    if container.type == 'container':
                        # Check GameState first, then fall back to World data
                        is_open = state.get_object_state(container_id, 'is_open', container.state.get('is_open', False))
                        if is_open:
                            contents = state.get_object_state(container_id, 'contents', container.state.get('contents', []))
                            available_objects.extend(contents)
                except (ValueError, AttributeError):
                    continue
            
            return self.world.find_object_by_name(name, available_objects)
        except Exception:
            return None
    
    def find_matching_objects(self, name: str, state: GameState) -> List[str]:
        """
        Find all objects matching a name in current room, inventory, and open containers.
        
        Args:
            name: The name to search for
            state: Current game state
            
        Returns:
            List of matching object IDs
        """
        matches = []
        try:
            current_room = self.world.get_room(state.current_room)
            available_objects = list(current_room.items) + list(state.inventory)
            
            # Add objects from open containers in room and inventory
            for container_id in list(current_room.items) + list(state.inventory):
                try:
                    container = self.world.get_object(container_id)
                    if container.type == 'container':
                        # Check GameState first, then fall back to World data
                        is_open = state.get_object_state(container_id, 'is_open', container.state.get('is_open', False))
                        if is_open:
                            contents = state.get_object_state(container_id, 'contents', container.state.get('contents', []))
                            available_objects.extend(contents)
                except (ValueError, AttributeError):
                    continue
            
            for obj_id in available_objects:
                try:
                    obj = self.world.get_object(obj_id)
                    # Check if name matches object ID or any of its names
                    if (name.lower() == obj_id.lower() or 
                        name.lower() in [n.lower() for n in [obj.name]]):
                        matches.append(obj_id)
                except ValueError:
                    continue
        except Exception:
            pass
        
        return matches

    def resolve_object_reference(self, object_ref: str, state: GameState) -> Optional[str]:
        """
        Resolve an object reference (ID or name) to an object ID.

        This method allows objects to be referenced by either their ID or any of their names.
        For example, both "teeth" and "vampire fangs" would resolve to the same object.
        Also checks inside open containers.

        Args:
            object_ref: The object reference (ID or name)
            state: Current game state

        Returns:
            Object ID if found, None otherwise
        """
        if not object_ref:
            return None

        # First try direct ID match (case-insensitive)
        try:
            current_room = self.world.get_room(state.current_room)
            available_objects = list(current_room.items) + list(state.inventory)
            
            # Add objects from open containers in room and inventory
            for container_id in list(current_room.items) + list(state.inventory):
                try:
                    container = self.world.get_object(container_id)
                    if container.type == 'container':
                        # Check GameState first, then fall back to World data
                        is_open = state.get_object_state(container_id, 'is_open', container.state.get('is_open', False))
                        if is_open:
                            contents = state.get_object_state(container_id, 'contents', container.state.get('contents', []))
                            available_objects.extend(contents)
                except (ValueError, AttributeError):
                    continue

            # Check if it's a direct object ID
            for obj_id in available_objects:
                if object_ref.lower() == obj_id.lower():
                    return obj_id

            # Use the existing flexible name matching
            return self.world.find_object_by_name(object_ref, available_objects)
        except Exception:
            return None

    def is_object_accessible(self, object_id: str, state: GameState) -> bool:
        """
        Check if an object is accessible (visible/interactable) to the player.
        
        Checks:
        1. In current room
        2. In inventory
        3. Inside an open container in room or inventory
        
        Args:
            object_id: The object identifier
            state: Current game state
            
        Returns:
            True if accessible, False otherwise
        """
        try:
            current_room = self.world.get_room(state.current_room)
            
            # 1. Check direct presence
            if object_id in current_room.items or object_id in state.inventory or object_id in current_room.global_items:
                return True
            
            # 2. Check inside containers
            for container_id in list(current_room.items) + list(state.inventory) + list(current_room.global_items):
                try:
                    container = self.world.get_object(container_id)
                    if container.type == 'container':
                        # Check GameState first, then fall back to World data
                        is_open = state.get_object_state(container_id, 'is_open', container.state.get('is_open', False))
                        if is_open:
                            contents = state.get_object_state(container_id, 'contents', container.state.get('contents', []))
                            if object_id in contents:
                                return True
                except (ValueError, AttributeError):
                    continue
            
            return False
        except Exception:
            return False

    def get_full_room_description(self, state: GameState) -> str:
        """
        Get the full room description including visible objects.

        Args:
            state: Current game state

        Returns:
            Complete room description with objects listed
        """
        # Check if room is lit
        is_lit = self.is_room_lit(state.current_room, state)

        if not is_lit:
            # Return darkness description for unlit rooms
            return self.get_darkness_description(state.current_room)

        # Get room description with objects
        description = self.world.get_room_description(
            state.current_room,
            state.sanity,
            include_objects=True
        )

        # Add contents of open/transparent containers in the room
        current_room_obj = self.world.get_room(state.current_room)
        # Check both items and global items
        for item_id in list(current_room_obj.items) + list(current_room_obj.global_items):
            try:
                item = self.world.get_object(item_id)
                if item.type == "container":
                    is_open = state.get_object_state(item_id, 'is_open', item.state.get('is_open', False))
                    is_transparent = state.get_object_state(item_id, 'is_transparent', item.state.get('is_transparent', False))
                    
                    if is_open or is_transparent:
                        contents = state.get_object_state(item_id, 'contents', item.state.get('contents', []))
                        if contents:
                            content_names = []
                            for content_id in contents:
                                try:
                                    content_obj = self.world.get_object(content_id)
                                    # Use spooky name if available
                                    content_name = content_obj.name_spooky if content_obj.name_spooky else content_obj.name
                                    content_names.append(content_name)
                                except ValueError:
                                    continue
                            
                            if content_names:
                                # Use spooky name for container if available
                                container_name = item.name_spooky if item.name_spooky else item.name
                                if is_open:
                                    description += f" Inside the {container_name}, you see: {', '.join(content_names)}."
                                else:
                                    description += f" Through the {container_name}, you see: {', '.join(content_names)}."
            except ValueError:
                continue

        return description

    def handle_look(self, state: GameState) -> ActionResult:
        """
        Handle LOOK command (look around current room).

        Returns full room description with visible objects.

        Args:
            state: Current game state

        Returns:
            ActionResult with room description
        """
        description = self.get_full_room_description(state)
        return ActionResult(
            success=True,
            message=description
        )

    def handle_inventory(self, state: GameState) -> ActionResult:
        """
        Handle INVENTORY command.

        Lists items in player's inventory.

        Args:
            state: Current game state

        Returns:
            ActionResult with inventory listing
        """
        if not state.inventory:
            return ActionResult(
                success=True,
                message="You are empty-handed. The void claims all."
            )
        
        # Get display names for all items
        items = []
        for item_id in state.inventory:
            name = self._get_object_names(item_id)
            # Capitalize first letter
            name = name[0].upper() + name[1:] if name else name
            items.append(f"  A {name}")
            
        message = "You are carrying:\n" + "\n".join(items)
        
        return ActionResult(
            success=True,
            message=message
        )

    def create_disambiguation_prompt(self, matches: List[str]) -> str:
        """
        Create a prompt asking the player to clarify which object they mean.
        
        Args:
            matches: List of matching object IDs
            
        Returns:
            Disambiguation prompt message
        """
        if len(matches) == 0:
            return "I don't see that here."
        
        if len(matches) == 1:
            return ""  # No disambiguation needed
        
        # Get object names for display
        object_names = []
        for obj_id in matches:
            try:
                obj = self.world.get_object(obj_id)
                # Use first name from names list
                display_name = obj.name if [obj.name] else obj_id
                object_names.append(display_name)
            except ValueError:
                object_names.append(obj_id)
        
        # Format prompt
        if len(object_names) == 2:
            return f"Which do you mean, the {object_names[0]} or the {object_names[1]}?"
        else:
            names_list = ", ".join(f"the {name}" for name in object_names[:-1])
            return f"Which do you mean, {names_list}, or the {object_names[-1]}?"
    
    def check_prerequisites(
        self,
        verb: str,
        object_id: Optional[str],
        state: GameState
    ) -> Optional[ActionResult]:
        """
        Check if prerequisites are met for a command.
        
        Verifies that required conditions are satisfied before executing
        a command. Returns error message if prerequisites not met.
        
        Args:
            verb: The command verb
            object_id: The target object (if any)
            state: Current game state
            
        Returns:
            ActionResult with error if prerequisites not met, None if OK
            
        Requirements: 11.4
        """
        # Check object-specific prerequisites
        if object_id:
            try:
                obj = self.world.get_object(object_id)
                
                # Check if object has prerequisites
                prerequisites = obj.state.get('prerequisites', {})
                
                if prerequisites:
                    # Check flag prerequisites
                    required_flags = prerequisites.get('flags', {})
                    for flag_name, required_value in required_flags.items():
                        actual_value = state.get_flag(flag_name, False)
                        if actual_value != required_value:
                            reason = prerequisites.get('failure_message', 
                                f"You can't do that yet.")
                            return ActionResult(
                                success=False,
                                message=reason
                            )
                    
                    # Check inventory prerequisites
                    required_items = prerequisites.get('required_items', [])
                    for item in required_items:
                        if item not in state.inventory:
                            item_obj = self.world.get_object(item)
                            item_name = item_obj.name if item_[obj.name] else item
                            return ActionResult(
                                success=False,
                                message=f"You need the {item_name} to do that."
                            )
                    
                    # Check location prerequisites
                    required_room = prerequisites.get('required_room', None)
                    if required_room and state.current_room != required_room:
                        return ActionResult(
                            success=False,
                            message="You can't do that here."
                        )
            except ValueError:
                pass
        
        # Check verb-specific prerequisites
        if verb == "UNLOCK":
            # Unlocking requires object to be locked
            if object_id:
                try:
                    obj = self.world.get_object(object_id)
                    if not obj.state.get('is_locked', False):
                        display_name = self._get_object_names(object_id)
                        return ActionResult(
                            success=False,
                            message=f"The {display_name} isn't locked."
                        )
                except ValueError:
                    pass
        
        elif verb == "LOCK":
            # Locking requires object to be unlocked
            if object_id:
                try:
                    obj = self.world.get_object(object_id)
                    if obj.state.get('is_locked', False):
                        display_name = self._get_object_names(object_id)
                        return ActionResult(
                            success=False,
                            message=f"The {display_name} is already locked."
                        )
                except ValueError:
                    pass
        
        elif verb == "OPEN":
            # Opening requires object to be closed
            if object_id:
                try:
                    obj = self.world.get_object(object_id)
                    if obj.state.get('is_open', False):
                        display_name = self._get_object_names(object_id)
                        return ActionResult(
                            success=False,
                            message=f"The {display_name} is already open."
                        )
                except ValueError:
                    pass
        
        elif verb == "CLOSE":
            # Closing requires object to be open
            if object_id:
                try:
                    obj = self.world.get_object(object_id)
                    if not obj.state.get('is_open', False):
                        display_name = self._get_object_names(object_id)
                        return ActionResult(
                            success=False,
                            message=f"The {display_name} is already closed."
                        )
                except ValueError:
                    pass
        
        # No prerequisites failed
        return None
    
    def expand_multi_object(
        self,
        object_spec: str,
        state: GameState
    ) -> List[str]:
        """
        Expand multi-object specifiers like 'all', 'everything', etc.
        
        Args:
            object_spec: The object specification (e.g., 'all', 'everything')
            state: Current game state
            
        Returns:
            List of object IDs matching the specification
            
        Requirements: 11.5
        """
        current_room = self.world.get_room(state.current_room)
        
        # Handle 'all' or 'everything'
        if object_spec.lower() in ['all', 'everything']:
            # Return all takeable objects in room
            objects = []
            for obj_id in current_room.items:
                try:
                    obj = self.world.get_object(obj_id)
                    if obj.state.get('is_takeable', True):
                        objects.append(obj_id)
                except ValueError:
                    continue
            return objects
        
        # Handle 'all except X' or 'everything but X'
        if 'except' in object_spec.lower() or 'but' in object_spec.lower():
            parts = object_spec.lower().replace('but', 'except').split('except')
            if len(parts) == 2:
                excluded = parts[1].strip()
                objects = []
                for obj_id in current_room.items:
                    try:
                        obj = self.world.get_object(obj_id)
                        if obj.state.get('is_takeable', True):
                            # Check if this object matches the exclusion
                            if excluded not in obj_id.lower() and excluded not in [n.lower() for n in [obj.name]]:
                                objects.append(obj_id)
                    except ValueError:
                        continue
                return objects
        
        # Single object
        return [object_spec]
    
    def handle_multi_object_command(
        self,
        verb: str,
        objects: List[str],
        state: GameState,
        target: Optional[str] = None
    ) -> ActionResult:
        """
        Handle commands that affect multiple objects.
        
        Processes each object individually and combines results.
        
        Args:
            verb: The command verb
            objects: List of object IDs to process
            state: Current game state
            target: Optional target for the command
            
        Returns:
            ActionResult with combined results
            
        Requirements: 11.5
        """
        if not objects:
            return ActionResult(
                success=False,
                message="There's nothing here to do that with."
            )
        
        results = []
        success_count = 0
        
        for obj_id in objects:
            # Create a command for this object
            from command_parser import ParsedCommand
            cmd = ParsedCommand(
                verb=verb,
                object=obj_id,
                target=target
            )
            
            # Execute the command
            result = self.execute_command(cmd, state)
            
            if result.success:
                success_count += 1
                results.append(f"{obj_id}: {result.message}")
            else:
                results.append(f"{obj_id}: {result.message}")
        
        # Combine results
        combined_message = "\n".join(results)
        
        return ActionResult(
            success=success_count > 0,
            message=combined_message,
            room_changed=False
        )
    
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
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here.",
                    room_changed=False
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Check if object is enterable
            is_enterable = game_object.state.get('is_enterable', False)
            
            if not is_enterable:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You can't enter the {display_name}.",
                    room_changed=False
                )
            
            # Check if object has an entry destination
            entry_destination = game_object.state.get('entry_destination', None)
            
            if not entry_destination:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"There's nowhere to go inside the {display_name}.",
                    room_changed=False
                )
            
            # Check if entry requires any conditions
            entry_condition = game_object.state.get('entry_condition', None)
            if entry_condition:
                # Check if condition flag is met
                condition_met = state.get_flag(entry_condition, False)
                if not condition_met:
                    display_name = self._get_object_names(object_id)
                    return ActionResult(
                        success=False,
                        message=f"You can't enter the {display_name} right now.",
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
                description = self.world.get_room_description(entry_destination, state.sanity, include_objects=True)
            
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
            display_name = self._get_object_names(object_id)
            enter_message = f"You enter the {display_name}, crossing into its shadowy interior."
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
                message="The shadows twist and writhe, preventing your passage into the unknown.",
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
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You're not in the {display_name}.",
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
                description = self.world.get_room_description(exit_destination, state.sanity, include_objects=True)
            
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
            display_name = self._get_object_names(object_id)
            exit_message = f"You exit the {display_name}, emerging back into the open."
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
                message="The darkness clings to you, refusing to release its grip as you try to leave.",
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
                current_vehicle_name = self._get_object_names(state.current_vehicle)
                return ActionResult(
                    success=False,
                    message=f"You're already in the {current_vehicle_name}. You need to disembark first.",
                    room_changed=False
                )
            
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if vehicle is in current room or inventory
            vehicle_in_room = vehicle_id in current_room.items
            vehicle_in_inventory = vehicle_id in state.inventory
            
            if not vehicle_in_room and not vehicle_in_inventory:
                display_name = self._get_object_names(vehicle_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here.",
                    room_changed=False
                )
            
            # Get vehicle object
            vehicle = self.world.get_object(vehicle_id)
            
            # Check if object is actually a vehicle
            is_vehicle = vehicle.state.get('is_vehicle', False)
            
            if not is_vehicle:
                display_name = self._get_object_names(vehicle_id)
                return ActionResult(
                    success=False,
                    message=f"You can't board the {display_name}.",
                    room_changed=False
                )
            
            # Check if vehicle requires specific conditions
            requires_water = vehicle.state.get('requires_water', False)
            if requires_water:
                # Check if current room has water
                room_has_water = current_room.state.get('has_water', False)
                if not room_has_water:
                    display_name = self._get_object_names(vehicle_id)
                    return ActionResult(
                        success=False,
                        message=f"The {display_name} can't be used here. It needs water.",
                        room_changed=False
                    )
            
            # Board the vehicle
            state.current_vehicle = vehicle_id
            
            # Create success message with haunted theme
            display_name = self._get_object_names(vehicle_id)
            board_message = f"You climb into the {display_name}, settling into its cold, unwelcoming interior."
            
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
            display_name = self._get_object_names(vehicle_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here.",
                room_changed=False
            )
        except Exception as e:
            # Unexpected error
            return ActionResult(
                success=False,
                message="An unseen force prevents you from boarding the cursed vessel.",
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
                vehicle_name = self._get_object_names(vehicle_id)
                current_vehicle_name = self._get_object_names(state.current_vehicle)
                return ActionResult(
                    success=False,
                    message=f"You're not in the {vehicle_name}. You're in the {current_vehicle_name}.",
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
                message="The cursed vessel seems reluctant to release you from its cold embrace.",
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
                        display_name = self._get_object_names(object_id)
                        return ActionResult(
                            success=False,
                            message=f"You don't see any {display_name} here.",
                            room_changed=False
                        )
                    except ValueError:
                        # Object doesn't exist at all
                        display_name = self._get_object_names(object_id)
                        return ActionResult(
                            success=False,
                            message=f"You don't see any {display_name} here.",
                            room_changed=False
                        )
                
                # Get object and check if it's climbable
                game_object = self.world.get_object(object_id)
                is_climbable = game_object.state.get('is_climbable', False)
                
                if not is_climbable:
                    display_name = self._get_object_names(object_id)
                    return ActionResult(
                        success=False,
                        message=f"You can't climb the {display_name}.",
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
                message="The ancient structure groans and shifts, denying your ascent into the gloom.",
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
                message="The spectral forces of this place resist your efforts. Perhaps try another approach.",
                room_changed=False
            )

    def handle_back(
        self,
        state: GameState
    ) -> ActionResult:
        """
        Handle BACK command - go back to the previous room.

        Maintains a history of visited rooms and returns to the most recent one.

        Args:
            state: Current game state

        Returns:
            ActionResult with success status and movement information

        Requirements: Follows standard Zork I BACK command behavior
        """
        if not state.visit_history or len(state.visit_history) < 2:
            return ActionResult(
                success=False,
                message="You can't go back. The spirits have already obscured your path here.",
                room_changed=False
            )

        # Get the previous room (second to last in history)
        previous_room_id = state.visit_history[-2]

        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if there's a connection back
            if previous_room_id not in current_room.exits.values():
                return ActionResult(
                    success=False,
                    message="The way back has vanished into the mist.",
                    room_changed=False
                )

            # Find which direction leads back
            back_direction = None
            for direction, target_room in current_room.exits.items():
                if target_room == previous_room_id:
                    back_direction = direction
                    break

            if not back_direction:
                return ActionResult(
                    success=False,
                    message="An unseen force prevents you from returning that way.",
                    room_changed=False
                )

            # Move back to previous room
            state.move_to_room(previous_room_id)

            # Get room description based on lighting and sanity
            target_room = self.world.get_room(previous_room_id)
            is_lit = self.is_room_lit(previous_room_id, state)

            if not is_lit:
                description = self.get_darkness_description(previous_room_id)
            else:
                description = self.world.get_room_description(previous_room_id, state.sanity)

            # Apply room effects
            sanity_change = 0
            notifications = []

            if target_room.sanity_effect != 0:
                sanity_change = target_room.sanity_effect
                state.sanity = max(0, min(100, state.sanity + sanity_change))

                if sanity_change < 0:
                    notifications.append("Returning brings a fresh wave of unease...")
                elif sanity_change > 0:
                    notifications.append("The familiar surroundings offer small comfort.")

            state.increment_turn()

            return ActionResult(
                success=True,
                message=f"You retrace your steps, moving {back_direction.lower()}.\n\n{description}",
                room_changed=True,
                new_room=previous_room_id,
                state_changes={
                    'current_room': previous_room_id,
                    'moves': state.moves,
                    'turn_count': state.turn_count,
                    'sanity': state.sanity
                },
                notifications=notifications,
                sanity_change=sanity_change
            )

        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"An error occurred: {str(e)}",
                room_changed=False
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The shadows twist and turn, preventing your retreat.",
                room_changed=False
            )

    def handle_stand(
        self,
        object_id: Optional[str],
        state: GameState
    ) -> ActionResult:
        """
        Handle STAND command - stand up from sitting/lying position.

        Args:
            object_id: Optional object to stand on/against
            state: Current game state

        Returns:
            ActionResult with success status

        Requirements: Follows standard Zork I STAND command behavior
        """
        # Check if player is currently sitting/lying
        if not state.get_flag('is_sitting') and not state.get_flag('is_lying'):
            return ActionResult(
                success=False,
                message="You are already standing, surrounded by the eerie silence.",
                room_changed=False
            )

        # Set player state to standing
        state.set_flag('is_sitting', False)
        state.set_flag('is_lying', False)

        state.increment_turn()

        message = "You rise to your feet, brushing imaginary dust from your clothes."

        # Add context based on object
        if object_id:
            try:
                obj = self.world.get_object(object_id)
                message = f"You rise from the {obj.name.lower()}, your joints protesting the movement."
            except ValueError:
                display_name = self._get_object_names(object_id)
                message = f"You stand up from beside the {display_name}."

        # Add sanity flavor for low sanity
        if state.sanity < 30:
            message += " The effort leaves you feeling drained and vulnerable."

        return ActionResult(
            success=True,
            message=message,
            room_changed=False,
            state_changes={
                'is_sitting': False,
                'is_lying': False,
                'turn_count': state.turn_count
            }
        )

    def handle_follow(
        self,
        object_id: Optional[str],
        state: GameState
    ) -> ActionResult:
        """
        Handle FOLLOW command - follow a creature or character.

        Args:
            object_id: The creature/character to follow
            state: Current game state

        Returns:
            ActionResult with success status

        Requirements: Follows standard Zork I FOLLOW command behavior
        """
        if not object_id:
            return ActionResult(
                success=False,
                message="Who do you wish to follow through these shadowed halls?",
                room_changed=False
            )

        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if target exists
            try:
                target = self.world.get_object(object_id)
            except ValueError:
                return self._handle_missing_object(object_id, state, "FOLLOW")

            # Check if target is in current room
            if object_id not in current_room.items:
                return ActionResult(
                    success=False,
                    message=f"The {target.name.lower()} is not here to follow.",
                    room_changed=False
                )

            # Check if target is mobile/followable
            if not target.type in ["creature", "person", "npc"]:
                return ActionResult(
                    success=False,
                    message=f"The {target.name.lower()} cannot be followed - it seems to be rooted in place.",
                    room_changed=False
                )

            # Check if target moves (simplified - just check if there's an exit where target was)
            if not target.state.get('can_move', False):
                return ActionResult(
                    success=False,
                    message=f"The {target.name.lower()} doesn't seem to be going anywhere right now.",
                    room_changed=False
                )

            # For now, simulate following by checking all exits for where the creature might go
            possible_directions = list(current_room.exits.keys())

            if not possible_directions:
                return ActionResult(
                    success=False,
                    message="There are no obvious paths to follow.",
                    room_changed=False
                )

            # Pick a random direction (in a real game, creatures would have predefined paths)
            import random
            follow_direction = random.choice(possible_directions)

            # Move in that direction
            return self.handle_movement(follow_direction, state)

        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"An error occurred: {str(e)}",
                room_changed=False
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The shadows swirl and dance, confusing your sense of direction.",
                room_changed=False
            )

    def handle_swim(
        self,
        state: GameState
    ) -> ActionResult:
        """
        Handle SWIM command - attempt to swim.

        Args:
            state: Current game state

        Returns:
            ActionResult with success status

        Requirements: Follows standard Zork I SWIM command behavior
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if room has water (by name or id)
            room_name_lower = current_room.name.lower()
            room_id_lower = current_room.id.lower()
            has_water = any(word in room_name_lower or word in room_id_lower 
                          for word in ['water', 'river', 'stream', 'lake', 'pool', 'reservoir'])

            if not has_water:
                return ActionResult(
                    success=False,
                    message="There's no water here to swim in. Only shadows and dust.",
                    room_changed=False
                )

            # For now, swimming is just for flavor
            state.increment_turn()

            messages = [
                "You swim through the cold, dark water, feeling unseen things brush against you.",
                "The water is shockingly cold, but you swim with determination.",
                "Swimming in these haunted waters fills you with dread."
            ]

            import random
            message = random.choice(messages)

            return ActionResult(
                success=True,
                message=message,
                room_changed=False,
                state_changes={
                    'turn_count': state.turn_count
                }
            )

        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"An error occurred: {str(e)}",
                room_changed=False
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The water churns and whispers, refusing your entry.",
                room_changed=False
            )

    def handle_wait(
        self,
        state: GameState
    ) -> ActionResult:
        """
        Handle WAIT command - wait and observe surroundings.

        Players can wait to observe events that happen over time or to
        time passes in the haunted house. Some events may only occur when waiting.

        Args:
            state: Current game state

        Returns:
            ActionResult with success status and observational message

        Requirements: Follows standard Zork I WAIT command behavior
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Increment turn counter
            state.increment_turn()

            # Check for timed events in the current room
            notifications = []
            room_events = current_room.state.get('timed_events', [])

            # Generate waiting messages
            wait_messages = [
                "Time passes slowly in the oppressive gloom.",
                "You stand perfectly still, listening to the distant echoes of this haunted place.",
                "The shadows seem to shift and dance at the edge of your vision.",
                "A cold draft whispers through the corridors as you wait.",
                "You wait, feeling the weight of ages pressing down on you.",
                "The silence stretches, thick with unspoken dread.",
                "You observe the room carefully, but nothing seems to change.",
                "Your patience is rewarded with subtle movements in the darkness."
            ]

            # Add low sanity flavor
            if state.sanity < 30:
                wait_messages.append(" The waiting makes your mind wander to dark places...")
            elif state.sanity > 80:
                wait_messages.append(" You feel calm enough to notice details others might miss.")

            # Check for room-specific timed events
            if room_events:
                event_message = room_events[state.turn_count % len(room_events)]
                if event_message:
                    wait_messages.insert(0, event_message)
                else:
                    wait_messages[-1] = event_message

            import random
            message = random.choice(wait_messages)

            # Check for any objects that might change while waiting
            if current_room.items:
                interactive_objects = [
                    item for item in current_room.items
                    if self.world.get_object(item).state.get('changes_while_waiting', False)
                ]

                if interactive_objects:
                    obj_names = [self._get_object_names(item) for item in interactive_objects[:3]]
                    message += f"\n\nThe {', '.join(obj_names)} seems to shift slightly in the gloom."

            return ActionResult(
                success=True,
                message=message,
                room_changed=False,
                state_changes={
                    'turn_count': state.turn_count
                },
                notifications=notifications
            )

        except ValueError as e:
            return ActionResult(
                success=False,
                message="The very act of waiting feels somehow wrong in this place.",
                room_changed=False
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The shadows resist your stillness, urging you to keep moving.",
                room_changed=False
            )

    def handle_take(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle taking an object from the current room or open containers.
        
        Validates that object is takeable, adds to inventory, removes from room/container.
        
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
            # Check if object is in current room or global items
            if object_id not in current_room.items and object_id not in current_room.global_items:
                # Check if already in inventory
                if object_id in state.inventory:
                    return ActionResult(
                        success=False,
                        message="The cursed object already weighs heavy in your possession."
                    )
                
                # Check if object is in an open container in the room or inventory
                found_in_container = None
                for item_id in list(current_room.items) + list(state.inventory) + list(current_room.global_items):
                    try:
                        item = self.world.get_object(item_id)
                        if item.type == "container":
                            # Check GameState first, then fall back to World data
                            is_open = state.get_object_state(item_id, 'is_open', item.state.get('is_open', False))
                            is_transparent = state.get_object_state(item_id, 'is_transparent', item.state.get('is_transparent', False))
                            
                            if is_open or is_transparent:
                                contents = state.get_object_state(item_id, 'contents', item.state.get('contents', []))
                                if object_id in contents:
                                    found_in_container = item_id
                                    break
                    except:
                        continue
                
                if found_in_container:
                    # Delegate to handle_take_from_container
                    return self.handle_take_from_container(object_id, found_in_container, state)
                
                # Try to get object name for better error message
                try:
                    obj = self.world.get_object(object_id)
                    display_name = obj.name
                except ValueError:
                    display_name = object_id

                return ActionResult(
                    success=False,
                    message=f"The shadows reveal no {display_name} in this forsaken place."
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
                    message="The cursed object resists your grasp, as if bound to this place by dark forces."
                )
            
            # Find TAKE interaction for response message
            take_message = "You grasp the object with trembling hands, feeling its cold weight."
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
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"The shadows reveal no {display_name} in this forsaken place."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The cursed object slips through your trembling fingers like smoke."
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
                    message="Your trembling hands find no such cursed thing among your possessions."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Find DROP interaction for response message
            drop_message = "You release the object, watching it fall into the darkness below."
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
                message="Your trembling hands find no such cursed thing among your possessions."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The object seems to resist being released, clinging to your grasp with unnatural force."
            )

    def _manage_container_contents(
        self,
        container_id: str,
        is_opening: bool,
        state: GameState
    ) -> List[str]:
        """
        Handle container opening/closing without moving contents to room.
        Items stay in containers and must be taken from there.

        Args:
            container_id: The container object ID
            is_opening: True if opening, False if closing
            state: Current game state

        Returns:
            List of notifications about container state changes
        """
        notifications = []

        try:
            container = self.world.get_object(container_id)

            # Check if this is actually a container
            if container.type != "container":
                return notifications

            # No content movement - items stay in container
            # This is the correct text adventure behavior

        except ValueError:
            # Container doesn't exist
            pass
        except Exception as e:
            # Log error but don't crash
            pass

        return notifications

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
            
            # Check if object is in current room, inventory, or global items
            object_in_room = object_id in current_room.items
            object_in_global = object_id in current_room.global_items
            object_in_inventory = object_id in state.inventory
            
            if not object_in_room and not object_in_inventory and not object_in_global:
                # Try to get object name for better error message
                try:
                    obj = self.world.get_object(object_id)
                    display_name = obj.name
                except ValueError:
                    display_name = object_id

                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Check current state before attempting action
            # Check current state before attempting action
            if verb == "OPEN":
                is_open = state.get_object_state(object_id, 'is_open', game_object.state.get('is_open', False))
                if is_open:
                    display_name = self._get_object_names(object_id)
                    return ActionResult(
                        success=False,
                        message=f"The {display_name} is already open."
                    )
            elif verb == "CLOSE":
                is_open = state.get_object_state(object_id, 'is_open', game_object.state.get('is_open', False))
                if not is_open:
                    display_name = self._get_object_names(object_id)
                    return ActionResult(
                        success=False,
                        message=f"The {display_name} is already closed."
                    )
            elif verb == "LOCK":
                is_locked = state.get_object_state(object_id, 'is_locked', game_object.state.get('is_locked', False))
                if is_locked:
                    display_name = self._get_object_names(object_id)
                    return ActionResult(
                        success=False,
                        message=f"The {display_name} is already locked."
                    )
            elif verb == "UNLOCK":
                is_locked = state.get_object_state(object_id, 'is_locked', game_object.state.get('is_locked', False))
                if not is_locked:
                    display_name = self._get_object_names(object_id)
                    return ActionResult(
                        success=False,
                        message=f"The {display_name} is already unlocked."
                    )
            
            # Find matching interaction
            matching_interaction = None
            for interaction in game_object.interactions:
                if interaction.verb == verb:
                    # Check if interaction has conditions
                    if interaction.condition:
                        # Check if all conditions are met
                        conditions_met = True
                        for key, required_value in interaction.condition.items():
                            # Get current value from GameState, falling back to WorldData
                            current_value = state.get_object_state(object_id, key, game_object.state.get(key, None))
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
            
            # Apply state changes to GameState (not World object)
            if matching_interaction.state_change:
                for key, value in matching_interaction.state_change.items():
                    state.set_object_state(object_id, key, value)
            
            # Apply flag changes to game state
            if matching_interaction.flag_change:
                for flag_name, flag_value in matching_interaction.flag_change.items():
                    state.set_flag(flag_name, flag_value)

            # Handle puzzle-specific logic
            notifications = []

            # Handle container content management
            if verb in ["OPEN", "CLOSE"]:
                container_notifications = self._manage_container_contents(
                    object_id,
                    verb == "OPEN",
                    state
                )
                notifications.extend(container_notifications)
            
            # Puzzle 1: Moving rug reveals trap door
            if object_id == "rug" and verb == "MOVE":
                is_moved = state.get_object_state("rug", "is_moved", False)
                if is_moved:
                    # Rug has been moved, make trap door visible
                    state.set_flag("rug_moved", True)
                    state.set_object_state("trap_door", "is_visible", True)
                    notifications.append("The trap door is now visible!")
            
            # Puzzle 2: Opening kitchen window allows entry
            if object_id == "kitchen_window" and verb == "OPEN":
                is_open = state.get_object_state("kitchen_window", "is_open", False)
                if is_open:
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
                is_open = state.get_object_state("trap_door", "is_open", False)
                if is_open:
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
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The malevolent forces of this place thwart your attempt."
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
            
            # Check if object is accessible
            # Check if object is accessible
            if not self.is_object_accessible(object_id, state):
                # Try to get object name for better error message
                try:
                    obj = self.world.get_object(object_id)
                    display_name = obj.name
                except ValueError:
                    display_name = object_id
                    
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
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
            
            # Check if it's a container and list contents if open/transparent
            if game_object.type == "container":
                is_open = state.get_object_state(object_id, 'is_open', game_object.state.get('is_open', False))
                is_transparent = state.get_object_state(object_id, 'is_transparent', game_object.state.get('is_transparent', False))
                
                if is_open or is_transparent:
                    contents = state.get_object_state(object_id, 'contents', game_object.state.get('contents', []))
                    if contents:
                        content_names = []
                        for item_id in contents:
                            try:
                                item = self.world.get_object(item_id)
                                # Use spooky name if available
                                item_name = item.name_spooky if item.name_spooky else item.name
                                content_names.append(item_name)
                            except ValueError:
                                continue
                        
                        if content_names:
                            if is_open:
                                description += f" Inside, you see: {', '.join(content_names)}."
                            else:
                                description += f" Through the surface, you see: {', '.join(content_names)}."
                    elif is_open:
                        description += " It is empty."

            return ActionResult(
                success=True,
                message=description,
                state_changes={'sanity': state.sanity} if sanity_change != 0 else {},
                notifications=notifications,
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"The shadows reveal no {display_name} in this forsaken place."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The shadows obscure your vision, hiding the object's true nature."
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
                # Try to get object name for better error message
                display_name = self._get_object_names(container_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
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
            is_transparent = state.get_object_state(container_id, 'is_transparent', container.state.get('is_transparent', False))
            is_open = state.get_object_state(container_id, 'is_open', container.state.get('is_open', False))
            
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
                contents = state.get_object_state(container_id, 'contents', container.state.get('contents', []))
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
            contents = state.get_object_state(container_id, 'contents', container.state.get('contents', []))
            # Create a copy to avoid modifying the default list if it came from WorldData
            contents = list(contents)
            contents.append(object_id)
            state.set_object_state(container_id, 'contents', contents)
            
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
            display_name = self._get_object_names(container_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The cursed container resists your attempt to place the object within its depths."
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
                display_name = self._get_object_names(container_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
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
            is_transparent = state.get_object_state(container_id, 'is_transparent', container.state.get('is_transparent', False))
            is_open = state.get_object_state(container_id, 'is_open', container.state.get('is_open', False))
            
            if not is_open and not is_transparent:
                return ActionResult(
                    success=False,
                    message="The container is closed."
                )
            
            # Check if object is in container
            contents = state.get_object_state(container_id, 'contents', container.state.get('contents', []))
            if object_id not in contents:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"There's no {display_name} in the {container.name}."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
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
            contents = state.get_object_state(container_id, 'contents', container.state.get('contents', []))
            # Create a copy to avoid modifying the default list if it came from WorldData
            contents = list(contents)
            if object_id in contents:
                contents.remove(object_id)
            state.set_object_state(container_id, 'contents', contents)
            
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
            is_transparent = state.get_object_state(container_id, 'is_transparent', container.state.get('is_transparent', False))
            is_open = state.get_object_state(container_id, 'is_open', container.state.get('is_open', False))
            
            # Build description with contents if visible
            if is_open or is_transparent:
                contents = state.get_object_state(container_id, 'contents', container.state.get('contents', []))
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
                message="The cursed lamp flickers and resists your command, as if possessed by malevolent spirits."
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
                message="The cursed lamp flickers and resists your command, as if possessed by malevolent spirits."
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
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )
            
            # Check if key is in inventory
            if key_id not in state.inventory:
                display_name = self._get_object_names(key_id)
                return ActionResult(
                    success=False,
                    message=f"You don't have the {display_name}."
                )
            
            # Get object and key data
            game_object = self.world.get_object(object_id)
            key_object = self.world.get_object(key_id)
            
            # Check if object is lockable
            is_lockable = game_object.state.get('is_lockable', False)
            
            if not is_lockable:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"The {display_name} cannot be locked."
                )
            
            # Check if object is already locked
            is_locked = game_object.state.get('is_locked', False)
            
            if is_locked:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"The {display_name} is already locked."
                )
            
            # Check if key matches the lock
            required_key = game_object.state.get('required_key', None)
            
            if required_key and required_key != key_id:
                key_name = self._get_object_names(key_id)
                return ActionResult(
                    success=False,
                    message=f"The {key_name} doesn't fit the lock."
                )
            
            # Lock the object
            game_object.state['is_locked'] = True
            
            # Create success message with haunted theme
            key_display_name = self._get_object_names(key_id)
            lock_message = f"You lock the {game_object.name} with the {key_display_name}. A cold click echoes in the darkness."
            
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
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The ancient lock resists your efforts, as if cursed to remain forever sealed."
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
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )
            
            # Check if key is in inventory
            if key_id not in state.inventory:
                display_name = self._get_object_names(key_id)
                return ActionResult(
                    success=False,
                    message=f"You don't have the {display_name}."
                )
            
            # Get object and key data
            game_object = self.world.get_object(object_id)
            key_object = self.world.get_object(key_id)
            
            # Check if object is lockable
            is_lockable = game_object.state.get('is_lockable', False)
            
            if not is_lockable:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"The {display_name} cannot be unlocked."
                )
            
            # Check if object is already unlocked
            is_locked = game_object.state.get('is_locked', False)
            
            if not is_locked:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"The {display_name} is already unlocked."
                )
            
            # Check if key matches the lock
            required_key = game_object.state.get('required_key', None)
            
            if required_key and required_key != key_id:
                key_name = self._get_object_names(key_id)
                return ActionResult(
                    success=False,
                    message=f"The {key_name} doesn't fit the lock."
                )
            
            # Unlock the object
            game_object.state['is_locked'] = False
            
            # Create success message with haunted theme
            unlock_message = f"You unlock the {game_object.name} with the {key_object.name}. The mechanism groans as it releases."
            
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
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The cursed lock refuses to yield, its mechanism twisted by dark enchantments."
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
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Check if object is turnable
            is_turnable = game_object.state.get('is_turnable', False)
            
            if not is_turnable:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You can't turn the {display_name}."
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
                    notifications.append(f"The {game_object.name} clicks into place!")
                else:
                    game_object.state['is_activated'] = False
            
            # Apply any flag changes based on activation
            if game_object.state.get('is_activated', False):
                activation_flag = game_object.state.get('activation_flag', None)
                if activation_flag:
                    state.set_flag(activation_flag, True)
            
            # Create success message with haunted theme
            turn_message = f"You turn the {game_object.name}. It rotates with an eerie creak."
            
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
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The object resists your attempt to turn it, held fast by spectral forces."
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
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Check if object is moveable
            is_moveable = game_object.state.get('is_moveable', False)
            
            if not is_moveable:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"The {display_name} won't budge."
                )
            
            # Check if already pushed
            is_pushed = game_object.state.get('is_pushed', False)
            
            if is_pushed:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"The {display_name} has already been pushed as far as it will go."
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
                            notifications.append(f"Pushing the {game_object.name} reveals {revealed_obj.name_spooky}!")
                        except ValueError:
                            notifications.append(f"Pushing the {game_object.name} reveals something hidden!")
            
            # Apply any flag changes
            push_flag = game_object.state.get('push_flag', None)
            if push_flag:
                state.set_flag(push_flag, True)
            
            # Create success message with haunted theme
            push_message = f"You push the {game_object.name}. It slides across the floor with a grinding sound."
            
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
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The object refuses to budge, as if rooted in place by unseen hands."
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
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )
            
            # Get object data
            game_object = self.world.get_object(object_id)
            
            # Check if object is moveable
            is_moveable = game_object.state.get('is_moveable', False)
            
            if not is_moveable:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"The {display_name} won't budge."
                )
            
            # Check if already pulled
            is_pulled = game_object.state.get('is_pulled', False)
            
            if is_pulled:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"The {display_name} has already been pulled as far as it will go."
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
                            notifications.append(f"Pulling the {game_object.name} reveals {revealed_obj.name_spooky}!")
                        except ValueError:
                            notifications.append(f"Pulling the {game_object.name} reveals something hidden!")
            
            # Apply any flag changes
            pull_flag = game_object.state.get('pull_flag', None)
            if pull_flag:
                state.set_flag(pull_flag, True)
            
            # Create success message with haunted theme
            pull_message = f"You pull the {game_object.name}. It drags toward you with a scraping sound."
            
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
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The object resists your pull, held fast by malevolent forces."
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
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't have the {display_name}."
                )
            
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if target is in current room or inventory
            target_in_room = target_id in current_room.items
            target_in_inventory = target_id in state.inventory
            
            if not target_in_room and not target_in_inventory:
                target_name = self._get_object_names(target_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {target_name} here."
                )
            
            # Get rope and target objects
            rope_object = self.world.get_object(object_id)
            target_object = self.world.get_object(target_id)
            
            # Check if object is rope-like
            is_rope = rope_object.state.get('is_rope', False)
            can_tie = rope_object.state.get('can_tie', False)
            

            
            # Check if rope is already tied
            is_tied = rope_object.state.get('is_tied', False)
            
            if not is_rope or not can_tie:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You can't tie the {display_name}."
                )
            

            
            # Check if rope is already tied
            is_tied = rope_object.state.get('is_tied', False)
            
            if is_tied:
                tied_to = rope_object.state.get('tied_to', 'something')
                display_name = self._get_object_names(object_id)
                # Try to resolve tied_to name if it's an ID
                tied_to_name = self._get_object_names(tied_to) if self.world.objects.get(tied_to) else tied_to
                return ActionResult(
                    success=False,
                    message=f"The {display_name} is already tied to {tied_to_name}."
                )
            
            # Check if target is valid for tying
            tie_targets = rope_object.state.get('tie_targets', [])
            
            if tie_targets and target_id not in tie_targets:
                display_name = self._get_object_names(object_id)
                target_name = self._get_object_names(target_id)
                return ActionResult(
                    success=False,
                    message=f"You can't tie the {display_name} to the {target_name}."
                )
            
            # Check if target can be tied to
            can_be_tied_to = target_object.state.get('can_be_tied_to', True)
            
            if not can_be_tied_to:
                target_name = self._get_object_names(target_id)
                return ActionResult(
                    success=False,
                    message=f"You can't tie anything to the {target_name}."
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
            display_name = self._get_object_names(object_id)
            target_name = self._get_object_names(target_id)
            tie_message = f"You tie the {display_name} to the {target_name}. The knot holds fast, though your fingers tremble."
            
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
            target_name = self._get_object_names(target_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {target_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The rope slips through your fingers like a serpent, refusing to be bound."
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
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )
            
            # Get rope object
            rope_object = self.world.get_object(object_id)
            
            # Check if object is rope-like
            is_rope = rope_object.state.get('is_rope', False)
            
            if not is_rope:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You can't untie the {display_name}."
                )
            
            # Check if rope is tied
            is_tied = rope_object.state.get('is_tied', False)
            
            if not is_tied:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"The {display_name} is not tied to anything."
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
            display_name = self._get_object_names(object_id)
            untie_message = f"You untie the {display_name}. The knot comes loose with an eerie whisper."
            
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
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The knot tightens impossibly, as if cursed to remain forever bound."
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
                container_name = self._get_object_names(container_id)
                return ActionResult(
                    success=False,
                    message=f"You don't have the {container_name}."
                )
            
            # Check if source is in current room or inventory
            source_in_room = source_id in current_room.items
            source_in_inventory = source_id in state.inventory
            
            if not source_in_room and not source_in_inventory:
                source_name = self._get_object_names(source_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {source_name} here."
                )
            
            # Get container and source objects
            container_object = self.world.get_object(container_id)
            source_object = self.world.get_object(source_id)
            
            # Check if container can hold liquids
            can_hold_liquid = container_object.state.get('can_hold_liquid', False)
            
            if not can_hold_liquid:
                container_name = self._get_object_names(container_id)
                return ActionResult(
                    success=False,
                    message=f"You can't fill the {container_name} with liquid."
                )
            
            # Check if source has liquid
            has_liquid = source_object.state.get('has_liquid', False)
            is_liquid_source = source_object.state.get('is_liquid_source', False)
            
            if not has_liquid and not is_liquid_source:
                source_name = self._get_object_names(source_id)
                return ActionResult(
                    success=False,
                    message=f"The {source_name} has no liquid to fill from."
                )
            
            # Check if container is already full
            is_full = container_object.state.get('is_full', False)
            liquid_level = container_object.state.get('liquid_level', 0)
            max_capacity = container_object.state.get('liquid_capacity', 100)
            
            if is_full or liquid_level >= max_capacity:
                container_name = self._get_object_names(container_id)
                return ActionResult(
                    success=False,
                    message=f"The {container_name} is already full."
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
            container_name = self._get_object_names(container_id)
            source_name = self._get_object_names(source_id)
            fill_message = f"You fill the {container_name} with {liquid_type} from the {source_name}. The liquid swirls with an unnatural darkness."
            
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
                message="The liquid refuses to flow, as if repelled by dark enchantments."
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
                container_name = self._get_object_names(container_id)
                return ActionResult(
                    success=False,
                    message=f"You don't have the {container_name}."
                )
            
            # Get container object
            container_object = self.world.get_object(container_id)
            
            # Check if container can hold liquids
            can_hold_liquid = container_object.state.get('can_hold_liquid', False)
            
            if not can_hold_liquid:
                container_name = self._get_object_names(container_id)
                return ActionResult(
                    success=False,
                    message=f"The {container_name} doesn't contain any liquid."
                )
            
            # Check if container has liquid
            is_empty = container_object.state.get('is_empty', True)
            liquid_level = container_object.state.get('liquid_level', 0)
            
            if is_empty or liquid_level <= 0:
                container_name = self._get_object_names(container_id)
                return ActionResult(
                    success=False,
                    message=f"The {container_name} is empty."
                )
            
            # Get liquid type
            liquid_type = container_object.state.get('liquid_type', 'liquid')
            
            # Handle pouring into another container
            if target_id:
                # Check if target is in current room or inventory
                target_in_room = target_id in current_room.items
                target_in_inventory = target_id in state.inventory
                
                if not target_in_room and not target_in_inventory:
                    target_name = self._get_object_names(target_id)
                    return ActionResult(
                        success=False,
                        message=f"You don't see any {target_name} here."
                    )
                
                # Get target object
                target_object = self.world.get_object(target_id)
                
                # Check if target can hold liquids
                target_can_hold_liquid = target_object.state.get('can_hold_liquid', False)
                
                if not target_can_hold_liquid:
                    # Pouring onto an object that can't hold liquid
                    target_name = self._get_object_names(target_id)
                    pour_message = f"You pour the {liquid_type} onto the {target_name}. It spills away into the shadows."
                else:
                    # Check if target is full
                    target_is_full = target_object.state.get('is_full', False)
                    target_liquid_level = target_object.state.get('liquid_level', 0)
                    target_max_capacity = target_object.state.get('liquid_capacity', 100)
                    
                    if target_is_full or target_liquid_level >= target_max_capacity:
                        target_name = self._get_object_names(target_id)
                        return ActionResult(
                            success=False,
                            message=f"The {target_name} is already full."
                        )
                    
                    # Pour into target container
                    target_object.state['is_full'] = True
                    target_object.state['liquid_level'] = target_max_capacity
                    target_object.state['liquid_type'] = liquid_type
                    target_object.state['is_empty'] = False
                    
                    container_name = self._get_object_names(container_id)
                    target_name = self._get_object_names(target_id)
                    pour_message = f"You pour the {liquid_type} from the {container_name} into the {target_name}."
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
            missing_id = target_id if target_id else container_id
            display_name = self._get_object_names(missing_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The liquid clings to the container, refusing to pour as if alive."
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
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
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
                
                display_name = self._get_object_names(object_id)
                message = f"You look under the {display_name}."
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
            display_name = self._get_object_names(object_id)
            default_messages = [
                f"You peer beneath the {display_name}. Nothing but shadows and dust.",
                f"There's nothing under the {display_name} but darkness.",
                f"You find nothing of interest beneath the {display_name}.",
                f"The space under the {display_name} is empty, save for cobwebs."
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
                message="The shadows beneath writhe and twist, obscuring your view."
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
                display_name = self._get_object_names(container_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )
            
            # Get container object
            container = self.world.get_object(container_id)
            
            # Check if object is actually a container
            if container.type != "container":
                container_name = self._get_object_names(container_id)
                return ActionResult(
                    success=False,
                    message=f"You can't look inside the {container_name}."
                )
            
            # Check if container is open or transparent
            is_transparent = container.state.get('is_transparent', False)
            is_open = container.state.get('is_open', False)
            
            if not is_open and not is_transparent:
                container_name = self._get_object_names(container_id)
                return ActionResult(
                    success=False,
                    message=f"The {container_name} is closed. You can't see inside."
                )
            
            # Get contents
            contents = container.state.get('contents', [])
            
            if not contents:
                container_name = self._get_object_names(container_id)
                return ActionResult(
                    success=True,
                    message=f"The {container_name} is empty. Nothing but shadows within."
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
                container_name = self._get_object_names(container_id)
                return ActionResult(
                    success=True,
                    message=f"The {container_name} appears empty."
                )
            
            # Format contents list
            if len(contents_names) == 1:
                contents_str = contents_names[0]
            elif len(contents_names) == 2:
                contents_str = f"{contents_names[0]} and {contents_names[1]}"
            else:
                contents_str = ", ".join(contents_names[:-1]) + f", and {contents_names[-1]}"
            
            container_name = self._get_object_names(container_id)
            message = f"Inside the {container_name}, you see: {contents_str}."
            
            return ActionResult(
                success=True,
                message=message
            )
            
        except ValueError as e:
            container_name = self._get_object_names(container_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {container_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The interior is shrouded in unnatural darkness that defies your gaze."
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
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
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
                
                display_name = self._get_object_names(object_id)
                message = f"You look behind the {display_name}."
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
            display_name = self._get_object_names(object_id)
            default_messages = [
                f"You peer behind the {display_name}. Nothing but empty space.",
                f"There's nothing behind the {display_name} but cold air.",
                f"You find nothing of interest behind the {display_name}.",
                f"The space behind the {display_name} is empty and foreboding."
            ]
            
            # Use a consistent message based on object_id hash for consistency
            message_idx = hash(object_id) % len(default_messages)
            
            return ActionResult(
                success=True,
                message=default_messages[message_idx],
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The shadows behind the object seem to shift and hide from your sight."
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
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
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
                
                display_name = self._get_object_names(object_id)
                message = f"You search the {display_name} thoroughly."
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
            display_name = self._get_object_names(object_id)
            default_messages = [
                f"You search the {display_name} carefully but find nothing of interest.",
                f"Your thorough search of the {display_name} reveals nothing unusual.",
                f"Despite your careful examination, the {display_name} yields no secrets.",
                f"You find nothing hidden in or on the {display_name}.",
                f"The {display_name} holds no hidden surprises, only shadows and dust."
            ]
            
            # Use a consistent message based on object_id hash for consistency
            message_idx = hash(object_id) % len(default_messages)
            
            return ActionResult(
                success=True,
                message=default_messages[message_idx],
                sanity_change=sanity_change
            )
            
        except ValueError as e:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The darkness seems to swallow your search, revealing nothing."
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
            object_id: The object to read (can be ID, name, or spooky name)
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 4.5
        """
        try:
            # Resolve flexible object name
            resolved_id = self.resolve_object_name(object_id, state)
            if not resolved_id:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )
            
            # Get object data
            game_object = self.world.get_object(resolved_id)
            
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
                display_name = game_object.name_spooky if game_object.name_spooky else game_object.name
                return ActionResult(
                    success=False,
                    message=f"There's nothing to read on the {display_name}."
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
            # Try to resolve name if possible, otherwise use ID
            try:
                display_name = self._get_object_names(object_id)
            except:
                display_name = object_id
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The text blurs and shifts before your eyes, as if cursed to remain unreadable."
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
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
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
            display_name = self._get_object_names(object_id)
            default_messages = [
                f"You listen carefully to the {display_name}, but hear nothing unusual.",
                f"The {display_name} is silent, revealing no audible secrets.",
                f"You press your ear close to the {display_name}, but it makes no sound.",
                f"The {display_name} offers no sounds, only an eerie silence.",
                f"Listening to the {display_name} yields nothing but the ambient sounds of this place."
            ]
            
            # Use a consistent message based on object_id hash for consistency
            message_idx = hash(object_id) % len(default_messages)
            
            return ActionResult(
                success=True,
                message=default_messages[message_idx]
            )
            
        except ValueError as e:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="An unnatural silence falls, as if the very air refuses to carry sound."
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
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
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
            display_name = self._get_object_names(object_id)
            default_messages = [
                f"You smell the {display_name}, but detect nothing unusual.",
                f"The {display_name} has no particular scent.",
                f"You sniff the {display_name}, but it smells unremarkable.",
                f"The {display_name} offers no distinctive odor.",
                f"Smelling the {display_name} reveals nothing but the ambient scents of this place."
            ]
            
            # Use a consistent message based on object_id hash for consistency
            message_idx = hash(object_id) % len(default_messages)
            
            return ActionResult(
                success=True,
                message=default_messages[message_idx]
            )
            
        except ValueError as e:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Your senses are overwhelmed by a nauseating miasma that defies description."
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
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )
            
            # Get the object
            game_object = self.world.get_object(object_id)
            
            # Check if object is flammable
            if not game_object.state.get('is_flammable', False):
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"The {display_name} won't burn."
                )
            
            # If fire source specified, validate it
            if fire_source_id:
                # Check if fire source is in inventory or room
                if fire_source_id not in state.inventory and fire_source_id not in current_room.items:
                    fire_source_name = self._get_object_names(fire_source_id)
                    return ActionResult(
                        success=False,
                        message=f"You don't have any {fire_source_name}."
                    )
                
                # Get fire source object
                fire_source = self.world.get_object(fire_source_id)
                
                # Check if it's actually a fire source
                if not fire_source.state.get('is_fire_source', False):
                    fire_source_name = self._get_object_names(fire_source_id)
                    return ActionResult(
                        success=False,
                        message=f"You can't burn things with the {fire_source_name}."
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
            display_name = self._get_object_names(object_id)
            burn_message = f"The {display_name} catches fire and burns to ashes, leaving nothing but a faint smell of smoke and decay."
            
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
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The flames sputter and die, as if the object is protected by dark magic."
            )
    
    def handle_cut(
        self,
        object_id: str,
        tool_id: Optional[str],
        state: GameState
    ) -> ActionResult:
        """
        Handle cutting an object with a cutting tool.
        
        Args:
            object_id: The object to cut
            tool_id: The cutting tool (sword, knife, etc.) - optional
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 6.2
        """
        try:
            current_room = self.world.get_room(state.current_room)
            
            if object_id not in current_room.items and object_id not in state.inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )
            
            game_object = self.world.get_object(object_id)
            
            if not game_object.state.get('is_cuttable', False):
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You can't cut the {display_name}."
                )
            
            if tool_id:
                if tool_id not in state.inventory and tool_id not in current_room.items:
                    tool_name = self._get_object_names(tool_id)
                    return ActionResult(
                        success=False,
                        message=f"You don't have any {tool_name}."
                    )
                
                tool = self.world.get_object(tool_id)
                
                if not tool.state.get('is_cutting_tool', False):
                    tool_name = self._get_object_names(tool_id)
                    return ActionResult(
                        success=False,
                        message=f"You can't cut things with the {tool_name}."
                    )
            
            notifications = []
            display_name = self._get_object_names(object_id)
            cut_message = f"You cut the {display_name}."
            
            for interaction in game_object.interactions:
                if interaction.verb == "CUT":
                    cut_message = interaction.response_spooky
                    
                    if interaction.state_change:
                        for key, value in interaction.state_change.items():
                            game_object.state[key] = value
                    
                    if interaction.flag_change:
                        for flag_name, flag_value in interaction.flag_change.items():
                            state.set_flag(flag_name, flag_value)
                    
                    if interaction.sanity_effect != 0:
                        state.sanity = max(0, min(100, state.sanity + interaction.sanity_effect))
                        if interaction.sanity_effect < 0:
                            notifications.append("The act of cutting disturbs you...")
                    
                    break
            
            game_object.state['is_cut'] = True
            
            return ActionResult(
                success=True,
                message=cut_message,
                state_changes={'sanity': state.sanity} if notifications else {},
                notifications=notifications
            )
            
        except ValueError:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception:
            return ActionResult(
                success=False,
                message="Your blade passes through the object as if cutting through smoke."
            )
    
    def handle_dig(
        self,
        location_id: Optional[str],
        tool_id: Optional[str],
        state: GameState
    ) -> ActionResult:
        """
        Handle digging at a location with a digging tool.
        
        Args:
            location_id: The location/object to dig (optional, defaults to current room)
            tool_id: The digging tool (shovel, etc.) - optional
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 6.3
        """
        try:
            current_room = self.world.get_room(state.current_room)
            
            # If no location specified, dig in current room
            if not location_id:
                # Check if room is diggable via flag
                if not state.get_flag(f"room_{state.current_room}_diggable", False):
                    return ActionResult(
                        success=False,
                        message="The ground here is too hard to dig."
                    )
                
                if tool_id:
                    if tool_id not in state.inventory:
                        return ActionResult(
                            success=False,
                            message=f"You don't have any {tool_id}."
                        )
                    
                    tool = self.world.get_object(tool_id)
                    if not tool.state.get('is_digging_tool', False):
                        return ActionResult(
                            success=False,
                            message=f"You can't dig with the {tool_id}."
                        )
                
                # Check if already dug
                if state.get_flag(f"dug_{state.current_room}", False):
                    return ActionResult(
                        success=False,
                        message="You've already dug here."
                    )
                
                # Mark as dug
                state.set_flag(f"dug_{state.current_room}", True)
                
                return ActionResult(
                    success=True,
                    message="You dig into the ground but find nothing."
                )
            
            # Digging at specific object
            if location_id not in current_room.items:
                display_name = self._get_object_names(location_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )
            
            game_object = self.world.get_object(location_id)
            
            if not game_object.state.get('is_diggable', False):
                display_name = self._get_object_names(location_id)
                return ActionResult(
                    success=False,
                    message=f"You can't dig at the {display_name}."
                )
            
            if tool_id:
                if tool_id not in state.inventory:
                    tool_name = self._get_object_names(tool_id)
                    return ActionResult(
                        success=False,
                        message=f"You don't have any {tool_name}."
                    )
                
                tool = self.world.get_object(tool_id)
                if not tool.state.get('is_digging_tool', False):
                    tool_name = self._get_object_names(tool_id)
                    return ActionResult(
                        success=False,
                        message=f"You can't dig with the {tool_name}."
                    )
            
            notifications = []
            display_name = self._get_object_names(location_id)
            dig_message = f"You dig at the {display_name}."
            
            for interaction in game_object.interactions:
                if interaction.verb == "DIG":
                    dig_message = interaction.response_spooky
                    
                    if interaction.state_change:
                        for key, value in interaction.state_change.items():
                            game_object.state[key] = value
                    
                    if interaction.flag_change:
                        for flag_name, flag_value in interaction.flag_change.items():
                            state.set_flag(flag_name, flag_value)
                    
                    if interaction.sanity_effect != 0:
                        state.sanity = max(0, min(100, state.sanity + interaction.sanity_effect))
                    
                    break
            
            game_object.state['is_dug'] = True
            
            return ActionResult(
                success=True,
                message=dig_message,
                state_changes={'sanity': state.sanity} if notifications else {},
                notifications=notifications
            )
            
        except ValueError:
            return ActionResult(
                success=False,
                message="You can't dig there."
            )
        except Exception:
            return ActionResult(
                success=False,
                message="The ground resists your efforts, as if the earth itself rejects your intrusion."
            )

    def handle_destroy(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle DESTROY command - attempt to destroy an object.

        Validates that the object is destructible and handles different
        types of destruction with appropriate messages.

        Args:
            object_id: The object to destroy
            state: Current game state

        Returns:
            ActionResult with success status and thematic message

        Requirements: Follows standard Zork I DESTROY command behavior
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if object exists
            try:
                game_object = self.world.get_object(object_id)
            except ValueError:
                return self._handle_missing_object(object_id, state, "DESTROY")

            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory

            if not object_in_room and not object_in_inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"There is no {display_name} here for you to destroy.",
                    room_changed=False
                )

            # Check if object is destructible
            if not game_object.state.get('destructible', False):
                return ActionResult(
                    success=False,
                    message=f"The {game_object.name.lower()} cannot be destroyed by your meager efforts.",
                    room_changed=False
                )

            # Check if object is already destroyed
            if game_object.state.get('is_destroyed', False):
                return ActionResult(
                    success=False,
                    message=f"The {game_object.name.lower()} is already a mere pile of wreckage.",
                    room_changed=False
                )

            # Get object name for messages
            obj_name = game_object.name or object_id

            # Destroy the object
            game_object.state['is_destroyed'] = True
            game_object.state['is_takeable'] = False  # Destroyed objects can't be taken

            # Remove from room or inventory
            if object_in_room:
                current_room.items.remove(object_id)
            if object_in_inventory:
                state.inventory.remove(object_id)

            # Increment turn counter
            state.increment_turn()

            # Generate thematic destruction message
            if state.sanity < 30:
                messages = [
                    f"You smash the {obj_name.lower()} with furious abandon, releasing a spray of splinters and dust. The violence feels satisfyingly final.",
                    f"Your hands tremble as you tear the {obj_name.lower()} apart. Fragments scatter across the floor like skeletal remains.",
                    f"The {obj_name.lower()} gives way with a terrible crack. The sound echoes through the halls like a death cry.",
                    f"Rage fills you as you destroy the {obj_name.lower()}. The act feels both catharticic and deeply unsettling."
                ]
            else:
                messages = [
                    f"You destroy the {obj_name.lower()}. It breaks apart with a series of cracks and splinters.",
                    f"The {obj_name.lower()} shatters under your assault. Nothing salvageable remains.",
                    f"You reduce the {obj_name.lower()} to pieces. A small puff of dust rises from the wreckage.",
                    f"The {obj_name.lower()} is now completely broken, its purpose served."
                ]

            import random
            message = random.choice(messages)

            # Add any special effects from object interactions
            notifications = []

            for interaction in game_object.interactions:
                if interaction.verb == "DESTROY":
                    if interaction.response_spooky:
                        message = interaction.response_spooky

                    if interaction.state_change:
                        for key, value in interaction.state_change.items():
                            game_object.state[key] = value

                    if interaction.flag_change:
                        for flag_name, flag_value in interaction.flag_change.items():
                            state.set_flag(flag_name, flag_value)

                    if interaction.sanity_effect != 0:
                        old_sanity = state.sanity
                        state.sanity = max(0, min(100, state.sanity + interaction.sanity_effect))

                        sanity_change = state.sanity - old_sanity
                        if sanity_change < 0:
                            notifications.append("The act of destruction unsettles your mind...")
                        elif sanity_change > 0:
                            notifications.append("A strange satisfaction comes from the destruction.")

                    break

            return ActionResult(
                success=True,
                message=message,
                room_changed=False,
                state_changes={
                    'sanity': state.sanity,
                    'turn_count': state.turn_count
                } if notifications else {},
                notifications=notifications
            )

        except ValueError as e:
            return ActionResult(
                success=False,
                message="You can't destroy that here.",
                room_changed=False
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Your destructive efforts are thwarted by unseen forces.",
                room_changed=False
            )

    def handle_inflate(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """Handle inflating an inflatable object."""
        try:
            current_room = self.world.get_room(state.current_room)
            
            if object_id not in current_room.items and object_id not in state.inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(success=False, message=f"You don't see any {display_name} here.")
            
            game_object = self.world.get_object(object_id)
            
            if not game_object.state.get('is_inflatable', False):
                display_name = self._get_object_names(object_id)
                return ActionResult(success=False, message=f"You can't inflate the {display_name}.")
            
            if game_object.state.get('is_inflated', False):
                display_name = self._get_object_names(object_id)
                return ActionResult(success=False, message=f"The {display_name} is already inflated.")
            
            game_object.state['is_inflated'] = True
            
            display_name = self._get_object_names(object_id)
            message = f"You inflate the {display_name}."
            for interaction in game_object.interactions:
                if interaction.verb == "INFLATE":
                    message = interaction.response_spooky
                    if interaction.state_change:
                        for key, value in interaction.state_change.items():
                            game_object.state[key] = value
                    if interaction.flag_change:
                        for flag_name, flag_value in interaction.flag_change.items():
                            state.set_flag(flag_name, flag_value)
                    break
            
            return ActionResult(success=True, message=message)
        except ValueError:
            display_name = self._get_object_names(object_id)
            return ActionResult(success=False, message=f"The shadows reveal no {display_name} in this forsaken place.")
        except Exception:
            return ActionResult(success=False, message="The object resists inflation, as if cursed to remain deflated.")
    
    def handle_deflate(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """Handle deflating an inflatable object."""
        try:
            current_room = self.world.get_room(state.current_room)
            
            if object_id not in current_room.items and object_id not in state.inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(success=False, message=f"You don't see any {display_name} here.")
            
            game_object = self.world.get_object(object_id)
            
            if not game_object.state.get('is_inflatable', False):
                display_name = self._get_object_names(object_id)
                return ActionResult(success=False, message=f"You can't deflate the {display_name}.")
            
            if not game_object.state.get('is_inflated', False):
                display_name = self._get_object_names(object_id)
                return ActionResult(success=False, message=f"The {display_name} is already deflated.")
            
            game_object.state['is_inflated'] = False
            
            display_name = self._get_object_names(object_id)
            message = f"You deflate the {display_name}."
            for interaction in game_object.interactions:
                if interaction.verb == "DEFLATE":
                    message = interaction.response_spooky
                    if interaction.state_change:
                        for key, value in interaction.state_change.items():
                            game_object.state[key] = value
                    if interaction.flag_change:
                        for flag_name, flag_value in interaction.flag_change.items():
                            state.set_flag(flag_name, flag_value)
                    break
            
            return ActionResult(success=True, message=message)
        except ValueError:
            display_name = self._get_object_names(object_id)
            return ActionResult(success=False, message=f"The shadows reveal no {display_name} in this forsaken place.")
        except Exception:
            return ActionResult(success=False, message="The object clings to its inflated form, resisting your efforts.")
    
    def handle_wave(self, object_id: str, state: GameState) -> ActionResult:
        """Handle waving an object."""
        try:
            if object_id not in state.inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(success=False, message=f"You don't have the {display_name}.")
            
            game_object = self.world.get_object(object_id)
            display_name = self._get_object_names(object_id)
            message = f"You wave the {display_name}. Nothing happens."
            
            for interaction in game_object.interactions:
                if interaction.verb == "WAVE":
                    message = interaction.response_spooky
                    if interaction.state_change:
                        for key, value in interaction.state_change.items():
                            game_object.state[key] = value
                    if interaction.flag_change:
                        for flag_name, flag_value in interaction.flag_change.items():
                            state.set_flag(flag_name, flag_value)
                    break
            
            return ActionResult(success=True, message=message)
        except ValueError:
            display_name = self._get_object_names(object_id)
            return ActionResult(success=False, message=f"Your trembling hands find no {display_name} among your cursed possessions.")
        except Exception:
            return ActionResult(success=False, message="The object slips from your grasp as you attempt to wave it.")
    
    def handle_rub(self, object_id: str, state: GameState) -> ActionResult:
        """Handle rubbing/touching an object."""
        try:
            current_room = self.world.get_room(state.current_room)
            if object_id not in current_room.items and object_id not in state.inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(success=False, message=f"You don't see any {display_name} here.")
            
            game_object = self.world.get_object(object_id)
            display_name = self._get_object_names(object_id)
            message = f"You rub the {display_name}. Nothing happens."
            
            for interaction in game_object.interactions:
                if interaction.verb == "RUB":
                    message = interaction.response_spooky
                    if interaction.state_change:
                        for key, value in interaction.state_change.items():
                            game_object.state[key] = value
                    if interaction.flag_change:
                        for flag_name, flag_value in interaction.flag_change.items():
                            state.set_flag(flag_name, flag_value)
                    break
            
            return ActionResult(success=True, message=message)
        except ValueError:
            display_name = self._get_object_names(object_id)
            return ActionResult(success=False, message=f"The shadows reveal no {display_name} in this forsaken place.")
        except Exception:
            return ActionResult(success=False, message="Your touch upon the object sends a chill through your bones.")
    
    def handle_shake(self, object_id: str, state: GameState) -> ActionResult:
        """Handle shaking an object."""
        try:
            current_room = self.world.get_room(state.current_room)
            if object_id not in current_room.items and object_id not in state.inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(success=False, message=f"You don't see any {display_name} here.")
            
            game_object = self.world.get_object(object_id)
            display_name = self._get_object_names(object_id)
            message = f"You shake the {display_name}. Nothing happens."
            
            for interaction in game_object.interactions:
                if interaction.verb == "SHAKE":
                    message = interaction.response_spooky
                    if interaction.state_change:
                        for key, value in interaction.state_change.items():
                            game_object.state[key] = value
                    if interaction.flag_change:
                        for flag_name, flag_value in interaction.flag_change.items():
                            state.set_flag(flag_name, flag_value)
                    break
            
            return ActionResult(success=True, message=message)
        except ValueError:
            display_name = self._get_object_names(object_id)
            return ActionResult(success=False, message=f"The shadows reveal no {display_name} in this forsaken place.")
        except Exception:
            return ActionResult(success=False, message="The object rattles ominously, as if something within stirs.")
    
    def handle_squeeze(self, object_id: str, state: GameState) -> ActionResult:
        """Handle squeezing an object."""
        try:
            current_room = self.world.get_room(state.current_room)
            if object_id not in current_room.items and object_id not in state.inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(success=False, message=f"You don't see any {display_name} here.")
            
            game_object = self.world.get_object(object_id)
            display_name = self._get_object_names(object_id)
            message = f"You squeeze the {display_name}. Nothing happens."
            
            for interaction in game_object.interactions:
                if interaction.verb == "SQUEEZE":
                    message = interaction.response_spooky
                    if interaction.state_change:
                        for key, value in interaction.state_change.items():
                            game_object.state[key] = value
                    if interaction.flag_change:
                        for flag_name, flag_value in interaction.flag_change.items():
                            state.set_flag(flag_name, flag_value)
                    break
            
            return ActionResult(success=True, message=message)
        except ValueError:
            display_name = self._get_object_names(object_id)
            return ActionResult(success=False, message=f"The shadows reveal no {display_name} in this forsaken place.")
        except Exception:
            return ActionResult(success=False, message="The object resists your grip, as if it has a will of its own.")

    def handle_frobozz(self, state: GameState) -> ActionResult:
        """
        Handle FROBOZZ magic word command.

        A legendary magic word from the Frobozz Magic Spell Company.
        In the haunted context, this attempts to channel forgotten power.

        Args:
            state: Current game state

        Returns:
            ActionResult with haunted themed response

        Requirements: 4.5, 5.10
        """
        # Low sanity makes the magic more erratic
        if state.sanity < 30:
            return ActionResult(
                success=True,
                message="The name FROBOZZ crackles on your tongue like black fire. Shadows writhe and coalesce, forming fleeting shapes of twisted faces before dissolving into mist."
            )
        elif state.sanity < 60:
            return ActionResult(
                success=True,
                message="You intone the ancient name 'FROBOZZ' and feel a surge of otherworldly energy. The air grows cold and your breath fogs like a ghost's sigh."
            )
        else:
            return ActionResult(
                success=True,
                message="The word 'FROBOZZ' echoes faintly in your mind, a remnant of forgotten magics. Nothing tangible happens, but you sense ancient power slumbering."
            )

    def handle_zork(self, state: GameState) -> ActionResult:
        """
        Handle ZORK special command.

        The name of the original empire, now a ghost of its former glory.
        Invoking it stirs echoes of the past within the haunted depths.

        Args:
            state: Current game state

        Returns:
            ActionResult with haunted themed response

        Requirements: 4.5, 5.10
        """
        # Check if player is in specific rooms for special effects
        current_room = self.world.get_room(state.current_room)
        room_id = current_room.id

        # Special response if in certain important locations
        if room_id in ["treasure_room", "crypt", "throne_room"]:
            return ActionResult(
                success=True,
                message=f"The name 'ZORK' resonates with power in this {current_room.name}. Ghostly whispers speak of fallen empires and forgotten kings. You feel the weight of history pressing down upon you."
            )
        elif state.sanity < 25:
            return ActionResult(
                success=True,
                message="ZORK! The name tears from your throat like a scream. Visions of burning cities and weeping ghosts flash through your mind. The darkness hungerily absorbs the echo."
            )
        else:
            return ActionResult(
                success=True,
                message="You speak the name of the fallen empire. A chill wind rustles through the haunted corridors, carrying whispers of what once was."
            )

    def handle_blast(self, target: str, state: GameState) -> ActionResult:
        """
        Handle BLAST magical destruction command.

        A powerful magical explosion that can destroy barriers and creatures.
        Particularly effective against supernatural entities.

        Args:
            target: The target to blast (can be None for area effect)
            state: Current game state

        Returns:
            ActionResult with success status and haunted themed message

        Requirements: 4.4, 5.8
        """
        if not target:
            # Area effect blast
            if state.sanity < 40:
                return ActionResult(
                    success=True,
                    message="You channel raw magical energy into a devastating blast! Shadows scream and dissipate as raw power erupts from your hands. The very foundations of the house tremble."
                )
            else:
                return ActionResult(
                    success=True,
                    message="You release a concussive burst of magical energy. Dust and debris swirl in the vortex, but the ancient structures of this place resist destruction."
                )

        # Targeted blast
        try:
            # Check if target is in room or inventory
            current_room = self.world.get_room(state.current_room)
            target_in_room = target in current_room.items
            target_in_inventory = target in state.inventory

            if not target_in_room and not target_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {target} here to blast."
                )

            # Get target object
            target_object = self.world.get_object(target)

            # Check if target can be destroyed by magic
            is_magical = target_object.state.get('magical', False)
            is_creature = target_object.type in ['creature', 'person', 'spirit']
            is_destructible = target_object.state.get('destructible', True)

            if not is_destructible:
                return ActionResult(
                    success=False,
                    message=f"The {target} resists your magical blast, absorbing the energy without harm."
                )

            # Apply blast effects
            if is_creature:
                if target_object.state.get('undead', False) or target_object.state.get('spectral', False):
                    # Extra damage to supernatural creatures
                    return ActionResult(
                        success=True,
                        message=f"Raw magical power blasts the {target}! The creature shrieks as holy and arcane energies tear it apart. It dissolves into ectoplasmic mist."
                    )
                else:
                    return ActionResult(
                        success=True,
                        message=f"Your magical blast strikes the {target} with tremendous force! The creature is thrown back, injured and dazed by the raw power."
                    )
            elif is_magical:
                return ActionResult(
                    success=True,
                    message=f"The {target} flares brightly as your blast hits it! Magical energy cascades through the object, causing it to crack and splinter with arcane power."
                )
            else:
                return ActionResult(
                    success=True,
                    message=f"Your magical blast hammers the {target}! The object shatters and explodes into fragments, consumed by the magical conflagration."
                )

        except ValueError:
            return ActionResult(
                success=False,
                message=f"There is no {target} here to target your blast at."
            )
        except Exception:
            return ActionResult(
                success=False,
                message="Your magical blast fizzles and misfires. The arcane energies refuse to cooperate, dissipating harmlessly."
            )

    def handle_wish(self, wish_text: str, state: GameState) -> ActionResult:
        """
        Handle WISH command for making wishes.

        A powerful magical command that can alter reality, but at great cost.
        In the haunted context, wishes often have twisted consequences.

        Args:
            wish_text: The content of the wish (can be None)
            state: Current game state

        Returns:
            ActionResult with haunted themed response and consequences

        Requirements: 4.5, 5.10
        """
        if not wish_text:
            return ActionResult(
                success=False,
                message="What do you wish for? Be careful what you ask for in this cursed place..."
            )

        # Low sanity makes wishes more dangerous
        if state.sanity < 20:
            return ActionResult(
                success=True,
                message=f"You wish for '{wish_text}' but the darkness twists your words! Your wish is granted in the most horrifying way imaginable. Something ancient laughs at your folly.",
                state_changes={
                    'sanity': max(0, state.sanity - 10)
                }
            )
        elif state.sanity < 50:
            return ActionResult(
                success=True,
                message=f"You wish for '{wish_text}' and feel reality shift around you. The house seems to approve of your desire, but you sense a terrible price will be extracted later.",
                state_changes={
                    'sanity': max(0, state.sanity - 5)
                }
            )
        else:
            # Common wish patterns with haunted effects
            wish_lower = wish_text.lower()
            if "wealth" in wish_lower or "riches" in wish_lower or "treasure" in wish_lower:
                return ActionResult(
                    success=True,
                    message="You wish for wealth, and ghostly coins appear in your hand - cold as death and stamped with forgotten faces. They vanish when you look away, leaving only the memory of their touch.",
                    state_changes={
                        'sanity': max(0, state.sanity - 3)
                    }
                )
            elif "exit" in wish_lower or "escape" in wish_lower or "leave" in wish_lower:
                return ActionResult(
                    success=True,
                    message="You wish to escape this place. For a moment, you see daylight and feel fresh air, then the illusion shatters. The house laughs at your hope of freedom.",
                    state_changes={
                        'sanity': max(0, state.sanity - 7)
                    }
                )
            elif "power" in wish_lower or "strength" in wish_lower:
                return ActionResult(
                    success=True,
                    message="You wish for power and feel it surge through you! But this is the house's power, and it comes with whispers of madness and shadows that cling to your soul.",
                    state_changes={
                        'sanity': max(0, state.sanity - 8)
                    }
                )
            else:
                return ActionResult(
                    success=True,
                    message=f"You wish for '{wish_text}'. The ancient powers consider your request, then remain silent. Some things are not meant to be granted, even by magic.",
                    state_changes={
                        'sanity': max(0, state.sanity - 2)
                    }
                )

    def handle_win(self, state: GameState) -> ActionResult:
        """
        Handle WIN command for instant victory.

        A meta-command that attempts to end the game in victory.
        In the haunted context, true victory comes at a terrible price.

        Args:
            state: Current game state

        Returns:
            ActionResult with haunted themed response

        Requirements: 4.5, 5.10
        """
        # Check if player has actually met victory conditions
        score = state.calculate_score()
        max_score = self.world.get_max_score()

        if score >= max_score * 0.9:  # Close to winning
            return ActionResult(
                success=True,
                message=f"You have truly triumphed! With a score of {score} out of {max_score}, you have conquered the haunted house. The shadows finally recede, and you walk out into the dawn, free at last."
            )
        elif state.sanity < 15:  # Very low sanity
            return ActionResult(
                success=True,
                message="You declare victory, but the haunted house has already claimed your mind. You 'win' by becoming one of the eternal residents, forever wandering these cursed halls. A hollow victory indeed."
            )
        else:
            return ActionResult(
                success=False,
                message=f"Victory cannot be claimed so easily. You have only achieved {score} out of {max_score} possible points. The house still holds many secrets, and you have not yet earned your freedom. Continue exploring, mortal..."
            )

    def handle_xyzzy(self, state: GameState) -> ActionResult:
        """Handle XYZZY easter egg command."""
        return ActionResult(success=True, message="A hollow voice whispers: 'Fool.' The ancient magic has long since faded from this cursed place.")
    
    def handle_plugh(self, state: GameState) -> ActionResult:
        """Handle PLUGH easter egg command."""
        return ActionResult(success=True, message="A spectral voice echoes: 'Nothing happens.' The old enchantments hold no power here.")
    
    def handle_hello(self, state: GameState) -> ActionResult:
        """Handle HELLO command."""
        return ActionResult(success=True, message="The shadows seem to shift in response, but no voice answers your greeting. You are alone... or are you?")
    
    def handle_pray(self, state: GameState) -> ActionResult:
        """Handle PRAY command."""
        return ActionResult(success=True, message="You offer a desperate prayer to whatever gods might listen. The darkness seems to press closer, as if offended by your plea.")
    
    def handle_jump(self, state: GameState) -> ActionResult:
        """Handle JUMP command."""
        return ActionResult(success=True, message="You jump up and down. The floorboards creak ominously beneath your feet.")
    
    def handle_yell(self, state: GameState) -> ActionResult:
        """Handle YELL command."""
        return ActionResult(success=True, message="Your scream echoes through the haunted halls, returning to you twisted and distorted. Something in the darkness laughs.")
    
    def handle_echo(self, text: str, state: GameState) -> ActionResult:
        """Handle ECHO command."""
        if not text:
            return ActionResult(success=True, message="Echo... echo... echo...")
        return ActionResult(success=True, message=f"Echo: {text}")
    
    def handle_curse(self, state: GameState) -> ActionResult:
        """Handle profanity/curse words."""
        messages = [
            "Such language! The spirits are offended by your crude words.",
            "Your profanity echoes through the halls, but the darkness does not care.",
            "Cursing won't help you here. The house has heard far worse.",
            "Mind your tongue! This place feeds on negativity.",
            "The shadows seem amused by your colorful language."
        ]
        import random
        return ActionResult(success=True, message=random.choice(messages))

    def handle_find(self, search_target: str, state: GameState) -> ActionResult:
        """
        Handle FIND/SEARCH FOR command for locating objects.

        Searches through the current room, inventory, and nearby containers
        to locate the specified object or type of object.

        Args:
            search_target: The object or category to search for
            state: Current game state

        Returns:
            ActionResult with search results and haunted themed message

        Requirements: 3.5, 5.1
        """
        if not search_target:
            return ActionResult(
                success=False,
                message="What are you trying to find? Be specific about what you seek in this haunted place."
            )

        current_room = self.world.get_room(state.current_room)
        search_target_lower = search_target.lower()
        found_locations = []

        # Search inventory
        for item_id in state.inventory:
            try:
                item = self.world.get_object(item_id)
                if search_target_lower in item.id.lower() or search_target_lower in item.name.lower():
                    found_locations.append(f"carrying the {item.name}")
            except ValueError:
                continue

        # Search room
        for item_id in current_room.items:
            try:
                item = self.world.get_object(item_id)
                if search_target_lower in item.id.lower() or search_target_lower in item.name.lower():
                    found_locations.append(f"{item.name} here in the {current_room.name}")
            except ValueError:
                continue

        # Search containers in room
        for item_id in current_room.items:
            try:
                item = self.world.get_object(item_id)
                if item.type == "container" and item.state.get('open', False):
                    for contained_id in item.state.get('contains', []):
                        contained_item = self.world.get_object(contained_id)
                        if (search_target_lower in contained_item.id.lower() or
                            search_target_lower in contained_item.name.lower()):
                            found_locations.append(f"{contained_item.name} inside the {item.name}")
            except ValueError:
                continue

        # Format results based on findings
        if not found_locations:
            # Provide helpful hints based on low sanity
            if state.sanity < 30:
                return ActionResult(
                    success=False,
                    message=f"You can't find any {search_target} here. The shadows mock your search, hiding things that might have been in plain sight."
                )
            else:
                return ActionResult(
                    success=False,
                    message=f"You search carefully but find no {search_target} in this area."
                )
        elif len(found_locations) == 1:
            return ActionResult(
                success=True,
                message=f"You find {found_locations[0]}."
            )
        else:
            found_list = "\n- ".join(found_locations)
            return ActionResult(
                success=True,
                message=f"You search for {search_target} and find:\n- {found_list}"
            )

    def handle_count(self, count_target: str, state: GameState) -> ActionResult:
        """
        Handle COUNT command for tallying items or treasures.

        Counts specific types of objects, treasures, or provides general inventory statistics.

        Args:
            count_target: What to count (can be None for general count)
            state: Current game state

        Returns:
            ActionResult with count results and haunted themed message

        Requirements: 3.5, 5.3
        """
        current_room = self.world.get_room(state.current_room)

        if not count_target:
            # General inventory count
            inventory_count = len(state.inventory)
            room_item_count = len(current_room.items)

            return ActionResult(
                success=True,
                message=f"You are carrying {inventory_count} item{'s' if inventory_count != 1 else ''}. "
                       f"There {'are' if room_item_count != 1 else 'is'} {room_item_count} "
                       f"object{'s' if room_item_count != 1 else ''} here in the {current_room.name}."
            )

        count_target_lower = count_target.lower()
        count = 0
        locations = []

        # Count in inventory
        for item_id in state.inventory:
            try:
                item = self.world.get_object(item_id)
                if (count_target_lower in item.id.lower() or
                    count_target_lower in item.name.lower() or
                    count_target_lower in item.type.lower()):
                    count += 1
                    locations.append(f"carrying {item.name}")
            except ValueError:
                continue

        # Count in room
        for item_id in current_room.items:
            try:
                item = self.world.get_object(item_id)
                if (count_target_lower in item.id.lower() or
                    count_target_lower in item.name.lower() or
                    count_target_lower in item.type.lower()):
                    count += 1
                    locations.append(f"{item.name} here")
            except ValueError:
                continue

        # Special case: count treasures
        if count_target_lower in ["treasure", "treasures", "valuable", "valuables"]:
            treasure_count = 0
            for item_id in state.inventory + current_room.items:
                try:
                    item = self.world.get_object(item_id)
                    if item.state.get('treasure', False):
                        treasure_count += 1
                except ValueError:
                    continue

            if treasure_count == 0:
                return ActionResult(
                    success=True,
                    message="You count no treasures here. The house's riches remain hidden or lost to time."
                )
            elif treasure_count == 1:
                return ActionResult(
                    success=True,
                    message=f"You count one treasure. Its value glimmers faintly in the darkness."
                )
            else:
                return ActionResult(
                    success=True,
                    message=f"You count {treasure_count} treasures. The accumulated wealth feels heavy with ancient curses."
                )

        if count == 0:
            return ActionResult(
                success=True,
                message=f"You count no {count_target} here. The darkness keeps its own tally of what passes through these halls."
            )
        elif count == 1:
            return ActionResult(
                success=True,
                message=f"You count one {count_target}: {locations[0] if locations else 'somewhere nearby'}."
            )
        else:
            return ActionResult(
                success=True,
                message=f"You count {count} instances of {count_target}."
            )

    def handle_version(self, state: GameState) -> ActionResult:
        """
        Handle VERSION command to display game information.

        Shows version details, build information, and game statistics
        with a haunted house twist on the traditional format.

        Args:
            state: Current game state

        Returns:
            ActionResult with version information

        Requirements: 8.1
        """
        import datetime

        # Calculate some game statistics
        rooms_visited = len(state.visit_history) if hasattr(state, 'visit_history') else 1
        current_score = state.calculate_score()
        max_score = self.world.get_max_score()
        score_percentage = int((current_score / max_score) * 100) if max_score > 0 else 0

        version_info = (
            "West of Haunted House\n"
            "A Cursed Reconstruction of Zork I: The Great Underground Empire\n"
            "========================================\n\n"
            f"Version: 1.3.37 (Haunted Edition)\n"
            f"Build Date: {datetime.datetime.now().strftime('%B %d, %Y')}\n"
            f"Engine: Python 3.12 with AWS Amplify Gen 2\n\n"
            f"Game Statistics:\n"
            f"- Rooms Explored: {rooms_visited} of 110\n"
            f"- Current Score: {current_score} out of {max_score} ({score_percentage}%)\n"
            f"- Sanity Level: {state.sanity}/100\n\n"
            f"The shadows whisper that you've been wandering for {state.turn_count} turns...\n"
            f"May the spirits have mercy on your soul."
        )

        return ActionResult(success=True, message=version_info)

    def handle_diagnose(self, state: GameState) -> ActionResult:
        """
        Handle DIAGNOSE command for debugging information.

        Provides detailed game state information for troubleshooting
        and debugging, formatted in a player-friendly way.

        Args:
            state: Current game state

        Returns:
            ActionResult with diagnostic information

        Requirements: 8.2
        """
        current_room = self.world.get_room(state.current_room)

        # Compile diagnostic information
        diagnostic_info = (
            "=== HAUNTED HOUSE DIAGNOSTIC REPORT ===\n\n"
            f"Player Status:\n"
            f"- Location: {current_room.name} (ID: {current_room.id})\n"
            f"- Sanity: {state.sanity}/100\n"
            f"- Turns: {state.turn_count}\n"
            f"- Score: {state.calculate_score()}\n\n"

            f"Inventory: {len(state.inventory)} items\n"
            f"- Objects: {', '.join(state.inventory) if state.inventory else 'None'}\n\n"

            f"Room Contents: {len(current_room.items)} items\n"
            f"- Objects: {', '.join(current_room.items) if current_room.items else 'None'}\n\n"

            f"Game Flags:\n"
        )

        # Add important flags (limit to most relevant ones)
        important_flags = ['lamp_on', 'door_open', 'box_open', 'trap_triggered', 'ghost_appeased']
        for flag in important_flags:
            value = state.flags.get(flag, False)
            diagnostic_info += f"- {flag}: {value}\n"

        # Add sanity-based commentary
        if state.sanity < 25:
            diagnostic_info += "\nDiagnostic complete. The machine spirits whisper of impending madness..."
        elif state.sanity < 50:
            diagnostic_info += "\nDiagnostic complete. The systems function normally, though shadows linger at the edges."
        else:
            diagnostic_info += "\nDiagnostic complete. All systems nominal for now."

        return ActionResult(success=True, message=diagnostic_info)

    def handle_script(self, state: GameState) -> ActionResult:
        """
        Handle SCRIPT command to start transcription.

        Begins recording all game input and output to a transcript file.
        In the haunted context, this is like keeping a diary of your descent.

        Args:
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 8.3
        """
        # Check if already recording
        if hasattr(state, 'script_active') and state.script_active:
            return ActionResult(
                success=False,
                message="A transcript is already being recorded. The spirits are diligently documenting your journey into madness."
            )

        # Activate script recording
        state.script_active = True
        state.script_start_turn = state.turn_count

        return ActionResult(
            success=True,
            message="Transcription begun. Every word, every command, every desperate scream will now be recorded for posterity. The house watches as you document your own unraveling...",
            state_changes={'script_active': True}
        )

    def handle_unscript(self, state: GameState) -> ActionResult:
        """
        Handle UNSCRIPT command to stop transcription.

        Ends the recording of game input/output and saves the transcript.
        A final record of your time in the haunted halls.

        Args:
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 8.3
        """
        # Check if currently recording
        if not hasattr(state, 'script_active') or not state.script_active:
            return ActionResult(
                success=False,
                message="No transcript is currently being recorded. Your journey goes undocumented, lost to the mists of time."
            )

        # Calculate transcription statistics
        turns_recorded = state.turn_count - getattr(state, 'script_start_turn', state.turn_count)

        # Deactivate script recording
        state.script_active = False
        transcript_data = getattr(state, 'transcript_data', [])

        return ActionResult(
            success=True,
            message=f"Transcription complete after {turns_recorded} turns. "
                   f"Your chronicle of this haunted place has been preserved ({len(transcript_data)} entries). "
                   f"Future generations may read of your exploits... if they dare.",
            state_changes={'script_active': False}
        )

    def handle_treasure(self, state: GameState) -> ActionResult:
        """
        Handle TREASURE command to list found treasures.

        Lists all treasures the player has found and scored, along with
        their total value and progress toward wealth goals.

        Args:
            state: Current game state

        Returns:
            ActionResult with treasure information and haunted themed message

        Requirements: 5.7
        """
        # Count treasures in inventory
        inventory_treasures = []
        inventory_value = 0

        for item_id in state.inventory:
            try:
                item = self.world.get_object(item_id)
                if item.state.get('treasure', False):
                    inventory_treasures.append(item.name)
                    inventory_value += item.state.get('value', 10)
            except ValueError:
                continue

        # Count treasures scored (in trophy case)
        scored_treasures = state.flags.get('treasures_scored', [])
        scored_value = state.flags.get('total_treasure_value', 0)

        # Calculate treasure statistics
        total_found = len(inventory_treasures) + len(scored_treasures)
        total_value = inventory_value + scored_value

        if total_found == 0:
            return ActionResult(
                success=True,
                message="You have found no treasures yet. The house's wealth remains hidden, waiting for worthy or foolish seekers."
            )

        treasure_report = "=== TREASURE INVENTORY ===\n\n"

        if inventory_treasures:
            treasure_report += f"Carried Treasures ({len(inventory_treasures)} items, {inventory_value} value):\n"
            for treasure in inventory_treasures:
                treasure_report += f"- {treasure}\n"
            treasure_report += "\n"

        if scored_treasures:
            treasure_report += f"Scored Treasures ({len(scored_treasures)} items, {scored_value} value):\n"
            for treasure_id in scored_treasures:
                treasure_report += f"- {treasure_id}\n"
            treasure_report += "\n"

        treasure_report += (
            f"Total: {total_found} treasures worth {total_value} value points\n\n"
        )

        if total_value < 50:
            treasure_report += "Your accumulation of wealth is modest. The spirits are unimpressed."
        elif total_value < 150:
            treasure_report += "You have gathered significant wealth. The house stirs, aware of your growing power."
        else:
            treasure_report += "Your wealth is legendary! The very foundations tremble at your accumulated riches."

        return ActionResult(success=True, message=treasure_report)

    def handle_bug(self, bug_report: str, state: GameState) -> ActionResult:
        """
        Handle BUG command for reporting issues.

        Allows players to report bugs or issues with the game,
        storing them for later review with haunted acknowledgement.

        Args:
            bug_report: The bug report text (can be None for prompt)
            state: Current game state

        Returns:
            ActionResult with confirmation and haunted themed message

        Requirements: 8.4
        """
        if not bug_report:
            return ActionResult(
                success=False,
                message="To report a bug, use: BUG <description of the issue>\n\n"
                       "Example: BUG the ghost keeps disappearing through walls\n\n"
                       "The shadows wait to hear of your troubles..."
            )

        # Store bug report (in a real implementation, this would save to a database)
        bug_id = f"bug_{state.turn_count}_{len(bug_report)}"
        bug_data = {
            'turn': state.turn_count,
            'location': state.current_room,
            'sanity': state.sanity,
            'report': bug_report,
            'timestamp': state.turn_count
        }

        # Add to bug reports in state (for demonstration)
        if not hasattr(state, 'bug_reports'):
            state.bug_reports = []
        state.bug_reports.append(bug_data)

        # Haunted response based on sanity level
        if state.sanity < 30:
            response = (
                f"Bug report #{bug_id} filed. The whispers acknowledge your torment. "
                f"Your fractured perception sees flaws others miss. Or perhaps the house "
                f"truly is broken... as broken as your sanity."
            )
        elif state.sanity < 60:
            response = (
                f"Bug report #{bug_id} noted. The shadows nod sagely at your report. "
                f"Even in this cursed place, things should work properly. Your vigilance "
                f"is appreciated... by someone, somewhere."
            )
        else:
            response = (
                f"Bug report #{bug_id} recorded. The house takes note of your observation. "
                f"Perfection is difficult to maintain in a place where reality itself is "
                f"questionable. Thank you for your attention to detail."
            )

        return ActionResult(
            success=True,
            message=response,
            state_changes={'bug_reports': state.bug_reports}
        )

    def handle_ring(self, object_id: str, state: GameState) -> ActionResult:
        """
        Handle RING command for ringing bells or objects.

        Rings bells, gongs, or other ringable objects to produce sound
        that may have various effects throughout the haunted house.

        Args:
            object_id: The object to ring (can be None for general ringing)
            state: Current game state

        Returns:
            ActionResult with success status and haunted themed message

        Requirements: 3.2, 4.7
        """
        if not object_id:
            return ActionResult(
                success=False,
                message="What do you want to ring? Specify a bell, gong, or other ringable object."
            )

        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if object is in room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory

            if not object_in_room and not object_in_inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here to ring."
                )

            # Get object
            ring_object = self.world.get_object(object_id)

            # Check if object can be rung
            can_ring = ring_object.state.get('ringable', False)
            is_bell = 'bell' in ring_object.name.lower() or 'gong' in ring_object.name.lower()

            if not can_ring and not is_bell:
                return ActionResult(
                    success=False,
                    message=f"The {ring_object.name} cannot be rung. It makes no sound when struck."
                )

            # Ring the object
            sound_message = ring_object.state.get('ring_sound', f"DONG! The {ring_object.name} rings out clearly")
            echo_message = ring_object.state.get('echo_message', None)

            # Apply any ring effects
            notifications = []
            ring_flag = ring_object.state.get('ring_flag', None)
            if ring_flag:
                state.set_flag(ring_flag, True)
                notifications.append(f"Flag {ring_flag} set to True")

            # Sanity-based effects
            if state.sanity < 25:
                return ActionResult(
                    success=True,
                    message=f"You ring the {ring_object.name} frantically! {sound_message} "
                           f"The sound distorts into a tormented scream that echoes through the haunted halls. "
                           f"Something answers your call from the darkness...",
                    state_changes={'flags': state.flags},
                    notifications=notifications
                )
            elif state.sanity < 50:
                return ActionResult(
                    success=True,
                    message=f"You ring the {ring_object.name}. {sound_message} "
                           f"The sound seems to awaken something in the shadows. Whispers join the echo. "
                           f"{' ' + echo_message if echo_message else ''}",
                    state_changes={'flags': state.flags},
                    notifications=notifications
                )
            else:
                return ActionResult(
                    success=True,
                    message=f"You ring the {ring_object.name}. {sound_message} "
                           f"The clear tone echoes through the house, a moment of clarity in the oppressive darkness. "
                           f"{' ' + echo_message if echo_message else ''}",
                    state_changes={'flags': state.flags},
                    notifications=notifications
                )

        except ValueError:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here to ring."
            )
        except Exception:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"The {display_name} resists your attempts to ring it, as if frozen by supernatural cold."
            )

    def handle_cross(self, object_id: str, state: GameState) -> ActionResult:
        """
        Handle CROSS command for crossing objects or areas.

        Used to cross bridges, cross oneself (religious gesture), or
        cross supernatural barriers that require faith or courage.

        Args:
            object_id: What to cross (can be None for crossing oneself)
            state: Current game state

        Returns:
            ActionResult with success status and haunted themed message

        Requirements: 3.1, 4.8
        """
        current_room = self.world.get_room(state.current_room)

        if not object_id:
            # Cross oneself (religious gesture)
            if state.sanity < 30:
                return ActionResult(
                    success=True,
                    message="You make the sign of the cross, but your hands tremble and the gesture feels hollow. "
                           "The darkness laughs at your feeble attempts at protection."
                )
            elif state.sanity < 60:
                return ActionResult(
                    success=True,
                    message="You cross yourself, whispering a forgotten prayer. For a moment, the shadows retreat slightly. "
                           "Small comfort in this accursed place."
                )
            else:
                return ActionResult(
                    success=True,
                    message="You make the sign of the cross with steady hands. Faith provides a small shield against the house's malevolence."
                )

        # Try to cross an object
        try:
            # Check if object is in room
            if object_id not in current_room.items:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here to cross."
                )

            cross_object = self.world.get_object(object_id)

            # Check if object can be crossed
            is_crossable = cross_object.state.get('crossable', False)
            is_bridge = 'bridge' in cross_object.name.lower()
            is_chasm = 'chasm' in cross_object.name.lower() or 'gap' in cross_object.name.lower()

            if not is_crossable and not is_bridge:
                return ActionResult(
                    success=False,
                    message=f"The {cross_object.name} cannot be crossed. There's no way across."
                )

            # Check if crossing is currently possible
            is_intact = cross_object.state.get('intact', True)
            is_deployed = cross_object.state.get('deployed', False) or cross_object.state.get('extended', False)

            if not is_intact:
                return ActionResult(
                    success=False,
                    message=f"The {cross_object.name} is broken or collapsed. You cannot cross it safely."
                )

            if not is_deployed and is_bridge:
                return ActionResult(
                    success=False,
                    message=f"The {cross_object.name} is not extended or deployed. You need to make it crossable first."
                )

            # Cross the object
            success_message = cross_object.state.get('cross_message', f"You carefully cross the {cross_object.name}")
            danger_level = cross_object.state.get('cross_danger', 0)

            if danger_level > 7 and state.sanity < 40:
                return ActionResult(
                    success=False,
                    message=f"As you start to cross the {cross_object.name}, your fear overwhelms you. "
                           f"The shadows reach for you, and you scramble back to safety."
                )
            elif danger_level > 5:
                return ActionResult(
                    success=True,
                    message=f"{success_message}. Your heart pounds as you traverse the dangerous crossing. "
                           f"The house seems to watch your passage with hungry anticipation."
                )
            else:
                return ActionResult(
                    success=True,
                    message=f"{success_message}. You reach the other side safely, though you feel the house's gaze upon you."
                )

        except ValueError:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here to cross."
            )
        except Exception:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"Something supernatural prevents you from crossing the {display_name}. "
                       f"The very air thickens, blocking your path."
            )

    def handle_breathe(self, state: GameState) -> ActionResult:
        """
        Handle BREATHE command for character rest and recovery.

        Allows the character to take a moment to breathe, potentially
        recovering small amounts of sanity or preparing for challenges.

        Args:
            state: Current game state

        Returns:
            ActionResult with success status and haunted themed message

        Requirements: 3.8
        """
        current_room = self.world.get_room(state.current_room)

        # Check room conditions
        room_air = current_room.state.get('air_quality', 'normal')
        has_ventilation = current_room.state.get('ventilated', False)

        # Sanity-based responses
        if state.sanity < 20:
            return ActionResult(
                success=True,
                message="You gasp for air but find none. Each breath feels like inhaling glass and ash. "
                       "The house steals the very air from your lungs. Your sanity continues to fray..."
            )
        elif state.sanity < 40:
            return ActionResult(
                success=True,
                message="You take a deep, shuddering breath. The air tastes of dust and decay. "
                       "For a moment, clarity returns, but the shadows press closer, hungry for your fear."
            )
        elif room_air == 'stale' and not has_ventilation:
            return ActionResult(
                success=True,
                message="You breathe deeply in the stagnant air. It provides little refreshment, "
                       "but you steel yourself for the challenges ahead. The house feels suffocating."
            )
        elif has_ventilation:
            return ActionResult(
                success=True,
                message="You breathe the relatively fresh air in this ventilated area. "
                       "It clears your mind and strengthens your resolve against the house's influence."
            )
        else:
            return ActionResult(
                success=True,
                message="You take a moment to breathe and center yourself. The rhythm calms your nerves. "
                       "You feel slightly more prepared to face the haunted horrors ahead."
            )

    def handle_activate(self, object_id: str, state: GameState) -> ActionResult:
        """
        Handle ACTIVATE command for turning on devices or mechanisms.

        Activates mechanical devices, magical artifacts, or other
        objects that can be switched on or triggered.

        Args:
            object_id: The object to activate
            state: Current game state

        Returns:
            ActionResult with success status and haunted themed message

        Requirements: 3.3, 4.1
        """
        if not object_id:
            return ActionResult(
                success=False,
                message="What do you want to activate? Specify a device, mechanism, or artifact."
            )

        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if object is in room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory

            if not object_in_room and not object_in_inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here to activate."
                )

            # Get object
            activate_object = self.world.get_object(object_id)

            # Check if object can be activated
            is_activatable = activate_object.state.get('activatable', False)
            is_device = activate_object.type in ['device', 'mechanism', 'artifact']
            has_power = activate_object.state.get('has_power', False)

            if not is_activatable and not is_device:
                return ActionResult(
                    success=False,
                    message=f"The {activate_object.name} cannot be activated. It doesn't have any switches or controls."
                )

            # Check activation requirements
            if not has_power:
                power_source = activate_object.state.get('power_source', None)
                if power_source:
                    return ActionResult(
                        success=False,
                        message=f"The {activate_object.name} has no power. You need to {power_source} first."
                    )
                else:
                    return ActionResult(
                        success=False,
                        message=f"The {activate_object.name} is powerless. It cannot be activated in its current state."
                    )

            # Check if already active
            is_active = activate_object.state.get('active', False)
            if is_active:
                return ActionResult(
                    success=False,
                    message=f"The {activate_object.name} is already active. It hums with energy."
                )

            # Activate the object
            activate_object.state['active'] = True

            # Get activation effects
            activate_message = activate_object.state.get('activate_message', f"The {activate_object.name} whirs to life")
            activate_sound = activate_object.state.get('activate_sound', "A low hum fills the air")

            # Apply any activation flags
            notifications = []
            activate_flag = activate_object.state.get('activate_flag', None)
            if activate_flag:
                state.set_flag(activate_flag, True)
                notifications.append(f"Flag {activate_flag} set to True")

            # Sanity-based response to activation
            if state.sanity < 30:
                return ActionResult(
                    success=True,
                    message=f"You fumble with the {activate_object.name}'s controls and it activates! {activate_message} "
                           f"{activate_sound}. The energy feels wrong, corrupted. You've unleashed something terrible...",
                    state_changes={'flags': state.flags},
                    notifications=notifications
                )
            elif state.sanity < 60:
                return ActionResult(
                    success=True,
                    message=f"You activate the {activate_object.name}. {activate_message} "
                           f"{activate_sound}. The device responds, but you feel the house's attention turn toward you.",
                    state_changes={'flags': state.flags},
                    notifications=notifications
                )
            else:
                return ActionResult(
                    success=True,
                    message=f"You successfully activate the {activate_object.name}. {activate_message} "
                           f"{activate_sound}. The mechanism functions as intended, providing a small advantage.",
                    state_changes={'flags': state.flags},
                    notifications=notifications
                )

        except ValueError:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here to activate."
            )
        except Exception:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"The {display_name} refuses to respond to your attempts. Supernatural interference blocks the activation."
            )

    def handle_command(self, text: str, state: GameState) -> ActionResult:
        """
        Handle COMMAND utility for displaying command help.

        Provides help with available commands and syntax.
        Enhanced version of the help system with haunted atmosphere.

        Args:
            text: Optional help topic or command name
            state: Current game state

        Returns:
            ActionResult with help information and haunted themed message

        Requirements: 8.5
        """
        if not text:
            return ActionResult(
                success=True,
                message="=== HAUNTED HOUSE COMMANDS ===\n\n"
                       "The shadows whisper forgotten command names...\n\n"
                       "Movement: GO, BACK, STAND, FOLLOW, SWIM, CLIMB\n"
                       "Objects: TAKE, DROP, EXAMINE, OPEN, CLOSE, SEARCH\n"
                       "Magic: CAST, ENCHANT, EXORCISE, FROBOZZ, ZORK\n"
                       "Utility: INVENTORY, LOOK, VERSION, DIAGNOSE\n"
                       "For specific help: COMMAND <command name>\n\n"
                       "Be careful what you ask for... the house listens."
            )

        # Help for specific command
        text_lower = text.lower()

        # Provide help for the requested command
        help_topics = {
            'movement': "GO/HEAD/WALK/TRAVEL <direction> - Move through the haunted halls\n"
                       "BACK - Return to previous room\n"
                       "CLIMB <object> - Scale ladders, stairs, or obstacles",
            'objects': "TAKE/GET <object> - Pick up items\n"
                      "EXAMINE/LOOK AT <object> - Study objects carefully\n"
                      "OPEN/UNLOCK <object> - Access containers and doors",
            'magic': "CAST <spell> [AT <target>] [WITH <instrument>] - Channel supernatural forces\n"
                    "ENCHANT <object> - Imbue with magical properties\n"
                    "EXORCISE <object> - Banish supernatural entities",
            'utility': "INVENTORY - Check your possessions\n"
                       "VERSION - Game information\n"
                       "DIAGNOSE - Debug information"
        }

        for topic, help_text in help_topics.items():
            if text_lower in topic:
                return ActionResult(
                    success=True,
                    message=f"=== {topic.upper()} COMMANDS ===\n\n{help_text}\n\n"
                           "Use COMMAND <topic> for more help... if you dare."
                )

        # Check if it's a specific verb help
        if text_upper := text.upper():
            if text_upper in ['GO', 'TAKE', 'EXAMINE', 'CAST', 'INVENTORY']:
                return ActionResult(
                    success=True,
                    message=f"The ancient knowledge of '{text_upper}' reveals itself to you...\n"
                           f"Try different approaches with this command. The house may respond differently "
                           f"based on your sanity level and current circumstances."
                )

        return ActionResult(
            success=True,
            message=f"The shadows offer no wisdom about '{text}'. Some secrets remain hidden "
                   f"even from those who seek knowledge. Try a different topic."
        )

    def handle_chomp(self, object_id: str, state: GameState) -> ActionResult:
        """
        Handle CHOMP command for aggressive eating/biting.

        An aggressive form of eating that can destroy objects or attack creatures.
        More dramatic than the normal EAT command with supernatural overtones.

        Args:
            object_id: The object to chomp (can be None for general chomping)
            state: Current game state

        Returns:
            ActionResult with success status and haunted themed message

        Requirements: 3.4, 4.2
        """
        if not object_id:
            if state.sanity < 30:
                return ActionResult(
                    success=True,
                    message="You chomp at the air with gnashing teeth! The shadows seem to recoil from your "
                           "ferocity. Something deep inside you yearns to bite and tear at this cursed place."
                )
            else:
                return ActionResult(
                    success=True,
                    message="You bare your teeth and chomp at nothing in particular. "
                           "This haunted place makes even simple actions feel like defiance."
                )

        try:
            # Check if object is in room or inventory
            current_room = self.world.get_room(state.current_room)
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory

            if not object_in_room and not object_in_inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here to chomp on."
                )

            # Get object
            chomp_object = self.world.get_object(object_id)

            # Check if object can be eaten/destroyed by chomping
            is_food = chomp_object.state.get('edible', False) or 'food' in chomp_object.name.lower()
            is_creature = chomp_object.type in ['creature', 'person']
            is_destructible = chomp_object.state.get('destructible', True)

            if not is_destructible:
                return ActionResult(
                    success=False,
                    message=f"You try to chomp the {chomp_object.name}, but it's too tough! Your teeth "
                           f"make an unsatisfying clinking sound."
                )

            if is_creature:
                if state.sanity < 25:
                    return ActionResult(
                        success=True,
                        message=f"You lunge and CHOMP the {chomp_object.name} with unnatural ferocity! "
                               f"Blood and ectoplasm spray everywhere. The creature shrieks as your "
                               f"bite tears into it. The house seems pleased by your violence.",
                        state_changes={'sanity': max(0, state.sanity - 5)}
                    )
                else:
                    return ActionResult(
                        success=True,
                        message=f"You try to bite the {chomp_object.name}! It dodges away, startled by your "
                               f"aggressive behavior. Maybe normal eating would be more civilized?"
                    )

            elif is_food:
                return ActionResult(
                    success=True,
                    message=f"You CHOMP down on the {chomp_object.name} with gusto! "
                           f"Food fragments fly everywhere as you devour it messily. "
                           f"A satisfying, if undignified, meal."
                )

            else:
                return ActionResult(
                    success=True,
                    message=f"You CHOMP the {chomp_object.name}! It shatters between your teeth "
                           f"into fragments. There's something cathartic about destroying things "
                           f"in this cursed place."
                )

        except ValueError:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here to chomp."
            )
        except Exception:
            return ActionResult(
                success=False,
                message="Your chomp goes wild and you bite your own tongue! "
                       "The pain grounds you in this terrible reality."
            )

    def handle_repent(self, state: GameState) -> ActionResult:
        """
        Handle REPENT command for expressing remorse.

        A spiritual command that may have effects on supernatural entities
        or the player's own sanity in the haunted context.

        Args:
            state: Current game state

        Returns:
            ActionResult with success status and haunted themed message

        Requirements: 4.9
        """
        current_room = self.world.get_room(state.current_room)

        # Check if there are supernatural entities present
        has_spirits = any(
            obj.type in ['spirit', 'ghost', 'undead'] or obj.state.get('supernatural', False)
            for obj_id in current_room.items
            for obj in [self.world.get_object(obj_id)]
            if hasattr(self.world, 'get_object')
        )

        if state.sanity < 20:
            return ActionResult(
                success=True,
                message="You fall to your knees and repent for your sins! Tears stream down your face as "
                       f"you beg forgiveness from powers seen and unseen.{' The spirits seem to mock your '
                       'broken state.' if has_spirits else ' The darkness offers no comfort.'}",
                state_changes={'sanity': min(100, state.sanity + 2)}
            )
        elif state.sanity < 50:
            return ActionResult(
                success=True,
                message=f"You offer a quiet prayer of repentance.{' The ghosts pause their haunting, '
                       f'respectful of your contrition.' if has_spirits else ' '
                       f'The weight of your actions feels slightly lighter.'}",
                state_changes={'sanity': min(100, state.sanity + 1)}
            )
        else:
            return ActionResult(
                success=True,
                message=f"You reflect on your actions and express remorse.{' The spirits acknowledge '
                       f'your sincerity with a brief moment of peace.' if has_spirits else ' '
                       f'Even in this haunted place, there is value in acknowledging one\'s faults.'}"
            )

    def handle_skip(self, state: GameState) -> ActionResult:
        """
        Handle SKIP command for movement.

        A form of movement or traversal, typically used for skipping over
        obstacles or moving quickly through areas.

        Args:
            state: Current game state

        Returns:
            ActionResult with success status and haunted themed message

        Requirements: 3.1
        """
        current_room = self.world.get_room(state.current_room)

        # Check if there are specific skip opportunities via game flags
        has_puddles = state.get_flag('has_puddles', False)
        has_rope = state.get_flag('rope_bridge', False)

        if has_puddles:
            return ActionResult(
                success=True,
                message="You skip playfully over the puddles on the floor. For a moment, you feel "
                       "like a child again, before the house reminds you of your true circumstances."
            )
        elif has_rope:
            return ActionResult(
                success=True,
                message="You skip across the rope bridge with surprising agility. The bridge sways "
                       "dangerously, but your light footing serves you well."
            )
        else:
            return ActionResult(
                success=True,
                message="You skip lightly across the room. The movement feels strangely out of place "
                       "in the oppressive atmosphere, but briefly lifts your spirits."
            )

    def handle_spay(self, state: GameState) -> ActionResult:
        """
        Handle SPAY command (likely a misspelling of SPRAY or SPIN).

        Handles ambiguous command that could be spray or spin related.
        Provides haunted theme interpretation of the action.

        Args:
            state: Current game state

        Returns:
            ActionResult with success status and haunted themed message

        Requirements: 3.9
        """
        # Since SPAY is ambiguous, provide a response that could work for either interpretation
        if state.sanity < 30:
            return ActionResult(
                success=True,
                message="You attempt to spay something... or maybe spray? Or spin? The command feels "
                       "wrong in your mind, like trying to speak a forgotten language. "
                       "The house watches your confusion with amusement."
            )
        else:
            return ActionResult(
                success=True,
                message="Did you mean SPRAY or SPIN? In your confusion, you manage to do both "
                       "simultaneously - spraying imaginary substances while spinning in circles. "
                       "You feel slightly dizzy but strangely accomplished."
            )

    def handle_spin(self, state: GameState) -> ActionResult:
        """
        Handle SPIN command for rotating movement.

        Spins around in place, potentially dizzying or affecting perception.
        In haunted context, may interact with supernatural phenomena.

        Args:
            state: Current game state

        Returns:
            ActionResult with success status and haunted themed message

        Requirements: 3.1
        """
        current_room = self.world.get_room(state.current_room)

        if state.sanity < 25:
            return ActionResult(
                success=True,
                message="You spin wildly around and around! The room blurs into a vortex of "
                       "shadows and whispers. When you stop, the world seems... different. "
                       "Was that always there?",
                state_changes={'sanity': max(0, state.sanity - 3)}
            )
        elif state.sanity < 60:
            return ActionResult(
                success=True,
                message="You spin in a circle. The haunted room spins with you, or is it the other way "
                       "around? For a moment, you see things at the edge of your vision that weren't there before."
            )
        else:
            return ActionResult(
                success=True,
                message="You spin around once. The room remains stubbornly haunted, but the "
                       "brief moment of dizziness provides a small distraction from your grim reality."
            )

    def handle_spray(self, object_id: str, target: str, state: GameState) -> ActionResult:
        """
        Handle SPRAY command for spraying substances.

        Sprays liquids, powders, or other substances on objects or areas.
        Can be used for cleaning, applying chemicals, or creating effects.

        Args:
            object_id: What to spray from (container, bottle, etc.)
            target: What to spray on (can be None for general spraying)
            state: Current game state

        Returns:
            ActionResult with success status and haunted themed message

        Requirements: 3.3, 4.1
        """
        if not object_id:
            return ActionResult(
                success=False,
                message="What do you want to spray? You need a container or spray device."
            )

        try:
            # Check if object is in inventory
            if object_id not in state.inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't have any {display_name} to spray with."
                )

            # Get spray object
            spray_object = self.world.get_object(object_id)

            # Check if object can be sprayed from
            can_spray = spray_object.state.get('sprayable', False)
            is_container = spray_object.type == 'container'
            contains_liquid = spray_object.state.get('contains_liquid', False)

            if not can_spray and not (is_container and contains_liquid):
                return ActionResult(
                    success=False,
                    message=f"The {spray_object.name} cannot be sprayed from. It's empty or not designed for spraying."
                )

            if not target:
                return ActionResult(
                    success=True,
                    message=f"You spray {spray_object.name} into the air around you. "
                           f"Mist drifts through the haunted room, catching the dim light in tiny droplets."
                )

            # Check if target is in room
            current_room = self.world.get_room(state.current_room)
            target_in_room = target in current_room.items

            if not target_in_room:
                target_display_name = self._get_object_names(target)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {target_display_name} here to spray."
                )

            # Spray the target
            spray_effect = spray_object.state.get('spray_effect', 'wet')
            target_object = self.world.get_object(target)

            # Apply spray effects
            if spray_effect == 'holy_water' and target_object.state.get('undead', False):
                return ActionResult(
                    success=True,
                    message=f"You spray holy water from the {spray_object.name} onto the {target_object.name}! "
                           f"The supernatural entity shrieks and dissolves in a cloud of steam. "
                           f"The power of righteousness burns through the cursed air."
                )
            elif spray_effect == 'acid':
                return ActionResult(
                    success=True,
                    message=f"You spray corrosive acid from the {spray_object.name} onto the {target_object.name}! "
                           f"The material bubbles and melts away, releasing foul fumes that even "
                           f"the house seems to dislike."
                )
            else:
                return ActionResult(
                    success=True,
                    message=f"You spray the {target_object.name} with contents from the {spray_object.name}. "
                           f"The {target_object.name} is now {spray_effect}. The spray seems to have "
                           f"no supernatural effect, but at least you feel productive."
                )

        except ValueError:
            target_display_name = self._get_object_names(target)
            return ActionResult(
                success=False,
                message=f"You don't see any {target_display_name} here to spray."
            )
        except Exception:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"The {display_name} clogs up or breaks! Spraying mechanics fail you "
                       f"when you need them most."
            )

    def handle_stay(self, state: GameState) -> ActionResult:
        """
        Handle STAY command for remaining in place.

        Used to tell creatures or companions to stay put,
        or to commit to staying in a location yourself.

        Args:
            state: Current game state

        Returns:
            ActionResult with success status and haunted themed message

        Requirements: 3.8
        """
        current_room = self.world.get_room(state.current_room)

        # Check if there are creatures that might respond to STAY
        creatures_here = [
            obj_id for obj_id in current_room.items
            if hasattr(self.world, 'get_object') and
            self.world.get_object(obj_id).type in ['creature', 'person']
        ]

        if creatures_here and state.sanity < 40:
            return ActionResult(
                success=True,
                message=f"You tell the creatures to stay, but they seem more interested in you. "
                       f"Maybe staying put wasn't the best idea when surrounded by things that "
                       f"want to eat you in this haunted place."
            )
        elif creatures_here:
            return ActionResult(
                success=True,
                message=f"You gesture for the creatures to stay. They pause, watching you with "
                       f"uncanny intelligence. For now, they remain where they are."
            )
        else:
            return ActionResult(
                success=True,
                message=f"You resolve to stay here in the {current_room.name}. "
                       f"The shadows seem pleased to have company. You wonder if staying put "
                       f"is really the wisest choice in a place that feeds on hesitation."
            )

    def handle_wind(self, object_id: str, state: GameState) -> ActionResult:
        """
        Handle WIND command for winding up objects.

        Winds up clockwork mechanisms, toys, or other windable objects.
        In haunted context, may interact with supernatural mechanics.

        Args:
            object_id: The object to windup (can be None for general winding)
            state: Current game state

        Returns:
            ActionResult with success status and haunted themed message

        Requirements: 3.3
        """
        if not object_id:
            return ActionResult(
                success=False,
                message="What do you want to wind? Specify a clockwork device or windable object."
            )

        try:
            # Check if object is in room or inventory
            current_room = self.world.get_room(state.current_room)
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory

            if not object_in_room and not object_in_inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here to wind."
                )

            # Get object
            wind_object = self.world.get_object(object_id)

            # Check if object can be wound
            is_windable = wind_object.state.get('windable', False)
            is_clockwork = 'clockwork' in wind_object.name.lower() or 'toy' in wind_object.name.lower()
            has_key = wind_object.state.get('has_key', False)

            if not is_windable and not is_clockwork:
                return ActionResult(
                    success=False,
                    message=f"The {wind_object.name} cannot be wound up. There's no winding mechanism."
                )

            # Check if object is already wound
            is_wound = wind_object.state.get('wound_up', False)
            if is_wound:
                return ActionResult(
                    success=False,
                    message=f"The {wind_object.name} is already fully wound. Winding it more might break it."
                )

            # Wind the object
            wind_object.state['wound_up'] = True
            wind_object.state['wind_turns'] = wind_object.state.get('wind_turns', 0) + 1

            # Apply winding effects
            wind_sound = wind_object.state.get('wind_sound', 'clicking sounds')
            wind_effect = wind_object.state.get('wind_effect', None)

            if state.sanity < 30:
                return ActionResult(
                    success=True,
                    message=f"You wind the {wind_object.name} frantically! The {wind_sound} sound distorted, "
                           f"like time itself is unraveling.{' ' + wind_effect if wind_effect else ''} "
                           f"The mechanism feels wrong, as if powered by nightmares.",
                    state_changes={'flags': {f'{object_id}_wound': True}}
                )
            else:
                return ActionResult(
                    success=True,
                    message=f"You carefully wind the {wind_object.name}. {wind_sound} fill the air. "
                           f"{' ' + wind_effect if wind_effect else ''}The clockwork mechanism seems ready.",
                    state_changes={'flags': {f'{object_id}_wound': True}}
                )

        except ValueError:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here to wind."
            )
        except Exception:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"The {display_name} resists being wound. The mechanism is stuck or "
                       f"supernaturally cold to the touch."
            )

    def handle_blow_out(self, object_id: str, state: GameState) -> ActionResult:
        """
        Handle BLOW OUT command for extinguishing flames or objects.

        Blows out candles, flames, or other light sources. More forceful
        than normal EXTINGUISH, using breath instead of action.

        Args:
            object_id: The object to blow out (can be None for general blowing)
            state: Current game state

        Returns:
            ActionResult with success status and haunted themed message

        Requirements: 3.6
        """
        if not object_id:
            if state.sanity < 25:
                return ActionResult(
                    success=True,
                    message="You blow out a long, shaky breath. The air ripples, and for a moment, "
                           "you see ghostly shapes in your exhalation. The house seems to breathe with you."
                )
            else:
                return ActionResult(
                    success=True,
                    message="You blow out a breath of air. Nothing much happens in these still, "
                           "haunted halls, but at least you're still breathing."
                )

        try:
            # Check if object is in room
            current_room = self.world.get_room(state.current_room)
            object_in_room = object_id in current_room.items

            if not object_in_room:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here to blow out."
                )

            # Get object
            blow_object = self.world.get_object(object_id)

            # Check if object can be blown out
            is_blowable = blow_object.state.get('blowable', False)
            has_flame = blow_object.state.get('on_fire', False)
            is_light_source = blow_object.state.get('light_source', False)
            is_candle = 'candle' in blow_object.name.lower() or 'torch' in blow_object.name.lower()

            if not (is_blowable or has_flame or is_light_source or is_candle):
                return ActionResult(
                    success=False,
                    message=f"You can't blow out the {blow_object.name}. It's not on fire or designed to be blown out."
                )

            # Blow out the object
            if has_flame or is_light_source:
                blow_object.state['on_fire'] = False
                blow_object.state['light_source'] = False
                blow_object.state['light_level'] = 0

                if state.sanity < 30:
                    return ActionResult(
                        success=True,
                        message=f"The {blow_object.name} sputters out as you blow on it! The flame dies with a "
                               f"final, desperate hiss. Darkness rushes in to fill the void. "
                               f"Something whispers your name in the sudden gloom."
                    )
                else:
                    return ActionResult(
                        success=True,
                        message=f"You blow out the {blow_object.name}. The flame extinguishes with a soft "
                               f"puff of smoke. The room grows darker, but your eyes adjust quickly."
                    )
            else:
                return ActionResult(
                    success=True,
                    message=f"You blow on the {blow_object.name} but nothing happens. "
                           f"Some things resist being changed by simple breath."
                )

        except ValueError:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here to blow out."
            )
        except Exception:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"Your breath fails you! The {display_name} remains unchanged, "
                       f"mocking your attempts to control it."
            )

    def handle_blow_up(self, object_id: str, state: GameState) -> ActionResult:
        """
        Handle BLOW UP command for inflating or exploding objects.

        Can either inflate objects (like balloons) or cause them to explode.
        The haunted version adds supernatural explosion effects.

        Args:
            object_id: The object to blow up
            state: Current game state

        Returns:
            ActionResult with success status and haunted themed message

        Requirements: 3.7, 4.4
        """
        if not object_id:
            return ActionResult(
                success=False,
                message="What do you want to blow up? Be more specific... the house takes things literally."
            )

        try:
            # Check if object is in room or inventory
            current_room = self.world.get_room(state.current_room)
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory

            if not object_in_room and not object_in_inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here to blow up."
                )

            # Get object
            blow_object = self.world.get_object(object_id)

            # Check what type of blow up this is
            is_inflatable = blow_object.state.get('inflatable', False)
            is_explosive = blow_object.state.get('explosive', False)
            is_balloon = 'balloon' in blow_object.name.lower()

            if is_inflatable or is_balloon:
                # Inflate the object
                is_inflated = blow_object.state.get('inflated', False)
                if is_inflated:
                    return ActionResult(
                        success=False,
                        message=f"The {blow_object.name} is already inflated! It might pop if you try to inflate it more."
                    )

                blow_object.state['inflated'] = True
                return ActionResult(
                    success=True,
                    message=f"You blow up the {blow_object.name}. It expands to its full size, "
                           f"ready for whatever purpose it serves in this haunted place."
                )

            elif is_explosive:
                # Explode the object
                explosion_radius = blow_object.state.get('explosion_radius', 3)
                damage_type = blow_object.state.get('damage_type', 'magical')

                if state.sanity < 30:
                    return ActionResult(
                        success=True,
                        message=f"You trigger the {blow_object.name} and it EXPLODES! {damage_type.title()} "
                               f"energy blasts outward in a {explosion_radius}-foot radius. "
                               f"Reality itself seems to warp in the aftermath. The house feeds on the chaos.",
                        state_changes={'sanity': max(0, state.sanity - 10)}
                    )
                else:
                    return ActionResult(
                        success=True,
                        message=f"The {blow_object.name} explodes violently! {damage_type.title()} fragments "
                               f"fly everywhere. The explosion shakes the foundations and echoes through the halls."
                    )

            else:
                return ActionResult(
                    success=False,
                    message=f"You can't blow up the {blow_object.name}. It's not inflatable or explosive."
                )

        except ValueError:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here to blow up."
            )
        except Exception:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"Something goes wrong with the {display_name}! Better back away before it "
                       f"does something unexpected in this haunted place."
            )

    def handle_send_for(self, target: str, state: GameState) -> ActionResult:
        """
        Handle SEND FOR command for summoning or calling entities.

        Attempts to summon, call, or send for creatures, people, or supernatural entities.
        In haunted context, may contact spirits or call forth aid from beyond.

        Args:
            target: What or who to send for
            state: Current game state

        Returns:
            ActionResult with success status and haunted themed message

        Requirements: 4.6, 5.9
        """
        if not target:
            return ActionResult(
                success=False,
                message="Who or what do you want to send for? The house listens to your call..."
            )

        current_room = self.world.get_room(state.current_room)
        target_lower = target.lower()

        # Check for common summoning targets
        if target_lower in ['help', 'assistance', 'aid', 'rescue']:
            if state.sanity < 30:
                return ActionResult(
                    success=True,
                    message="You cry out for help, but only shadows answer. "
                           "Whispers echo back your pleas, twisted into mockery. "
                           "No help is coming in this place.",
                    state_changes={'sanity': max(0, state.sanity - 2)}
                )
            elif state.sanity < 60:
                return ActionResult(
                    success=True,
                    message=f"You call for {target}! Your voice echoes through the haunted halls. "
                           f"Something stirs in the darkness, but it doesn't sound like help. "
                           f"Maybe be more specific about who you want to summon."
                )
            else:
                return ActionResult(
                    success=True,
                    message=f"You call out for {target}. The house remains silent, "
                           f"as if contemplating your request. Some forces cannot be summoned lightly."
                )

        elif target_lower in ['ghost', 'spirit', 'specter', 'phantom']:
            if state.sanity < 25:
                return ActionResult(
                    success=True,
                    message=f"You attempt to summon a {target}! The shadows deepen and coalesce "
                           f"around you. You've attracted attention, but not the kind you wanted. "
                           f"Multiple spectral forms now watch you with hunger.",
                    state_changes={'sanity': max(0, state.sanity - 8)}
                )
            else:
                return ActionResult(
                    success=True,
                    message=f"You call for a {target}. A cold spot forms in the room, and you feel "
                           f"an otherworldly presence. The spirit doesn't speak, but acknowledges your call. "
                           f"What do you want with it?"
                )

        elif target_lower in ['servant', 'butler', 'maid', 'assistant']:
            if current_room.state.get('has_bell', False):
                return ActionResult(
                    success=True,
                    message=f"You send for a {target}! A bell rings faintly in the distance. "
                           f"Footsteps approach, then stop. The house remembers its old servants, "
                           f"but they may not be what you expect anymore."
                )
            else:
                return ActionResult(
                    success=True,
                    message=f"You call for a {target}, but no one answers. "
                           f"In this haunted place, the servants have long since departed "
                           f"... or have they?"
                )

        elif any(creature_name in target_lower for creature_name in ['dog', 'cat', 'animal', 'beast']):
            return ActionResult(
                success=True,
                message=f"You call for a {target}. Something rustles in the shadows, "
                       f"but when it emerges, it's not quite the animal you expected. "
                       f"The house's pets are... unusual."
            )

        else:
            # Generic summoning attempt
            if state.sanity < 40:
                return ActionResult(
                    success=True,
                    message=f"You send for {target}! The ground trembles slightly and the air grows thick. "
                           f"You sense that your call was answered, but not by {target}. "
                           f"Something else came instead.",
                    state_changes={'sanity': max(0, state.sanity - 5)}
                )
            else:
                return ActionResult(
                    success=True,
                    message=f"You attempt to send for {target}. Your voice carries through the haunted halls, "
                           f"but the only response is the settling dust and distant, unsettling whispers. "
                           f"Perhaps this isn't the right place for summoning allies."
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
                message="The cursed treasure resists being placed, as if it yearns to remain with you."
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
                display_name = self._get_object_names(target_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )
            
            # Get target object
            target = self.world.get_object(target_id)
            
            # Check if target is a creature
            is_creature = target.state.get('is_creature', False)
            
            if not is_creature:
                display_name = self._get_object_names(target_id)
                return ActionResult(
                    success=False,
                    message=f"You can't attack the {display_name}."
                )
            
            # Check if weapon is specified and in inventory
            weapon = None
            weapon_damage = 1  # Base damage for bare hands
            weapon_name = "your bare hands"
            
            if weapon_id:
                if weapon_id not in state.inventory:
                    display_name = self._get_object_names(weapon_id)
                    return ActionResult(
                        success=False,
                        message=f"You don't have the {display_name}."
                    )
                
                weapon = self.world.get_object(weapon_id)
                
                # Check if object is actually a weapon
                is_weapon = weapon.state.get('is_weapon', False)
                
                if not is_weapon:
                    display_name = self._get_object_names(weapon_id)
                    return ActionResult(
                        success=False,
                        message=f"The {display_name} is not a weapon."
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
                message="The spectral forces intervene, disrupting your attack in a swirl of darkness."
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
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't have the {display_name}."
                )
            
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if target is in current room
            if target_id not in current_room.items:
                target_display_name = self._get_object_names(target_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {target_display_name} here."
                )
            
            # Get object and target
            game_object = self.world.get_object(object_id)
            target = self.world.get_object(target_id)
            
            # Check if object is throwable
            is_throwable = game_object.state.get('is_throwable', True)  # Most objects can be thrown
            
            if not is_throwable:
                return ActionResult(
                    success=False,
                    message=f"You can't throw the {game_object.name}."
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
                message="The object slips from your grasp mid-throw, vanishing into the shadows."
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
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't have the {display_name}."
                )
            
            # Get current room
            current_room = self.world.get_room(state.current_room)
            
            # Check if NPC is in current room
            if npc_id not in current_room.items:
                display_name = self._get_object_names(npc_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )
            
            # Get object and NPC
            game_object = self.world.get_object(object_id)
            npc = self.world.get_object(npc_id)
            
            # Check if target is an NPC
            is_npc = npc.state.get('is_npc', False)
            is_creature = npc.state.get('is_creature', False)
            
            if not is_npc and not is_creature:
                display_name = self._get_object_names(npc_id)
                return ActionResult(
                    success=False,
                    message=f"You can't give things to the {display_name}."
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
            display_name = self._get_object_names(npc_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="The cursed object refuses to leave your possession, clinging to you with unnatural force."
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
                message="Your words seem to dissolve into the air, unheard by mortal or spirit."
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
                message="The creature remains in its cursed slumber, beyond the reach of mortal intervention."
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
                message="The shadows seem to recoil from your advance, leaving only cold emptiness."
            )
    
    def handle_save(
        self,
        state: GameState
    ) -> ActionResult:
        """
        Handle saving the current game state.
        
        Serializes current game state to JSON and stores in DynamoDB with
        unique save ID. Includes timestamp and session info. Returns success
        message with save ID.
        
        Args:
            state: Current game state
            
        Returns:
            ActionResult with success status and save ID
            
        Requirements: 7.1
        """
        try:
            # Generate a unique save ID
            import uuid
            save_id = str(uuid.uuid4())[:8]  # Use first 8 chars for readability
            
            # Create a save key in the flags
            save_key = f"save_{save_id}"
            
            # Store the save ID in the state flags for reference
            state.set_flag(save_key, True)
            state.set_flag('last_save_id', save_id)
            
            # The actual saving to DynamoDB happens in the Lambda handler
            # This method just marks the state as ready to save
            
            return ActionResult(
                success=True,
                message=f"Game saved successfully. Your save ID is: {save_id}\n\nYou can restore this game later using the RESTORE command.",
                state_changes={
                    'flags': state.flags
                }
            )
            
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"Failed to save game: {str(e)}"
            )
    
    def handle_restore(
        self,
        save_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle restoring a previously saved game state.
        
        Loads game state from DynamoDB by save ID, deserializes JSON to
        GameState object, validates save data integrity, and returns success
        message.
        
        Args:
            save_id: The save ID to restore
            state: Current game state (will be replaced)
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 7.2
        """
        try:
            # Check if save ID exists in flags
            save_key = f"save_{save_id}"
            save_exists = state.get_flag(save_key, False)
            
            if not save_exists:
                return ActionResult(
                    success=False,
                    message=f"Save ID '{save_id}' not found. Please check the ID and try again."
                )
            
            # The actual restoration from DynamoDB happens in the Lambda handler
            # This method just validates the save ID
            
            return ActionResult(
                success=True,
                message=f"Game restored successfully from save ID: {save_id}\n\nWelcome back to the haunted house...",
                state_changes={
                    'current_room': state.current_room,
                    'inventory': state.inventory,
                    'sanity': state.sanity,
                    'score': state.score
                }
            )
            
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"Failed to restore game: {str(e)}"
            )
    
    def handle_restart(
        self,
        state: GameState
    ) -> ActionResult:
        """
        Handle restarting the game from the beginning.
        
        Resets game state to initial values, clears inventory, flags, and
        score, returns to starting room, and returns confirmation message.
        
        Args:
            state: Current game state
            
        Returns:
            ActionResult with success status and message
            
        Requirements: 7.3
        """
        try:
            # Reset to initial state
            starting_room = "west_of_house"
            
            # Clear inventory
            state.inventory.clear()
            
            # Reset flags
            state.flags.clear()
            
            # Reset statistics
            state.score = 0
            state.moves = 0
            state.turn_count = 0
            
            # Reset Halloween mechanics
            state.sanity = 100
            state.cursed = False
            state.blood_moon_active = True
            state.souls_collected = 0
            state.curse_duration = 0
            
            # Reset lamp
            state.lamp_battery = 200
            
            # Reset other state
            state.lucky = False
            state.thief_here = False
            state.current_vehicle = None
            
            # Clear visited rooms
            state.rooms_visited.clear()
            
            # Clear object states (reset containers, etc.)
            state.object_states.clear()
            
            # Move to starting room
            state.move_to_room(starting_room)
            
            # Get starting room description
            description = self.world.get_room_description(starting_room, state.sanity)
            
            restart_message = "The world dissolves around you, and you find yourself back where it all began...\n\n"
            restart_message += description
            
            return ActionResult(
                success=True,
                message=restart_message,
                room_changed=True,
                new_room=starting_room,
                inventory_changed=True,
                state_changes={
                    'current_room': state.current_room,
                    'inventory': state.inventory,
                    'flags': state.flags,
                    'score': state.score,
                    'moves': state.moves,
                    'sanity': state.sanity,
                    'turn_count': state.turn_count
                }
            )
            
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"Failed to restart game: {str(e)}"
            )
    
    def handle_score(
        self,
        state: GameState
    ) -> ActionResult:
        """
        Handle displaying the current score and rank.
        
        Displays current score and rank, calculates rank based on score
        thresholds, shows treasures collected, and returns formatted score
        display.
        
        Args:
            state: Current game state
            
        Returns:
            ActionResult with success status and score display
            
        Requirements: 7.5
        """
        try:
            score = state.score
            moves = state.moves
            
            # Calculate rank based on score thresholds
            if score >= 350:
                rank = "Master Adventurer"
            elif score >= 300:
                rank = "Experienced Adventurer"
            elif score >= 200:
                rank = "Adventurer"
            elif score >= 100:
                rank = "Junior Adventurer"
            elif score >= 50:
                rank = "Novice Adventurer"
            else:
                rank = "Beginner"
            
            # Count treasures collected (items in trophy case)
            treasures_collected = 0
            try:
                trophy_case = self.world.get_object("trophy_case")
                contents = trophy_case.state.get('contents', [])
                treasures_collected = len(contents)
            except ValueError:
                pass
            
            # Format score display with haunted theme
            score_message = f"Your score is {score} out of 350 possible points.\n"
            score_message += f"You have made {moves} moves.\n"
            score_message += f"Your rank is: {rank}\n"
            score_message += f"Treasures collected: {treasures_collected}\n"
            score_message += f"Sanity: {state.sanity}/100\n"
            score_message += f"Souls collected: {state.souls_collected}\n"
            
            if state.cursed:
                score_message += "\nYou are cursed!"
            
            if state.blood_moon_active:
                score_message += "\nThe blood moon hangs heavy in the sky..."
            
            return ActionResult(
                success=True,
                message=score_message
            )
            
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"Failed to display score: {str(e)}"
            )
    
    def handle_verbose(
        self,
        state: GameState
    ) -> ActionResult:
        """
        Handle setting verbosity to VERBOSE mode.
        
        Sets verbosity field to VERBOSE (always show full descriptions).
        Returns confirmation message.
        
        Args:
            state: Current game state
            
        Returns:
            ActionResult with success status and confirmation
            
        Requirements: 7.6
        """
        try:
            # Set verbosity to VERBOSE
            state.set_flag('verbosity', 'verbose')
            
            return ActionResult(
                success=True,
                message="Verbose mode enabled. You will now see full room descriptions every time.",
                state_changes={
                    'flags': state.flags
                }
            )
            
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"Failed to set verbosity: {str(e)}"
            )
    
    def handle_brief(
        self,
        state: GameState
    ) -> ActionResult:
        """
        Handle setting verbosity to BRIEF mode.
        
        Sets verbosity field to BRIEF (full on first visit, abbreviated after).
        Returns confirmation message.
        
        Args:
            state: Current game state
            
        Returns:
            ActionResult with success status and confirmation
            
        Requirements: 7.7
        """
        try:
            # Set verbosity to BRIEF
            state.set_flag('verbosity', 'brief')
            
            return ActionResult(
                success=True,
                message="Brief mode enabled. You will see full descriptions on first visit, then abbreviated descriptions.",
                state_changes={
                    'flags': state.flags
                }
            )
            
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"Failed to set verbosity: {str(e)}"
            )
    
    def handle_superbrief(
        self,
        state: GameState
    ) -> ActionResult:
        """
        Handle setting verbosity to SUPERBRIEF mode.
        
        Sets verbosity field to SUPERBRIEF (room name only).
        Returns confirmation message.
        
        Args:
            state: Current game state
            
        Returns:
            ActionResult with success status and confirmation
            
        Requirements: 7.8
        """
        try:
            # Set verbosity to SUPERBRIEF
            state.set_flag('verbosity', 'superbrief')
            
            return ActionResult(
                success=True,
                message="Superbrief mode enabled. You will only see room names.",
                state_changes={
                    'flags': state.flags
                }
            )
            
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"Failed to set verbosity: {str(e)}"
            )
    
    def _handle_unknown_command(
        self,
        command: ParsedCommand,
        state: GameState
    ) -> ActionResult:
        """
        Handle unknown commands with helpful suggestions.
        
        Provides clear feedback when a command is not recognized,
        suggesting alternative commands the player might try.
        
        Args:
            command: The parsed command with UNKNOWN verb
            state: Current game state
            
        Returns:
            ActionResult with helpful error message
            
        Requirements: 9.1
        """
        # Get the raw input if available
        raw_input = command.object if command.object else "that"
        
        # Provide helpful suggestions based on common patterns
        suggestions = [
            "Try commands like:",
            "  • Movement: 'go north', 'south', 'enter', 'climb up'",
            "  • Objects: 'take lamp', 'examine mailbox', 'open door'",
            "  • Utility: 'inventory', 'look', 'score'"
        ]
        
        message = f"I don't understand '{raw_input}'.\n\n" + "\n".join(suggestions)
        
        return ActionResult(
            success=False,
            message=message
        )
    
    def _handle_unimplemented_command(
        self,
        command: ParsedCommand,
        state: GameState
    ) -> ActionResult:
        """
        Handle recognized but unimplemented commands.
        
        Provides specific feedback when a command is recognized but not yet
        available, and suggests alternative commands when appropriate.
        
        Args:
            command: The parsed command
            state: Current game state
            
        Returns:
            ActionResult with specific error message and suggestions
            
        Requirements: 9.1
        """
        verb = command.verb.lower().replace('_', ' ')
        
        # Provide context-specific suggestions based on verb type
        suggestions = []
        
        # Movement-related commands
        if command.verb in ['WALK_TO', 'RUN_TO', 'TRAVEL_TO']:
            suggestions = [
                "Try using directional commands instead:",
                "  • 'go north', 'south', 'east', 'west'",
                "  • 'up', 'down', 'in', 'out'"
            ]
        
        # Object interaction commands
        elif command.verb in ['USE', 'APPLY', 'OPERATE']:
            suggestions = [
                "Try being more specific:",
                "  • 'open <object>', 'turn <object>'",
                "  • 'push <object>', 'pull <object>'"
            ]
        
        # Communication commands
        elif command.verb in ['SAY', 'SPEAK', 'TALK']:
            suggestions = [
                "Try these communication commands:",
                "  • 'tell <npc> about <topic>'",
                "  • 'ask <npc> about <topic>'"
            ]
        
        # Default suggestions
        else:
            suggestions = [
                "This command is recognized but not yet available.",
                "Try alternative commands like:",
                "  • 'examine <object>' to inspect things",
                "  • 'take <object>' or 'drop <object>'",
                "  • 'open <object>' or 'close <object>'"
            ]
        
        message = f"The '{verb}' command is not yet implemented.\n\n" + "\n".join(suggestions)
        
        return ActionResult(
            success=False,
            message=message
        )
    
    def _handle_missing_object(
        self,
        object_name: str,
        state: GameState,
        verb: Optional[str] = None
    ) -> ActionResult:
        """
        Handle commands referencing missing objects with enhanced guidance.

        Provides clear, contextual information about missing objects
        and suggests alternatives based on the current location and verb.

        Args:
            object_name: The name of the missing object
            state: Current game state
            verb: Optional verb for contextual suggestions

        Returns:
            ActionResult with enhanced error message

        Requirements: 9.3
        """
        # Get current room information
        try:
            current_room = self.world.get_room(state.current_room)
            room_items = current_room.items
            inventory_items = state.inventory
        except Exception:
            room_items = []
            inventory_items = []

        # Check if object exists in the game world at all
        try:
            obj = self.world.get_object(object_name)
            # Object exists but not here
            display_name = obj.name if obj.name else object_name
            message = f"You don't see any {display_name} here."

            # Check if object might be in inventory
            if object_name.lower() in [item.lower() for item in inventory_items]:
                message = f"You already have the {object_name}."
            # Check if object is in room but different name used
            elif any(object_name.lower() in self._get_object_names(item).lower()
                     for item in room_items):
                message = f"Be more specific. What {object_name} do you mean?"
            # Provide contextual hints
            else:
                # Check for similar objects in room
                similar_objects = self._find_similar_objects(object_name, room_items)
                if similar_objects:
                    if len(similar_objects) == 1:
                        message += f"\n\nDo you mean the {similar_objects[0]}?"
                    else:
                        obj_list = ", ".join(similar_objects)
                        message += f"\n\nI see: {obj_list}"

                # Suggest looking around
                if room_items:
                    message += f"\n\nTake a look around - you might find what you're seeking."
                else:
                    message += f"\n\nThe shadows here seem to swallow everything whole..."

        except ValueError:
            # Object doesn't exist in game - try to suggest alternatives
            message = f"I don't know what '{object_name}' is."

            # Look for similar object names in room and inventory
            all_objects = room_items + inventory_items
            similar_objects = self._find_similar_objects(object_name, all_objects)

            if similar_objects:
                if len(similar_objects) == 1:
                    message += f" Do you mean the {similar_objects[0]}?"
                else:
                    obj_list = ", ".join(similar_objects)
                    message += f" Perhaps you mean one of: {obj_list}"

        # Add verb-specific suggestions
            if verb.lower() in ['take', 'get', 'carry']:
                if room_items:
                    takeable_names = [self._get_object_names(item) for item in room_items[:3]]
                    message += f"\n\nYou could try taking: {', '.join(takeable_names)}"
            elif verb.lower() in ['open', 'close']:
                openable_objects = [self._get_object_names(item) for item in room_items + inventory_items
                                  if self._is_openable(item)]
                if openable_objects:
                    message += f"\n\nYou might try opening: {', '.join(openable_objects[:3])}"
            elif verb.lower() in ['examine', 'look', 'check']:
                if room_items:
                    examine_names = [self._get_object_names(item) for item in room_items[:3]]
                    message += f"\n\nYou can examine: {', '.join(examine_names)}"

        # General help
        message += "\n\nType 'look' to see your surroundings or 'inventory' to check your possessions."

        return ActionResult(
            success=False,
            message=message
        )

    def _get_object_names(self, object_id: str) -> str:
        """Get display names for an object."""
        try:
            obj = self.world.get_object(object_id)
            return obj.name if obj.name else object_id
        except:
            return object_id

    def _is_openable(self, object_id: str) -> bool:
        """Check if object can be opened."""
        try:
            obj = self.world.get_object(object_id)
            return obj.type == "container" or obj.state.get('can_open', False)
        except:
            return False

    def _find_similar_objects(self, target: str, object_list: List[str]) -> List[str]:
        """Find objects with similar names to target."""
        target_lower = target.lower()
        similar = []

        for obj_id in object_list:
            try:
                obj = self.world.get_object(obj_id)
                obj_names = [obj.name.lower()] if obj.name else [obj_id.lower()]

                # Check for partial matches or contains
                for name in obj_names:
                    if (target_lower in name or name in target_lower or
                        (len(target) > 3 and name.startswith(target_lower[:3]))):
                        if obj.name not in similar:
                            similar.append(obj.name)
            except:
                # If object not found, check ID directly
                if target_lower in obj_id.lower() or obj_id.lower().startswith(target_lower[:3]):
                    if obj_id not in similar:
                        similar.append(obj_id)

        return similar[:3]  # Limit to 3 suggestions

    def _should_validate_object(self, verb: str) -> bool:
        """
        Determine if an object should be validated for this verb.

        Some verbs like 'LOOK' or 'INVENTORY' don't require object validation
        as they have their own special handling.
        """
        # Verbs that don't need object validation
        no_validation_verbs = {
            'LOOK', 'INVENTORY', 'I', 'SCORE', 'RESTART', 'SAVE', 'RESTORE',
            'VERBOSE', 'BRIEF', 'SUPERBRIEF', 'HELP', 'QUIT', 'XYZZY', 'PLUGH',
            'HELLO', 'PRAY', 'JUMP', 'YELL', 'CURSE', 'LISTEN', 'SMELL'
        }

        # Verbs that handle their own validation internally
        self_validating_verbs = {
            'GO', 'EXIT', 'ENTER', 'BOARD', 'DISEMBARK'
        }

        return verb not in no_validation_verbs and verb not in self_validating_verbs

    def _handle_impossible_action(
        self,
        action: str,
        reason: str,
        hint: Optional[str] = None,
        object_id: Optional[str] = None,
        state: Optional[GameState] = None
    ) -> ActionResult:
        """
        Handle impossible actions with enhanced explanations.

        Explains why an action cannot be performed with thematic
        language and contextual hints for the haunted setting.

        Args:
            action: Description of the attempted action
            reason: Why the action is impossible
            hint: Optional hint for the player
            object_id: Optional object being acted upon for context
            state: Optional game state for additional context

        Returns:
            ActionResult with enhanced explanation

        Requirements: 9.4
        """
        # Add haunted atmosphere to explanations
        haunted_reasons = [
            "the shadows resist your will",
            "otherworldly forces prevent it",
            "the very air grows cold at the thought",
            "ancient curses bind this place",
            "the spirits will not allow it",
            "dark magic holds it fast",
            "your fingers pass through like smoke",
            "an invisible barrier blocks your way"
        ]

        # Create thematic explanation
        if "locked" in reason.lower():
            message = f"The {object_id if object_id else 'object'} is sealed tight."
            if hint:
                message += f" {hint}"
            else:
                message += " Perhaps there's a key hidden somewhere in these haunted halls."
        elif "heavy" in reason.lower():
            message = f"Your supernatural strength isn't enough to {action}."
            message += f" The object seems anchored by more than mere weight."
        elif "darkness" in reason.lower() or "can't see" in reason.lower():
            message = f"You grope blindly in the oppressive darkness."
            message += " Who knows what horrors await the unwary in this blackness?"
        else:
            # Add haunted flavor to generic reasons
            if state and state.sanity < 30:
                # Low sanity adds to the atmosphere
                message = f"You try to {action}, but {reason}."
                message += f" The walls seem to whisper mocking laughter..."
            else:
                message = f"You cannot {action}. {reason}"

        # Add contextual hints based on action type
        if not hint:
            action_lower = action.lower()
            if any(word in action_lower for word in ['open', 'unlock']):
                message += "\n\nPerhaps you need to find something to help with that."
            elif any(word in action_lower for word in ['move', 'push', 'pull']):
                message += "\n\nSometimes the solution requires thinking rather than force."
            elif any(word in action_lower for word in ['read', 'examine']):
                message += "\n\nYour eyes strain in the gloom. Perhaps more light would help?"

        # Add hint if provided
        if hint:
            message += f"\n\n{hint}"

        return ActionResult(
            success=False,
            message=message
        )
    
    def _validate_command_syntax(
        self,
        command: ParsedCommand,
        state: GameState
    ) -> Optional[ActionResult]:
        """
        Validate command syntax and provide usage guidance.

        Detects common syntax errors and provides helpful suggestions
        for correct usage based on command patterns.

        Args:
            command: The parsed command to validate
            state: Current game state

        Returns:
            ActionResult with usage guidance if syntax error detected,
            None if command syntax is valid

        Requirements: 9.2
        """
        verb = command.verb

        # Commands that require an object
        object_required_verbs = {
            'TAKE', 'DROP', 'EXAMINE', 'OPEN', 'CLOSE', 'READ', 'LOCK', 'UNLOCK',
            'TURN', 'PUSH', 'PULL', 'TIE', 'UNTIE', 'FILL', 'POUR', 'BURN', 'CUT',
            'DIG', 'INFLATE', 'DEFLATE', 'WAVE', 'RUB', 'SHAKE', 'SQUEEZE',
            'ATTACK', 'THROW', 'GIVE', 'TELL', 'ASK', 'WAKE', 'KISS', 'BOARD',
            'ENTER', 'CLIMB'
        }

        # Commands that can accept optional object
        object_optional_verbs = {
            'LOOK', 'SEARCH', 'LISTEN', 'SMELL', 'ECHO'
        }

        # Commands that require a target/preposition
        target_required_verbs = {
            'GIVE': 'Who do you want to give the object to?',
            'PUT': 'Where do you want to put the object?',
            'THROW': 'What do you want to throw the object at?',
            'TELL': 'Who do you want to talk to?',
            'ASK': 'Who do you want to ask?'
        }

        # Check if verb requires an object but none provided
        if verb in object_required_verbs and not command.object and not command.objects:
            return self._handle_missing_parameter(
                verb.lower(),
                f"an object to {verb.lower()}",
                self._get_usage_examples(verb),
                state
            )

        # Check if verb requires specific preposition structure
        if verb in ['TAKE'] and command.preposition == 'FROM' and not command.target:
            return self._handle_missing_parameter(
                verb.lower(),
                "a container to take from",
                ["take key from chest", "get sword from pedestal"],
                state
            )

        # Check for GO command without direction
        if verb == 'GO' and not command.direction:
            return self._handle_missing_parameter(
                verb.lower(),
                "a direction to go",
                ["go north", "go south", "go up", "go down"],
                state
            )

        # Check for invalid preposition usage
        if verb == 'TAKE' and command.preposition and command.preposition not in ['FROM']:
            return self._handle_incorrect_usage(
                f'take {command.preposition.lower()}',
                'TAKE <object> [FROM <container>]',
                'take key, take sword from chest'
            )

        # Check for GIVE without target
        if verb == 'GIVE' and not command.target:
            return self._handle_missing_parameter(
                verb.lower(),
                "someone to give the object to",
                ["give lantern to thief", "give leaflet to ghost"],
                state
            )

        # Check for TURN without object
        if verb == 'TURN' and not command.object and not command.direction:
            return self._handle_missing_parameter(
                verb.lower(),
                "something to turn or a direction",
                ["turn dial", "turn wheel", "turn left", "turn right"],
                state
            )

        # Check for LOOK with invalid structure
        if verb == 'LOOK' and command.preposition:
            valid_look_preps = ['IN', 'INSIDE', 'UNDER', 'BEHIND', 'AT', 'ON']
            if command.preposition not in valid_look_preps:
                return self._handle_incorrect_usage(
                    f'look {command.preposition.lower()}',
                    'LOOK [IN/INSIDE/UNDER/BEHIND/AT/ON] <object>',
                    'look in chest, look under table, look at painting'
                )

        return None

    def handle_wear(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle wearing equipment and clothing items.

        Allows players to wear wearable items like clothing, armor, and accessories.
        Maintains a worn equipment system and prevents wearing non-wearable items.
        Provides haunted atmosphere messages and sanity integration.

        Args:
            object_id: The object to wear
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 4.4
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if object is in inventory
            if object_id not in state.inventory:
                if object_id in current_room.items:
                    display_name = self._get_object_names(object_id)
                    return ActionResult(
                        success=False,
                        message=f"You need to take the {display_name} first before you can wear it."
                    )
                else:
                    display_name = self._get_object_names(object_id)
                    return ActionResult(
                        success=False,
                        message=f"You don't have the {display_name}."
                    )

            # Get object data
            game_object = self.world.get_object(object_id)

            # Check if object can be worn
            is_wearable = game_object.state.get('wearable', False)

            if not is_wearable:
                # Thematic messages for non-wearable items
                wearable_messages = [
                    f"You can't wear the {game_object.name}. It's not designed to be worn.",
                    f"The {game_object.name} resists your attempts to wear it. Some things were never meant as clothing.",
                    f"You try to wear the {game_object.name}, but it simply doesn't fit or function as apparel.",
                    f"The spirits mock your attempt to wear the {game_object.name}. Not everything is clothing, you know."
                ]

                if state.sanity < 30:
                    wearable_messages.append(f"You desperately try to wear the {game_object.name}, but the shadows prevent such foolishness.")

                import random
                return ActionResult(
                    success=False,
                    message=random.choice(wearable_messages)
                )

            # Check if already worn
            is_worn = game_object.state.get('worn', False)

            if is_worn:
                return ActionResult(
                    success=False,
                    message=f"You are already wearing the {game_object.name}."
                )

            # Initialize worn equipment list if not present
            if not hasattr(state, 'worn_equipment'):
                state.worn_equipment = []

            # Wear the object
            game_object.state['worn'] = True
            if object_id not in state.worn_equipment:
                state.worn_equipment.append(object_id)

            # Success messages with haunted atmosphere
            if state.sanity < 30:
                messages = [
                    f"The {game_object.name} settles upon you with an unnatural weight. You feel changed... somehow.",
                    f"You don the {game_object.name}. For a moment, you glimpse yourself in someone else's eyes.",
                    f"The {game_object.name} wraps around you like a shroud. The darkness feels more... comfortable now.",
                    f"Wearing the {game_object.name}, you hear faint whispers of approval from the void."
                ]
            else:
                messages = [
                    f"You put on the {game_object.name}. It fits surprisingly well.",
                    f"You are now wearing the {game_object.name}.",
                    f"The {game_object.name} is quite comfortable once you get used to it.",
                    f"You adjust the {game_object.name} until it sits just right."
                ]

            import random
            notifications = []

            # Check for special effects
            protection = game_object.state.get('protection', 0)
            if protection > 0:
                notifications.append(f"The {game_object.name} offers some protection against the house's malevolence.")

            curse = game_object.state.get('curse_on_wear', False)
            if curse:
                notifications.append(f"A sense of dread accompanies wearing the {game_object.name}.")
                # Small sanity penalty for cursed items
                sanity_change = -2
            else:
                sanity_change = 0

            return ActionResult(
                success=True,
                message=random.choice(messages),
                notifications=notifications,
                sanity_change=sanity_change
            )

        except ValueError as e:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't have the {display_name}."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something prevents you from wearing that item.",
                room_changed=False
            )

    def handle_remove(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle removing worn equipment and clothing items.

        Allows players to remove worn items, returning them to inventory.
        Prevents removing items that aren't worn and handles cursed items.
        Provides haunted atmosphere messages and sanity integration.

        Args:
            object_id: The object to remove
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 4.4
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Get object data
            game_object = self.world.get_object(object_id)

            # Check if object can be worn
            is_wearable = game_object.state.get('wearable', False)

            if not is_wearable:
                return ActionResult(
                    success=False,
                    message=f"The {game_object.name} isn't something you can wear or remove."
                )

            # Check if currently worn
            is_worn = game_object.state.get('worn', False)

            if not is_worn:
                return ActionResult(
                    success=False,
                    message=f"You aren't wearing the {game_object.name}."
                )

            # Check for cursed items that resist removal
            curse_resists = game_object.state.get('cursed', False) or game_object.state.get('curse_on_wear', False)

            if curse_resists:
                # Chance-based removal for cursed items
                import random
                if random.random() < 0.7:  # 70% chance of failure
                    curse_messages = [
                        f"The {game_object.name} refuses to be removed! It clings to you with supernatural strength.",
                        f"You try to remove the {game_object.name}, but an unseen force holds it in place.",
                        f"The {game_object.name} tightens its grip on you. It seems to have plans for you.",
                        f"Spectral hands restrain your attempts to remove the {game_object.name}."
                    ]

                    if state.sanity < 30:
                        curse_messages.append(f"The {game_object.name} whispers that you will never be free of it.")

                    return ActionResult(
                        success=False,
                        message=random.choice(curse_messages),
                        sanity_change=-1  # Sanity loss from cursed item resistance
                    )

            # Remove the object
            game_object.state['worn'] = False

            # Update worn equipment list
            if hasattr(state, 'worn_equipment') and object_id in state.worn_equipment:
                state.worn_equipment.remove(object_id)

            # Success messages with haunted atmosphere
            if state.sanity < 30:
                messages = [
                    f"You remove the {game_object.name}. For a terrible moment, you feel utterly exposed and vulnerable.",
                    f"The {game_object.name} comes away with a reluctant sigh. The air grows colder against your skin.",
                    f"Removing the {game_object.name} feels like shedding a second skin. You shudder uncontrollably.",
                    f"The {game_object.name} finally releases its hold on you. You feel... lighter, but also more fragile."
                ]
            else:
                messages = [
                    f"You take off the {game_object.name}.",
                    f"You remove the {game_object.name}.",
                    f"The {game_object.name} is removed.",
                    f"You slip out of the {game_object.name}."
                ]

            import random
            notifications = []

            # Check for special effects when removing
            if curse_resists:
                notifications.append(f"You feel a sense of relief as the cursed influence fades.")
                # Small sanity restoration for removing cursed items
                sanity_change = 2
            else:
                sanity_change = 0

            return ActionResult(
                success=True,
                message=random.choice(messages),
                notifications=notifications,
                sanity_change=sanity_change
            )

        except ValueError as e:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something prevents you from removing that item.",
                room_changed=False
            )

    def handle_eat(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle eating food items and consumables.

        Allows players to eat edible items, consuming them and providing
        nourishment or special effects. Handles cursed food, health benefits,
        and hunger management with haunted atmosphere messages.

        Args:
            object_id: The object to eat
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 4.5
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if object is in inventory or current room
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory

            if not object_in_room and not object_in_inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't have the {display_name}."
                )

            # If object is in room but not inventory, require taking it first
            if object_in_room and not object_in_inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You need to take the {display_name} first before you can eat it."
                )

            # Get object data
            game_object = self.world.get_object(object_id)

            # Check if object can be eaten
            is_edible = game_object.state.get('edible', False)
            food_type = game_object.state.get('food_type', 'food')

            if not is_edible:
                # Thematic messages for non-edible items
                inedible_messages = [
                    f"You can't eat the {game_object.name}! It's not food.",
                    f"That's plainly inedible! Even your hunger pangs won't help you eat {game_object.name}.",
                    f"The spirits whisper that {game_object.name} was never meant for consumption.",
                    f"You try to eat the {game_object.name}, but your teeth find no purchase. It's not edible."
                ]

                if state.sanity < 30:
                    inedible_messages.append(f"In your desperation, you consider eating the {game_object.name}, but wisdom prevails.")

                import random
                return ActionResult(
                    success=False,
                    message=random.choice(inedible_messages)
                )

            # Get food properties
            nutrition = game_object.state.get('nutrition', 0)
            cursed = game_object.state.get('cursed', False)
            poison = game_object.state.get('poison', False)
            magic_effect = game_object.state.get('magic_effect', None)

            # Handle cursed food
            if cursed:
                curse_messages = [
                    f"As you eat the {game_object.name}, an unnatural cold spreads through your veins.",
                    f"The {game_object.name} tastes of ashes and regret. A curse takes hold!",
                    f"You consume the {game_object.name} and feel your very essence being tainted.",
                    f"The {game_object.name} was cursed! You feel a malignant force invade your body."
                ]

                if state.sanity < 30:
                    curse_messages.append(f"The cursed {game_object.name} welcomes your despair. You were already lost.")

                import random

                # Remove from inventory after eating
                state.inventory.remove(object_id)

                return ActionResult(
                    success=True,
                    message=random.choice(curse_messages),
                    notifications=[f"The curse leaves you feeling weak and disoriented."],
                    sanity_change=-5,  # Significant sanity loss from cursed food
                    health_change=-2   # Health damage from curse
                )

            # Handle poisoned food
            if poison:
                poison_messages = [
                    f"The {game_object.name} tastes bitter... terribly bitter. Poison!",
                    f"You barely swallow the {game_object.name} when your throat begins to burn.",
                    f"The {game_object.name} was poisoned! You feel your strength fading.",
                    f"A wave of nausea overtakes you as the poison takes effect."
                ]

                import random

                # Remove from inventory after eating
                state.inventory.remove(object_id)

                return ActionResult(
                    success=True,
                    message=random.choice(poison_messages),
                    notifications=[f"The poison courses through your veins, seeking vital organs."],
                    health_change=-4   # Significant health damage from poison
                )

            # Success messages with haunted atmosphere
            if state.sanity < 30:
                messages = [
                    f"You devour the {game_object.name} with desperate hunger. For a moment, you forget the darkness.",
                    f"The {game_object.name} provides fleeting comfort in this endless nightmare.",
                    f"As you eat the {game_object.name}, you wonder if you're consuming hope itself.",
                    f"The {game_object.name} tastes like fear and desperation, but your stomach settles."
                ]
            else:
                messages = [
                    f"You eat the {game_object.name}.",
                    f"You consume the {game_object.name}.",
                    f"The {game_object.name} is quite satisfying.",
                    f"You finish the {game_object.name} and feel better."
                ]

            import random
            notifications = []

            # Handle nutrition/health benefits
            health_change = 0
            if nutrition > 0:
                health_change = nutrition
                notifications.append(f"The {game_object.name} restores some of your vitality.")

            # Handle magic effects
            if magic_effect:
                if magic_effect == 'sanity_restore':
                    notifications.append(f"The {game_object.name} clears your mind of haunting whispers.")
                    health_change = 2  # Small health boost from magic
                elif magic_effect == 'strength':
                    notifications.append(f"The {game_object.name} fills you with unnatural strength.")
                elif magic_effect == 'vision':
                    notifications.append(f"The {game_object.name} grants you glimpses of unseen truths.")

            # Remove from inventory after eating
            state.inventory.remove(object_id)

            return ActionResult(
                success=True,
                message=random.choice(messages),
                notifications=notifications,
                sanity_change=1 if not cursed else 0,  # Small sanity boost from normal food
                health_change=health_change
            )

        except ValueError as e:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't have the {display_name}."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something prevents you from eating that item.",
                room_changed=False
            )

    def handle_drink(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle drinking liquids and potions.

        Allows players to drink liquids from containers or standalone beverages.
        Handles potions, poisoned drinks, cursed liquids, and thirst management
        with haunted atmosphere messages.

        Args:
            object_id: The object to drink
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 4.5
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if object is in inventory or current room
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory

            if not object_in_room and not object_in_inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't have the {display_name}."
                )

            # If object is in room but not inventory, require taking it first
            if object_in_room and not object_in_inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You need to take the {display_name} first before you can drink it."
                )

            # Get object data
            game_object = self.world.get_object(object_id)

            # Check if object can be drunk
            is_drinkable = game_object.state.get('drinkable', False)
            is_container = game_object.state.get('is_container', False)
            liquid_type = game_object.state.get('liquid_type', 'liquid')

            # Check if it's a container with liquid
            if is_container:
                can_hold_liquid = game_object.state.get('can_hold_liquid', False)
                is_empty = game_object.state.get('is_empty', True)
                liquid_level = game_object.state.get('liquid_level', 0)

                if not can_hold_liquid or is_empty or liquid_level <= 0:
                    return ActionResult(
                        success=False,
                        message=f"The {game_object.name} is empty or doesn't contain any liquid."
                    )

                # Get liquid properties from container
                liquid_type = game_object.state.get('liquid_type', 'water')
                cursed = game_object.state.get('liquid_cursed', False)
                poison = game_object.state.get('liquid_poison', False)
                magic_effect = game_object.state.get('liquid_magic_effect', None)

                # Empty the container
                game_object.state['is_empty'] = True
                game_object.state['liquid_level'] = 0

            elif is_drinkable:
                # Direct drinkable item (potion, etc.)
                cursed = game_object.state.get('cursed', False)
                poison = game_object.state.get('poison', False)
                magic_effect = game_object.state.get('magic_effect', None)
            else:
                # Not drinkable
                non_drinkable_messages = [
                    f"You can't drink the {game_object.name}! It's not a liquid.",
                    f"That's not something you can drink. Your throat refuses the attempt.",
                    f"The {game_object.name} resists your efforts to consume it as liquid.",
                    f"You try to drink the {game_object.name}, but it's not designed for consumption."
                ]

                if state.sanity < 30:
                    non_drinkable_messages.append(f"In your madness, you consider drinking the {game_object.name}, but reality intervenes.")

                import random
                return ActionResult(
                    success=False,
                    message=random.choice(non_drinkable_messages)
                )

            # Handle cursed liquids
            if cursed:
                curse_messages = [
                    f"The {liquid_type} burns like ice as it goes down. A curse takes hold!",
                    f"As you drink the {liquid_type}, dark whispers fill your mind.",
                    f"The {liquid_type} was cursed! You feel corruption spreading through you.",
                    f"An unholy power emanates from the {liquid_type}. You are tainted!"
                ]

                if state.sanity < 30:
                    curse_messages.append(f"The cursed {liquid_type} feels comfortingly familiar. Your soul darkens further.")

                import random

                # Remove from inventory if it was a drinkable item, not a container
                if not is_container and object_id in state.inventory:
                    state.inventory.remove(object_id)

                return ActionResult(
                    success=True,
                    message=random.choice(curse_messages),
                    notifications=[f"The curse warps your mind and body."],
                    sanity_change=-6,  # Major sanity loss from cursed liquids
                    health_change=-3   # Health damage from curse
                )

            # Handle poisoned liquids
            if poison:
                poison_messages = [
                    f"The {liquid_type} tastes of bitter almonds! Poison!",
                    f"Your throat constricts as the poison takes effect.",
                    f"The {liquid_type} was poisoned! You clutch your stomach in pain.",
                    f"A burning sensation spreads from your chest. The poison works quickly."
                ]

                import random

                # Remove from inventory if it was a drinkable item, not a container
                if not is_container and object_id in state.inventory:
                    state.inventory.remove(object_id)

                return ActionResult(
                    success=True,
                    message=random.choice(poison_messages),
                    notifications=[f"The poison courses through your bloodstream."],
                    health_change=-5   # Major health damage from poison
                )

            # Success messages with haunted atmosphere
            if state.sanity < 30:
                messages = [
                    f"The {liquid_type} slides down your throat like shadow and memory.",
                    f"You drink the {liquid_type}. For a moment, the world seems less terrifying.",
                    f"The {liquid_type} tastes of forgotten dreams and whispered secrets.",
                    f"As you drink the {liquid_type}, you feel the darkness recede slightly."
                ]
            else:
                messages = [
                    f"You drink the {liquid_type}.",
                    f"The {liquid_type} is refreshing.",
                    f"You finish the {liquid_type} and feel refreshed.",
                    f"The {liquid_type} quenches your thirst."
                ]

            import random
            notifications = []

            # Handle magic effects
            health_change = 0
            if magic_effect:
                if magic_effect == 'healing':
                    health_change = 4
                    notifications.append(f"The {liquid_type} glows with healing energy.")
                elif magic_effect == 'sanity_restore':
                    notifications.append(f"The {liquid_type} clears your mind of dark thoughts.")
                    health_change = 2
                elif magic_effect == 'strength':
                    notifications.append(f"The {liquid_type} fills you with supernatural power.")
                elif magic_effect == 'vision':
                    notifications.append(f"The {liquid_type} grants you visions of things to come.")
            else:
                # Normal liquid provides minor benefit
                health_change = 1
                notifications.append(f"The {liquid_type} refreshes you.")

            # Remove from inventory if it was a drinkable item, not a container
            if not is_container and object_id in state.inventory:
                state.inventory.remove(object_id)

            return ActionResult(
                success=True,
                message=random.choice(messages),
                notifications=notifications,
                sanity_change=2 if magic_effect == 'sanity_restore' else 1,
                health_change=health_change
            )

        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't have the {object_id}."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something prevents you from drinking that item.",
                room_changed=False
            )

    def handle_move(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle moving objects (separate from PUSH/PULL).

        Allows moving movable objects to different positions, rearranging
        items in rooms, and specialized object repositioning. Different
        from PUSH/PULL which are force-based movements.

        Args:
            object_id: The object to move
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 4.6
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory

            if not object_in_room and not object_in_inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )

            # Get object data
            game_object = self.world.get_object(object_id)

            # First check if object has a MOVE interaction
            for interaction in game_object.interactions:
                if interaction.verb == "MOVE":
                    # Check conditions
                    if interaction.condition:
                        conditions_met = all(
                            game_object.state.get(key) == value
                            for key, value in interaction.condition.items()
                        )
                        if not conditions_met:
                            continue
                    
                    # Apply state changes
                    if interaction.state_change:
                        for key, value in interaction.state_change.items():
                            game_object.state[key] = value
                    
                    # Apply flag changes
                    if interaction.flag_change:
                        for key, value in interaction.flag_change.items():
                            state.set_flag(key, value)
                    
                    # Apply sanity effect
                    if interaction.sanity_effect:
                        state.sanity = max(0, min(100, state.sanity + interaction.sanity_effect))
                    
                    return ActionResult(
                        success=True,
                        message=interaction.response_spooky,
                        sanity_change=interaction.sanity_effect
                    )

            # If no interaction found, check if object can be moved via state
            is_movable = game_object.state.get('movable', False)
            is_moveable_alt = game_object.state.get('moveable', False)  # Alternative spelling

            if not is_movable and not is_moveable_alt:
                # Check for fixed in place property
                is_fixed = game_object.state.get('fixed', False)
                if is_fixed:
                    return ActionResult(
                        success=False,
                        message=f"The {game_object.name} is fixed in place and cannot be moved."
                    )

                # Check if too heavy
                is_heavy = game_object.state.get('too_heavy', False)
                if is_heavy:
                    heavy_messages = [
                        f"The {game_object.name} is far too heavy to move by yourself.",
                        f"You try to move the {game_object.name}, but it won't budge. It's too heavy.",
                        f"The {game_object.name} weighs a ton. There's no way you can move it.",
                        f"Despite your best efforts, the {game_object.name} remains stubbornly immobile."
                    ]

                    if state.sanity < 30:
                        heavy_messages.append(f"The shadows mock your pathetic attempt to move the {game_object.name}. Even the darkness laughs at your weakness.")

                    import random
                    return ActionResult(
                        success=False,
                        message=random.choice(heavy_messages)
                    )

                # Default immovable response
                immovable_messages = [
                    f"The {game_object.name} can't be moved.",
                    f"You can't move the {game_object.name}.",
                    f"The {game_object.name} is not meant to be moved.",
                    f"Your efforts to move the {game_object.name} prove futile."
                ]

                import random
                return ActionResult(
                    success=False,
                    message=random.choice(immovable_messages)
                )

            # Success messages with haunted atmosphere
            if state.sanity < 30:
                messages = [
                    f"You move the {game_object.name}. The shadows seem to shift to accommodate its new position.",
                    f"The {game_object.name} slides into its new place with an unnatural ease.",
                    f"As you move the {game_object.name}, you hear faint whispers of approval from the void.",
                    f"The {game_object.name} settles into its new location. For a moment, you feel the room's geometry change."
                ]
            else:
                messages = [
                    f"You move the {game_object.name}.",
                    f"The {game_object.name} is now in a different position.",
                    f"You successfully reposition the {game_object.name}.",
                    f"The {game_object.name} has been moved."
                ]

            import random
            notifications = []

            # Check for special effects of moving
            reveals_under = game_object.state.get('reveals_under_when_moved', [])
            if reveals_under:
                for item_id in reveals_under:
                    if item_id not in current_room.items:
                        current_room.items.append(item_id)
                        try:
                            revealed_obj = self.world.get_object(item_id)
                            notifications.append(f"Moving the {game_object.name} reveals {revealed_obj.name_spooky}!")
                        except ValueError:
                            notifications.append(f"Moving the {game_object.name} reveals something hidden!")

            # Update object state
            position = game_object.state.get('position', 'here')
            new_positions = ['there', 'aside', 'center', 'corner']
            import random
            new_position = random.choice(new_positions)
            game_object.state['position'] = new_position

            # Check for trigger effects
            if game_object.state.get('triggers_on_move', False):
                notifications.append(f"The {game_object.name} emits a low hum as it settles in its new position.")
                # Could trigger sanity change or other effects here

            return ActionResult(
                success=True,
                message=random.choice(messages),
                notifications=notifications,
                sanity_change=0
            )

        except ValueError as e:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something prevents you from moving that object.",
                room_changed=False
            )

    def handle_raise(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle raising/lifting objects upward.

        Allows lifting objects to higher positions, raising levers,
        or elevating movable items. Supports both RAISE and "RAISE UP".

        Args:
            object_id: The object to raise
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 4.7
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory

            if not object_in_room and not object_in_inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )

            # Get object data
            game_object = self.world.get_object(object_id)

            # Check if object can be raised
            can_raise = game_object.state.get('can_raise', False)
            is_raised = game_object.state.get('raised', False)

            if not can_raise:
                raise_messages = [
                    f"You can't raise the {game_object.name}.",
                    f"The {game_object.name} doesn't respond to being raised.",
                    f"The {game_object.name} is not designed to be raised.",
                    f"Your attempt to raise the {game_object.name} fails completely."
                ]

                if state.sanity < 30:
                    raise_messages.append(f"The shadows hold the {game_object.name} down. Some things are not meant to rise.")

                import random
                return ActionResult(
                    success=False,
                    message=random.choice(raise_messages)
                )

            if is_raised:
                return ActionResult(
                    success=False,
                    message=f"The {game_object.name} is already raised."
                )

            # Success messages with haunted atmosphere
            if state.sanity < 30:
                messages = [
                    f"You raise the {game_object.name}. Unnatural resistance gives way to your touch.",
                    f"The {game_object.name} rises as if compelled by unseen forces.",
                    f"As you raise the {game_object.name}, you hear a distant, ethereal sigh.",
                    f"The {game_object.name} ascends. For a moment, you feel the room's attention focus upon it."
                ]
            else:
                messages = [
                    f"You raise the {game_object.name}.",
                    f"The {game_object.name} is now in a raised position.",
                    f"You successfully raise the {game_object.name}.",
                    f"The {game_object.name} has been raised."
                ]

            import random
            notifications = []

            # Update object state
            game_object.state['raised'] = True

            # Check for special effects
            reveals_when_raised = game_object.state.get('reveals_when_raised', [])
            if reveals_when_raised:
                for item_id in reveals_when_raised:
                    if item_id not in current_room.items:
                        current_room.items.append(item_id)
                        try:
                            revealed_obj = self.world.get_object(item_id)
                            notifications.append(f"Raising the {game_object.name} reveals {revealed_obj.name_spooky}!")
                        except ValueError:
                            notifications.append(f"Raising the {game_object.name} reveals something hidden!")

            # Check for trigger effects
            if game_object.state.get('triggers_when_raised', False):
                notifications.append(f"The {game_object.name} emits a soft glow as it reaches its raised position.")

            return ActionResult(
                success=True,
                message=random.choice(messages),
                notifications=notifications,
                sanity_change=0
            )

        except ValueError as e:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something prevents you from raising that object.",
                room_changed=False
            )

    def handle_lower(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle lowering objects downward.

        Allows lowering raised objects, pulling items down from heights,
        or lowering movable items to ground level.

        Args:
            object_id: The object to lower
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 4.7
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory

            if not object_in_room and not object_in_inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )

            # Get object data
            game_object = self.world.get_object(object_id)

            # Check if object can be lowered
            can_lower = game_object.state.get('can_lower', False)
            is_raised = game_object.state.get('raised', False)

            if not can_lower:
                lower_messages = [
                    f"You can't lower the {game_object.name}.",
                    f"The {game_object.name} doesn't respond to being lowered.",
                    f"The {game_object.name} is not designed to be lowered.",
                    f"Your attempt to lower the {game_object.name} has no effect."
                ]

                import random
                return ActionResult(
                    success=False,
                    message=random.choice(lower_messages)
                )

            if not is_raised:
                return ActionResult(
                    success=False,
                    message=f"The {game_object.name} is not currently raised."
                )

            # Success messages with haunted atmosphere
            if state.sanity < 30:
                messages = [
                    f"You lower the {game_object.name}. The darkness seems to reach up to help it down.",
                    f"The {game_object.name} descends with unnatural reluctance.",
                    f"As you lower the {game_object.name}, whispers of disappointment echo through the void.",
                    f"The {game_object.name} returns to its earthly position. The room feels heavier somehow."
                ]
            else:
                messages = [
                    f"You lower the {game_object.name}.",
                    f"The {game_object.name} is now in a lowered position.",
                    f"You successfully lower the {game_object.name}.",
                    f"The {game_object.name} has been lowered."
                ]

            import random

            # Update object state
            game_object.state['raised'] = False

            return ActionResult(
                success=True,
                message=random.choice(messages),
                sanity_change=0
            )

        except ValueError as e:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something prevents you from lowering that object.",
                room_changed=False
            )

    def handle_slide(
        self,
        object_id: str,
        target_id: Optional[str],
        state: GameState
    ) -> ActionResult:
        """
        Handle sliding objects, optionally under other objects.

        Allows sliding movable objects across surfaces, and sliding
        objects underneath other objects for access or discovery.

        Args:
            object_id: The object to slide
            target_id: The target to slide under (optional)
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 4.8
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory

            if not object_in_room and not object_in_inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )

            # Get object data
            game_object = self.world.get_object(object_id)

            # Check if object can be slid
            can_slide = game_object.state.get('can_slide', False)

            if not can_slide:
                slide_messages = [
                    f"The {game_object.name} won't slide.",
                    f"You can't slide the {game_object.name}.",
                    f"The {game_object.name} offers too much resistance to slide.",
                    f"Friction prevents the {game_object.name} from sliding."
                ]

                if state.sanity < 30:
                    slide_messages.append(f"The ground itself seems to hold the {game_object.name} fast. The house doesn't want it moved.")

                import random
                return ActionResult(
                    success=False,
                    message=random.choice(slide_messages)
                )

            # Handle sliding under another object
            if target_id:
                # Check if target exists and is in room
                if target_id not in current_room.items:
                    target_name = self._get_object_names(target_id)
                    return ActionResult(
                        success=False,
                        message=f"You don't see any {target_name} here."
                    )

                target_object = self.world.get_object(target_id)
                can_slide_under = target_object.state.get('can_slide_under', False)

                if not can_slide_under:
                    return ActionResult(
                        success=False,
                        message=f"You can't slide anything under the {target_object.name}."
                    )

                # Success messages for sliding under
                if state.sanity < 30:
                    messages = [
                        f"You slide the {game_object.name} under the {target_object.name}. The shadows seem to part to make way.",
                        f"The {game_object.name} disappears beneath the {target_object.name}. You hope nothing lurks there.",
                        f"As you slide the {game_object.name} under the {target_object.name}, you hear faint scratching sounds.",
                        f"The {game_object.name} slides smoothly under the {target_object.name}. The darkness below seems welcoming."
                    ]
                else:
                    messages = [
                        f"You slide the {game_object.name} under the {target_object.name}.",
                        f"The {game_object.name} is now under the {target_object.name}.",
                        f"You successfully slide the {game_object.name} beneath the {target_object.name}."
                    ]

                import random
                notifications = []

                # Check for hidden items revealed
                reveals_under_target = target_object.state.get('reveals_under', [])
                if reveals_under_target:
                    for item_id in reveals_under_target:
                        if item_id not in current_room.items:
                            current_room.items.append(item_id)
                            try:
                                revealed_obj = self.world.get_object(item_id)
                                notifications.append(f"Sliding the {game_object.name} under the {target_object.name} reveals {revealed_obj.name_spooky}!")
                            except ValueError:
                                notifications.append(f"Sliding the {game_object.name} under the {target_object.name} reveals something hidden!")

                return ActionResult(
                    success=True,
                    message=random.choice(messages),
                    notifications=notifications,
                    sanity_change=0
                )

            # Regular sliding without target
            if state.sanity < 30:
                messages = [
                    f"The {game_object.name} slides across the floor with eerie silence.",
                    f"You slide the {game_object.name}. It moves as if propelled by ghostly hands.",
                    f"The {game_object.name} glides smoothly. For a moment, you see fleeting images in its wake.",
                    f"As the {game_object.name} slides, you hear whispers from the space it leaves behind."
                ]
            else:
                messages = [
                    f"You slide the {game_object.name}.",
                    f"The {game_object.name} slides easily across the surface.",
                    f"The {game_object.name} moves to a new position.",
                    f"You successfully slide the {game_object.name}."
                ]

            import random

            return ActionResult(
                success=True,
                message=random.choice(messages),
                sanity_change=0
            )

        except ValueError as e:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something prevents you from sliding that object.",
                room_changed=False
            )

    def handle_spring(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle making objects spring up or activate suddenly.

        Allows triggering spring-loaded mechanisms, making objects
        jump up from hidden positions, or activating surprise elements.

        Args:
            object_id: The object to make spring
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 4.9
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory

            if not object_in_room and not object_in_inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )

            # Get object data
            game_object = self.world.get_object(object_id)

            # Check if object can spring
            can_spring = game_object.state.get('can_spring', False)
            is_sprung = game_object.state.get('sprung', False)

            if not can_spring:
                spring_messages = [
                    f"The {game_object.name} doesn't spring.",
                    f"You try to make the {game_object.name} spring, but nothing happens.",
                    f"The {game_object.name} is not designed to spring.",
                    f"Your attempt to spring the {game_object.name} fails."
                ]

                import random
                return ActionResult(
                    success=False,
                    message=random.choice(spring_messages)
                )

            if is_sprung:
                return ActionResult(
                    success=False,
                    message=f"The {game_object.name} has already sprung."
                )

            # Success messages with haunted atmosphere
            if state.sanity < 30:
                messages = [
                    f"The {game_object.name} springs up with unnatural speed! Ghostly laughter echoes.",
                    f"The {game_object.name} springs suddenly. For a moment, you see skeletal hands helping it rise.",
                    f"The {game_object.name} leaps upward as if possessed by vengeful spirits.",
                    f"The {game_object.name} springs. The air grows cold and you feel unseen eyes watching."
                ]
            else:
                messages = [
                    f"The {game_object.name} springs up!",
                    f"The {game_object.name} springs suddenly.",
                    f"The {game_object.name} leaps into position.",
                    f"The {game_object.name} has sprung."
                ]

            import random
            notifications = []

            # Update object state
            game_object.state['sprung'] = True

            # Check for spring effects
            reveals_when_sprung = game_object.state.get('reveals_when_sprung', [])
            if reveals_when_sprung:
                for item_id in reveals_when_sprung:
                    if item_id not in current_room.items:
                        current_room.items.append(item_id)
                        try:
                            revealed_obj = self.world.get_object(item_id)
                            notifications.append(f"The {game_object.name} springs, revealing {revealed_obj.name_spooky}!")
                        except ValueError:
                            notifications.append(f"The {game_object.name} springs, revealing something hidden!")

            # Check for spring damage
            spring_damage = game_object.state.get('spring_damage', 0)
            if spring_damage > 0:
                notifications.append(f"The {game_object.name} strikes you as it springs!")

            return ActionResult(
                success=True,
                message=random.choice(messages),
                notifications=notifications,
                sanity_change=0,
                health_change=-spring_damage
            )

        except ValueError as e:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something prevents you from springing that object.",
                room_changed=False
            )

    def handle_hatch(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle hatching eggs, containers, or enclosures.

        Allows hatching eggs, opening sealed containers, or breaking
        out of enclosed spaces with young creatures or items.

        Args:
            object_id: The object to hatch
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 4.9
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory

            if not object_in_room and not object_in_inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {display_name} here."
                )

            # Get object data
            game_object = self.world.get_object(object_id)

            # Check if object can hatch
            can_hatch = game_object.state.get('can_hatch', False)
            is_hatched = game_object.state.get('hatched', False)

            if not can_hatch:
                hatch_messages = [
                    f"The {game_object.name} won't hatch.",
                    f"You can't hatch the {game_object.name}.",
                    f"The {game_object.name} is not an egg or hatchable container.",
                    f"Your attempt to hatch the {game_object.name} has no effect."
                ]

                import random
                return ActionResult(
                    success=False,
                    message=random.choice(hatch_messages)
                )

            if is_hatched:
                return ActionResult(
                    success=False,
                    message=f"The {game_object.name} has already hatched."
                )

            # Success messages with haunted atmosphere
            if state.sanity < 30:
                messages = [
                    f"The {game_object.name} hatches with an unnatural cracking sound. Something dark emerges.",
                    f"The {game_object.name} splits open. A twisted creature crawls out into the world.",
                    f"The {game_object.name} hatches. You hear distant screams as whatever was inside is born.",
                    f"The {game_object.name} breaks open. The shadows seem to rejoice at whatever has emerged."
                ]
            else:
                messages = [
                    f"The {game_object.name} hatches!",
                    f"The {game_object.name} cracks open and something emerges.",
                    f"The {game_object.name} has hatched.",
                    f"The {game_object.name} splits open."
                ]

            import random
            notifications = []

            # Update object state
            game_object.state['hatched'] = True

            # Check for hatched contents
            hatched_contents = game_object.state.get('hatched_contents', [])
            if hatched_contents:
                for item_id in hatched_contents:
                    current_room.items.append(item_id)
                    try:
                        hatched_obj = self.world.get_object(item_id)
                        notifications.append(f"From the {game_object.name} emerges {hatched_obj.name_spooky}!")
                    except ValueError:
                        notifications.append(f"From the {game_object.name} emerges something unexpected!")

            # Check for special hatched creature
            hatched_creature = game_object.state.get('hatched_creature', None)
            if hatched_creature:
                notifications.append(f"A terrifying creature emerges from the {game_object.name}!")

            return ActionResult(
                success=True,
                message=random.choice(messages),
                notifications=notifications,
                sanity_change=0
            )

        except ValueError as e:
            display_name = self._get_object_names(object_id)
            return ActionResult(
                success=False,
                message=f"You don't see any {display_name} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something prevents you from hatching that object.",
                room_changed=False
            )

    def handle_apply(
        self,
        object_id: str,
        target_id: Optional[str],
        state: GameState
    ) -> ActionResult:
        """
        Handle applying one object to another.

        Allows applying salves, ointments, or special items to other
        objects or surfaces, with various effects.

        Args:
            object_id: The object to apply
            target_id: The target to apply to (optional)
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 4.10
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if object is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory

            if not object_in_room and not object_in_inventory:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"You don't have the {display_name}."
                )

            # Get object data
            game_object = self.world.get_object(object_id)

            # Check if object can be applied
            can_apply = game_object.state.get('can_apply', False)

            if not can_apply:
                apply_messages = [
                    f"You can't apply the {game_object.name}.",
                    f"The {game_object.name} cannot be applied to anything.",
                    f"The {game_object.name} is not something you apply.",
                    f"Your attempt to apply the {game_object.name} fails."
                ]

                import random
                return ActionResult(
                    success=False,
                    message=random.choice(apply_messages)
                )

            # If no target specified
            if not target_id:
                return ActionResult(
                    success=False,
                    message=f"What do you want to apply the {game_object.name} to?"
                )

            # Check if target exists and is accessible
            target_in_room = target_id in current_room.items
            target_in_inventory = target_id in state.inventory

            if not target_in_room and not target_in_inventory:
                target_name = self._get_object_names(target_id)
                return ActionResult(
                    success=False,
                    message=f"You don't see any {target_name} here."
                )

            # Get target object
            target_object = self.world.get_object(target_id)

            # Success messages with haunted atmosphere
            if state.sanity < 30:
                messages = [
                    f"You apply the {game_object.name} to the {target_object.name}. Dark forces seem to respond.",
                    f"The {game_object.name} sinks into the {target_object.name} with unnatural ease.",
                    f"As you apply the {game_object.name} to the {target_object.name}, you hear whispers from beyond.",
                    f"The {game_object.name} merges with the {target_object.name}. The room feels somehow changed."
                ]
            else:
                messages = [
                    f"You apply the {game_object.name} to the {target_object.name}.",
                    f"The {game_object.name} is applied to the {target_object.name}.",
                    f"You successfully apply the {game_object.name} to the {target_object.name}."
                ]

            import random
            notifications = []

            # Check for apply effects
            apply_effect = game_object.state.get('apply_effect', None)
            if apply_effect:
                notifications.append(f"The {object_id} affects the {target_id}!")

                # Apply different effects
                if apply_effect == 'heal':
                    notifications.append(f"The {target_id} looks healthier after the application.")
                elif apply_effect == 'clean':
                    notifications.append(f"The {target_id} becomes clean and pristine.")
                elif apply_effect == 'activate':
                    notifications.append(f"The {target_id} glows with newfound energy.")
                elif apply_effect == 'curse':
                    notifications.append(f"The {target_id} seems darker and more menacing.")
                elif apply_effect == 'reveal':
                    reveals_when_applied = target_object.state.get('reveals_when_applied', [])
                    if reveals_when_applied:
                        for item_id in reveals_when_applied:
                            if item_id not in current_room.items:
                                current_room.items.append(item_id)
                                try:
                                    revealed_obj = self.world.get_object(item_id)
                                    notifications.append(f"The application reveals {revealed_obj.name_spooky}!")
                                except ValueError:
                                    notifications.append(f"The application reveals something hidden!")

            return ActionResult(
                success=True,
                message=random.choice(messages),
                notifications=notifications,
                sanity_change=0
            )

        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't have the {object_id}."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something prevents you from applying that object.",
                room_changed=False
            )

    def handle_brush(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle brushing objects for cleaning or discovery.

        Allows brushing away dust, dirt, or concealment to reveal
        hidden objects, writings, or details.

        Args:
            object_id: The object to brush
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 4.10
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

            # Check if object can be brushed
            can_brush = game_object.state.get('can_brush', False)
            is_brushed = game_object.state.get('brushed', False)

            if not can_brush:
                # Check if it's generally brushable (surfaces, etc.)
                is_surface = game_object.state.get('is_surface', False)
                if not is_surface:
                    brush_messages = [
                        f"You can't brush the {object_id}.",
                        f"The {object_id} doesn't need brushing.",
                        f"Brushing the {object_id} would have no effect.",
                        f"The {object_id} is not something you brush."
                    ]

                    import random
                    return ActionResult(
                        success=False,
                        message=random.choice(brush_messages)
                    )

            if is_brushed:
                return ActionResult(
                    success=False,
                    message=f"The {object_id} has already been brushed clean."
                )

            # Success messages with haunted atmosphere
            if state.sanity < 30:
                messages = [
                    f"You brush the {object_id}. Ghostly dust motes dance in the air as you clean.",
                    f"The {object_id} seems to resist your efforts, as if the dirt itself is alive.",
                    f"As you brush the {object_id}, you feel ancient spirits resent the disturbance.",
                    f"You brush away centuries of grime. The air grows heavy with released memories."
                ]
            else:
                messages = [
                    f"You brush the {object_id}.",
                    f"The {object_id} becomes clean.",
                    f"You brush the {object_id} clean.",
                    f"The {object_id} is now brushed."
                ]

            import random
            notifications = []

            # Update object state
            game_object.state['brushed'] = True

            # Check for revealed items when brushed
            reveals_when_brushed = game_object.state.get('reveals_when_brushed', [])
            if reveals_when_brushed:
                for item_id in reveals_when_brushed:
                    if item_id not in current_room.items:
                        current_room.items.append(item_id)
                        try:
                            revealed_obj = self.world.get_object(item_id)
                            notifications.append(f"Brushing the {object_id} reveals {revealed_obj.name_spooky}!")
                        except ValueError:
                            notifications.append(f"Brushing the {object_id} reveals something hidden!")

            # Check for revealed writings
            reveals_writing = game_object.state.get('reveals_writing_when_brushed', None)
            if reveals_writing:
                notifications.append(f"Brushing the {object_id} reveals ancient writing: '{reveals_writing}'")

            return ActionResult(
                success=True,
                message=random.choice(messages),
                notifications=notifications,
                sanity_change=0
            )

        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Something prevents you from brushing that object.",
                room_changed=False
            )

    def handle_say(
        self,
        text: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle speaking phrases or sentences.

        Allows players to say phrases, communicate with NPCs,
        or trigger voice-activated mechanisms in the haunted house.

        Args:
            text: The text to say
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 5.2
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if text is provided
            if not text or text.strip() == "":
                return ActionResult(
                    success=False,
                    message="What do you want to say?"
                )

            # Clean up the text
            said_text = text.strip().strip('"\'').strip()

            # Success messages with haunted atmosphere
            if state.sanity < 30:
                messages = [
                    f'You say "{said_text}". Your voice echoes strangely, as if the house is listening.',
                    f'You speak: "{said_text}". The shadows seem to lean in to hear better.',
                    f'You say "{said_text}". For a moment, you hear your own words whispered back in a different language.',
                    f'You say: "{said_text}". The walls seem to absorb your words, storing them for later use.'
                ]
            else:
                messages = [
                    f'You say "{said_text}".',
                    f'You speak: "{said_text}".',
                    f'You say: "{said_text}".',
                    f'Your voice: "{said_text}".'
                ]

            import random
            notifications = []

            # Check for NPCs in room that might respond
            for item_id in current_room.items:
                game_object = self.world.get_object(item_id)
                is_npc = game_object.state.get('is_npc', False)
                is_creature = game_object.state.get('is_creature', False)

                if is_npc or is_creature:
                    # Get possible responses
                    responses = game_object.state.get('responses', [])
                    if responses:
                        import random
                        response = random.choice(responses)
                        notifications.append(f"The {item_id} {response}")
                    else:
                        # Default responses for different entity types
                        if is_npc:
                            default_responses = [
                                f"The {item_id} nods attentively.",
                                f"The {item_id} seems to consider your words.",
                                f"The {item_id} gives you an inscrutable look.",
                                f"The {item_id} appears interested in what you said."
                            ]
                            notifications.append(random.choice(default_responses))
                        elif is_creature:
                            creature_responses = [
                                f"The {item_id} perks up its ears.",
                                f"The {item_id} turns its head toward you.",
                                f"The {item_id} seems to understand your words.",
                                f"The {item_id} makes a soft sound in response."
                            ]
                            notifications.append(random.choice(creature_responses))

            # Check for voice-activated mechanisms
            voice_triggers = current_room.state.get('voice_triggers', [])
            if voice_triggers:
                for trigger in voice_triggers:
                    if trigger['phrase'].lower() in said_text.lower():
                        if trigger['action'] == 'open':
                            notifications.append(f"Something in the room responds to your words!")
                        elif trigger['action'] == 'reveal':
                            for item_id in trigger['reveals']:
                                if item_id not in current_room.items:
                                    current_room.items.append(item_id)
                                    try:
                                        revealed_obj = self.world.get_object(item_id)
                                        notifications.append(f"Your words reveal {revealed_obj.name_spooky}!")
                                    except ValueError:
                                        notifications.append(f"Your words reveal something hidden!")

            return ActionResult(
                success=True,
                message=random.choice(messages),
                notifications=notifications,
                sanity_change=0
            )

        except Exception as e:
            return ActionResult(
                success=False,
                message="Your words seem to catch in your throat.",
                room_changed=False
            )

    def handle_whisper(
        self,
        text: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle whispering quietly.

        Allows players to whisper phrases, communicate secretly with NPCs,
        or trigger sensitive mechanisms that respond to quiet speech.

        Args:
            text: The text to whisper
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 5.2
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if text is provided
            if not text or text.strip() == "":
                return ActionResult(
                    success=False,
                    message="What do you want to whisper?"
                )

            # Clean up the text
            whispered_text = text.strip().strip('"\'').strip()

            # Success messages with haunted atmosphere
            if state.sanity < 30:
                messages = [
                    f'You whisper "{whispered_text}". The darkness leans closer to hear your secret.',
                    f'You whisper: "{whispered_text}". Faint, ghostly whispers answer in return.',
                    f'You whisper "{whispered_text}". The house holds your words close to its heart.',
                    f'You whisper: "{whispered_text}". Something in the shadows nods in understanding.'
                ]
            else:
                messages = [
                    f'You whisper "{whispered_text}".',
                    f'You whisper: "{whispered_text}".',
                    f'You say quietly: "{whispered_text}".',
                    f'You whisper: "{whispered_text}".'
                ]

            import random
            notifications = []

            # Check for NPCs that might hear whispers
            for item_id in current_room.items:
                game_object = self.world.get_object(item_id)
                is_npc = game_object.state.get('is_npc', False)

                if is_npc:
                    # NPCs might respond to whispers differently
                    can_hear_whisper = game_object.state.get('can_hear_whisper', False)
                    if can_hear_whisper:
                        whisper_responses = game_object.state.get('whisper_responses', [])
                        if whisper_responses:
                            import random
                            response = random.choice(whisper_responses)
                            notifications.append(f"The {item_id} leans closer and {response}")
                        else:
                            default_whispers = [
                                f"The {item_id} listens intently to your whisper.",
                                f"The {item_id} nods knowingly at your quiet words.",
                                f"The {item_id} seems intrigued by your whispered message.",
                                f"The {item_id} gives you a secretive glance."
                            ]
                            notifications.append(random.choice(default_whispers))
                    else:
                        notifications.append(f"The {item_id} seems unaware of your quiet words.")

            # Check for whisper-sensitive mechanisms
            whisper_triggers = current_room.state.get('whisper_triggers', [])
            if whisper_triggers:
                for trigger in whisper_triggers:
                    if trigger['phrase'].lower() in whispered_text.lower():
                        notifications.append(f"Something responds to your whispered words!")
                        # Could trigger special effects here

            return ActionResult(
                success=True,
                message=random.choice(messages),
                notifications=notifications,
                sanity_change=0
            )

        except Exception as e:
            return ActionResult(
                success=False,
                message="Your whisper catches in your throat.",
                room_changed=False
            )

    def handle_answer(
        self,
        text: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle answering questions or responding to prompts.

        Allows players to answer riddles, respond to NPC questions,
        or provide answers to voice-activated puzzles.

        Args:
            text: The answer text
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 5.2
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if text is provided
            if not text or text.strip() == "":
                return ActionResult(
                    success=False,
                    message="What is your answer?"
                )

            # Clean up the text
            answer_text = text.strip().strip('"\'').strip()

            # Check if there's an active question in the room
            current_question = current_room.state.get('current_question', None)
            questioner = current_room.state.get('questioner', None)

            if not current_question:
                return ActionResult(
                    success=False,
                    message="No one has asked you anything to answer."
                )

            # Success messages with haunted atmosphere
            if state.sanity < 30:
                messages = [
                    f'You answer: "{answer_text}". The air grows heavy with anticipation.',
                    f'Your answer: "{answer_text}". Ancient eyes seem to judge your response.',
                    f'You respond: "{answer_text}". The house holds its breath, waiting.',
                    f'You give your answer: "{answer_text}". Something unseen considers your words.'
                ]
            else:
                messages = [
                    f'You answer: "{answer_text}".',
                    f'Your response: "{answer_text}".',
                    f'You reply: "{answer_text}".',
                    f'Your answer: "{answer_text}".'
                ]

            import random
            notifications = []

            # Check if answer is correct
            correct_answers = current_room.state.get('correct_answers', [])
            is_correct = False

            for correct_answer in correct_answers:
                if answer_text.lower() == correct_answer.lower():
                    is_correct = True
                    break

            if is_correct:
                notifications.append(f"Correct! The {questioner} seems satisfied.")

                # Trigger reward/reveal for correct answer
                reward = current_room.state.get('answer_reward', None)
                if reward:
                    if reward.get('item'):
                        item_id = reward['item']
                        if item_id not in current_room.items:
                            current_room.items.append(item_id)
                            try:
                                reward_obj = self.world.get_object(item_id)
                                notifications.append(f"As a reward, you receive {reward_obj.name_spooky}!")
                            except ValueError:
                                notifications.append(f"As a reward, you receive something unexpected!")

                    if reward.get('open'):
                        notifications.append("A door or passage opens in response!")

                    if reward.get('message'):
                        notifications.append(reward['message'])

                # Clear the question
                current_room.state['current_question'] = None
                current_room.state['questioner'] = None

            else:
                notifications.append(f"The {questioner} shakes its head. That doesn't seem right.")

                # Check for penalty
                penalty = current_room.state.get('answer_penalty', None)
                if penalty and penalty.get('message'):
                    notifications.append(penalty['message'])
                if penalty and penalty.get('sanity_loss', 0) > 0:
                    # Apply sanity loss for wrong answer
                    notifications.append(f"The wrong answer unnerves you.")

            return ActionResult(
                success=True,
                message=random.choice(messages),
                notifications=notifications,
                sanity_change=0
            )

        except Exception as e:
            return ActionResult(
                success=False,
                message="Your answer seems to catch in your throat.",
                room_changed=False
            )

    def handle_cast(
        self,
        spell_name: str,
        target_id: Optional[str],
        instrument_id: Optional[str],
        state: GameState
    ) -> ActionResult:
        """
        Handle casting magical spells and incantations.

        Allows casting spells at targets or with magical instruments,
        with various magical effects and haunted atmosphere integration.
        Supports basic magic system for haunted theme.

        Args:
            spell_name: The spell to cast
            target_id: The target of the spell (optional)
            instrument_id: Magical instrument used (optional)
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 5.3
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if spell name is provided
            if not spell_name or spell_name.strip() == "":
                return ActionResult(
                    success=False,
                    message="What spell do you want to cast?"
                )

            # Clean up spell name
            spell = spell_name.strip().strip('"\'').strip()

            # Get available spells (could be from learned spells, room availability, etc.)
            available_spells = current_room.state.get('available_spells', [])
            learned_spells = state.get('learned_spells', [])

            # Check if spell is available
            spell_available = spell in available_spells or spell in learned_spells

            if not spell_available:
                magic_messages = [
                    f"You don't know the spell '{spell}'.",
                    f"The spell '{spell}' is not available here.",
                    f"You haven't learned the spell '{spell}'.",
                    f"The mystical words for '{spell}' escape your mind."
                ]

                if state.sanity < 30:
                    magic_messages.append(f"The shadows mock your attempt to cast '{spell}'.")

                import random
                return ActionResult(
                    success=False,
                    message=random.choice(magic_messages)
                )

            # Get spell properties from room or game state
            spell_data = current_room.state.get('spells', {}).get(spell, {})
            if not spell_data:
                spell_data = {}

            # Check spell requirements
            requires_target = spell_data.get('requires_target', False)
            requires_instrument = spell_data.get('requires_instrument', False)
            mana_cost = spell_data.get('mana_cost', 0)
            sanity_cost = spell_data.get('sanity_cost', 0)

            # Check mana requirement if implemented
            if hasattr(state, 'mana') and mana_cost > 0:
                if state.mana < mana_cost:
                    return ActionResult(
                        success=False,
                        message=f"You don't have enough mana to cast {spell}. (Requires {mana_cost} mana)"
                    )

            # Check if target is required
            if requires_target and not target_id:
                return ActionResult(
                    success=False,
                    message=f"The spell '{spell}' requires a target."
                )

            # Check if instrument is required
            if requires_instrument and not instrument_id:
                return ActionResult(
                    success=False,
                    message=f"The spell '{spell}' requires a magical instrument."
                )

            # Verify target exists if required
            if requires_target and target_id:
                target_in_room = target_id in current_room.items
                target_in_inventory = target_id in state.inventory

                if not target_in_room and not target_in_inventory:
                    return ActionResult(
                        success=False,
                        message=f"You don't see any {target_id} here."
                    )

            # Verify instrument exists if required
            if requires_instrument and instrument_id:
                instrument_in_room = instrument_id in current_room.items
                instrument_in_inventory = instrument_id in state.inventory

                if not instrument_in_room and not instrument_in_inventory:
                    return ActionResult(
                        success=False,
                        message=f"You don't have the {instrument_id}."
                    )

            # Success messages with haunted atmosphere
            if state.sanity < 30:
                messages = [
                    f"You cast '{spell}' with trembling hands. Arcane energy crackles around you!",
                    f"The words of power for '{spell}' echo with otherworldly resonance.",
                    f"You cast '{spell}'. The shadows seem to recoil from your magical power.",
                    f"The spell '{spell}' manifests with terrifying beauty and deadly purpose."
                ]
            else:
                messages = [
                    f"You cast '{spell}'.",
                    f"You cast the spell '{spell}'.",
                    f"The spell '{spell}' is cast.",
                    f"Magical energy flows from your fingertips."
                ]

            import random
            notifications = []

            # Apply spell effects
            spell_effect = spell_data.get('effect', None)
            if spell_effect:
                if spell_effect == 'heal':
                    notifications.append(f"Warm healing energy flows through the room.")
                    if target_id:
                        notifications.append(f"The {target_id} looks healthier.")
                elif spell_effect == 'reveal':
                    notifications.append(f"The spell reveals hidden truths!")
                    reveals = spell_data.get('reveals', [])
                    for item_id in reveals:
                        if item_id not in current_room.items:
                            current_room.items.append(item_id)
                            try:
                                revealed_obj = self.world.get_object(item_id)
                                notifications.append(f"You see {revealed_obj.name_spooky}!")
                            except ValueError:
                                notifications.append(f"You see something mysterious appear!")
                elif spell_effect == 'damage':
                    if target_id:
                        notifications.append(f"Magical energy strikes the {target_id}!")
                    else:
                        notifications.append("Destructive magic fills the air!")
                elif spell_effect == 'protect':
                    notifications.append("A magical shield forms around you.")
                elif spell_effect == 'sanity_restore':
                    notifications.append("Your mind feels clearer, more focused.")
                elif spell_effect == 'detect':
                    notifications.append("Your magical senses detect nearby presences.")
                elif spell_effect == 'light':
                    notifications.append("Magical light illuminates the area.")
                elif spell_effect == 'darken':
                    notifications.append("Supernatural darkness fills the room.")
                elif spell_effect == 'teleport':
                    notifications.append("Reality shifts around you!")

                # Apply mana/sanity costs
                if hasattr(state, 'mana'):
                    state.mana -= mana_cost
                if sanity_cost > 0:
                    notifications.append(f"The spell drains {sanity_cost} sanity.")

            return ActionResult(
                success=True,
                message=random.choice(messages),
                notifications=notifications,
                sanity_change=-sanity_cost
            )

        except Exception as e:
            return ActionResult(
                success=False,
                message="The magic words fizzle and fade from your mind.",
                room_changed=False
            )

    def handle_enchant(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle enchanting objects with magical properties.

        Allows adding magical properties to items, making them enchanted
        with various effects and haunted atmosphere theming.

        Args:
            object_id: The object to enchant
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 5.3
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

            # Check if object can be enchanted
            is_enchantable = game_object.state.get('enchantable', False)
            is_enchanted = game_object.state.get('enchanted', False)

            if not is_enchantable:
                enchant_messages = [
                    f"You can't enchant the {object_id}.",
                    f"The {object_id} resists magical enchantment.",
                    f"The {object_id} is too mundane for enchantment.",
                    f"Your magical efforts have no effect on the {object_id}."
                ]

                if state.sanity < 30:
                    enchant_messages.append(f"The {object_id} seems to absorb your magical energy, neutralizing it.")

                import random
                return ActionResult(
                    success=False,
                    message=random.choice(enchant_messages)
                )

            if is_enchanted:
                return ActionResult(
                    success=False,
                    message=f"The {object_id} is already enchanted."
                )

            # Success messages with haunted atmosphere
            if state.sanity < 30:
                messages = [
                    f"You enchant the {object_id}. Dark runes appear on its surface, glowing ominously.",
                    f"The {object_id} accepts your magic willingly. Something ancient awakens within.",
                    f"You channel your will into the {object_id}. It pulses with sinister power.",
                    f"The {object_id} becomes enchanted. You feel its newfound malevolent awareness."
                ]
            else:
                messages = [
                    f"You enchant the {object_id}.",
                    f"The {object_id} becomes magical.",
                    f"You successfully enchant the {object_id}.",
                    f"Magical energy infuses the {object_id}."
                ]

            import random

            # Update object state
            game_object.state['enchanted'] = True
            game_object.state['enchantment'] = 'basic'  # Could be more complex

            notifications = []

            # Add enchantment effects
            enchantment_effect = game_object.state.get('enchantment_effect', None)
            if enchantment_effect:
                notifications.append(f"The {object_id} now has magical {enchantment_effect} properties!")

            # Apply sanity cost for magic
            notifications.append(f"Enchanting drains your mental energy.")

            return ActionResult(
                success=True,
                message=random.choice(messages),
                notifications=notifications,
                sanity_change=-2  # Enchanting costs sanity
            )

        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Your enchantment spell fails to take hold.",
                room_changed=False
            )

    def handle_disenchant(
        self,
        object_id: str,
        state: GameState
    ) -> ActionResult:
        """
        Handle removing enchantments from objects.

        Allows removing magical properties from enchanted items,
        returning them to mundane state with proper validation.

        Args:
            object_id: The object to disenchant
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 5.3
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

            # Check if object is enchanted
            is_enchanted = game_object.state.get('enchanted', False)
            is_moveable = game_object.state.get('moveable', True) # Assuming default is moveable

            if not is_moveable:
                display_name = self._get_object_names(object_id)
                return ActionResult(
                    success=False,
                    message=f"The {display_name} won't budge."
                )

            if not is_enchanted:
                return ActionResult(
                    success=False,
                    message=f"The {object_id} is not enchanted."
                )

            # Success messages with haunted atmosphere
            if state.sanity < 30:
                messages = [
                    f"You disenchant the {object_id}. The runes fade slowly, as if reluctant to disappear.",
                    f"The magic releases its hold on the {object_id}. It feels lighter, more normal.",
                    f"You strip the enchantment from the {object_id}. The house seems relieved.",
                    f"The {object_id} returns to its mundane state. The shadows seem less interested in it now."
                ]
            else:
                messages = [
                    f"You disenchant the {object_id}.",
                    f"The {object_id} is no longer enchanted.",
                    f"You successfully disenchant the {object_id}.",
                    f"The magic fades from the {object_id}."
                ]

            import random

            # Update object state
            game_object.state['enchanted'] = True
            game_object.state['enchantment'] = None

            notifications = []
            notifications.append(f"The enchantment is removed from the {object_id}.")

            # Restore some sanity as magic is more controllable now
            notifications.append("You feel more in control of reality.")

            return ActionResult(
                success=True,
                message=random.choice(messages),
                notifications=notifications,
                sanity_change=1  # Disenchanting restores sanity
            )

        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Your disenchantment spell fails to work.",
                room_changed=False
            )

    def handle_exorcise(
        self,
        object_id: str,
        direction: Optional[str],
        state: GameState
    ) -> ActionResult:
        """
        Handle exorcising supernatural influences from objects or rooms.

        Allows casting out demons, ghosts, or other supernatural entities
        from objects, locations, or the current room entirely. Includes support
        for EXORCISE OUT and EXORCISE AWAY variants.

        Args:
            object_id: The target of exorcism
            direction: Direction for exorcise (OUT/AWAY) (optional)
            state: Current game state

        Returns:
            ActionResult with success status and message

        Requirements: 5.3
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Special case: EXORCISE without target affects entire room
            if not object_id:
                return self._exorcise_room(state)

            # Check if target is in current room or inventory
            object_in_room = object_id in current_room.items
            object_in_inventory = object_id in state.inventory

            if not object_in_room and not object_in_inventory:
                return ActionResult(
                    success=False,
                    message=f"You don't see any {object_id} here."
                )

            # Get object data
            game_object = self.world.get_object(object_id)

            # Check if object is cursed or haunted
            is_cursed = game_object.state.get('cursed', False)
            is_haunted = game_object.state.get('haunted', False)
            has_supatural = game_object.state.get('supernatural', False)

            if not (is_cursed or is_haunted or has_supernatural):
                exorcise_messages = [
                    f"The {object_id} shows no signs of supernatural influence.",
                    f"There's nothing to exorcise from the {object_id}.",
                    f"The {object_id} appears completely normal.",
                    f"Your exorcism has no effect on the {object_id}."
                ]

                if state.sanity < 30:
                    exorcise_messages.append(f"The shadows laugh at your attempt to exorcise the {object_id}.")

                import random
                return ActionResult(
                    success=False,
                    message=random.choice(exorcise_messages)
                )

            # Success messages with haunted atmosphere
            if state.sanity < 30:
                messages = [
                    f"You exorcise the {object_id}. Violent energy erupts as evil is forced out!",
                    f"The {object_id} convulses as demonic presence is expelled!",
                    f"Holy power surges through the {object_id}, expelling the darkness within!",
                    f"The {object_id} shudders as supernatural influence is cast out!"
                ]
            else:
                messages = [
                    f"You exorcise the {object_id}.",
                    f"The {object_id} is cleansed of supernatural influence.",
                    f"Your exorcism successfully clears the {object_id}.",
                    f"The {object_id} has been exorcised."
                ]

            import random
            notifications = []

            # Update object state
            game_object.state['cursed'] = False
            game_object.state['haunted'] = False
            game_object.state['supernatural'] = False
            game_object.state['exorcised'] = True

            # Check for special effects
            if is_cursed:
                notifications.append(f"The curse on the {object_id} has been broken!")
            if is_haunted:
                notifications.append(f"The haunting presence in the {object_id} has been dispersed.")

            # Remove supernatural effects if any
            for key in ['ghost_effect', 'demonic_influence', 'spectral_presence']:
                if key in game_object.state:
                    del game_object.state[key]

            # Apply sanity restoration for successful exorcism
            notifications.append("You feel spiritually refreshed by your righteous act.")

            return ActionResult(
                success=True,
                message=random.choice(messages),
                notifications=notifications,
                sanity_change=3  # Exorcising restores sanity
            )

        except ValueError as e:
            return ActionResult(
                success=False,
                message=f"You don't see any {object_id} here."
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message="Your exorcism fails to take hold.",
                room_changed=False
            )

    def _exorcise_room(
        self,
        state: GameState
    ) -> ActionResult:
        """
        Handle exorcising an entire room of supernatural influence.

        Special case for EXORCISE without target - affects entire room.

        Args:
            state: Current game state

        Returns:
           ActionResult with success status and message
        """
        try:
            # Get current room
            current_room = self.world.get_room(state.current_room)

            # Check if room is haunted or cursed
            is_haunted = current_room.state.get('haunted', False)
            is_cursed = current_room.state.get('cursed', False)
            supernatural_presences = current_room.state.get('supernatural_presences', [])

            if not (is_haunted or is_cursed or supernatural_presences):
                room_messages = [
                    "This room shows no signs of supernatural influence.",
                    "There's nothing to exorcise here.",
                    "This area seems completely normal."
                    "Your exorcism has no effect here."
                ]

                if state.sanity < 30:
                    room_messages.append("The shadows find your exorcism amusing.")

                import random
                return ActionResult(
                    success=False,
                    message=random.choice(room_messages)
                )

            # Success messages with haunted atmosphere
            if state.sanity < 30:
                messages = [
                    f"You exorcise the room! Holy power floods the area, purging darkness!",
                    f"Supernatural entities flee from your righteous power!",
                    f"The room convulses as evil is forced out by divine might!",
                    f"Demonic presences scatter as your exorcism takes effect!"
                ]
            else:
                messages = [
                    f"You exorcise the entire room.",
                    "Holy energy purges the room of supernatural influence.",
                    "The room is cleansed of all supernatural influence.",
                    "Your exorcism successfully clears the area."
                ]

            import random
            notifications = []

            # Update room state
            current_room.state['haunted'] = False
            current_room.state['cursed'] = False
            current_room.state['exorcised'] = True

            # Clear supernatural presences
            if supernatural_presences:
                current_room.state['supernatural_presences'] = []
                notifications.append(f"{len(supernatural_presences)} supernatural entities have been banished!")

            # Check for room effects
            if is_haunted:
                notifications.append("The haunting energy of this room has been dispersed.")
            if is_cursed:
                notifications.append("The curse on this room has been broken.")

            # Apply sanity restoration
            notifications.append("The spiritual atmosphere improves significantly.")

            return ActionResult(
                success=True,
                message=random.choice(messages),
                notifications=notifications,
                sanity_change=5  # Room-wide exorcism restores more sanity
            )

        except Exception as e:
            return ActionResult(
                success=False,
                message="Your room-wide exorcism fails to take effect.",
                room_changed=False
            )

    def _get_usage_examples(self, verb: str) -> List[str]:
        """Get usage examples for a given verb."""
        examples = {
            'TAKE': ['take lantern', 'get sword', 'take key from chest'],
            'DROP': ['drop lantern', 'put down sword'],
            'EXAMINE': ['examine table', 'look at painting', 'check door'],
            'OPEN': ['open door', 'open chest'],
            'CLOSE': ['close door', 'shut chest'],
            'READ': ['read parchment', 'read sign'],
            'MOVE': ['move table', 'reposition chair', 'shift statue'],
            'RAISE': ['raise lever', 'lift gate', 'raise up portcullis'],
            'LOWER': ['lower bridge', 'lower drawbridge', 'lower platform'],
            'SLIDE': ['slide box', 'slide paper under door', 'slide panel'],
            'SPRING': ['spring trap', 'spring latch', 'spring open'],
            'HATCH': ['hatch egg', 'hatch container', 'hatch cocoon'],
            'APPLY': ['apply salve to wound', 'apply ointment to statue', 'apply polish to mirror'],
            'BRUSH': ['brush dust from painting', 'brush away cobwebs', 'brush clean surface'],
            'LOCK': ['lock door with key'],
            'UNLOCK': ['unlock door with key'],
            'TURN': ['turn dial', 'turn wheel', 'rotate crank'],
            'PUSH': ['push button', 'push stone'],
            'PULL': ['pull lever', 'pull rope'],
            'TIE': ['tie rope to post'],
            'UNTIE': ['untie rope'],
            'FILL': ['fill bottle with water'],
            'POUR': ['pour water on plant'],
            'BURN': ['burn paper with torch'],
            'CUT': ['cut rope with knife'],
            'DIG': ['dig with shovel'],
            'INFLATE': ['inflate boat'],
            'DEFLATE': ['deflate boat'],
            'WAVE': ['wave wand'],
            'RUB': ['rub lamp', 'touch statue'],
            'SHAKE': ['shake tree'],
            'SQUEEZE': ['squeeze sponge'],
            'WEAR': ['wear cloak', 'put on amulet', 'don armor'],
            'REMOVE': ['remove cloak', 'take off amulet', 'doff armor'],
            'EAT': ['eat bread', 'consume mushroom', 'devour apple'],
            'DRINK': ['drink water', 'quaff potion', 'swallow elixir'],
            'ATTACK': ['attack goblin with sword'],
            'THROW': ['throw rock at window'],
            'SAY': ['say hello', 'say "open sesame"', 'say I am lost'],
            'WHISPER': ['whisper secret', 'whisper "password" to guard', 'whisper to ghost'],
            'ANSWER': ['answer "42"', 'answer "riddle"', 'answer question'],
            'GIVE': ['give coin to merchant'],
            'TELL': ['tell ghost about treasure'],
            'ASK': ['ask wizard about spell'],
            'WAKE': ['wake sleeping guard'],
            'KISS': ['kiss princess'],
            'BOARD': ['board boat'],
            'ENTER': ['enter house', 'go inside'],
            'CLIMB': ['climb ladder', 'climb up'],
            # Magic system commands
            'CAST': ['cast fireball', 'cast lightning at goblin', 'cast heal with wand'],
            'INCANT': ['incant spell words', 'chant ancient verse', 'invoke magical power'],
            'CHANT': ['chant magic words', 'chant incantation', 'chant spell'],
            'ENCHANT': ['enchant sword', 'enchant amulet', 'enchant weapon'],
            'DISENCHANT': ['disenchant sword', 'disenchant amulet', 'disenchant object'],
            'EXORCISE': ['exorcise ghost', 'exorcise demon from room', 'exorcise spirit out of house'],
            # Special and easter egg commands
            'FROBOZZ': ['frobozz'],
            'ZORK': ['zork'],
            'BLAST': ['blast', 'blast door', 'blast goblin'],
            'WISH': ['wish for wealth', 'wish "I want to escape"', 'wish for power'],
            'WIN': ['win'],
            # Utility and information commands
            'FIND': ['find key', 'find sword', 'search for treasure'],
            'SEARCH FOR': ['search for key', 'search for hidden door', 'search for magic items'],
            'COUNT': ['count', 'count treasures', 'count weapons', 'count items'],
            'VERSION': ['version'],
            'DIAGNOSE': ['diagnose'],
            'SCRIPT': ['script'],
            'UNSCRIPT': ['unscript'],
            # Remaining utility and special commands
            'TREASURE': ['treasure'],
            'BUG': ['bug the door is stuck', 'bug ghost disappeared', 'bug lamp wont light'],
            'RING': ['ring bell', 'ring gong', 'ring dinner bell'],
            'CROSS': ['cross', 'cross bridge', 'cross chasm'],
            'BREATHE': ['breathe'],
            'ACTIVATE': ['activate device', 'activate mechanism', 'activate artifact'],
            # Final utility commands
            'COMMAND': ['command', 'command movement', 'command magic'],
            'CHOMP': ['chomp food', 'chomp rope', 'chomp'],
            'REPENT': ['repent'],
            'SKIP': ['skip'],
            'SPAY': ['spay'],
            'SPIN': ['spin'],
            # Atmospheric and action commands
            'SPRAY': ['spray bottle at target', 'spray water on plant', 'spray acid on lock'],
            'STAY': ['stay'],
            'WIND': ['wind clockwork toy', 'wind music box', 'wind device'],
            'windup': ['windup toy', 'windup clock', 'windup mechanism'],
            'BLOW OUT': ['blow out candle', 'blow out torch', 'blow out'],
            'BLOW UP': ['blow up balloon', 'blow up explosive'],
            'SEND FOR': ['send for help', 'send for ghost', 'send for servant']
        }
        return examples.get(verb, [f'{verb.lower()} <object>'])

    def _handle_incorrect_usage(
        self,
        verb: str,
        correct_usage: str,
        example: Optional[str] = None
    ) -> ActionResult:
        """
        Handle incorrect command usage with guidance.
        
        Provides usage examples and suggests correct syntax when
        a command is used incorrectly.
        
        Args:
            verb: The verb that was used incorrectly
            correct_usage: Description of correct usage
            example: Optional example command
            
        Returns:
            ActionResult with usage guidance
            
        Requirements: 9.2
        """
        message = f"Incorrect usage of '{verb}'.\n\nUsage: {correct_usage}"
        
        if example:
            message += f"\n\nExample: {example}"
        
        return ActionResult(
            success=False,
            message=message
        )
    
    def _handle_missing_parameter(
        self,
        verb: str,
        missing_param: str,
        examples: Optional[List[str]] = None,
        state: Optional[GameState] = None
    ) -> ActionResult:
        """
        Handle commands with missing parameters with enhanced guidance.

        Prompts for missing information with context-aware suggestions
        and interactive guidance to help complete the command correctly.

        Args:
            verb: The verb being used
            missing_param: Description of what's missing
            examples: Optional list of example commands
            state: Optional game state for context-aware suggestions

        Returns:
            ActionResult with enhanced prompt for missing information

        Requirements: 9.5
        """
        # Create contextual prompt based on verb type
        verb_lower = verb.lower()

        if verb_lower in ['take', 'get', 'carry', 'pick up']:
            message = f"What would you like to {verb_lower}?"
        elif verb_lower in ['examine', 'look at', 'check', 'search']:
            message = f"What catches your eye in the gloom?"
        elif verb_lower in ['open', 'unlock', 'break']:
            message = f"What do you seek to {verb_lower}?"
        elif verb_lower in ['give', 'offer', 'show']:
            message = f"What do you wish to {verb_lower}, and to whom?"
        elif verb_lower in ['put', 'place', 'set']:
            message = f"Where do you intend to {verb_lower} it?"
        elif verb_lower in ['turn', 'rotate', 'move']:
            message = f"What mysterious mechanism calls to you?"
        elif verb_lower in ['attack', 'hit', 'strike']:
            message = f"What stirs your anger in this haunted place?"
        else:
            message = f"What do you want to {verb_lower} {missing_param}?"

        # Add context-aware suggestions if we have game state
        if state:
            try:
                current_room = self.world.get_room(state.current_room)

                # Suggest visible objects
                if current_room.items and verb_lower in ['take', 'examine', 'open']:
                    visible_items = current_room.items[:3]  # Limit to 3
                    message += f"\n\nYou can see: {', '.join(visible_items)}"

                # Suggest inventory items for certain verbs
                if state.inventory and verb_lower in ['drop', 'give', 'put']:
                    inv_items = state.inventory[:3]
                    message += f"\n\nYou carry: {', '.join(inv_items)}"

            except Exception:
                # If we can't get context, continue without it
                pass

        # Add haunted atmosphere
        haunted_intros = [
            "The shadows wait patiently...",
            "Your voice echoes slightly in the still air.",
            "Even the dust seems to hold its breath.",
            "The house listens to your every word.",
            "Something stirs just beyond your sight."
        ]

        # Randomly add atmosphere for certain verbs
        import random
        if verb_lower in ['examine', 'search', 'listen'] and random.random() < 0.3:
            message += f"\n\n{random.choice(haunted_intros)}"

        # Add examples if provided
        if examples:
            message += "\n\nFor example:"
            for example in examples[:3]:  # Limit to 3 examples
                message += f"\n  • {example}"

        # Add helpful hint
        if verb_lower in ['go', 'move']:
            message += "\n\nTry: north, south, east, west, up, down, in, out"
        elif verb_lower in ['inventory', 'i']:
            message += "\n\nJust type 'inventory' or 'i' to see what you carry."
        elif verb_lower in ['look']:
            message += "\n\nType 'look' for a detailed description of your surroundings."

        return ActionResult(
            success=False,
            message=message
        )
    
    def check_disambiguation(
        self,
        command: ParsedCommand,
        state: GameState
    ) -> Optional[ActionResult]:
        """
        Check if command requires disambiguation and handle it.
        
        If the command refers to an ambiguous object name, prompts the player
        to clarify which object they mean. Stores disambiguation context in
        game state for follow-up resolution.
        
        Args:
            command: Parsed command
            state: Current game state
            
        Returns:
            ActionResult with disambiguation prompt if needed, None otherwise
            
        Requirements: 11.3
        """
        # Skip if no object specified
        if not command.object:
            return None
        
        # Check if we're resolving a previous disambiguation
        if state.disambiguation_context:
            # Player should be providing clarification
            # Clear context and let command proceed
            state.disambiguation_context = None
            return None
        
        # Find all matching objects
        matches = self.find_matching_objects(command.object, state)
        
        # If no matches or single match, no disambiguation needed
        if len(matches) <= 1:
            return None
        
        # Multiple matches - need disambiguation
        prompt = self.create_disambiguation_prompt(matches)
        
        # Store disambiguation context
        state.disambiguation_context = {
            'command': command.verb,
            'object': command.object,
            'matches': matches,
            'target': command.target,
            'preposition': command.preposition
        }
        
        return ActionResult(
            success=False,
            message=prompt
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
        # Handle multi-object commands
        if command.objects and len(command.objects) > 1:
            return self.handle_multi_object_command(
                command.verb,
                command.objects,
                state,
                command.target
            )
        
        # Expand 'all' or 'everything' specifiers
        if command.object and command.object.lower() in ['all', 'everything']:
            objects = self.expand_multi_object(command.object, state)
            if len(objects) > 1:
                return self.handle_multi_object_command(
                    command.verb,
                    objects,
                    state,
                    command.target
                )
            elif len(objects) == 1:
                command.object = objects[0]
            else:
                return ActionResult(
                    success=False,
                    message="There's nothing here to do that with."
                )
        
        # Check for disambiguation needs
        disambiguation_result = self.check_disambiguation(command, state)
        if disambiguation_result:
            return disambiguation_result
        
        # Validate command syntax and provide usage guidance
        syntax_validation = self._validate_command_syntax(command, state)
        if syntax_validation:
            return syntax_validation

        # Validate objects exist and provide enhanced missing object messages
        if command.object and self._should_validate_object(command.verb):
            resolved_object = self.resolve_object_name(command.object, state)
            if not resolved_object:
                return self._handle_missing_object(command.object, state, command.verb)
            # Update command object with resolved ID
            command.object = resolved_object

        # Check prerequisites
        prerequisite_result = self.check_prerequisites(command.verb, command.object, state)
        if prerequisite_result:
            return prerequisite_result
        
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

        # Handle BACK command (go back the way we came)
        if command.verb == "BACK":
            return self.handle_back(state)

        # Handle STAND command (stand up from sitting/lying)
        if command.verb == "STAND":
            return self.handle_stand(command.object, state)

        # Handle FOLLOW command (follow creature/character)
        if command.verb == "FOLLOW":
            return self.handle_follow(command.object, state)

        # Handle SWIM command
        if command.verb == "SWIM":
            return self.handle_swim(state)

        # Handle WAIT command (wait and observe)
        if command.verb == "WAIT":
            return self.handle_wait(state)

        # Handle LOOK command (look around current room)
        if command.verb == "LOOK" and not command.object:
            return self.handle_look(state)

        # Handle INVENTORY command
        if command.verb in ["INVENTORY", "I"]:
            return self.handle_inventory(state)

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

        # Handle destroy commands (format: "destroy object", "break object", "smash object")
        if command.verb == "DESTROY" and command.object:
            return self.handle_destroy(command.object, state)

        # Handle eat commands (format: "eat object", "consume object", "devour object")
        if command.verb == "EAT" and command.object:
            return self.handle_eat(command.object, state)

        # Handle drink commands (format: "drink object", "quaff object", "swallow object")
        if command.verb == "DRINK" and command.object:
            return self.handle_drink(command.object, state)

        # Handle wear commands (format: "wear object", "put on object", "don object")
        if command.verb == "WEAR" and command.object:
            return self.handle_wear(command.object, state)

        # Handle remove commands (format: "remove object", "take off object", "doff object")
        if command.verb == "REMOVE" and command.object:
            return self.handle_remove(command.object, state)

        # Handle move commands (object repositioning, separate from player movement)
        if command.verb == "MOVE" and command.object:
            return self.handle_move(command.object, state)

        # Handle raise/lower commands
        if command.verb == "RAISE" and command.object:
            return self.handle_raise(command.object, state)

        if command.verb == "LOWER" and command.object:
            return self.handle_lower(command.object, state)

        # Handle slide commands
        if command.verb == "SLIDE" and command.object:
            return self.handle_slide(command.object, command.target, state)

        # Handle special object manipulation commands
        if command.verb == "SPRING" and command.object:
            return self.handle_spring(command.object, state)

        if command.verb == "HATCH" and command.object:
            return self.handle_hatch(command.object, state)

        if command.verb == "APPLY" and command.object:
            return self.handle_apply(command.object, command.target, state)

        if command.verb == "BRUSH" and command.object:
            return self.handle_brush(command.object, state)

        # Handle object interaction commands (OPEN, CLOSE)
        if command.verb in ["OPEN", "CLOSE"] and command.object:
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
        
        # Handle cut commands (format: "cut object" or "cut object with tool")
        if command.verb == "CUT" and command.object:
            return self.handle_cut(command.object, command.target, state)
        
        # Handle dig commands (format: "dig" or "dig object" or "dig with tool")
        if command.verb == "DIG":
            return self.handle_dig(command.object, command.target, state)
        
        # Handle inflate commands
        if command.verb == "INFLATE" and command.object:
            return self.handle_inflate(command.object, state)
        
        # Handle deflate commands
        if command.verb == "DEFLATE" and command.object:
            return self.handle_deflate(command.object, state)
        
        # Handle wave commands
        if command.verb == "WAVE" and command.object:
            return self.handle_wave(command.object, state)
        
        # Handle rub commands
        if command.verb == "RUB" and command.object:
            return self.handle_rub(command.object, state)
        
        # Handle shake commands
        if command.verb == "SHAKE" and command.object:
            return self.handle_shake(command.object, state)
        
        # Handle squeeze commands
        if command.verb == "SQUEEZE" and command.object:
            return self.handle_squeeze(command.object, state)
        
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

        # Handle communication commands
        if command.verb == "SAY":
            return self.handle_say(command.object, state)

        if command.verb == "WHISPER":
            return self.handle_whisper(command.object, state)

        if command.verb == "ANSWER":
            return self.handle_answer(command.object, state)

        # Handle wake commands
        if command.verb == "WAKE" and command.object:
            return self.handle_wake(command.object, state)

        # Handle kiss commands
        if command.verb == "KISS" and command.object:
            return self.handle_kiss(command.object, state)

        # Handle magic system commands
        if command.verb == "CAST" and command.object:
            return self.handle_cast(command.object, command.target, command.instrument, state)

        if command.verb == "INCANT":
            return self.handle_cast(command.object, command.target, command.instrument, state)

        if command.verb == "CHANT" or command.verb == "INCANT":
            return self.handle_cast(command.object, command.target, command.instrument, state)

        # Handle enchant/disenchant commands
        if command.verb == "ENCHANT" and command.object:
            return self.handle_enchant(command.object, state)

        if command.verb == "DISENCHANT":
            return self.handle_disenchant(command.object, state)

        # Handle exorcise commands
        if command.verb == "EXORCISE" and command.object:
            return self.handle_exorcise(command.object, command.target, state)

        if command.verb in ["EXORCISE OUT", "EXORCISE AWAY"] and command.object:
            return self.handle_exorcise(command.object, command.verb, state)

        # Handle special and easter egg commands
        if command.verb == "FROBOZZ":
            return self.handle_frobozz(state)

        if command.verb == "ZORK":
            return self.handle_zork(state)

        if command.verb == "BLAST":
            return self.handle_blast(command.object, state)

        if command.verb == "WISH":
            return self.handle_wish(command.object, state)

        if command.verb == "WIN":
            return self.handle_win(state)
        
        # Handle easter egg commands
        if command.verb == "XYZZY":
            return self.handle_xyzzy(state)
        
        if command.verb == "PLUGH":
            return self.handle_plugh(state)
        
        if command.verb == "HELLO":
            return self.handle_hello(state)
        
        if command.verb == "PRAY":
            return self.handle_pray(state)
        
        if command.verb == "JUMP":
            return self.handle_jump(state)
        
        if command.verb == "YELL":
            return self.handle_yell(state)
        
        if command.verb == "ECHO":
            return self.handle_echo(command.object, state)
        
        # Handle profanity/curse words
        if command.verb == "CURSE":
            return self.handle_curse(state)

        # Handle utility and information commands
        if command.verb in ["FIND", "SEARCH FOR"] and command.object:
            return self.handle_find(command.object, state)

        if command.verb == "COUNT":
            return self.handle_count(command.object, state)

        if command.verb == "VERSION":
            return self.handle_version(state)

        if command.verb == "DIAGNOSE":
            return self.handle_diagnose(state)

        if command.verb == "SCRIPT":
            return self.handle_script(state)

        if command.verb == "UNSCRIPT":
            return self.handle_unscript(state)

        # Handle remaining utility and special commands
        if command.verb == "TREASURE":
            return self.handle_treasure(state)

        if command.verb == "BUG":
            return self.handle_bug(command.object, state)

        if command.verb == "RING" and command.object:
            return self.handle_ring(command.object, state)

        if command.verb == "CROSS":
            return self.handle_cross(command.object, state)

        if command.verb == "BREATHE":
            return self.handle_breathe(state)

        if command.verb == "ACTIVATE" and command.object:
            return self.handle_activate(command.object, state)

        # Handle final utility commands
        if command.verb == "COMMAND":
            return self.handle_command(command.object, state)

        if command.verb == "CHOMP" and command.object:
            return self.handle_chomp(command.object, state)

        if command.verb == "CHOMP":
            return self.handle_chomp(None, state)

        if command.verb == "REPENT":
            return self.handle_repent(state)

        if command.verb == "SKIP":
            return self.handle_skip(state)

        if command.verb == "SPAY":
            return self.handle_spay(state)

        if command.verb == "SPIN":
            return self.handle_spin(state)

        # Handle atmospheric and action commands
        if command.verb == "SPRAY" and command.object:
            return self.handle_spray(command.object, command.target, state)

        if command.verb == "STAY":
            return self.handle_stay(state)

        if command.verb == "WIND" and command.object:
            return self.handle_wind(command.object, state)

        if command.verb == "windup" and command.object:
            return self.handle_wind(command.object, state)

        if command.verb == "BLOW OUT" and command.object:
            return self.handle_blow_out(command.object, state)

        if command.verb == "BLOW UP" and command.object:
            return self.handle_blow_up(command.object, state)

        # Handle SEND FOR command
        if command.verb == "SEND FOR" and command.object:
            return self.handle_send_for(command.object, state)

        # Handle save command
        if command.verb == "SAVE":
            return self.handle_save(state)
        
        # Handle restore command (format: "restore save_id")
        if command.verb == "RESTORE":
            if not command.object:
                return ActionResult(
                    success=False,
                    message="Please specify a save ID to restore. Example: RESTORE abc123"
                )
            return self.handle_restore(command.object, state)
        
        # Handle restart command
        if command.verb == "RESTART":
            return self.handle_restart(state)
        
        # Handle score command
        if command.verb == "SCORE":
            return self.handle_score(state)
        
        # Handle verbose command
        if command.verb == "VERBOSE":
            return self.handle_verbose(state)
        
        # Handle brief command
        if command.verb == "BRIEF":
            return self.handle_brief(state)
        
        # Handle superbrief command
        if command.verb == "SUPERBRIEF":
            return self.handle_superbrief(state)
        
        # Handle unknown commands
        if command.verb == "UNKNOWN":
            return self._handle_unknown_command(command, state)
        
        # Placeholder for other command types (to be implemented in future tasks)
        return self._handle_unimplemented_command(command, state)

