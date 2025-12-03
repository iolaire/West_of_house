# Zork I Command Audit

## Overview

This document provides a comprehensive audit of all commands from the original Zork I game, comparing them against the current West of Haunted House implementation. Commands are categorized by functional area and prioritized by gameplay impact and implementation complexity.

**Audit Date:** December 3, 2025  
**Source:** Zork I source files (gsyntax.zil, gverbs.zil)  
**Current Implementation:** src/lambda/game_handler/game_engine.py

---

## Summary Statistics

- **Total Zork I Commands:** 89 unique verbs
- **Currently Implemented:** 11 commands (12%)
- **Not Implemented:** 78 commands (88%)
- **High Priority:** 35 commands
- **Medium Priority:** 28 commands
- **Low Priority:** 15 commands
- **Easter Eggs/Special:** 11 commands

---

## Implementation Status Legend

- ✅ **Fully Implemented** - Command works as expected
- 🟡 **Partially Implemented** - Basic functionality exists but incomplete
- ❌ **Not Implemented** - Returns "not yet implemented" message
- 🎯 **High Priority** - Critical for gameplay
- 🔵 **Medium Priority** - Important but not critical
- 🟢 **Low Priority** - Nice to have
- 🎪 **Easter Egg** - Special/humor commands

---

## Category 1: Movement Commands (9 commands)

### Currently Implemented (1/9)

| Command | Status | Priority | Notes |
|---------|--------|----------|-------|
| GO (N/S/E/W/UP/DOWN/IN/OUT) | ✅ | 🎯 | Fully implemented with exit validation |

### Not Implemented (8/9)

| Command | Status | Priority | Complexity | Notes |
|---------|--------|----------|------------|-------|
| CLIMB | ❌ | 🎯 | Medium | CLIMB UP/DOWN with climbable objects (tree, stairs, ladder) |
| ENTER | ❌ | 🎯 | Low | Enter objects/passages (vehicles, buildings) |
| EXIT | ❌ | 🎯 | Low | Exit current location or object |
| BOARD | ❌ | 🔵 | Medium | Board vehicles (boat, basket) |
| DISEMBARK | ❌ | 🔵 | Medium | Get out of vehicles (also GET OUT) |
| WALK TO | ❌ | 🟢 | Low | Navigate to specific location |
| CROSS | ❌ | 🟢 | Low | Cross objects (river, bridge) |
| SWIM | ❌ | 🟢 | Low | Swim in water |
| BACK | ❌ | 🟢 | Low | Return to previous room |

**Category Priority:** HIGH - Movement is core gameplay

---

## Category 2: Object Manipulation Commands (18 commands)

### Currently Implemented (6/18)

| Command | Status | Priority | Notes |
|---------|--------|----------|-------|
| TAKE | ✅ | 🎯 | Fully implemented with inventory management |
| DROP | ✅ | 🎯 | Fully implemented |
| OPEN | ✅ | 🎯 | Implemented via handle_object_interaction |
| CLOSE | ✅ | 🎯 | Implemented via handle_object_interaction |
| PUT | ✅ | 🎯 | Implemented for containers |
| MOVE | ✅ | 🔵 | Implemented via handle_object_interaction |

### Not Implemented (12/18)

| Command | Status | Priority | Complexity | Notes |
|---------|--------|----------|------------|-------|
| LOCK | ❌ | 🎯 | Medium | Lock objects with keys |
| UNLOCK | ❌ | 🎯 | Medium | Unlock objects with keys |
| TURN | ❌ | 🎯 | Medium | Turn dials, valves, objects |
| PUSH | ❌ | 🔵 | Low | Push moveable objects |
| PULL | ❌ | 🔵 | Low | Pull moveable objects |
| TIE | ❌ | 🔵 | Medium | Tie rope-like objects to targets |
| UNTIE | ❌ | 🔵 | Medium | Untie previously tied objects |
| FILL | ❌ | 🔵 | Medium | Fill containers from liquid sources |
| POUR | ❌ | 🔵 | Medium | Pour liquids from containers |
| RAISE | ❌ | 🟢 | Low | Raise objects |
| LOWER | ❌ | 🟢 | Low | Lower objects |
| WIND | ❌ | 🟢 | Low | Wind up objects |

