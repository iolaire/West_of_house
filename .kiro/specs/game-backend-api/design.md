# Design Document

## Overview

The West of Haunted House backend is a Python-based serverless game engine deployed on AWS Lambda that resurrects the classic Zork I text adventure with Halloween-themed transformations. The system processes natural language commands, manages game state including the original Zork mechanics plus the sanity system, and serves JSON responses to a React frontend hosted on AWS Amplify.

**MVP Architecture**: The system uses AWS Lambda for compute (pay-per-invocation), DynamoDB for session storage (on-demand billing), and Amplify for hosting and API management. This serverless architecture minimizes costs while providing scalability.

The architecture follows a clean separation of concerns with distinct layers for API handling, game logic, state management, and data persistence. The engine loads haunted theme data from JSON files bundled with the Lambda deployment and dynamically selects appropriate descriptions based on game state (primarily sanity level in MVP).

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              React Frontend (AWS Amplify Hosting)           │
│  (Grimoire UI with left pane image, right pane text/input) │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTPS/JSON
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  AWS Amplify API Gateway                    │
│  - REST API endpoints                                       │
│  - Request routing                                          │
│  - CORS handling                                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              AWS Lambda Functions (Python 3.12)             │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  game_handler Lambda                                 │  │
│  │  - Command Parser                                    │  │
│  │  - Game State Manager                                │  │
│  │  - Action Executor                                   │  │
│  │  - Sanity System (MVP Halloween mechanic)           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  World Data (bundled in Lambda)                      │  │
│  │  - Rooms JSON (haunted descriptions)                 │  │
│  │  - Objects JSON (spooky interactions)                │  │
│  │  - Flags JSON (initial state)                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              AWS DynamoDB (On-Demand)                       │
│  - Session storage (game state)                             │
│  - TTL for automatic cleanup                                │
│  - Pay-per-request pricing                                  │
└─────────────────────────────────────────────────────────────┘

Cost Optimization:
- Lambda: Free tier 1M requests/month, then $0.20 per 1M
- DynamoDB: Free tier 25GB storage, then $0.25/GB
- Amplify Hosting: Free tier 15GB/month, then $0.15/GB
- Estimated cost: <$5/month for 1000 games/month
```

### Technology Stack

- **Compute**: AWS Lambda (Python 3.12 runtime)
- **API**: AWS Amplify API (REST)
- **Database**: AWS DynamoDB (on-demand billing)
- **Hosting**: AWS Amplify Hosting (React frontend)
- **Deployment**: AWS CLI + Amplify CLI (ZIP file deployment)
- **Testing**: pytest with property-based testing using Hypothesis
- **Cost Target**: <$5/month for typical usage (1000 games/month)

### AWS Services Cost Breakdown

**Lambda**:
- Free tier: 1M requests/month + 400,000 GB-seconds compute
- Beyond free tier: $0.20 per 1M requests + $0.0000166667 per GB-second
- Estimated: ~500ms per request, 128MB memory = $0.10/month for 1000 games

**DynamoDB**:
- Free tier: 25 WCU, 25 RCU, 25GB storage
- On-demand: $1.25 per million write requests, $0.25 per million read requests
- Estimated: ~10 reads + 5 writes per game = $0.02/month for 1000 games

**Amplify Hosting**:
- Free tier: 15GB served/month, 1000 build minutes/month
- Beyond free tier: $0.15/GB served, $0.01/build minute
- Estimated: ~5MB per page load = $0.50/month for 1000 games

**Total Estimated Cost**: ~$0.62/month (well under $5 target)

## Components and Interfaces

### 1. AWS Lambda API Handler

**Responsibilities:**
- Handle API Gateway events
- Validate session identifiers
- Format JSON responses
- Interact with DynamoDB for session storage
- Error handling and logging

**Lambda Function**: `game_handler`
**Runtime**: Python 3.12
**Memory**: 128MB (cost-optimized)
**Timeout**: 30 seconds
**Environment Variables**: DynamoDB table name, region

**Key API Endpoints (via Amplify API Gateway):**

```python
POST /api/game/new
    Request: {}
    Response: {
        "session_id": "uuid",
        "room": "west_of_house",
        "description": "spooky description...",
        "exits": ["NORTH", "SOUTH", "EAST", "WEST"],
        "items_visible": ["mailbox"],
        "state": {
            "sanity": 100,
            "cursed": false,
            "blood_moon_active": true,
            "souls_collected": 0,
            "score": 0,
            "moves": 0
        }
    }

POST /api/game/command
    Request: {
        "session_id": "uuid",
        "command": "go north"
    }
    Response: {
        "success": true,
        "message": "spooky response text...",
        "room": "north_of_house",
        "description": "spooky description...",
        "exits": ["SOUTH", "WEST", "EAST", "NORTH"],
        "items_visible": [],
        "inventory": ["lamp", "sword"],
        "state": {
            "sanity": 95,
            "cursed": false,
            "blood_moon_active": true,
            "souls_collected": 0,
            "score": 0,
            "moves": 1,
            "lamp_battery": 200
        },
        "notifications": ["Your sanity slips..."]
    }

GET /api/game/state/{session_id}
    Response: {
        "current_room": "west_of_house",
        "inventory": [...],
        "flags": {...},
        "state": {...}
    }

POST /api/game/save
    Request: {
        "session_id": "uuid",
        "save_name": "my_save"
    }
    Response: {
        "success": true,
        "save_id": "save_uuid"
    }

