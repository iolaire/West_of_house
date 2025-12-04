# Object Interaction Extraction Process

## Overview

This document describes the automated process for extracting object interactions from the original Zork I source code and transforming them into haunted versions for West of Haunted House.

## The Problem

The original `west_of_house_objects_haunted.json` file had:
- 122 objects defined
- Only 35 interactions (mostly for mailbox, leaflet, lamp, sword, rug, trap_door)
- Most objects had empty `interactions` arrays
- Missing critical verb handlers (TAKE, DROP, EXAMINE, OPEN, CLOSE, etc.)
- No container logic for bottles, bags, coffins, nests, etc.

## The Solution

Three Python scripts that work together to extract, merge, and transform object data:

### 1. `extract_zork_interactions.py`

**Purpose:** Parse the original Zork I ZIL (Zork Implementation Language) source code to extract complete object definitions.

**What it extracts:**
- Object metadata (synonyms, adjectives, descriptions, flags)
- Action routines (verb handlers)
- Response text from TELL statements
- State management (CONTBIT, TAKEBIT, OPENBIT, etc.)
- Container capacities, treasure values, initial locations

**Output:** `reference/json/zork_objects_extracted.json`
- 140 objects
- 510 interactions with verbs and responses
- Complete metadata for each object

**Key features:**
- Parses all 10 ZIL files in `reference/zork1-master/`
- Extracts OBJECT definitions with regex patterns
- Finds ACTION routines and VERB? handlers
- Determines object types from FLAGS (container, item, npc, door, scenery)
- Builds initial state from flags (is_open, is_taken, is_on, etc.)

### 2. `merge_haunted_interactions.py`

**Purpose:** Merge extracted Zork data with existing haunted objects, preserving hand-crafted spooky responses.

**What it does:**
- Loads extracted Zork interactions
- Loads existing haunted objects
- Merges by verb, keeping existing spooky responses
- Adds missing interactions from Zork source
- Marks new interactions with `[NEEDS SPOOKY VERSION]` placeholder

**Output:** `reference/west_of_house_json/west_of_house_objects_haunted_merged.json`
- 145 objects (140 from Zork + 5 haunted-only)
- 524 interactions
- Preserves all existing spooky responses
- Adds missing verbs and responses

**Merge logic:**
```python
For each object:
  For each interaction:
    If haunted version exists:
      Keep haunted response_spooky
      Add extracted response_original
    Else:
      Add extracted interaction
      Mark as needing spooky version
```

### 3. `generate_spooky_responses.py`

**Purpose:** Automatically generate spooky/haunted versions of original Zork responses using transformation rules.

**Transformation techniques:**

#### Word Substitutions
```python
'house' → 'manor'
'door' → 'coffin lid'
'lamp' → 'cursed lantern'
'sword' → 'spectral blade'
'troll' → 'flesh-eating ogre'
'water' → 'tainted water'
```

#### Atmospheric Additions (by verb)
- **TAKE:** "It's cold to the touch.", "Your fingers tingle with dark energy."
- **OPEN:** "The hinges scream in protest.", "Cold air flows from within."
- **CLOSE:** "It slams shut with a sound like breaking bones."
- **EXAMINE:** "It's covered in strange symbols.", "Dark stains mar its surface."

#### Sensory Enhancements
- **Sound:** "You hear distant screaming.", "Chains rattle in the distance."
- **Smell:** "The smell of decay is overwhelming.", "You smell sulfur and rot."
- **Touch:** "It's cold as ice.", "Your skin crawls at the touch."
- **Sight:** "Shadows move in the corners of your vision."

#### Object-Specific Transformations
Hand-crafted responses for key objects:
- **Mailbox:** "The rusted mailbox creaks open, its hinges screaming..."
- **Leaflet:** "ABANDON HOPE, ALL YE WHO ENTER HERE..."
- **Lamp:** "The lantern flickers to life with a sickly green flame..."
- **Sword:** "The blade is forged from some otherworldly metal..."
- **Rug:** "Its underside is soaked with old blood..."

**Output:** `reference/west_of_house_json/west_of_house_objects_haunted_complete.json`
- 145 objects
- 524 interactions
- All interactions have both original and spooky responses
- No placeholders remaining

## Results

### Before
```json
{
  "bottle": {
    "name": "vial of poison",
    "type": "item",
    "state": {},
    "interactions": []
  }
}
```