**Category Priority:** HIGH - Essential for puzzle solving

---

## Category 3: Examination Commands (10 commands)

### Currently Implemented (2/10)

| Command | Status | Priority | Notes |
|---------|--------|----------|-------|
| EXAMINE | ✅ | 🎯 | Fully implemented with spooky descriptions |
| LOOK | ✅ | 🎯 | Implemented as room description |

### Not Implemented (8/10)

| Command | Status | Priority | Complexity | Notes |
|---------|--------|----------|------------|-------|
| LOOK UNDER | ❌ | 🎯 | Low | Look under objects |
| LOOK BEHIND | ❌ | 🎯 | Low | Look behind objects |
| LOOK INSIDE | ❌ | 🎯 | Low | Look inside containers (partially via EXAMINE) |
| SEARCH | ❌ | 🎯 | Low | Search objects/locations |
| READ | ❌ | 🎯 | Low | Read readable objects (books, signs, notes) |
| LISTEN | ❌ | 🔵 | Low | Listen to objects/rooms |
| SMELL | ❌ | 🔵 | Low | Smell objects/rooms |
| COUNT | ❌ | 🟢 | Low | Count objects |

**Category Priority:** HIGH - Important for puzzle clues

---

## Category 4: Combat & Interaction Commands (11 commands)

### Currently Implemented (0/11)

None implemented yet.

### Not Implemented (11/11)

| Command | Status | Priority | Complexity | Notes |
|---------|--------|----------|------------|-------|
| ATTACK | ❌ | 🎯 | High | Attack creatures with weapons |
| KILL | ❌ | 🎯 | High | Synonym for ATTACK |
| FIGHT | ❌ | 🎯 | High | Synonym for ATTACK |
| THROW | ❌ | 🔵 | Medium | Throw objects at targets |
| GIVE | ❌ | 🔵 | Medium | Give objects to NPCs |
| TELL | ❌ | 🔵 | Medium | Talk to NPCs |
| ASK | ❌ | 🔵 | Medium | Ask NPCs about topics |
| WAKE | ❌ | 🔵 | Low | Wake sleeping creatures |
| KISS | ❌ | 🟢 | Low | Kiss NPCs (humorous) |
| STAB | ❌ | 🟢 | Low | Synonym for ATTACK |
| SWING | ❌ | 🟢 | Low | Swing weapon at target |

**Category Priority:** HIGH - Required for creature encounters

---

## Category 5: Utility Commands (15 commands)

### Currently Implemented (0/15)

None implemented yet.

### Not Implemented (15/15)

| Command | Status | Priority | Complexity | Notes |
|---------|--------|----------|------------|-------|
| BURN | ❌ | 🔵 | Medium | Burn flammable objects with fire sources |
| CUT | ❌ | 🔵 | Medium | Cut objects with cutting tools |
| DIG | ❌ | 🔵 | Medium | Dig at locations with tools |
| INFLATE | ❌ | 🔵 | Medium | Inflate inflatable objects |
| DEFLATE | ❌ | 🔵 | Medium | Deflate inflatable objects |
| WAVE | ❌ | 🟢 | Low | Wave objects |
| RUB | ❌ | 🟢 | Low | Rub/touch objects |
| SHAKE | ❌ | 🟢 | Low | Shake objects |
| SQUEEZE | ❌ | 🟢 | Low | Squeeze objects |
| STRIKE | ❌ | 🟢 | Low | Strike objects |
| BRUSH | ❌ | 🟢 | Low | Brush/clean objects |
| KICK | ❌ | 🟢 | Low | Kick objects |
| KNOCK | ❌ | 🟢 | Low | Knock on objects |
| RING | ❌ | 🟢 | Low | Ring objects (bells) |
| PLAY | ❌ | 🟢 | Low | Play objects (instruments) |