POST /api/game/load
    Request: {
        "save_id": "save_uuid"
    }
    Response: {
        "session_id": "new_uuid",
        "room": "...",
        "description": "...",
        ...
    }
```

### 2. Command Parser

**Responsibilities:**
- Parse natural language input
- Extract verbs and objects
- Handle synonyms and variations
- Provide helpful error messages

**Interface:**

```python
class CommandParser:
    def parse(self, command: str) -> ParsedCommand:
        """
        Parse natural language command into structured format.
        
        Examples:
            "go north" -> ParsedCommand(verb="GO", direction="NORTH")
            "take lamp" -> ParsedCommand(verb="TAKE", object="lamp")
            "open mailbox" -> ParsedCommand(verb="OPEN", object="mailbox")
            "attack troll with sword" -> ParsedCommand(
                verb="ATTACK", 
                target="troll", 
                instrument="sword"
            )
        """
        pass
    
    def get_synonyms(self, word: str) -> List[str]:
        """Return list of synonyms for a word."""
        pass
```

**Verb Categories:**
- Movement: GO, NORTH, SOUTH, EAST, WEST, UP, DOWN, IN, OUT
- Object manipulation: TAKE, DROP, PUT, OPEN, CLOSE, EXAMINE, READ
- Combat: ATTACK, KILL, FIGHT
- Utility: INVENTORY, LOOK, SAVE, LOAD, QUIT
- Special: MOVE (rug), RING (bell), LIGHT, EXTINGUISH

### 3. Game State Manager

**Responsibilities:**
- Track current room and inventory
- Manage all game flags
- Handle state transitions
- Persist state to session store

**Interface:**

```python
class GameState:
    session_id: str
    current_room: str
    inventory: List[str]
    flags: Dict[str, Union[bool, int]]
    rooms_visited: Set[str]
    turn_count: int
    
    # Halloween mechanics
    sanity: int  # 0-100
    cursed: bool
    blood_moon_active: bool
    souls_collected: int
    curse_duration: int
    
    # Original Zork state
    score: int
    lamp_battery: int
    lucky: bool
    thief_here: bool
    
    def move_to_room(self, room_id: str) -> None:
        """Move player to new room and trigger room effects."""
        pass
    
    def add_to_inventory(self, object_id: str) -> bool:
        """Add object to inventory if possible."""
        pass
    
    def remove_from_inventory(self, object_id: str) -> bool:
        """Remove object from inventory."""
        pass
    
    def set_flag(self, flag_name: str, value: Union[bool, int]) -> None:
        """Update a game flag."""
        pass
    
    def get_flag(self, flag_name: str) -> Union[bool, int]:
        """Get current value of a flag."""
        pass
    
    def increment_turn(self) -> None:
        """Advance turn counter and trigger turn-based effects."""
        pass
```

### 4. Action Executor

**Responsibilities:**
- Execute parsed commands
- Validate prerequisites
- Update game state
- Generate response messages

**Interface:**

```python
class ActionExecutor:
    def execute(
        self, 
        command: ParsedCommand, 
        state: GameState, 
        world: WorldData
    ) -> ActionResult:
        """Execute a command and return the result."""
        pass
    
    def handle_movement(
        self, 
        direction: str, 
        state: GameState, 
        world: WorldData
    ) -> ActionResult:
        """Handle player movement between rooms."""
        pass
    
    def handle_object_interaction(
        self, 
        verb: str, 
        object_id: str, 
        state: GameState, 
        world: WorldData
    ) -> ActionResult:
        """Handle interactions with objects."""
        pass
    
    def handle_combat(
        self, 
        target: str, 
        weapon: Optional[str], 
        state: GameState, 
        world: WorldData
    ) -> ActionResult:
        """Handle combat encounters."""
        pass
```

### 5. Halloween Mechanics Engine

**Responsibilities:**
- Manage sanity system
- Apply curse effects
- Track blood moon cycle
- Handle soul collection

**Interface:**

```python
class HalloweenMechanics:
    def apply_sanity_loss(
        self, 
        state: GameState, 
        amount: int, 
        reason: str
    ) -> List[str]:
        """
        Decrease sanity and return notification messages.
        Returns list of effects triggered.
        """
        pass
    
    def apply_sanity_gain(
        self, 
        state: GameState, 
        amount: int
    ) -> None:
        """Increase sanity (capped at 100)."""
        pass
    
    def get_description_variant(
        self, 
        base_description: str, 
        sanity_level: int
    ) -> str:
        """
        Return appropriate description based on sanity.
        100-75: Normal spooky
        74-50: Enhanced disturbed
        49-25: Unreliable narrator
        24-0: Garbled/broken
        """
        pass
    
    def apply_curse(
        self, 
        state: GameState, 
        source: str
    ) -> str:
        """Apply curse status and return notification."""
        pass
    
    def remove_curse(
        self, 
        state: GameState, 
        method: str
    ) -> str:
        """Remove curse status and return notification."""
        pass
    
    def get_curse_modifiers(
        self, 
        state: GameState
    ) -> Dict[str, float]:
        """
        Return combat/gameplay modifiers when cursed.
        Returns: {
            "damage_dealt": 0.5,
            "damage_taken": 1.5,
            "lamp_drain": 2.0
        }
        """
        pass
    
    def update_blood_moon(
        self, 
        state: GameState
    ) -> Optional[str]:
        """
        Update blood moon phase based on turn count.
        Returns notification if phase changed.
        """
        pass
    
    def is_blood_moon_active(
        self, 
        turn_count: int
    ) -> bool:
        """Check if blood moon is currently active."""
        return (turn_count % 100) < 50
    
    def award_souls(
        self, 
        state: GameState, 
        amount: int, 
        source: str
    ) -> List[str]:
        """
        Award souls and check for milestone achievements.
        Returns list of notifications/achievements.
        """
        pass
    
    def spend_souls(
        self, 
        state: GameState, 
        amount: int, 
        action: str
    ) -> bool:
        """
        Spend souls if available.
        Returns True if successful.
        """
        pass
