"""
World Data Loader for West of Haunted House

This module loads game data from JSON files and provides access to rooms,
objects, and flags. It implements caching for Lambda warm starts to improve
performance.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any


@dataclass
class Room:
    """Represents a room in the game world."""
    id: str
    name: str
    description_original: str
    description_spooky: str
    exits: Dict[str, str]
    items: List[str]
    flags_required: Optional[Dict[str, bool]] = None
    sanity_effect: int = 0
    is_safe_room: bool = False
    is_cursed_room: bool = False
    is_dark: bool = False


@dataclass
class Interaction:
    """Represents an interaction with a game object."""
    verb: str
    condition: Optional[Dict[str, Any]]
    response_original: str
    response_spooky: str
    state_change: Optional[Dict[str, Any]] = None
    flag_change: Optional[Dict[str, Any]] = None
    sanity_effect: int = 0
    curse_trigger: bool = False


@dataclass
class GameObject:
    """Represents an object in the game world."""
    id: str
    name: str
    name_spooky: Optional[str]
    type: str
    state: Dict[str, Union[bool, int, str]]
    interactions: List[Interaction]
    is_takeable: bool = False
    is_treasure: bool = False
    treasure_value: int = 0
    size: int = 1
    capacity: int = 0
    contents: List[str] = field(default_factory=list)
    soul_value: int = 0


class WorldData:
    """
    Manages game world data including rooms, objects, and flags.
    Implements caching for Lambda warm starts.
    """
    
    # Class-level cache for Lambda warm starts
    _cache: Optional[Dict[str, Any]] = None
    
    def __init__(self):
        """Initialize WorldData with empty collections."""
        self.rooms: Dict[str, Room] = {}
        self.objects: Dict[str, GameObject] = {}
        self.initial_flags: Dict[str, Union[bool, int]] = {}
        self._loaded = False
    
    def load_from_json(self, data_dir: str) -> None:
        """
        Load all game data from JSON files.
        
        Uses class-level caching to improve performance on Lambda warm starts.
        
        Args:
            data_dir: Directory containing JSON data files
            
        Raises:
            FileNotFoundError: If data files are missing
            json.JSONDecodeError: If JSON files are malformed
            ValueError: If required fields are missing
        """
        # Check if we have cached data
        if WorldData._cache is not None:
            self._load_from_cache()
            return
        
        # Load fresh data from files
        try:
            rooms_path = os.path.join(data_dir, 'rooms_haunted.json')
            objects_path = os.path.join(data_dir, 'objects_haunted.json')
            flags_path = os.path.join(data_dir, 'flags_haunted.json')
            
            # Verify files exist
            if not os.path.exists(rooms_path):
                raise FileNotFoundError(f"Rooms data file not found: {rooms_path}")
            if not os.path.exists(objects_path):
                raise FileNotFoundError(f"Objects data file not found: {objects_path}")
            if not os.path.exists(flags_path):
                raise FileNotFoundError(f"Flags data file not found: {flags_path}")
            
            # Load rooms
            with open(rooms_path, 'r') as f:
                rooms_data = json.load(f)
                self._load_rooms(rooms_data)
            
            # Load objects
            with open(objects_path, 'r') as f:
                objects_data = json.load(f)
                self._load_objects(objects_data)
            
            # Load flags
            with open(flags_path, 'r') as f:
                self.initial_flags = json.load(f)
            
            # Cache the loaded data
            WorldData._cache = {
                'rooms': self.rooms,
                'objects': self.objects,
                'initial_flags': self.initial_flags
            }
            
            self._loaded = True
            
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Malformed JSON in data files: {e.msg}",
                e.doc,
                e.pos
            )
        except FileNotFoundError:
            # Re-raise FileNotFoundError without wrapping
            raise
        except Exception as e:
            raise ValueError(f"Error loading world data: {str(e)}")
    
    def _load_from_cache(self) -> None:
        """Load data from class-level cache."""
        if WorldData._cache is None:
            raise ValueError("Cache is empty")
        
        self.rooms = WorldData._cache['rooms']
        self.objects = WorldData._cache['objects']
        self.initial_flags = WorldData._cache['initial_flags']
        self._loaded = True
    
    def _load_rooms(self, rooms_data: Dict[str, Any]) -> None:
        """
        Parse and load room data.
        
        Args:
            rooms_data: Dictionary of room data from JSON
            
        Raises:
            ValueError: If required fields are missing
        """
        for room_id, room_dict in rooms_data.items():
            try:
                # Validate required fields
                required_fields = ['name', 'description_spooky', 'exits', 'items']
                for field in required_fields:
                    if field not in room_dict:
                        raise ValueError(f"Room {room_id} missing required field: {field}")
                
                room = Room(
                    id=room_id,
                    name=room_dict['name'],
                    description_original=room_dict.get('description_original', ''),
                    description_spooky=room_dict['description_spooky'],
                    exits=room_dict['exits'],
                    items=room_dict['items'],
                    flags_required=room_dict.get('flags_required'),
                    sanity_effect=room_dict.get('sanity_effect', 0),
                    is_safe_room=room_dict.get('is_safe_room', False),
                    is_cursed_room=room_dict.get('is_cursed_room', False),
                    is_dark=room_dict.get('is_dark', False)
                )
                self.rooms[room_id] = room
            except Exception as e:
                raise ValueError(f"Error loading room {room_id}: {str(e)}")
    
    def _load_objects(self, objects_data: Dict[str, Any]) -> None:
        """
        Parse and load object data.
        
        Args:
            objects_data: Dictionary of object data from JSON
            
        Raises:
            ValueError: If required fields are missing
        """
        for object_id, object_dict in objects_data.items():
            try:
                # Validate required fields
                required_fields = ['name', 'type', 'state', 'interactions']
                for field in required_fields:
                    if field not in object_dict:
                        raise ValueError(f"Object {object_id} missing required field: {field}")
                
                # Parse interactions
                interactions = []
                for interaction_dict in object_dict['interactions']:
                    interaction = Interaction(
                        verb=interaction_dict['verb'],
                        condition=interaction_dict.get('condition'),
                        response_original=interaction_dict.get('response_original', ''),
                        response_spooky=interaction_dict['response_spooky'],
                        state_change=interaction_dict.get('state_change'),
                        flag_change=interaction_dict.get('flag_change'),
                        sanity_effect=interaction_dict.get('sanity_effect', 0),
                        curse_trigger=interaction_dict.get('curse_trigger', False)
                    )
                    interactions.append(interaction)
                
                game_object = GameObject(
                    id=object_id,
                    name=object_dict['name'],
                    name_spooky=object_dict.get('name_spooky'),
                    type=object_dict['type'],
                    state=object_dict['state'],
                    interactions=interactions,
                    is_takeable=object_dict.get('is_takeable', False),
                    is_treasure=object_dict.get('is_treasure', False),
                    treasure_value=object_dict.get('treasure_value', 0),
                    size=object_dict.get('size', 1),
                    capacity=object_dict.get('capacity', 0),
                    contents=object_dict.get('contents', []),
                    soul_value=object_dict.get('soul_value', 0)
                )
                self.objects[object_id] = game_object
            except Exception as e:
                raise ValueError(f"Error loading object {object_id}: {str(e)}")
    
    def get_room(self, room_id: str) -> Room:
        """
        Get room data by ID.
        
        Args:
            room_id: The room identifier
            
        Returns:
            Room object
            
        Raises:
            ValueError: If room not found or data not loaded
        """
        if not self._loaded:
            raise ValueError("World data not loaded. Call load_from_json() first.")
        
        if room_id not in self.rooms:
            raise ValueError(f"Room not found: {room_id}")
        
        return self.rooms[room_id]
    
    def get_object(self, object_id: str) -> GameObject:
        """
        Get object data by ID.
        
        Args:
            object_id: The object identifier
            
        Returns:
            GameObject object
            
        Raises:
            ValueError: If object not found or data not loaded
        """
        if not self._loaded:
            raise ValueError("World data not loaded. Call load_from_json() first.")
        
        if object_id not in self.objects:
            raise ValueError(f"Object not found: {object_id}")
        
        return self.objects[object_id]
    
    def find_object_by_name(self, name: str, available_objects: List[str]) -> Optional[str]:
        """
        Find object ID by flexible name matching.
        
        Matches against:
        - Object ID (exact or partial)
        - Display name (exact or partial)
        - Spooky name (exact or partial)
        
        Args:
            name: The name to search for (e.g., "parchment", "cursed", "leaflet")
            available_objects: List of object IDs to search within
            
        Returns:
            Object ID if found, None otherwise
        """
        if not self._loaded:
            return None
        
        name_lower = name.lower().strip()
        
        # First pass: exact ID match
        if name_lower in available_objects:
            return name_lower
        
        # Second pass: check if name matches object ID, display name, or spooky name
        for obj_id in available_objects:
            if obj_id not in self.objects:
                continue
            
            obj = self.objects[obj_id]
            
            # Check object ID (with underscores replaced by spaces)
            if name_lower == obj_id.replace('_', ' '):
                return obj_id
            
            # Check display name
            if obj.name and name_lower == obj.name.lower():
                return obj_id
            
            # Check spooky name
            if obj.name_spooky and name_lower == obj.name_spooky.lower():
                return obj_id
        
        # Third pass: partial matches (any word in the name)
        for obj_id in available_objects:
            if obj_id not in self.objects:
                continue
            
            obj = self.objects[obj_id]
            
            # Check if name is a word in object ID
            obj_id_words = obj_id.replace('_', ' ').lower().split()
            if name_lower in obj_id_words:
                return obj_id
            
            # Check if name is a word in display name
            if obj.name:
                name_words = obj.name.lower().split()
                if name_lower in name_words:
                    return obj_id
            
            # Check if name is a word in spooky name
            if obj.name_spooky:
                spooky_words = obj.name_spooky.lower().split()
                if name_lower in spooky_words:
                    return obj_id
        
        return None
    
    def get_room_description(self, room_id: str, sanity_level: int) -> str:
        """
        Get appropriate room description based on sanity level.
        
        Always returns spooky description as per requirements.
        
        Args:
            room_id: The room identifier
            sanity_level: Current sanity level (0-100)
            
        Returns:
            Room description string
            
        Raises:
            ValueError: If room not found
        """
        room = self.get_room(room_id)
        # Always use spooky description per requirements 19.5, 20.1
        return room.description_spooky
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear the class-level cache. Useful for testing."""
        cls._cache = None
