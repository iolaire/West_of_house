"""
Game State Manager for West of Haunted House

This module manages game state including player location, inventory, flags,
and statistics. It provides serialization/deserialization for DynamoDB storage
and state manipulation methods.
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Set, Union, Any, Optional
from datetime import datetime, timedelta


@dataclass
class GameState:
    """
    Represents the complete state of a game session.
    
    Includes player location, inventory, game flags, Halloween mechanics
    (sanity, curse, blood moon, souls), and original Zork statistics.
    """
    
    # Session identification
    session_id: str
    
    # Player location and inventory
    current_room: str
    inventory: List[str] = field(default_factory=list)
    current_vehicle: Optional[str] = None  # Track which vehicle player is in
    
    # Game flags (boolean and numeric state variables)
    flags: Dict[str, Union[bool, int]] = field(default_factory=dict)
    
    # Rooms visited tracking
    rooms_visited: Set[str] = field(default_factory=set)
    
    # Turn counter
    turn_count: int = 0
    
    # Halloween mechanics (MVP focus)
    sanity: int = 100  # 0-100 scale
    cursed: bool = False
    blood_moon_active: bool = True
    souls_collected: int = 0
    curse_duration: int = 0
    
    # Original Zork state
    score: int = 0
    moves: int = 0
    lamp_battery: int = 200
    lucky: bool = False
    thief_here: bool = False
    
    # Session metadata
    created_at: Optional[str] = None
    last_accessed: Optional[str] = None
    expires: Optional[int] = None  # Unix timestamp for DynamoDB TTL
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.last_accessed is None:
            self.last_accessed = datetime.utcnow().isoformat()
    
    def move_to_room(self, room_id: str) -> None:
        """
        Move player to a new room and track visited rooms.
        
        Args:
            room_id: The target room identifier
        """
        self.current_room = room_id
        self.rooms_visited.add(room_id)
        self.last_accessed = datetime.utcnow().isoformat()
    
    def add_to_inventory(self, object_id: str) -> bool:
        """
        Add an object to the player's inventory.
        
        Args:
            object_id: The object identifier to add
            
        Returns:
            True if added successfully, False if already in inventory
        """
        if object_id in self.inventory:
            return False
        self.inventory.append(object_id)
        self.last_accessed = datetime.utcnow().isoformat()
        return True
    
    def remove_from_inventory(self, object_id: str) -> bool:
        """
        Remove an object from the player's inventory.
        
        Args:
            object_id: The object identifier to remove
            
        Returns:
            True if removed successfully, False if not in inventory
        """
        if object_id not in self.inventory:
            return False
        self.inventory.remove(object_id)
        self.last_accessed = datetime.utcnow().isoformat()
        return True
    
    def set_flag(self, flag_name: str, value: Union[bool, int]) -> None:
        """
        Update a game flag.
        
        Args:
            flag_name: The flag identifier
            value: The new flag value (boolean or integer)
        """
        self.flags[flag_name] = value
        self.last_accessed = datetime.utcnow().isoformat()
    
    def get_flag(self, flag_name: str, default: Union[bool, int] = False) -> Union[bool, int]:
        """
        Get the current value of a game flag.
        
        Args:
            flag_name: The flag identifier
            default: Default value if flag doesn't exist
            
        Returns:
            The flag value or default if not set
        """
        return self.flags.get(flag_name, default)
    
    def increment_turn(self) -> None:
        """
        Advance the turn counter and trigger turn-based effects.
        
        Updates moves counter, turn count, and last accessed timestamp.
        """
        self.turn_count += 1
        self.moves += 1
        self.last_accessed = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize game state to a dictionary for DynamoDB storage.
        
        Converts sets to lists for JSON compatibility.
        
        Returns:
            Dictionary representation of game state
        """
        state_dict = asdict(self)
        # Convert set to list for JSON serialization
        state_dict['rooms_visited'] = list(self.rooms_visited)
        return state_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameState':
        """
        Deserialize game state from a dictionary.
        
        Converts lists back to sets where appropriate.
        
        Args:
            data: Dictionary containing game state data
            
        Returns:
            GameState instance
        """
        # Convert rooms_visited list back to set
        if 'rooms_visited' in data and isinstance(data['rooms_visited'], list):
            data['rooms_visited'] = set(data['rooms_visited'])
        
        return cls(**data)
    
    def to_json(self) -> str:
        """
        Serialize game state to JSON string.
        
        Returns:
            JSON string representation of game state
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'GameState':
        """
        Deserialize game state from JSON string.
        
        Args:
            json_str: JSON string containing game state
            
        Returns:
            GameState instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def create_new_game(cls, starting_room: str = "west_of_house") -> 'GameState':
        """
        Create a new game state with default starting values.
        
        Args:
            starting_room: The room where the player starts (default: "west_of_house")
            
        Returns:
            New GameState instance with initial values
        """
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Set TTL to 1 hour from now (3600 seconds)
        expires = int((now + timedelta(hours=1)).timestamp())
        
        return cls(
            session_id=session_id,
            current_room=starting_room,
            inventory=[],
            flags={},
            rooms_visited={starting_room},
            turn_count=0,
            sanity=100,
            cursed=False,
            blood_moon_active=True,
            souls_collected=0,
            curse_duration=0,
            score=0,
            moves=0,
            lamp_battery=200,
            lucky=False,
            thief_here=False,
            created_at=now.isoformat(),
            last_accessed=now.isoformat(),
            expires=expires
        )
    
    def update_ttl(self, hours: int = 1) -> None:
        """
        Update the TTL (Time To Live) for session expiration.
        
        Args:
            hours: Number of hours until expiration (default: 1)
        """
        now = datetime.utcnow()
        self.expires = int((now + timedelta(hours=hours)).timestamp())
        self.last_accessed = now.isoformat()