```

### 6. World Data Loader

**Responsibilities:**
- Load JSON data files
- Provide access to room/object/flag data
- Cache loaded data

**Interface:**

```python
class WorldData:
    rooms: Dict[str, Room]
    objects: Dict[str, GameObject]
    initial_flags: Dict[str, Union[bool, int]]
    
    def load_from_json(self, data_dir: str) -> None:
        """Load all game data from JSON files."""
        pass
    
    def get_room(self, room_id: str) -> Room:
        """Get room data by ID."""
        pass
    
    def get_object(self, object_id: str) -> GameObject:
        """Get object data by ID."""
        pass
    
    def get_room_description(
        self, 
        room_id: str, 
        sanity_level: int
    ) -> str:
        """Get appropriate room description based on sanity."""
        pass
```

## Data Models

### Room Model

```python
@dataclass
class Room:
    id: str
    name: str
    description_original: str
    description_spooky: str
    exits: Dict[str, str]  # direction -> room_id
    items: List[str]  # object IDs present in room
    flags_required: Optional[Dict[str, bool]] = None  # conditional exits
    sanity_effect: int = 0  # sanity change when entering
    is_safe_room: bool = False  # for sanity restoration
    is_cursed_room: bool = False  # triggers curse effects
    is_dark: bool = False  # requires light source
```

### GameObject Model

```python
@dataclass
class GameObject:
    id: str
    name: str
    name_spooky: Optional[str]
    type: str  # "item", "container", "scenery", "npc"
    state: Dict[str, Union[bool, int, str]]
    interactions: List[Interaction]
    is_takeable: bool = False
    is_treasure: bool = False
    treasure_value: int = 0
    size: int = 1
    capacity: int = 0  # for containers
    soul_value: int = 0  # souls awarded when defeated/collected

@dataclass
class Interaction:
    verb: str
    condition: Optional[Dict[str, Any]]
    response_original: str
    response_spooky: str
    state_change: Optional[Dict[str, Any]]
    flag_change: Optional[Dict[str, Any]]
    sanity_effect: int = 0
    curse_trigger: bool = False
```

### ParsedCommand Model

```python
@dataclass
class ParsedCommand:
    verb: str
    object: Optional[str] = None
    target: Optional[str] = None
    instrument: Optional[str] = None
    direction: Optional[str] = None
    preposition: Optional[str] = None
```

### ActionResult Model

```python
@dataclass
class ActionResult:
    success: bool
    message: str
    room_changed: bool = False
    new_room: Optional[str] = None
    inventory_changed: bool = False
    state_changes: Dict[str, Any] = field(default_factory=dict)
    notifications: List[str] = field(default_factory=list)
    sanity_change: int = 0
    souls_awarded: int = 0
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Session uniqueness
*For any* two new game creations, the generated session identifiers should be different.
**Validates: Requirements 1.1**

### Property 2: Initialization consistency
*For any* new game creation, all game state variables should be initialized to the same starting values (sanity=100, cursed=false, blood_moon_active=true, souls_collected=0, score=0, moves=0).
**Validates: Requirements 1.2, 1.5**

### Property 3: Starting room consistency
*For any* new game creation, the player should always start in the "west_of_house" room.
**Validates: Requirements 1.3**

### Property 4: Command parsing determinism
*For any* command string, parsing it multiple times should always produce the same ParsedCommand result.
**Validates: Requirements 2.2**

### Property 5: Invalid command state preservation
*For any* game state and invalid command, executing the invalid command should leave the game state unchanged.
**Validates: Requirements 2.5, 16.5**

### Property 6: Movement validation
*For any* room and direction, attempting to move in that direction should succeed if and only if the room has an exit in that direction (and any required flags are set).
**Validates: Requirements 3.1, 3.4, 3.5**

### Property 7: Object conservation (take/drop)
*For any* game state, taking an object from a room and then dropping it should result in the object being back in the room and not in inventory.
**Validates: Requirements 4.2, 4.3**

### Property 8: Inventory tracking
*For any* sequence of take and drop operations, the inventory should contain exactly the objects that were taken minus the objects that were dropped.
**Validates: Requirements 5.1, 5.5**

### Property 9: Non-takeable objects
*For any* object marked as not takeable, attempting to take it should always fail and not add it to inventory.
**Validates: Requirements 5.2**

### Property 10: Sanity bounds
*For any* sequence of sanity changes, the sanity value should always remain between 0 and 100 (inclusive).
**Validates: Requirements 6.1, 6.5**

### Property 11: Sanity threshold effects
*For any* game state with sanity below 75, room and object descriptions should use the disturbed variant; below 50 should use unreliable narrator; below 25 should apply severe effects.
**Validates: Requirements 6.2, 6.3, 6.4**

