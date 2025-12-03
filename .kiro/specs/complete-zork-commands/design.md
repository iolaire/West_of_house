# Design Document: Complete Zork Command Implementation

## Overview

This design addresses the systematic implementation of all original Zork I commands in the West of Haunted House game engine. The current implementation has many commands returning "not yet implemented" messages. This feature will provide complete command coverage, ensuring players can interact with the game world using the full vocabulary of the original Zork I, adapted for the haunted theme.

The implementation will follow a phased approach:
1. Audit existing commands against Zork I source
2. Implement core missing commands (movement, object manipulation)
3. Implement utility commands (burn, cut, dig, etc.)
4. Implement meta-game commands (save, restore, verbosity)
5. Implement special/easter egg commands
6. Ensure all commands use haunted theme descriptions

## Architecture

### Command Processing Flow

```
Player Input
    ↓
Command Parser (existing)
    ↓
Parsed Command Object
    ↓
Game Engine Router (execute_command)
    ↓
Command Handler (new/updated)
    ↓
Action Result
    ↓
Response to Player
```

### Component Responsibilities

**Command Parser** (existing `command_parser.py`):
- Tokenizes player input
- Identifies verbs, objects, prepositions
- Handles synonyms and abbreviations
- Returns ParsedCommand object

**Game Engine** (`game_engine.py`):
- Routes commands to appropriate handlers
- Maintains game state consistency
- Applies side effects (sanity, flags, etc.)
- Returns ActionResult objects

**Command Handlers** (new methods in `game_engine.py`):
- Implement specific command logic
- Validate prerequisites
- Update object and game state
- Generate thematic responses

**World Data** (existing `world_loader.py`):
- Provides object properties
- Defines interaction rules
- Stores object states

## Components and Interfaces

### New Command Handler Methods

Each command category will have dedicated handler methods in the GameEngine class:

```python
# Movement commands
def handle_climb(self, direction: str, object_id: Optional[str], state: GameState) -> ActionResult
def handle_enter(self, object_id: Optional[str], state: GameState) -> ActionResult
def handle_exit(self, object_id: Optional[str], state: GameState) -> ActionResult
def handle_board(self, vehicle_id: str, state: GameState) -> ActionResult
def handle_disembark(self, vehicle_id: Optional[str], state: GameState) -> ActionResult

# Object manipulation commands
def handle_lock(self, object_id: str, key_id: str, state: GameState) -> ActionResult
def handle_unlock(self, object_id: str, key_id: str, state: GameState) -> ActionResult
def handle_turn(self, object_id: str, state: GameState) -> ActionResult
def handle_push(self, object_id: str, state: GameState) -> ActionResult
def handle_pull(self, object_id: str, state: GameState) -> ActionResult
def handle_tie(self, object_id: str, target_id: str, state: GameState) -> ActionResult
def handle_untie(self, object_id: str, state: GameState) -> ActionResult
def handle_fill(self, container_id: str, source_id: str, state: GameState) -> ActionResult
def handle_pour(self, container_id: str, target_id: Optional[str], state: GameState) -> ActionResult

# Examination commands
def handle_look_under(self, object_id: str, state: GameState) -> ActionResult
def handle_look_behind(self, object_id: str, state: GameState) -> ActionResult
def handle_search(self, object_id: str, state: GameState) -> ActionResult
def handle_read(self, object_id: str, state: GameState) -> ActionResult
def handle_listen(self, object_id: Optional[str], state: GameState) -> ActionResult
def handle_smell(self, object_id: Optional[str], state: GameState) -> ActionResult

# Combat/interaction commands
def handle_attack(self, target_id: str, weapon_id: Optional[str], state: GameState) -> ActionResult
def handle_throw(self, object_id: str, target_id: str, state: GameState) -> ActionResult
def handle_give(self, object_id: str, npc_id: str, state: GameState) -> ActionResult
def handle_tell(self, npc_id: str, message: Optional[str], state: GameState) -> ActionResult
def handle_wake(self, creature_id: str, state: GameState) -> ActionResult
def handle_kiss(self, npc_id: str, state: GameState) -> ActionResult

# Utility commands
def handle_burn(self, object_id: str, fire_source_id: str, state: GameState) -> ActionResult
def handle_cut(self, object_id: str, tool_id: str, state: GameState) -> ActionResult
def handle_dig(self, location: str, tool_id: Optional[str], state: GameState) -> ActionResult
def handle_inflate(self, object_id: str, tool_id: Optional[str], state: GameState) -> ActionResult
def handle_deflate(self, object_id: str, state: GameState) -> ActionResult
def handle_wave(self, object_id: str, state: GameState) -> ActionResult
def handle_rub(self, object_id: str, state: GameState) -> ActionResult
def handle_shake(self, object_id: str, state: GameState) -> ActionResult
def handle_squeeze(self, object_id: str, state: GameState) -> ActionResult

# Meta-game commands
def handle_save(self, state: GameState) -> ActionResult
def handle_restore(self, save_id: str, state: GameState) -> ActionResult
def handle_restart(self, state: GameState) -> ActionResult
def handle_score(self, state: GameState) -> ActionResult
def handle_verbose(self, state: GameState) -> ActionResult
def handle_brief(self, state: GameState) -> ActionResult
def handle_superbrief(self, state: GameState) -> ActionResult

# Special commands
def handle_easter_egg(self, command: str, state: GameState) -> ActionResult
def handle_hello(self, state: GameState) -> ActionResult
def handle_curse(self, state: GameState) -> ActionResult
def handle_pray(self, state: GameState) -> ActionResult
def handle_jump(self, state: GameState) -> ActionResult
def handle_yell(self, state: GameState) -> ActionResult
def handle_echo(self, text: str, state: GameState) -> ActionResult
```