**Category Priority:** MEDIUM - Adds depth to interactions

---

## Category 6: Consumption Commands (3 commands)

### Currently Implemented (0/3)

None implemented yet.

### Not Implemented (3/3)

| Command | Status | Priority | Complexity | Notes |
|---------|--------|----------|------------|-------|
| EAT | ❌ | 🔵 | Low | Eat food items |
| DRINK | ❌ | 🔵 | Low | Drink liquids |
| TASTE | ❌ | 🟢 | Low | Taste objects |

**Category Priority:** MEDIUM - Needed for food/water puzzles

---

## Category 7: Meta-Game Commands (8 commands)

### Currently Implemented (1/8)

| Command | Status | Priority | Notes |
|---------|--------|----------|-------|
| INVENTORY | ✅ | 🎯 | Fully implemented |

### Not Implemented (7/8)

| Command | Status | Priority | Complexity | Notes |
|---------|--------|----------|------------|-------|
| SAVE | ❌ | 🎯 | High | Save game state to DynamoDB |
| RESTORE | ❌ | 🎯 | High | Load saved game state |
| RESTART | ❌ | 🎯 | Low | Restart game from beginning |
| SCORE | ❌ | 🎯 | Low | Display current score and rank |
| VERBOSE | ❌ | 🔵 | Low | Always show full room descriptions |
| BRIEF | ❌ | 🔵 | Low | Show abbreviated descriptions after first visit |
| SUPERBRIEF | ❌ | 🔵 | Low | Show room name only |

**Category Priority:** HIGH - Essential for game management

---

## Category 8: Special & Easter Egg Commands (11 commands)

### Currently Implemented (0/11)

None implemented yet.

### Not Implemented (11/11)

| Command | Status | Priority | Complexity | Notes |
|---------|--------|----------|------------|-------|
| XYZZY | ❌ | 🎪 | Low | Magic word easter egg |
| PLUGH | ❌ | 🎪 | Low | Magic word easter egg |
| HELLO | ❌ | 🎪 | Low | Greeting response |
| CURSE | ❌ | 🎪 | Low | Profanity handling |
| PRAY | ❌ | 🎪 | Low | Prayer response |
| JUMP | ❌ | 🎪 | Low | Jumping action |
| YELL | ❌ | 🎪 | Low | Yelling/screaming |
| ECHO | ❌ | 🎪 | Low | Echo back player's words |
| ZORK | ❌ | 🎪 | Low | FROBOZZ Corporation message |
| WIN | ❌ | 🎪 | Low | Humorous response |
| ODYSSEUS | ❌ | 🎪 | Low | Special cyclops interaction |

**Category Priority:** LOW - Fun but not essential

---

## Category 9: Miscellaneous Commands (4 commands)

### Not Implemented (4/4)

| Command | Status | Priority | Complexity | Notes |
|---------|--------|----------|------------|-------|
| WAIT | ❌ | 🔵 | Low | Wait/pass time |
| FIND | ❌ | 🟢 | Low | Find object location |
| FOLLOW | ❌ | 🟢 | Low | Follow NPCs |
| LEAVE | ❌ | 🟢 | Low | Leave current location |

**Category Priority:** LOW - Convenience commands

---

## Implementation Priority Ranking

### Phase 1: Critical Commands (Must Have)

1. **LOCK/UNLOCK** - Essential for grating puzzle and other locked objects
2. **TURN** - Needed for dial/valve puzzles
3. **ATTACK/KILL** - Required for creature encounters (troll, thief, etc.)
4. **SAVE/RESTORE** - Critical for player experience
5. **SCORE** - Important feedback mechanism
6. **CLIMB** - Needed for tree, stairs, ladder navigation
7. **ENTER/EXIT** - Essential for building/vehicle entry
8. **LOOK UNDER/BEHIND** - Important for finding hidden objects
9. **SEARCH** - Key for puzzle solving
10. **READ** - Essential for books, signs, notes

### Phase 2: Important Commands (Should Have)