### Property 12: Curse effects application
*For any* game state where cursed is true, combat calculations should apply the curse modifiers (0.5x damage dealt, 1.5x damage taken, 2x lamp drain).
**Validates: Requirements 7.2, 7.5, 14.4**

### Property 13: Blood moon cycle determinism
*For any* turn count, the blood moon phase should be deterministically calculated as (turn_count % 100) < 50.
**Validates: Requirements 8.1**

### Property 14: Blood moon sanity multiplier
*For any* sanity loss event during blood moon, the sanity decrease should be doubled compared to the same event outside blood moon.
**Validates: Requirements 8.2**

### Property 15: Soul collection accumulation
*For any* sequence of soul-awarding events, souls_collected should equal the sum of all soul values awarded minus any souls spent.
**Validates: Requirements 9.1, 9.2, 9.4, 9.5**

### Property 16: Save/load round trip
*For any* game state, saving it and then loading it should restore the exact same game state (all rooms, objects, flags, inventory, statistics).
**Validates: Requirements 10.1, 10.2, 10.3, 10.4**

### Property 17: API response format consistency
*For any* successful API request, the response should always be valid JSON with the expected schema (success, message, room, description, exits, inventory, state, notifications fields).
**Validates: Requirements 11.2, 19.2, 19.4**

### Property 18: Combat determinism
*For any* combat scenario with the same attacker, defender, weapons, and modifiers, the outcome should be deterministic (same damage, same result).
**Validates: Requirements 12.1, 12.4**

### Property 19: Score accumulation
*For any* sequence of treasure placements, the score should equal the sum of all treasure values placed in the trophy case.
**Validates: Requirements 13.1, 13.2**

### Property 20: Win condition trigger
*For any* game state where score reaches 350, the won_flag should be set to true.
**Validates: Requirements 13.4**

### Property 21: Lamp battery drain
*For any* turn where the lamp is on and curse is false, lamp_battery should decrease by exactly 1; if curse is true, it should decrease by exactly 2.
**Validates: Requirements 14.2, 14.4**

### Property 22: Lamp auto-shutoff
*For any* game state where lamp_battery reaches 0, the lamp should automatically turn off.
**Validates: Requirements 14.3**

### Property 23: Container capacity enforcement
*For any* container with capacity C, the total size of objects in the container should never exceed C.
**Validates: Requirements 15.2**

### Property 24: Container object conservation
*For any* object in a container, taking it from the container should remove it from the container and add it to inventory.
**Validates: Requirements 15.3**

### Property 25: Error status codes
*For any* invalid session ID, the API should return HTTP 404; for malformed JSON, HTTP 400; for internal errors, HTTP 500; for rate limit exceeded, HTTP 429.
**Validates: Requirements 16.1, 16.2, 16.3, 16.4**

### Property 26: Thief item return
*For any* items stolen by the thief, defeating the thief should return all stolen items to the room.
**Validates: Requirements 17.2**

### Property 27: Puzzle prerequisite enforcement
*For any* puzzle action, it should only succeed if all prerequisites are met.
**Validates: Requirements 18.1**

### Property 28: Spooky description usage
*For any* room or object description displayed, the system should use the description_spooky or response_spooky field, never the original field.
**Validates: Requirements 19.5, 20.1, 20.2**

### Property 29: Session expiration cleanup
*For any* session that has expired, running cleanup should remove it from the session store.
**Validates: Requirements 21.2, 21.4**

### Property 30: Session limit enforcement
*For any* attempt to create a new session when the limit is reached, the system should reject the request with an error.
**Validates: Requirements 21.5**

## Error Handling

### Error Categories

**1. Client Errors (4xx)**
- 400 Bad Request: Malformed JSON, invalid command syntax
- 404 Not Found: Invalid session ID, non-existent object/room
- 429 Too Many Requests: Rate limit exceeded

**2. Server Errors (5xx)**
- 500 Internal Server Error: Unexpected exceptions, data corruption
- 503 Service Unavailable: System overload, maintenance mode

### Error Response Format

```json
{
    "success": false,
    "error": {
        "code": "INVALID_SESSION",
        "message": "Session not found or expired",
        "details": "Session ID: abc123 does not exist"
    }
}
```

### Error Handling Strategy

1. **Input Validation**: Validate all inputs before processing
2. **Graceful Degradation**: Return partial results when possible
3. **State Rollback**: Revert state changes on errors
4. **Logging**: Log all errors with context for debugging
5. **User-Friendly Messages**: Provide helpful error messages without exposing internals

### Critical Error Scenarios

**Session Not Found**
- Cause: Invalid or expired session ID
- Response: 404 with clear message
- Recovery: User must start new game

**State Corruption**
- Cause: Concurrent modification, data inconsistency
- Response: 500 with generic message
- Recovery: Restore from last valid save or restart

**Rate Limit Exceeded**
- Cause: Too many requests in time window
- Response: 429 with retry-after header
- Recovery: Wait and retry

**Data Load Failure**
- Cause: Missing or corrupted JSON files
- Response: 500 on startup
- Recovery: Restore data files from backup

## Testing Strategy

### Unit Testing

**Coverage Areas:**
- Command parser: Test all verb/object combinations
- State manager: Test flag updates, inventory operations
- Action executor: Test each action type
- Halloween mechanics: Test sanity, curse, blood moon, souls
- World data loader: Test JSON parsing

