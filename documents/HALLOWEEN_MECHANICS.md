# Halloween Gameplay Mechanics

## New Flag System Integration

The four new Halloween flags add atmospheric depth and optional challenge mechanics while preserving the original Zork gameplay.

---

## 1. Sanity System (`sanity: 100`)

### Core Mechanic
A mental health meter that decreases when encountering horrific events, creating tension without breaking classic gameplay.

### Sanity Loss Triggers
- **Minor Loss (-5)**: Reading cursed texts, examining disturbing objects
- **Moderate Loss (-10)**: Witnessing supernatural events, entering cursed areas
- **Major Loss (-20)**: Encountering powerful entities, dying and respawning
- **Severe Loss (-30)**: Breaking mirrors, disturbing graves, reading the grimoire

### Sanity Effects by Level

**100-75 (Stable)**
- Normal gameplay
- Standard descriptions
- Clear thinking

**74-50 (Unsettled)**
- Descriptions become more disturbing
- Occasional hallucinations in text ("You hear whispers...")
- Minor visual distortions in UI (text flickers)
- Inventory items occasionally "shift" in description

**49-25 (Disturbed)**
- Unreliable narrator kicks in
- Room descriptions may lie or mislead
- Phantom items appear/disappear
- Commands occasionally misinterpreted
- Screen effects intensify (blood drips, shadows move)

**24-0 (Broken)**
- Cannot distinguish reality from nightmare
- Random teleportation between rooms
- Inventory scrambles
- Cannot read text clearly (garbled letters)
- Must restore sanity to continue effectively

### Sanity Restoration
- **Rest in safe rooms** (+10 per turn): Kitchen, Attic
- **Consume items** (+20): Holy water, blessed bread
- **Light sources** (+5 per turn): Cursed lantern when lit
- **Solve puzzles** (+15): Completing objectives restores purpose
- **Place treasures** (+10): Each treasure in trophy case

### Implementation Example
```python
def enter_room(room_id):
    if room_id in CURSED_ROOMS:
        sanity -= 10
        if sanity < 50:
            description = get_disturbed_description(room_id)
        else:
            description = get_normal_description(room_id)
    
    if sanity <= 0:
        trigger_madness_event()
```

---

## 2. Cursed Status (`cursed: false`)

### Core Mechanic
A binary state that fundamentally alters gameplay when triggered, adding risk/reward decisions.