### Enhanced ParsedCommand Object

The existing ParsedCommand dataclass may need additional fields:

```python
@dataclass
class ParsedCommand:
    verb: str                    # Primary verb (OPEN, TAKE, etc.)
    object: Optional[str]        # Primary object
    target: Optional[str]        # Secondary object
    direction: Optional[str]     # Direction for movement
    preposition: Optional[str]   # Preposition (IN, ON, WITH, etc.)
    modifiers: List[str]         # Additional modifiers
    raw_input: str              # Original player input
```

### Object Property Extensions

Some objects will need new properties in the JSON data:

```json
{
  "id": "rope",
  "type": "tool",
  "properties": {
    "is_rope": true,
    "can_tie": true,
    "tie_targets": ["hook", "railing"]
  }
}
```

```json
{
  "id": "boat",
  "type": "vehicle",
  "properties": {
    "is_vehicle": true,
    "capacity": 2,
    "requires_water": true
  }
}
```

## Data Models

### Command Category Enum

```python
from enum import Enum

class CommandCategory(Enum):
    MOVEMENT = "movement"
    OBJECT_MANIPULATION = "object_manipulation"
    EXAMINATION = "examination"
    COMBAT = "combat"
    UTILITY = "utility"
    META_GAME = "meta_game"
    SPECIAL = "special"
```

### Command Registry

A registry mapping verbs to handlers and categories:

```python
COMMAND_REGISTRY = {
    "CLIMB": {
        "handler": "handle_climb",
        "category": CommandCategory.MOVEMENT,
        "requires_object": True,
        "requires_direction": True
    },
    "OPEN": {
        "handler": "handle_object_interaction",
        "category": CommandCategory.OBJECT_MANIPULATION,
        "requires_object": True
    },
    "BURN": {
        "handler": "handle_burn",
        "category": CommandCategory.UTILITY,
        "requires_object": True,
        "requires_tool": True
    },
    # ... etc
}
```

### Verbosity State

Add to GameState:

```python
class VerbosityLevel(Enum):
    VERBOSE = "verbose"      # Full descriptions always
    BRIEF = "brief"          # Full on first visit, brief after
    SUPERBRIEF = "superbrief"  # Room name only

@dataclass
class GameState:
    # ... existing fields ...
    verbosity: VerbosityLevel = VerbosityLevel.BRIEF
    visited_rooms: Set[str] = field(default_factory=set)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Climb movement consistency
*For any* climbable object and valid direction (UP/DOWN), executing CLIMB should result in the player moving to the connected room in that direction
**Validates: Requirements 2.1**

### Property 2: Enter/Exit inverse operations
*For any* room with an entrance, entering then immediately exiting should return the player to the original room (round-trip property)
**Validates: Requirements 2.2**

### Property 3: Board/Disembark inverse operations
*For any* vehicle object, boarding then immediately disembarking should return the player to the original location (round-trip property)
**Validates: Requirements 2.3, 2.4**

### Property 4: Open/Close inverse operations
*For any* closeable object, opening then closing should return the object to its original closed state (round-trip property)
**Validates: Requirements 3.1, 3.2**

### Property 5: Lock/Unlock inverse operations
*For any* lockable object and appropriate key, locking then unlocking should return the object to its original unlocked state (round-trip property)
**Validates: Requirements 3.3**

### Property 6: Turn command state changes
*For any* turnable object, executing TURN should change the object's state (rotation, activation, etc.)
**Validates: Requirements 3.4**

### Property 7: Push/Pull object relocation
*For any* moveable object, executing PUSH or PULL should change the object's location or position state
**Validates: Requirements 3.5**

### Property 8: Tie/Untie inverse operations
*For any* rope-like object and valid target, tying then untying should return objects to their original unbound state (round-trip property)
**Validates: Requirements 3.6**

### Property 9: Fill/Pour inverse operations
*For any* container and liquid source, filling then pouring should return the container to its original empty state (round-trip property)
**Validates: Requirements 3.7, 3.8**

### Property 10: Examine returns descriptions
*For any* object in the game world, executing EXAMINE should return a non-empty description string
**Validates: Requirements 4.1**

### Property 11: Look under/behind reveals information
*For any* object, executing LOOK UNDER or LOOK BEHIND should return a response (either revealing something or stating nothing is there)
**Validates: Requirements 4.2**

### Property 12: Look inside container contents
*For any* open or transparent container, executing LOOK INSIDE should list all objects currently in the container
**Validates: Requirements 4.3**

### Property 13: Search reveals details
*For any* object or location, executing SEARCH should return a response describing what is found or not found
**Validates: Requirements 4.4**

### Property 14: Read displays text
*For any* readable object, executing READ should return the text content of that object
**Validates: Requirements 4.5**

### Property 15: Listen provides audio information
*For any* object or room, executing LISTEN should return a description of audible information
**Validates: Requirements 4.6**

### Property 16: Smell provides olfactory information
*For any* object or room, executing SMELL should return a description of olfactory information
**Validates: Requirements 4.7**

### Property 17: Attack initiates combat
*For any* creature and weapon, executing ATTACK should change the combat state (creature health, player status, etc.)
**Validates: Requirements 5.1**

### Property 18: Throw relocates object
*For any* throwable object and target, executing THROW should change the object's location
**Validates: Requirements 5.2**

### Property 19: Give transfers ownership
*For any* object and NPC, executing GIVE should transfer the object from player inventory to NPC possession
**Validates: Requirements 5.3**

### Property 20: Tell/Ask generates dialogue
*For any* NPC, executing TELL or ASK should return a dialogue response
**Validates: Requirements 5.4**

### Property 21: Wake changes creature state
*For any* sleeping creature, executing WAKE should change the creature's state from sleeping to awake
**Validates: Requirements 5.5**

### Property 22: Kiss generates response
*For any* NPC, executing KISS should return an appropriate response message
**Validates: Requirements 5.6**

### Property 23: Burn destroys flammable objects
*For any* flammable object and fire source, executing BURN should remove or change the state of the flammable object
**Validates: Requirements 6.1**

### Property 24: Cut modifies objects
*For any* cuttable object and cutting tool, executing CUT should change the object's state
**Validates: Requirements 6.2**

### Property 25: Dig reveals or modifies
*For any* location and digging tool, executing DIG should either reveal hidden items or modify the location state
**Validates: Requirements 6.3**

### Property 26: Inflate/Deflate inverse operations
*For any* inflatable object, inflating then deflating should return the object to its original deflated state (round-trip property)
**Validates: Requirements 6.4**

### Property 27: Wave generates response
*For any* object, executing WAVE should return a response message
**Validates: Requirements 6.5**

### Property 28: Rub/Touch generates response
*For any* object, executing RUB or TOUCH should return a response message
**Validates: Requirements 6.6**

### Property 29: Shake generates response or state change
*For any* object, executing SHAKE should return a response or change the object's state
**Validates: Requirements 6.7**

### Property 30: Squeeze generates response or state change
*For any* object, executing SQUEEZE should return a response or change the object's state
**Validates: Requirements 6.8**

### Property 31: Save/Restore round-trip
*For any* game state, saving then restoring should return the game to the exact same state (round-trip property)
**Validates: Requirements 7.1, 7.2**

### Property 32: Score displays current value
*For any* game state, executing SCORE should return the current score value
**Validates: Requirements 7.5**

### Property 33: Profanity handling
*For any* profanity input, the system should return a chiding response without executing harmful actions
**Validates: Requirements 8.3**

### Property 34: Echo repeats input
*For any* text input with ECHO command, the system should return a response containing the input text
**Validates: Requirements 8.7**

### Property 35: Unimplemented command messages
*For any* recognized but unimplemented command, the system should return a message indicating the command is not yet available
**Validates: Requirements 9.1**

### Property 36: Incorrect usage guidance
*For any* command used with incorrect syntax, the system should return guidance on correct usage
**Validates: Requirements 9.2**

### Property 37: Missing object messages
*For any* command referencing an object not present, the system should clearly state the object is not here
**Validates: Requirements 9.3**

### Property 38: Impossible action explanations
*For any* impossible action, the system should explain why it cannot be done
**Validates: Requirements 9.4**

### Property 39: Missing parameter prompts
*For any* command requiring additional objects, the system should prompt for the missing information
**Validates: Requirements 9.5**

### Property 40: Synonym equivalence
*For any* verb synonym and its primary verb, executing commands with either should produce equivalent results
**Validates: Requirements 10.1**

### Property 41: Abbreviation expansion
*For any* abbreviated command and its full form, both should produce equivalent results
**Validates: Requirements 10.2**

### Property 42: Variation mapping
*For any* command variation and its canonical form, both should produce the same action
**Validates: Requirements 10.3**

### Property 43: Preposition parsing
*For any* command with prepositions, the system should correctly parse and route to the appropriate handler
**Validates: Requirements 10.4**

### Property 44: Article handling
*For any* command with or without articles (a, an, the), both forms should produce equivalent results
**Validates: Requirements 10.5**

### Property 45: Disambiguation prompts
*For any* ambiguous command, the system should ask for clarification before proceeding
**Validates: Requirements 11.3**

### Property 46: Prerequisite checking
*For any* command with prerequisites, the system should verify prerequisites are met before execution
**Validates: Requirements 11.4**

### Property 47: Multi-object handling
*For any* command affecting multiple objects, all specified objects should be processed appropriately
**Validates: Requirements 11.5**

### Property 48: Spooky theme consistency
*For any* command execution, the response should use spooky/haunted theme descriptions
**Validates: Requirements 12.1**

### Property 49: Sanity effects application
*For any* command that affects sanity, the sanity value should change appropriately
**Validates: Requirements 12.2**

### Property 50: Supernatural event descriptions
*For any* command triggering supernatural events, the description should be thematically appropriate
**Validates: Requirements 12.3**

### Property 51: Curse effect application
*For any* command interacting with cursed objects, curse effects should be applied correctly
**Validates: Requirements 12.4**

### Property 52: Darkness atmosphere
*For any* command executed in darkness, the response should emphasize the horror atmosphere
**Validates: Requirements 12.5**

## Error Handling

### Command Not Found
- Return clear message: "I don't understand that command."
- Suggest similar commands if possible
- Maintain game state unchanged

### Object Not Found
- Return clear message: "You don't see any [object] here."
- Check inventory and current room
- Suggest looking around

### Invalid Syntax
- Return usage guidance: "Try: [verb] [object]"
- Provide examples of correct usage
- Don't penalize player for syntax errors

### Prerequisites Not Met
- Explain what's missing: "You need to [action] first."
- Provide hints when appropriate
- Maintain immersion with thematic language

### State Conflicts
- Handle gracefully: "You can't do that right now."
- Explain why if appropriate
- Suggest alternative actions

## Testing Strategy

### Unit Testing
- Test each command handler in isolation
- Mock world data and game state
- Verify correct ActionResult returned
- Test error conditions and edge cases
- Verify state changes are applied correctly

### Property-Based Testing
- Use Hypothesis library (Python)
- Generate random game states
- Generate random valid commands
- Verify properties hold across all inputs
- Test round-trip properties (open/close, lock/unlock, etc.)
- Test inverse operations
- Test state consistency
- Minimum 100 iterations per property test

### Integration Testing
- Test command sequences
- Verify state persistence across commands
- Test puzzle solutions using new commands
- Verify haunted theme consistency
- Test save/restore functionality

### Regression Testing
- Ensure existing commands still work
- Verify no breaking changes to current functionality
- Test backward compatibility with saved games

### Test Organization
```
tests/
├── unit/
│   ├── test_movement_commands.py
│   ├── test_object_commands.py
│   ├── test_utility_commands.py
│   ├── test_meta_commands.py
│   └── test_special_commands.py
├── property/
│   ├── test_properties_movement.py
│   ├── test_properties_objects.py
│   ├── test_properties_round_trip.py
│   ├── test_properties_theme.py
│   └── test_properties_errors.py
└── integration/
    ├── test_command_sequences.py
    ├── test_puzzle_solutions.py
    └── test_save_restore.py