### After
```json
{
  "bottle": {
    "name": "vial of poison",
    "type": "container",
    "state": {
      "is_open": false,
      "is_locked": false,
      "is_taken": false
    },
    "interactions": [
      {
        "verb": "TAKE",
        "response_original": "Taken.",
        "response_spooky": "grasped. It's cold to the touch.",
        "state_change": {"is_taken": true}
      },
      {
        "verb": "OPEN",
        "condition": {"is_open": false},
        "response_original": "Opened.",
        "response_spooky": "creaked open. The hinges scream in protest.",
        "state_change": {"is_open": true}
      },
      {
        "verb": "EXAMINE",
        "response_original": "glass bottle",
        "response_spooky": "glass vial Dark stains mar its surface."
      }
      // ... 5 more interactions
    ]
  }
}
```

## Statistics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Objects | 122 | 145 | +23 |
| Interactions | 35 | 524 | +489 |
| Objects with interactions | ~10 | 145 | +135 |
| Container objects | 6 | 20 | +14 |
| Items | 30 | 50 | +20 |
| NPCs | 2 | 6 | +4 |

## Usage

### Run all three scripts in sequence:

```bash
# 1. Extract from Zork source
python3 scripts/extract_zork_interactions.py

# 2. Merge with haunted objects
python3 scripts/merge_haunted_interactions.py

# 3. Generate spooky responses
python3 scripts/generate_spooky_responses.py
```

### Or run individually:

```bash
# Just extract
python3 scripts/extract_zork_interactions.py
# Output: reference/json/zork_objects_extracted.json

# Just merge
python3 scripts/merge_haunted_interactions.py
# Output: reference/west_of_house_json/west_of_house_objects_haunted_merged.json

# Just transform
python3 scripts/generate_spooky_responses.py
# Output: reference/west_of_house_json/west_of_house_objects_haunted_complete.json
```

## Key Objects Enhanced

### Containers (now with full OPEN/CLOSE/PUT logic)
- mailbox, bottle, sandwich_bag, coffin, altar, trophy_case
- nest, egg, buoy, machine, inflated_boat, tube
- chalice, raised_basket, pedestal

### Items (now with TAKE/DROP/EXAMINE)
- lamp, sword, knife, rope, shovel, pump, wrench, screwdriver
- skull, painting, diamond, emerald, jade, bracelet, coins
- book, map, leaflet, match, candles, torch

### NPCs (now with interaction logic)
- troll, thief, cyclops, bat, ghosts

### Doors (now with OPEN/CLOSE)
- front_door, trap_door, grate, barrow_door, kitchen_window

## Container Objects with Initial Contents

From the Zork source analysis, these containers start with items inside:

| Container | Initial Contents |
|-----------|------------------|
| BOTTLE | water |
| SANDWICH-BAG | lunch, garlic |
| COFFIN | sceptre |
| ALTAR | book |
| TROPHY-CASE | map (invisible) |
| NEST | egg |
| EGG | canary |
| BROKEN-EGG | broken_canary |
| BUOY | emerald |
| MAILBOX | advertisement |
| INFLATED-BOAT | boat_label |
| THIEF | large_bag, stiletto |
| PEDESTAL | torch |
| TUBE | putty |
| TROLL | axe |

## Next Steps

1. **Update game engine** to use the complete object data
2. **Implement container logic** for PUT/GET commands
3. **Add nested container support** (egg contains canary)
4. **Test all interactions** with property-based tests
5. **Manual review** of generated spooky responses for quality
6. **Add more object-specific transformations** for unique items

## Files Generated

All generated files are in `reference/` (gitignored):

- `reference/json/zork_objects_extracted.json` - Raw extracted data
- `reference/west_of_house_json/west_of_house_objects_haunted_merged.json` - Merged data
- `reference/west_of_house_json/west_of_house_objects_haunted_complete.json` - Final output
- `reference/west_of_house_json/west_of_house_objects_haunted_merged.report.txt` - Merge report

## Maintenance

To re-run the extraction process:

1. If Zork source changes, run `extract_zork_interactions.py`
2. If you add hand-crafted spooky responses, run `merge_haunted_interactions.py`
3. To regenerate all spooky responses, run `generate_spooky_responses.py`

The scripts are idempotent - running them multiple times produces the same output.

## Architecture Notes

The extraction process preserves the original Zork game logic while adding the haunted theme layer:

```
Original Zork ZIL Source
         ↓
   [extract_zork_interactions.py]
         ↓
  zork_objects_extracted.json (140 objects, 510 interactions)
         ↓
   [merge_haunted_interactions.py]
         ↓
  west_of_house_objects_haunted_merged.json (145 objects, 524 interactions)
         ↓
   [generate_spooky_responses.py]
         ↓
  west_of_house_objects_haunted_complete.json (145 objects, 524 spooky interactions)
         ↓
    [Game Engine]
         ↓
   Player Experience
```

This approach ensures:
- ✅ Complete game mechanics from original Zork
- ✅ Consistent haunted theme throughout
- ✅ Easy to update and maintain
- ✅ Preserves hand-crafted responses
- ✅ Automated generation for bulk content