**Example Unit Tests:**
```python
def test_parse_movement_command():
    parser = CommandParser()
    result = parser.parse("go north")
    assert result.verb == "GO"
    assert result.direction == "NORTH"

def test_take_object_adds_to_inventory():
    state = GameState()
    state.current_room = "living_room"
    executor = ActionExecutor()
    result = executor.execute(
        ParsedCommand(verb="TAKE", object="lamp"),
        state,
        world_data
    )
    assert "lamp" in state.inventory
    assert result.success is True

def test_sanity_cannot_exceed_100():
    mechanics = HalloweenMechanics()
    state = GameState(sanity=95)
    mechanics.apply_sanity_gain(state, 20)
    assert state.sanity == 100
```

### Property-Based Testing

**Framework**: Hypothesis (Python property-based testing library)

**Configuration**: Each property test should run a minimum of 100 iterations to ensure thorough coverage of the input space.

**Test Tagging**: Each property-based test MUST be tagged with a comment explicitly referencing the correctness property in the design document using this exact format: `# Feature: game-backend-api, Property {number}: {property_text}`

**Property Test Examples:**

```python
from hypothesis import given, strategies as st

# Feature: game-backend-api, Property 1: Session uniqueness
@given(st.integers(min_value=1, max_value=1000))
def test_session_uniqueness(num_sessions):
    """For any number of new games, all session IDs should be unique."""
    engine = GameEngine()
    session_ids = set()
    
    for _ in range(num_sessions):
        result = engine.create_new_game()
        assert result["session_id"] not in session_ids
        session_ids.add(result["session_id"])

# Feature: game-backend-api, Property 2: Initialization consistency
@given(st.integers(min_value=1, max_value=100))
def test_initialization_consistency(num_games):
    """For any new game, initial state should be consistent."""
    engine = GameEngine()
    
    for _ in range(num_games):
        result = engine.create_new_game()
        state = result["state"]
        assert state["sanity"] == 100
        assert state["cursed"] is False
        assert state["blood_moon_active"] is True
        assert state["souls_collected"] == 0
        assert state["score"] == 0
        assert state["moves"] == 0

# Feature: game-backend-api, Property 4: Command parsing determinism
@given(st.text(min_size=1, max_size=50))
def test_command_parsing_determinism(command):
    """For any command, parsing should be deterministic."""
    parser = CommandParser()
    result1 = parser.parse(command)
    result2 = parser.parse(command)
    assert result1 == result2

# Feature: game-backend-api, Property 5: Invalid command state preservation
@given(
    st.builds(GameState),
    st.text(min_size=1, max_size=50).filter(lambda x: not is_valid_command(x))
)
def test_invalid_command_preserves_state(initial_state, invalid_command):
    """For any invalid command, game state should remain unchanged."""
    engine = GameEngine()
    state_before = copy.deepcopy(initial_state)
    
    engine.execute_command(invalid_command, initial_state)
    
    assert initial_state == state_before

# Feature: game-backend-api, Property 7: Object conservation (take/drop)
@given(
    st.sampled_from(["lamp", "sword", "rope", "keys"]),
    st.sampled_from(["living_room", "kitchen", "attic"])
)
def test_take_drop_round_trip(object_id, room_id):
    """For any object, taking then dropping should return it to the room."""
    state = GameState(current_room=room_id)
    world = WorldData()
    executor = ActionExecutor()
    
    # Place object in room
    world.get_room(room_id).items.append(object_id)
    
    # Take object
    executor.execute(ParsedCommand(verb="TAKE", object=object_id), state, world)
    assert object_id in state.inventory
    assert object_id not in world.get_room(room_id).items
    
    # Drop object
    executor.execute(ParsedCommand(verb="DROP", object=object_id), state, world)
    assert object_id not in state.inventory
    assert object_id in world.get_room(room_id).items

# Feature: game-backend-api, Property 10: Sanity bounds
@given(
    st.integers(min_value=0, max_value=100),
    st.lists(st.integers(min_value=-50, max_value=50), min_size=1, max_size=20)
)
def test_sanity_bounds(initial_sanity, sanity_changes):
    """For any sequence of sanity changes, sanity should stay in [0, 100]."""
    state = GameState(sanity=initial_sanity)
    mechanics = HalloweenMechanics()
    
    for change in sanity_changes:
        if change > 0:
            mechanics.apply_sanity_gain(state, change)
        else:
            mechanics.apply_sanity_loss(state, abs(change), "test")
        
        assert 0 <= state.sanity <= 100

# Feature: game-backend-api, Property 13: Blood moon cycle determinism
@given(st.integers(min_value=0, max_value=10000))
def test_blood_moon_determinism(turn_count):
    """For any turn count, blood moon phase should be deterministic."""
    mechanics = HalloweenMechanics()
    
    expected = (turn_count % 100) < 50
    actual = mechanics.is_blood_moon_active(turn_count)
    
    assert actual == expected

# Feature: game-backend-api, Property 16: Save/load round trip
@given(st.builds(GameState))
def test_save_load_round_trip(original_state):
    """For any game state, save then load should restore exact state."""
    engine = GameEngine()
    
    # Save state
    save_data = engine.save_game(original_state)
    
    # Load state
    loaded_state = engine.load_game(save_data)
    
    # Compare all fields
    assert loaded_state.current_room == original_state.current_room
    assert loaded_state.inventory == original_state.inventory
    assert loaded_state.flags == original_state.flags
    assert loaded_state.sanity == original_state.sanity
    assert loaded_state.cursed == original_state.cursed
    assert loaded_state.blood_moon_active == original_state.blood_moon_active
    assert loaded_state.souls_collected == original_state.souls_collected
    assert loaded_state.score == original_state.score

# Feature: game-backend-api, Property 28: Spooky description usage
@given(st.sampled_from(list(world_data.rooms.keys())))
def test_spooky_descriptions_always_used(room_id):
    """For any room, the system should always use spooky descriptions."""
    world = WorldData()
    room = world.get_room(room_id)
    
    description = world.get_room_description(room_id, sanity_level=100)
    
    assert description == room.description_spooky
    assert description != room.description_original
```