### How to Become Cursed
- **Disturbing the skeleton** in the bone maze
- **Breaking a mirror** (7 turns of bad luck)
- **Stealing from the dead** without proper ritual
- **Failing the bell ceremony** at the temple
- **Opening cursed containers** without protection
- **Wearing cursed jewelry** (widow's bracelet, etc.)

### Curse Effects

**While Cursed:**
- **Combat penalty**: -50% damage dealt, +50% damage taken
- **Luck reversal**: `lucky` flag forced to false
- **Treasure corruption**: Treasures lose 50% value
- **NPC hostility**: Neutral NPCs become aggressive
- **Light drain**: Lantern battery drains 2x faster
- **Teleportation**: Random chance to be pulled to cursed locations
- **Item loss**: Small chance items slip from inventory

**Visual Indicators:**
- Purple aura around player avatar
- Inventory items appear tarnished
- Screen has purple vignette
- Cursed status icon in UI

### Breaking the Curse

**Methods:**
1. **Bell Ceremony** (Temple): Ring bell + candles + prayer
2. **Holy Water** (rare item): Consume to cleanse
3. **Exorcism** (Land of the Dead): Defeat all ghosts
4. **Sacrifice** (Altar): Place valuable treasure and destroy it
5. **Time** (expensive): 100 turns of gameplay

**Curse Progression:**
- Turn 1-20: Minor effects
- Turn 21-50: Moderate effects
- Turn 51+: Severe effects (permanent if not broken)

### Implementation Example
```python
def check_curse_effects():
    if cursed:
        if random.random() < 0.1:  # 10% chance per action
            teleport_to_random_cursed_room()
        
        if lamp_on:
            lamp_battery -= 2  # Double drain
        
        combat_modifier = 0.5  # Half damage
```

---

## 3. Blood Moon (`blood_moon_active: true`)

### Core Mechanic
A cyclical atmospheric event that changes the game world, adding time pressure and dynamic difficulty.

### Blood Moon Cycle
- **Duration**: 50 turns active, 50 turns inactive
- **Starts**: Active at game start (turn 0)
- **Cycles**: Repeats throughout game

### Blood Moon Effects

**When Active (Turns 0-50, 100-150, etc.):**

**Environmental:**
- Crimson lighting in all outdoor areas
- Blood river flows faster (navigation harder)
- Bone maze shifts (exits change)
- Cursed areas more dangerous

**Creature Behavior:**
- Vampire bat is active (otherwise sleeping)
- Ogre regenerates health
- Shadow thief appears more frequently
- Ghosts can leave Hades entrance

**Gameplay Changes:**
- Sanity drains 2x faster
- Cursed items more powerful (risk/reward)
- Blood rainbow appears (access to pot of gold)
- Certain puzzles only solvable during blood moon

**When Inactive (Turns 51-100, 151-200, etc.):**
- Normal lighting returns
- Creatures less aggressive
- Safer exploration
- Some areas inaccessible (rainbow gone)

### Strategic Implications
- **Speed runs**: Must complete during blood moon for full access
- **Safe play**: Wait out blood moon in safe rooms
- **Treasure hunting**: Some treasures only accessible during blood moon
- **Combat**: Avoid fights during blood moon unless necessary

### Visual Indicators
- Red moon icon in UI
- Turn counter shows "Blood Moon: 23 turns remaining"
- Screen has red tint during active phase
- Ambient sound changes (howling, screaming)

### Implementation Example
```python
def update_blood_moon(turn_count):
    cycle_position = turn_count % 100
    
    if cycle_position < 50:
        blood_moon_active = True
        sanity_drain_multiplier = 2.0
        enable_vampire_bat()
        show_blood_rainbow()
    else:
        blood_moon_active = False
        sanity_drain_multiplier = 1.0
        disable_vampire_bat()
        hide_blood_rainbow()
```

---

## 4. Souls Collected (`souls_collected: 0`)

### Core Mechanic
An alternative scoring system that rewards exploration of dark content and interaction with the supernatural.

### How to Collect Souls

**Defeating Cursed Enemies:**
- Flesh-eating ogre: 3 souls
- Shadow thief: 5 souls
- Vampire bat: 2 souls
- Ghosts (each): 1 soul

**Completing Dark Rituals:**
- Bell ceremony: 5 souls
- Blood sacrifice at altar: 3 souls
- Exorcism in Hades: 10 souls

**Finding Hidden Souls:**
- Trapped in mirrors: 2 souls each
- Bound in cursed objects: 1 soul each
- Freed from paintings: 3 souls

**Exploring Cursed Areas:**
- First visit to Realm of Eternal Torment: 5 souls
- Draining blood lake: 3 souls
- Completing bone maze: 5 souls

### Soul Usage

**Spend Souls For:**
- **Restore Sanity** (10 souls): Full sanity restoration
- **Break Curse** (15 souls): Instant curse removal
- **Extend Light** (5 souls): +100 turns lantern battery
- **Summon Aid** (20 souls): Temporary ghost ally
- **Unlock Secrets** (varies): Access hidden areas

**Soul Milestones:**
- **25 souls**: "Necromancer" achievement, unlock dark magic
- **50 souls**: "Soul Reaper" achievement, see hidden paths
- **100 souls**: "Death's Apprentice" achievement, alternate ending

### Alternative Win Condition
- **Original**: Collect all 19 treasures (350 points)
- **Halloween**: Collect 100 souls + defeat final boss
- **Perfect**: Both conditions for true ending

### Implementation Example
```python
def defeat_enemy(enemy_type):
    souls_gained = ENEMY_SOUL_VALUES[enemy_type]
    souls_collected += souls_gained
    
    show_message(f"You absorb {souls_gained} tortured souls...")
    
    if souls_collected >= 25 and not has_achievement("necromancer"):
        unlock_dark_magic()
        grant_achievement("necromancer")

def spend_souls(action, cost):
    if souls_collected >= cost:
        souls_collected -= cost
        execute_action(action)
        return True
    else:
        show_message("Not enough souls...")
        return False
```

---

## Integration with Original Gameplay

### Non-Intrusive Design
All Halloween mechanics are **optional enhancements**:
- Original Zork can be completed ignoring all new flags
- New mechanics add challenge and atmosphere
- Players can choose engagement level

### Difficulty Modes

**Classic Mode:**
- All Halloween flags disabled
- Pure Zork I experience
- Original descriptions only

**Haunted Mode (Default):**
- All Halloween flags active
- Sanity and curse mechanics enabled
- Blood moon cycles
- Soul collection optional

**Nightmare Mode:**
- Aggressive Halloween mechanics
- Sanity drains faster
- Curses harder to break
- Blood moon lasts longer
- Soul collection required for true ending

---

## UI Integration

### Status Display
```
┌─────────────────────────────────────┐
│ Score: 150/350  Souls: 23/100      │
│ Sanity: ████████░░ 82/100          │
│ Status: Cursed (12 turns)          │
│ Blood Moon: Active (8 turns left)  │
└─────────────────────────────────────┘
```

### Visual Feedback
- **Sanity bar**: Green → Yellow → Red → Purple
- **Curse indicator**: Purple skull icon
- **Blood moon**: Red moon icon + countdown
- **Soul counter**: Ghostly blue number

### Notifications
- "Your sanity slips..." (sanity loss)
- "A curse takes hold..." (cursed)
- "The blood moon rises..." (cycle start)
- "You feel souls drawn to you..." (collection)

---

## Balancing Considerations

### Sanity
- **Too punishing**: Players can't explore freely
- **Too lenient**: No tension or consequence
- **Sweet spot**: 2-3 restorations needed per playthrough

### Curse
- **Should feel impactful** but not game-breaking
- **Multiple cure methods** prevent frustration
- **Risk/reward** for cursed item usage

### Blood Moon
- **50-turn cycle** allows planning
- **Active phase** creates urgency
- **Inactive phase** allows recovery

### Souls
- **Optional system** doesn't block original win
- **Meaningful rewards** encourage engagement
- **Alternative ending** adds replay value

---

## Example Gameplay Scenarios

### Scenario 1: The Reckless Explorer
1. Player enters bone maze (sanity -10)
2. Disturbs skeleton (cursed = true)
3. Blood moon active (sanity drains 2x)
4. Sanity drops to 35 (disturbed state)
5. Room descriptions become unreliable
6. Player must find safe room and cure curse

### Scenario 2: The Soul Collector
1. Player defeats ogre (souls +3)
2. Completes bell ceremony (souls +5)
3. Reaches 25 souls (unlocks dark magic)
4. Uses dark magic to access hidden area
5. Finds trapped souls (souls +10)
6. Working toward 100-soul alternate ending

### Scenario 3: The Strategic Player
1. Blood moon rises (turn 0)
2. Player waits in kitchen (safe room)
3. Blood moon ends (turn 50)
4. Player explores during safe phase
5. Returns to safe room before next cycle
6. Completes game with minimal sanity loss

---

## Technical Implementation Notes

### State Management
```python
game_state = {
    "sanity": 100,
    "cursed": False,
    "blood_moon_active": True,
    "souls_collected": 0,
    "turn_count": 0,
    "curse_duration": 0
}

def update_game_state():
    turn_count += 1
    update_blood_moon(turn_count)
    apply_curse_effects()
    drain_sanity()
    check_milestones()
```

### Save/Load
All four flags must be saved with game state for proper restoration.

### Multiplayer/Speedrun
Flags can be disabled for competitive play or used as challenge modifiers.

---

**These mechanics transform Zork from a pure puzzle game into a survival-horror experience while respecting the original design.**