11. **BOARD/DISEMBARK** - Needed for boat, basket vehicles
12. **PUSH/PULL** - Common puzzle mechanics
13. **TIE/UNTIE** - Rope puzzles
14. **FILL/POUR** - Water/liquid puzzles
15. **THROW** - Combat and puzzle solving
16. **GIVE** - NPC interactions
17. **TELL/ASK** - NPC dialogue
18. **BURN** - Fire-based puzzles
19. **CUT** - Cutting tool puzzles
20. **DIG** - Digging puzzles
21. **INFLATE/DEFLATE** - Balloon/raft puzzles
22. **RESTART** - Player convenience
23. **VERBOSE/BRIEF/SUPERBRIEF** - Player preference
24. **EAT/DRINK** - Food/water mechanics
25. **LISTEN/SMELL** - Sensory examination

### Phase 3: Nice to Have Commands

26. **WAVE/RUB/SHAKE/SQUEEZE** - Object manipulation variety
27. **WAKE** - Sleeping creature interactions
28. **WAIT** - Time passage
29. **WALK TO** - Navigation convenience
30. **CROSS/SWIM** - Movement variety
31. **KISS** - Humorous interactions
32. **RAISE/LOWER** - Object positioning
33. **WIND** - Mechanical objects
34. **COUNT/FIND** - Information commands
35. **FOLLOW/LEAVE** - Navigation helpers

### Phase 4: Easter Eggs & Special

36. **XYZZY/PLUGH** - Classic easter eggs
37. **HELLO** - Greeting responses
38. **CURSE** - Profanity handling
39. **PRAY/JUMP/YELL/ECHO** - Atmospheric commands
40. **ZORK/WIN/ODYSSEUS** - Special responses

---

## Complexity Analysis

### Low Complexity (Quick Wins)
- Commands that return simple messages: HELLO, PRAY, JUMP, YELL, ECHO, WIN, ZORK
- Simple state checks: RESTART, SCORE, VERBOSE, BRIEF, SUPERBRIEF
- Basic object interactions: ENTER, EXIT, LOOK UNDER, LOOK BEHIND, SEARCH, READ

### Medium Complexity (Moderate Effort)
- Commands requiring object property checks: LOCK, UNLOCK, TURN, PUSH, PULL
- Commands with prerequisites: CLIMB, BOARD, DISEMBARK, TIE, UNTIE
- Commands with state changes: FILL, POUR, BURN, CUT, DIG, INFLATE, DEFLATE
- Simple NPC interactions: GIVE, WAKE

### High Complexity (Significant Effort)
- Combat system: ATTACK, KILL, FIGHT, THROW (requires damage calculation, health tracking)
- Dialogue system: TELL, ASK (requires conversation state management)
- Save/Restore: SAVE, RESTORE (requires DynamoDB integration, serialization)
- Complex NPC behaviors: FOLLOW (requires pathfinding)

---

## Synonym Mapping

Many commands have synonyms that should map to the same handler:

### Movement
- NORTH → N
- SOUTH → S
- EAST → E
- WEST → W
- UP → U
- DOWN → D
- NORTHWEST → NW
- NORTHEAST → NE
- SOUTHWEST → SW
- SOUTHEAST → SE

### Object Manipulation
- TAKE → GET, HOLD, CARRY, REMOVE, GRAB, CATCH
- DROP → LEAVE
- EXAMINE → DESCRIBE, WHAT, WHATS, X
- LOOK → L, STARE, GAZE
- OPEN → OPEN UP
- CLOSE → SHUT
- TURN → SET, FLIP
- PUSH → PRESS
- PULL → TUG, YANK
- TIE → FASTEN, SECURE, ATTACH
- UNTIE → FREE, RELEASE, UNFASTEN, UNATTACH, UNHOOK
- POUR → SPILL
- RAISE → LIFT
- MOVE → ROLL

### Combat
- ATTACK → FIGHT, HURT, INJURE, HIT
- KILL → MURDER, SLAY, DISPATCH
- THROW → HURL, CHUCK, TOSS
- SWING → THRUST