class SessionManager:
    """
    Manages game session persistence in DynamoDB.
    
    Provides operations for saving, loading, and deleting game sessions
    with proper error handling and TTL management.
    """
    
    def __init__(self, dynamodb_client, table_name: str):
        """
        Initialize SessionManager with DynamoDB client.
        
        Args:
            dynamodb_client: boto3 DynamoDB client or resource
            table_name: Name of the DynamoDB table for sessions
        """
        self.dynamodb = dynamodb_client
        self.table_name = table_name
    
    def save_session(self, state: GameState) -> bool:
        """
        Save game state to DynamoDB with TTL.
        
        Args:
            state: GameState instance to save
            
        Returns:
            True if save successful, False otherwise
            
        Raises:
            Exception: If DynamoDB operation fails
        """
        try:
            # Update last accessed timestamp and TTL
            state.update_ttl(hours=1)
            
            # Convert state to dictionary
            item = state.to_dict()
            
            # Ensure session_id is the partition key
            item['sessionId'] = state.session_id
            
            # Put item in DynamoDB
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item=self._serialize_item(item)
            )
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to save session {state.session_id}: {str(e)}")
    
    def load_session(self, session_id: str) -> Optional[GameState]:
        """
        Load game state from DynamoDB.
        
        Args:
            session_id: The session identifier to load
            
        Returns:
            GameState instance if found, None if not found
            
        Raises:
            Exception: If DynamoDB operation fails
        """
        try:
            # Get item from DynamoDB
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={'sessionId': {'S': session_id}}
            )
            
            # Check if item exists
            if 'Item' not in response:
                return None
            
            # Deserialize item
            item = self._deserialize_item(response['Item'])
            
            # Create GameState from dictionary
            state = GameState.from_dict(item)
            
            # Update last accessed timestamp
            state.last_accessed = datetime.utcnow().isoformat()
            
            return state
            
        except Exception as e:
            raise Exception(f"Failed to load session {session_id}: {str(e)}")
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a game session from DynamoDB.
        
        Args:
            session_id: The session identifier to delete
            
        Returns:
            True if deletion successful, False otherwise
            
        Raises:
            Exception: If DynamoDB operation fails
        """
        try:
            # Delete item from DynamoDB
            self.dynamodb.delete_item(
                TableName=self.table_name,
                Key={'sessionId': {'S': session_id}}
            )
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to delete session {session_id}: {str(e)}")
    
    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists in DynamoDB.
        
        Args:
            session_id: The session identifier to check
            
        Returns:
            True if session exists, False otherwise
        """
        try:
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={'sessionId': {'S': session_id}},
                ProjectionExpression='sessionId'
            )
            
            return 'Item' in response
            
        except Exception:
            return False
    
    def _serialize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize Python dictionary to DynamoDB format.
        
        Args:
            item: Python dictionary to serialize
            
        Returns:
            DynamoDB-formatted dictionary
        """
        serialized = {}
        
        for key, value in item.items():
            if value is None:
                continue
            elif isinstance(value, str):
                serialized[key] = {'S': value}
            elif isinstance(value, bool):
                serialized[key] = {'BOOL': value}
            elif isinstance(value, int):
                serialized[key] = {'N': str(value)}
            elif isinstance(value, float):
                serialized[key] = {'N': str(value)}
            elif isinstance(value, list):
                if len(value) == 0:
                    serialized[key] = {'L': []}
                elif isinstance(value[0], str):
                    serialized[key] = {'SS': value} if len(value) > 0 else {'L': []}
                else:
                    serialized[key] = {'L': [self._serialize_value(v) for v in value]}
            elif isinstance(value, dict):
                serialized[key] = {'M': self._serialize_item(value)}
            else:
                serialized[key] = {'S': str(value)}
        
        return serialized
    
    def _serialize_value(self, value: Any) -> Dict[str, Any]:
        """
        Serialize a single value to DynamoDB format.
        
        Args:
            value: Value to serialize
            
        Returns:
            DynamoDB-formatted value
        """
        if value is None:
            return {'NULL': True}
        elif isinstance(value, str):
            return {'S': value}
        elif isinstance(value, bool):
            return {'BOOL': value}
        elif isinstance(value, (int, float)):
            return {'N': str(value)}
        elif isinstance(value, list):
            return {'L': [self._serialize_value(v) for v in value]}
        elif isinstance(value, dict):
            return {'M': self._serialize_item(value)}
        else:
            return {'S': str(value)}
    
    def _deserialize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deserialize DynamoDB item to Python dictionary.
        
        Args:
            item: DynamoDB-formatted item
            
        Returns:
            Python dictionary
        """
        deserialized = {}
        
        for key, value in item.items():
            if 'S' in value:
                deserialized[key] = value['S']
            elif 'N' in value:
                # Try to convert to int, fall back to float
                try:
                    deserialized[key] = int(value['N'])
                except ValueError:
                    deserialized[key] = float(value['N'])
            elif 'BOOL' in value:
                deserialized[key] = value['BOOL']
            elif 'SS' in value:
                deserialized[key] = value['SS']
            elif 'L' in value:
                deserialized[key] = [self._deserialize_value(v) for v in value['L']]
            elif 'M' in value:
                deserialized[key] = self._deserialize_item(value['M'])
            elif 'NULL' in value:
                deserialized[key] = None
        
        return deserialized
    
    def _deserialize_value(self, value: Dict[str, Any]) -> Any:
        """
        Deserialize a single DynamoDB value.
        
        Args:
            value: DynamoDB-formatted value
            
        Returns:
            Python value
        """
        if 'S' in value:
            return value['S']
        elif 'N' in value:
            try:
                return int(value['N'])
            except ValueError:
                return float(value['N'])
        elif 'BOOL' in value:
            return value['BOOL']
        elif 'L' in value:
            return [self._deserialize_value(v) for v in value['L']]
        elif 'M' in value:
            return self._deserialize_item(value['M'])
        elif 'NULL' in value:
            return None
        else:
            return None
