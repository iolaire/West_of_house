# Comprehensive Comparison Report: Haunted Game Data

## Executive Summary

This report compares the current haunted game data against the reference haunted JSON files to identify discrepancies, missing items, and configuration issues.

**Key Findings:**
- 2 items missing from rooms
- 2 extra items in rooms
- 19 objects missing from objects file
- 4 items with incorrect placements
- All critical game objects are present

## 1. Room Items Analysis

### Missing Items (Reference → Current)
1. **grating_clearing (Ritual Circle)**
   - Missing: `grate`
   - This is a critical interactive object needed for gameplay

2. **kitchen (Cursed Kitchen)**
   - Missing: `kitchen_window`
   - This is an exit/interaction point

### Extra Items (Current → Reference)
1. **living_room (Parlor of Shadows)**
   - Extra: `wooden_door`
   - This item should be removed or added to reference

2. **mountains (Cursed Peaks)**
   - Extra: `mountain_range`
   - This item should be removed or added to reference

### Items Order Differences
- **west_of_house**: Items order swapped (mailbox ↔ front_door)
- **maintenance_room**: Items order changed (leak, screwdriver, tube, wrench moved)

## 2. Objects Analysis

### Missing Objects (19 total)

#### Item Type (1)
- `guidebook` - Important gameplay object that should be added

#### Scenery Type (16)
- `blessings`
- `global_objects`
- `ground`
- `grue`
- `hands`
- `intnum`
- `it`
- `local_globals`
- `lungs`
- `not_here_object`
- `pathobj`
- `pseudo_object`
- `rooms`
- `sailor`
- `stairs`
- `zorkmid`

#### NPC Type (2)
- `adventurer`
- `me`

### Container Objects Identified
The following objects appear to be containers based on their names:
- `bag_of_coins` (old bag)
- `large_bag` (body bag)
- `mailbox` (rusted mailbox)
- `sandwich_bag` (leather pouch)
- `tool_chest` (torture chest)
- `trophy_case` (cursed trophy case)

### Critical Objects Status
All critical objects are present in both files:
- ✓ lamp (cursed lantern)
- ✓ sword (spectral blade)
- ✓ keys (skeleton key)
- ✓ mailbox (rusted mailbox)
- ✓ rug
- ✓ trophy_case (cursed trophy case)
- ✓ cyclops
- ✓ troll
- ✓ thief

## 3. Object Placements

### Incorrect Placements
1. **grate**
   - Reference: `grating_clearing`
   - Current: Not placed
   - Action: Add to `grating_clearing`

2. **kitchen_window**
   - Reference: `kitchen`
   - Current: Not placed
   - Action: Add to `kitchen`

3. **mountain_range**
   - Reference: Not placed
   - Current: `mountains`
   - Action: Remove from `mountains`

4. **wooden_door**
   - Reference: Not placed
   - Current: `living_room`
   - Action: Remove from `living_room`

## 4. Recommendations

### Immediate Actions Required

1. **Fix Room Items**
   ```json
   // In rooms_haunted.json - grating_clearing
   "items": [
     "leaves",
     "grate"  // Add this
   ]

   // In rooms_haunted.json - kitchen
   "items": [
     "kitchen_table",
     "kitchen_window"  // Add this
   ]

   // In rooms_haunted.json - living_room
   "items": [
     "trophy_case",
     "rug",
     "trap_door",
     "sword",
     "lamp"
     // Remove "wooden_door"
   ]

   // In rooms_haunted.json - mountains
   "items": []  // Remove "mountain_range"
   ```

2. **Add Missing Objects**
   - Add `guidebook` object to `objects_haunted.json` with full configuration from reference

3. **Review Missing Objects**
   - Evaluate if the 18 missing scenery/internal objects are needed for current implementation
   - Many appear to be internal Zork machinery objects that may not be needed in modern implementation

### Optional Improvements

1. **Container Configuration**
   - Verify that container objects (mailbox, bags, chest, etc.) have proper content configuration
   - Check if any containers should have initial contents

2. **Object Properties Review**
   - Ensure all interactive objects have proper state management
   - Verify that objects with complex interactions (lamp, keys, etc.) have complete configuration

3. **Data Consistency**
   - Standardize item ordering in room arrays
   - Ensure all referenced objects exist in the objects file

## 5. File Locations

### Reference Files
- `/Volumes/Gold/vedfolnir/West_of_house/reference/west_of_house_json/west_of_house_rooms_haunted.json`
- `/Volumes/Gold/vedfolnir/West_of_house/reference/west_of_house_json/west_of_house_objects_haunted_complete.json`

### Current Files (to be modified)
- `/Volumes/Gold/vedfolnir/West_of_house/src/lambda/game_handler/data/rooms_haunted.json`
- `/Volumes/Gold/vedfolnir/West_of_house/src/lambda/game_handler/data/objects_haunted.json`

## 6. Impact Assessment

### High Priority (Affects Gameplay)
- Missing `grate` in grating_clearing (blocks progress)
- Missing `kitchen_window` in kitchen (blocks interaction)
- Missing `guidebook` object

### Medium Priority (Affects Completeness)
- Extra items in rooms (may cause confusion)
- Missing scenery objects (may affect atmosphere/descriptions)

### Low Priority
- Item order differences (cosmetic)
- Missing internal objects (likely not needed for modern implementation)

## 7. Next Steps

1. Implement the immediate actions listed above
2. Test the changes to ensure proper gameplay
3. Consider if any of the missing objects should be added for completeness
4. Document any design decisions about excluding certain objects