### Examination
- READ → SKIM
- SMELL → SNIFF
- RUB → TOUCH, FEEL, PAT, PET
- LISTEN → HEAR

### Consumption
- EAT → CONSUME, TASTE, BITE
- DRINK → IMBIBE, SWALLOW

### Utility
- BURN → INCINERATE, IGNITE
- CUT → SLICE, PIERCE
- BRUSH → CLEAN
- DESTROY → DAMAGE, BREAK, BLOCK, SMASH
- WAVE → BRANDISH
- JUMP → LEAP, DIVE
- YELL → SCREAM, SHOUT
- KICK → TAUNT
- KNOCK → RAP
- SWIM → BATHE, WADE

### Meta-Game
- INVENTORY → I
- QUIT → Q
- RESTART → RESTART
- SAVE → SAVE
- RESTORE → RESTORE
- SCORE → SCORE
- WAIT → Z

### Special
- CURSE → SHIT, FUCK, DAMN
- HELLO → HI
- ODYSSEUS → ULYSSES

---

## Preposition Handling

Commands often use prepositions that need to be parsed correctly:

- **WITH**: "attack troll with sword", "open door with key"
- **TO**: "tie rope to hook", "give sword to guard"
- **IN**: "put lamp in case", "look in box"
- **ON**: "put book on table", "climb on chair"
- **FROM**: "take sword from troll", "drink from bottle"
- **AT**: "throw rock at window", "look at painting"
- **UNDER**: "look under rug", "put box under table"
- **BEHIND**: "look behind door", "put key behind painting"
- **THROUGH**: "go through door"
- **ACROSS**: "swim across river"
- **OVER**: "jump over fence"
- **OFF**: "take hat off"
- **OUT**: "take lamp out", "get out"
- **UP**: "climb up tree", "pick up sword"
- **DOWN**: "climb down ladder", "put down lamp"

---

## Article Handling

The parser should ignore articles appropriately:
- **A**: "take a lamp"
- **AN**: "examine an object"
- **THE**: "open the door"

---

## Recommendations

### Immediate Actions (Phase 1)
1. Implement LOCK/UNLOCK for grating puzzle completion
2. Implement TURN for dial/valve puzzles
3. Implement CLIMB for tree/stairs navigation
4. Implement ENTER/EXIT for building entry
5. Implement LOOK UNDER/BEHIND for hidden objects
6. Implement SEARCH for thorough examination
7. Implement READ for books/signs/notes
8. Implement SAVE/RESTORE for game persistence
9. Implement SCORE for player feedback
10. Implement basic ATTACK for creature encounters

### Parser Enhancements
1. Add comprehensive synonym mapping
2. Improve preposition parsing
3. Add article handling (ignore A, AN, THE)
4. Add abbreviation support (N, S, E, W, I, X, etc.)
5. Add command variation mapping (GET/TAKE, LOOK/EXAMINE)

### Error Message Improvements
1. Provide specific "not yet implemented" messages
2. Suggest alternative commands when appropriate
3. Give usage examples for incorrect syntax
4. Explain why actions are impossible
5. Prompt for missing parameters

### Testing Strategy
1. Create unit tests for each command handler
2. Create property-based tests for command categories
3. Test synonym equivalence
4. Test preposition parsing
5. Test error handling and edge cases

---

## Conclusion

The current implementation has a solid foundation with 11 commands (12%) implemented. To reach feature parity with Zork I, we need to implement 78 additional commands (88%). By following the phased approach outlined above, we can systematically add commands in order of gameplay impact, starting with critical puzzle-solving commands and progressing to convenience and easter egg commands.

The priority should be:
1. **Phase 1 (Critical)**: 10 commands - Essential for core gameplay
2. **Phase 2 (Important)**: 15 commands - Needed for full puzzle support
3. **Phase 3 (Nice to Have)**: 10 commands - Adds variety and depth
4. **Phase 4 (Easter Eggs)**: 11 commands - Fun but not essential

This phased approach ensures that the most impactful commands are implemented first, allowing for incremental testing and validation while maintaining a playable game at each stage.