```

### Property Test Examples

```python
from hypothesis import given, strategies as st
import pytest

@given(
    climbable_object=st.sampled_from(['stairs', 'ladder', 'tree']),
    direction=st.sampled_from(['UP', 'DOWN'])
)
def test_climb_movement_consistency(climbable_object, direction):
    """
    Feature: complete-zork-commands, Property 1: Climb movement consistency
    
    For any climbable object and valid direction, executing CLIMB should
    result in the player moving to the connected room.
    """
    # Setup game state with climbable object
    state = create_test_state_with_object(climbable_object)
    original_room = state.current_room
    
    # Execute climb command
    result = engine.handle_climb(direction, climbable_object, state)
    
    # Verify movement occurred
    assert result.success
    assert result.room_changed
    assert state.current_room != original_room

@given(
    container=st.sampled_from(['box', 'chest', 'bag'])
)
def test_open_close_round_trip(container):
    """
    Feature: complete-zork-commands, Property 4: Open/Close inverse operations
    
    For any closeable object, opening then closing should return the object
    to its original closed state.
    """
    # Setup game state with closed container
    state = create_test_state_with_object(container)
    obj = engine.world.get_object(container)
    obj.state['is_open'] = False
    
    # Open then close
    open_result = engine.handle_object_interaction('OPEN', container, state)
    close_result = engine.handle_object_interaction('CLOSE', container, state)
    
    # Verify round-trip
    assert open_result.success
    assert close_result.success
    assert obj.state['is_open'] == False