### Integration Testing

**Test Scenarios:**
1. Complete game flow: New game → Move → Take objects → Solve puzzle → Win
2. Sanity degradation: Enter cursed rooms → Sanity drops → Descriptions change
3. Curse cycle: Trigger curse → Apply effects → Break curse
4. Blood moon cycle: Wait 50 turns → Blood moon ends → Effects change
5. Soul collection: Defeat enemies → Collect souls → Spend souls → Unlock abilities
6. Save/load: Play game → Save → Load → Continue from exact state
7. Combat: Attack NPC → Take damage → Defeat NPC → Collect rewards
8. Thief encounter: Thief steals → Defeat thief → Recover items

### Performance Testing

**Benchmarks:**
- Command processing: < 100ms average
- State serialization: < 50ms
- State deserialization: < 50ms
- Session lookup: < 10ms
- World data load: < 500ms (startup only)

**Load Testing:**
- Concurrent sessions: 1000+
- Requests per second: 100+
- Memory per session: < 1MB

## Deployment Considerations

### AWS Amplify Gen 2 Deployment

**Why Gen 2:**
- Resolves Gen 1 CLI environment variable resolution issues
- TypeScript-based infrastructure (code-first, type-safe)
- Better DynamoDB integration with automatic environment variables
- Modern developer experience with sandbox environments
- Future-proof approach (recommended for all new projects)

**Prerequisites:**
- Node.js v18.16.0 or later
- npm v6.14.4 or later
- AWS CLI installed and configured
- AWS account with appropriate permissions
- Python 3.12 for Lambda function development

**Gen 2 Project Structure:**
```
amplify/
├── backend.ts              # Backend definition entry point
├── data/
│   └── resource.ts         # DynamoDB table definitions
├── functions/
│   └── game-handler/
│       ├── resource.ts     # Lambda function definition (TypeScript)
│       ├── handler.py      # Python Lambda handler
│       └── requirements.txt
└── auth/
    └── resource.ts         # Auth configuration (if needed)
```

**Deployment Steps:**

1. **Create New Gen 2 Project**
```bash
npm create amplify@latest
# Project name: west-of-haunted-house
# Follow prompts to set up project structure
```

2. **Define DynamoDB Table** (`amplify/data/resource.ts`)
```typescript
import { defineData } from '@aws-amplify/backend';

export const data = defineData({
  name: 'GameSessions',
  schema: {
    GameSession: {
      sessionId: 'string',
      currentRoom: 'string',
      inventory: 'string[]',
      flags: 'json',
      sanity: 'number',
      score: 'number',
      moves: 'number',
      lampBattery: 'number',
      ttl: 'number'
    }
  }
});
```

