# Object Containment Analysis

## Summary

Reviewed the original Zork I source code (`reference/zork1-master/1dungeon.zil`) and verified object containment in the haunted rooms JSON file.

## Key Findings

### ✅ Fixed Issues
- Added `front_door` to `west_of_house`
- Added `barrow_door` and `barrow` to `stone_barrow`
- Added `control_panel` to `dam_room`

### Container Objects (Not Rooms)

The following are **container objects** that hold other objects. They should be defined in the objects JSON, not as rooms:

1. **altar** (in south_temple)
   - Contains: `book` (black book/necronomicon)

2. **attic_table** (in attic)
   - Contains: `knife` (nasty knife)

3. **bottle** (on kitchen_table)
   - Contains: `water` (quantity of water)

4. **buoy** (in river_4)
   - Contains: `emerald` (large emerald)

5. **coffin** (in egypt_room)
   - Contains: `sceptre` (necromancer's sceptre)

6. **egg** (in nest)
   - Contains: `canary` (golden clockwork canary)

7. **broken_egg** (created when egg breaks)
   - Contains: `broken_canary`

8. **inflated_boat** (created when inflatable_boat is inflated)
   - Contains: `boat_label` (tan label)

9. **kitchen_table** (in kitchen)
   - Contains: `sandwich_bag`, `bottle`

10. **mailbox** (at west_of_house)
    - Contains: `advertisement` (leaflet)

11. **nest** (in up_a_tree)
    - Contains: `egg` (jewel-encrusted egg)

12. **pedestal** (in torch_room)
    - Contains: `torch` (ivory torch)

13. **sandwich_bag** (on kitchen_table)
    - Contains: `lunch` (hot pepper sandwich), `garlic` (clove of garlic)

14. **trophy_case** (in living_room)
    - Contains: `map` (ancient map)

15. **tube** (in maintenance_room)
    - Contains: `putty` (viscous material)

### NPC Objects (Carry Items)

These are NPCs that carry objects:

1. **thief** (in round_room)
   - Carries: `large_bag`, `stiletto`

2. **troll** (in troll_room)
   - Carries: `axe` (bloody executioner's axe)

## Object Containment Hierarchy

```
Rooms
├── west_of_house
│   ├── mailbox (container)
│   │   └── advertisement (leaflet)
│   └── front_door (scenery)
│
├── kitchen
│   └── kitchen_table (container/surface)
│       ├── sandwich_bag (container)
│       │   ├── lunch (hot pepper sandwich)
│       │   └── garlic (clove of garlic)
│       └── bottle (container)
│           └── water (quantity of water)
│
├── attic
│   ├── attic_table (container/surface)
│   │   └── knife (nasty knife)
│   └── rope (large coil)
│
├── living_room
│   ├── trophy_case (container)
│   │   └── map (ancient map)
│   ├── rug (scenery)
│   ├── trap_door (door)
│   ├── sword (elvish sword)
│   └── lamp (brass lantern)
│
├── up_a_tree
│   └── nest (container)
│       └── egg (container)
│           └── canary (golden clockwork canary)
│
├── south_temple
│   ├── altar (container/surface)
│   │   └── book (necronomicon)
│   └── candles (pair of candles)
│
├── north_temple
│   ├── bell (brass funeral bell)
│   └── prayer (inscription)
│
├── torch_room
│   └── pedestal (container/surface)
│       └── torch (ivory torch)
│
├── egypt_room
│   └── coffin (container)
│       └── sceptre (necromancer's sceptre)
│
├── troll_room
│   └── troll (NPC)
│       └── axe (bloody executioner's axe)
│
├── round_room
│   └── thief (NPC)
│       ├── large_bag (container)
│       └── stiletto (weapon)
│
├── river_4
│   └── buoy (container)
│       └── emerald (large emerald)
│
├── maintenance_room
│   ├── tube (container)
│   │   └── putty (viscous material)
│   ├── screwdriver
│   ├── wrench
│   ├── leak (scenery)
│   ├── yellow_button (scenery)
│   ├── brown_button (scenery)
│   ├── red_button (scenery)
│   ├── blue_button (scenery)
│   └── tool_chest (container)
│
└── [other rooms...]
```

## Implementation Notes

### Container Objects
Container objects should have these properties in the objects JSON:
- `type`: "container"
- `state.is_open`: boolean
- `state.is_locked`: boolean (if applicable)
- `capacity`: number (optional)
- `contains`: array of object IDs (initial contents)

### Surface Objects
Surface objects (like tables) are containers that are always open:
- `type`: "surface" or "container"
- `state.is_open`: true (always)
- `state.is_locked`: false (always)

### NPC Inventory
NPCs carry objects that should be:
- Listed in the NPC's inventory property
- Not directly accessible until NPC is defeated/interacts

## Verification Status

✅ **Room containment verified** - All rooms have correct direct object references
✅ **Container hierarchy documented** - All nested containment relationships mapped
✅ **NPC inventory documented** - All NPC-carried objects identified

## Next Steps

1. Verify objects JSON has all container objects properly defined
2. Ensure container objects have correct `contains` arrays
3. Implement container opening/closing mechanics in game engine
4. Implement NPC inventory system
5. Add nested object access (e.g., "take leaflet from mailbox")