```

## Implementation Phases

### Phase 1: Command Audit (1-2 days)
- Review Zork I source code (gsyntax.zil, gverbs.zil)
- Document all verbs and their syntax
- Categorize commands by priority
- Create implementation checklist

### Phase 2: Core Movement Commands (2-3 days)
- Implement CLIMB, ENTER, EXIT
- Implement BOARD, DISEMBARK
- Add vehicle support to world data
- Write unit and property tests

### Phase 3: Object Manipulation Commands (3-4 days)
- Implement LOCK, UNLOCK, TURN
- Implement PUSH, PULL, TIE, UNTIE
- Implement FILL, POUR
- Add new object properties
- Write unit and property tests

### Phase 4: Examination Commands (2-3 days)
- Implement LOOK UNDER, LOOK BEHIND
- Implement SEARCH, READ
- Implement LISTEN, SMELL
- Write unit and property tests

### Phase 5: Combat/Interaction Commands (3-4 days)
- Implement ATTACK, THROW
- Implement GIVE, TELL, ASK
- Implement WAKE, KISS
- Add NPC interaction system
- Write unit and property tests

### Phase 6: Utility Commands (3-4 days)
- Implement BURN, CUT, DIG
- Implement INFLATE, DEFLATE
- Implement WAVE, RUB, SHAKE, SQUEEZE
- Write unit and property tests

### Phase 7: Meta-Game Commands (2-3 days)
- Implement SAVE, RESTORE
- Implement RESTART, SCORE
- Implement VERBOSE, BRIEF, SUPERBRIEF
- Add verbosity system
- Write unit and property tests

### Phase 8: Special Commands (1-2 days)
- Implement easter eggs (XYZZY, PLUGH)
- Implement HELLO, CURSE, PRAY
- Implement JUMP, YELL, ECHO
- Write unit and property tests

### Phase 9: Error Handling & Polish (2-3 days)
- Improve error messages
- Add command suggestions
- Enhance disambiguation
- Test edge cases

### Phase 10: Integration & Testing (2-3 days)
- Run full test suite
- Test command sequences
- Verify haunted theme consistency
- Performance testing
- Bug fixes

## Dependencies

- Existing command parser must support new verb types
- World data JSON files may need new object properties
- Game state may need new fields (verbosity, visited rooms)
- Save/restore system needs implementation
- NPC interaction system needs design

## Performance Considerations

- Command routing should be O(1) using dictionary lookup
- Object property checks should be cached where possible
- State updates should be atomic
- Save/restore should be efficient (JSON serialization)
- Property tests should complete in reasonable time (<5 minutes for full suite)

## Security Considerations

- Validate all player input before processing
- Prevent command injection attacks
- Sanitize saved game data
- Rate limit command execution if needed
- Prevent infinite loops in command sequences

## Backward Compatibility

- Existing saved games should continue to work
- Existing commands should maintain current behavior
- New commands should not break existing puzzles
- API changes should be backward compatible

## Future Enhancements

- Voice command support
- Command history and recall
- Command macros/shortcuts
- Natural language processing improvements
- Multi-language support
- Accessibility features (screen reader support)