3. **Define Lambda Function** (`amplify/functions/game-handler/resource.ts`)
```typescript
import { defineFunction } from '@aws-amplify/backend';
import { Code, Function, Runtime, Architecture } from 'aws-cdk-lib/aws-lambda';
import { Duration } from 'aws-cdk-lib';
import * as path from 'path';
import { execSync } from 'child_process';

const functionDir = path.dirname(fileURLToPath(import.meta.url));

export const gameHandler = defineFunction(
  (scope) =>
    new Function(scope, 'game-handler', {
      handler: 'index.handler',
      runtime: Runtime.PYTHON_3_12,
      architecture: Architecture.ARM_64,
      timeout: Duration.seconds(30),
      memorySize: 128,
      code: Code.fromAsset(functionDir, {
        bundling: {
          image: DockerImage.fromRegistry('dummy'),
          local: {
            tryBundle(outputDir: string) {
              // Install Python dependencies
              execSync(
                `pip install -r ${path.join(functionDir, 'requirements.txt')} -t ${outputDir} --platform manylinux2014_aarch64 --only-binary=:all:`
              );
              // Copy function code and data files
              execSync(`cp -r ${functionDir}/*.py ${outputDir}/`);
              execSync(`cp -r ${functionDir}/data ${outputDir}/`);
              return true;
            }
          }
        }
      }),
      environment: {
        TABLE_NAME: data.resources.tables.GameSessions.tableName
      }
    }),
  {
    resourceGroupName: 'api'
  }
);
```

4. **Define Backend** (`amplify/backend.ts`)
```typescript
import { defineBackend } from '@aws-amplify/backend';
import { gameHandler } from './functions/game-handler/resource';
import { data } from './data/resource';

const backend = defineBackend({
  gameHandler,
  data
});

// Grant Lambda function access to DynamoDB
backend.data.resources.tables.GameSessions.grantReadWriteData(
  backend.gameHandler.resources.lambda
);

// Add API Gateway integration
const api = backend.createRestApi('GameAPI', {
  defaultCorsPreflightOptions: {
    allowOrigins: ['*'],
    allowMethods: ['GET', 'POST'],
    allowHeaders: ['Content-Type']
  }
});

api.root.addResource('game').addResource('new').addMethod('POST', 
  new LambdaIntegration(backend.gameHandler.resources.lambda)
);

api.root.addResource('game').addResource('command').addMethod('POST',
  new LambdaIntegration(backend.gameHandler.resources.lambda)
);

api.root.addResource('game').addResource('state').addResource('{session_id}').addMethod('GET',
  new LambdaIntegration(backend.gameHandler.resources.lambda)
);
```

5. **Start Local Sandbox**
```bash
npx ampx sandbox
# Creates per-developer cloud environment for testing
```

6. **Deploy to Cloud**
```bash
# Option 1: Deploy via Git push (recommended)
git add .
git commit -m "Deploy game backend"
git push origin main

# Option 2: Manual deployment
npx ampx pipeline-deploy --branch main --app-id <app-id>
```

7. **Add Resource Tags**
All resources are automatically tagged via CDK:
```typescript
Tags.of(backend).add('Project', 'west-of-haunted-house');
Tags.of(backend).add('ManagedBy', 'vedfolnir');
Tags.of(backend).add('Environment', process.env.AMPLIFY_ENV || 'dev');
```

### IAM Roles and Permissions

**Lambda Execution Role**: `GameHandlerLambdaRole`

Least-privilege IAM policy for Lambda function:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem"
            ],
            "Resource": "arn:aws:dynamodb:us-east-1:ACCOUNT_ID:table/GameSessions"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:us-east-1:ACCOUNT_ID:log-group:/aws/lambda/gameHandler:*"
        }
    ]
}
```

**Key Security Principles:**
- No wildcard (*) permissions
- Scoped to specific DynamoDB table ARN
- No hardcoded credentials (uses IAM role)
- Separate roles for Lambda and API Gateway
- CloudWatch Logs access for debugging

**Amplify Auto-Generated Roles:**
- Amplify will automatically create IAM roles during deployment
- Review and verify permissions after deployment
- Ensure least-privilege principle is maintained

**Deployment IAM User/Role**: `West_of_house_AmplifyDeploymentUser`

Required permissions for deploying the application (for CI/CD or manual deployment):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "amplify:*"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:CreateFunction",
                "lambda:UpdateFunctionCode",
                "lambda:UpdateFunctionConfiguration",
                "lambda:GetFunction",
                "lambda:DeleteFunction",
                "lambda:AddPermission",
                "lambda:RemovePermission",
                "lambda:PublishVersion"
            ],
            "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:gameHandler*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:CreateTable",
                "dynamodb:DescribeTable",
                "dynamodb:UpdateTable",
                "dynamodb:DeleteTable",
                "dynamodb:UpdateTimeToLive",
                "dynamodb:DescribeTimeToLive"
            ],
            "Resource": "arn:aws:dynamodb:us-east-1:ACCOUNT_ID:table/GameSessions*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "apigateway:*"
            ],
            "Resource": "arn:aws:apigateway:us-east-1::/restapis/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:CreateRole",
                "iam:PutRolePolicy",
                "iam:AttachRolePolicy",
                "iam:GetRole",
                "iam:PassRole",
                "iam:DeleteRole",
                "iam:DeleteRolePolicy",
                "iam:DetachRolePolicy"
            ],
            "Resource": [
                "arn:aws:iam::ACCOUNT_ID:role/GameHandlerLambdaRole*",
                "arn:aws:iam::ACCOUNT_ID:role/amplify-*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:CreateStack",
                "cloudformation:UpdateStack",
                "cloudformation:DeleteStack",
                "cloudformation:DescribeStacks",
                "cloudformation:DescribeStackEvents",
                "cloudformation:DescribeStackResources",
                "cloudformation:GetTemplate"
            ],
            "Resource": "arn:aws:cloudformation:us-east-1:ACCOUNT_ID:stack/amplify-*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:CreateBucket",
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::amplify-*",
                "arn:aws:s3:::amplify-*/*"
            ]
        }
    ]
}
```

**Setup Instructions:**

1. **Create IAM User for Deployment**:
```bash
aws iam create-user --user-name West_of_house_AmplifyDeploymentUser
```

2. **Attach Deployment Policy**:
```bash
aws iam put-user-policy --user-name West_of_house_AmplifyDeploymentUser \
  --policy-name AmplifyDeploymentPolicy \
  --policy-document file://deployment-policy.json
```

3. **Create Access Keys**:
```bash
aws iam create-access-key --user-name West_of_house_AmplifyDeploymentUser
```

4. **Configure AWS CLI**:
```bash
aws configure --profile amplify-deploy
# Enter Access Key ID and Secret Access Key from step 3
```

5. **Use Profile for Deployment**:
```bash
export AWS_PROFILE=amplify-deploy
amplify push
```

**Security Best Practices:**
- Use separate IAM user for deployment (not root account)
- Rotate access keys regularly
- Use AWS Secrets Manager or environment variables for CI/CD
- Never commit access keys to version control
- Consider using IAM roles with temporary credentials for CI/CD

### Lambda Environment Variables

```python
{
    "DYNAMODB_TABLE": "GameSessions-dev",
    "AWS_REGION": "us-east-1",
    "SESSION_TIMEOUT": "3600",
    "LOG_LEVEL": "INFO"
}
```

### Project Structure

```
west-of-haunted-house/
├── README.md
├── .gitignore
├── project.md
│
├── documents/                    # Project documentation
│   ├── HALLOWEEN_MECHANICS.md
│   ├── HAUNTED_TRANSFORMATION.md
│   └── game_overview.md
│
├── data/                         # Game data (JSON files)
│   ├── rooms_haunted.json
│   ├── objects_haunted.json
│   └── flags_haunted.json
│
├── src/                          # Backend source code
│   ├── lambda/
│   │   ├── game_handler/
│   │   │   ├── index.py          # Lambda entry point
│   │   │   ├── game_engine.py    # Core game logic
│   │   │   ├── command_parser.py # Command parsing
│   │   │   ├── state_manager.py  # State management
│   │   │   ├── sanity_system.py  # Sanity mechanics
│   │   │   ├── world_loader.py   # Load game data
│   │   │   └── requirements.txt  # Python dependencies
│   │   └── layers/               # Shared Lambda layers
│   │       └── common/
│   │           └── python/
│   │               └── utils.py
│   └── frontend/                 # React frontend (future)
│       └── (React app files)
│
├── tests/                        # All tests
│   ├── unit/
│   │   ├── test_command_parser.py
│   │   ├── test_state_manager.py
│   │   ├── test_sanity_system.py
│   │   └── test_world_loader.py
│   ├── property/                 # Property-based tests
│   │   ├── test_properties_core.py
│   │   ├── test_properties_sanity.py
│   │   └── test_properties_state.py
│   └── integration/
│       ├── test_game_flow.py
│       └── test_api_endpoints.py
│
├── scripts/                      # Deployment and utility scripts
│   ├── deploy.sh                 # Amplify deployment script
│   ├── package_lambda.sh         # Package Lambda for deployment
│   └── estimate_costs.py         # AWS cost estimation
│
├── amplify/                      # Amplify configuration
│   ├── backend/
│   │   ├── api/
│   │   │   └── gameAPI/
│   │   ├── function/
│   │   │   └── gameHandler/
│   │   └── storage/
│   │       └── GameSessions/
│   └── team-provider-info.json
│
└── .kiro/                        # Kiro specs
    └── specs/
        └── game-backend-api/
            ├── requirements.md
            ├── design.md
            └── tasks.md
```

### Lambda Deployment Package Structure

When packaged for deployment, the Lambda function will have:

```
game_handler.zip
├── index.py                  # Entry point
├── game_engine.py
├── command_parser.py
├── state_manager.py
├── sanity_system.py
├── world_loader.py
├── data/                     # Bundled game data
│   ├── rooms_haunted.json
│   ├── objects_haunted.json
│   └── flags_haunted.json
└── (Python dependencies)     # boto3, etc.
```

### DynamoDB Table Schema

```json
{
    "TableName": "GameSessions",
    "KeySchema": [
        {
            "AttributeName": "sessionId",
            "KeyType": "HASH"
        }
    ],
    "AttributeDefinitions": [
        {
            "AttributeName": "sessionId",
            "AttributeType": "S"
        }
    ],
    "BillingMode": "PAY_PER_REQUEST",
    "TimeToLiveSpecification": {
        "Enabled": true,
        "AttributeName": "expires"
    }
}
```

### Scaling Strategy

1. **Auto-Scaling**: Lambda automatically scales based on requests
2. **DynamoDB**: On-demand billing scales automatically
3. **Caching**: World data cached in Lambda memory (warm starts)
4. **CDN**: Amplify CDN for frontend assets
5. **Cost Control**: Lambda concurrency limits to prevent runaway costs

## Security Considerations

### Input Validation

- Sanitize all user input
- Limit command length (max 500 characters)
- Validate session IDs (UUID format)
- Prevent SQL injection (use parameterized queries)
- Prevent XSS (escape output)

### Rate Limiting

- Per-session: 60 requests/minute
- Per-IP: 100 requests/minute
- Exponential backoff on repeated violations

### Session Security

- Use cryptographically secure random UUIDs
- Implement session expiration (1 hour default)
- Clear expired sessions regularly
- No sensitive data in session IDs

### CORS Configuration

```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})
```

## Monitoring and Logging

### Metrics to Track

- Request count by endpoint
- Response time percentiles (p50, p95, p99)
- Error rate by type
- Active session count
- Memory usage per session
- Command frequency distribution

### Logging Strategy

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Log levels:
# DEBUG: Command parsing details
# INFO: Game events (movement, object interactions)
# WARNING: Invalid commands, failed actions
# ERROR: Exceptions, state corruption
# CRITICAL: System failures, data loss
```

### Health Check Endpoint

```python
GET /api/health
Response: {
    "status": "healthy",
    "version": "1.0.0",
    "active_sessions": 42,
    "uptime_seconds": 3600
}
```

## Future Enhancements

1. **Multiplayer**: Shared world state, player interactions
2. **Achievements**: Track and display player accomplishments
3. **Leaderboards**: Compare scores and completion times
4. **Hints System**: Context-aware hints for stuck players
5. **Difficulty Modes**: Easy/Normal/Nightmare with different mechanics
6. **Custom Scenarios**: User-created rooms and puzzles
7. **Voice Commands**: Speech-to-text integration
8. **Mobile App**: Native iOS/Android clients
9. **Analytics**: Player behavior tracking and heatmaps
10. **Mod Support**: Plugin system for custom content
