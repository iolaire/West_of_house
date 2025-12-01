# Flag Name Transformations: Classic → Haunted

## Core Game State Flags

| Original Flag | Haunted Flag | Description |
|--------------|--------------|-------------|
| `cyclops_flag` | `ogre_flag` | Cyclops → One-eyed Ogre defeated/pacified |
| `troll_flag` | `ogre_defeated_flag` | Troll → Flesh-eating Ogre defeated |
| `lld_flag` | `realm_of_dead_flag` | Land of Living Dead → Realm of Eternal Torment accessible |
| `low_tide` | `blood_drained` | Reservoir drained → Blood Lake drained |
| `magic_flag` | `dark_passage_flag` | Magic passage → Cursed Passage opened |
| `rainbow_flag` | `blood_rainbow_flag` | Rainbow → Blood Rainbow walkable |
| `thief_here` | `shadow_thief_here` | Thief → Shadow Thief present |
| `thief_engrossed` | `shadow_thief_engrossed` | Thief → Shadow Thief distracted |
| `lamp_battery` | `cursed_lantern_battery` | Brass lantern → Cursed Lantern battery life |
| `mirror_mung` | `mirror_broken` | Mirror damaged → Cursed Mirror broken (bad luck) |
| `grunlock` | `grate_unlocked` | Grating unlocked → Iron Grating unlocked |
| `coffin_cure` | `sarcophagus_cure` | Coffin → Cursed Sarcophagus cure obtained |
| `kitchen_window_flag` | `broken_window_flag` | Kitchen window → Broken Window opened |
| `loud_flag` | `screaming_chamber_flag` | Loud room → Chamber of Screams state |

## Unchanged Technical Flags
These keep their original names as they're mechanical/structural:

| Flag | Reason to Keep |
|------|----------------|
| `deflate` | Technical state (boat deflated) |
| `dome_flag` | Structural reference (rope tied) |
| `empty_handed` | Mechanical constraint |
| `gate_flag` | Generic gate state |
| `gates_open` | Generic gate state |
| `buoy_flag` | Object state |
| `cage_top` | Mechanical position |
| `rug_moved` | Object state |
| `grate_revealed` | Discovery state |
| `lucky` | Game mechanic |
| `score` | Core game metric |
| `moves` | Core game metric |
| `won_flag` | Win condition |

## New Halloween-Specific Flags

| Flag | Initial Value | Purpose |
|------|---------------|---------|
| `sanity` | 100 | Mental health meter (0-100) |
| `cursed` | false | Player curse status |
| `blood_moon_active` | true | Atmospheric cycle state |
| `souls_collected` | 0 | Alternative scoring system |

## Rationale for Changes

### Creature Names
- **cyclops_flag → ogre_flag**: Cyclops becomes "One-eyed Ogre" in haunted theme
- **troll_flag → ogre_defeated_flag**: Troll becomes "Flesh-eating Ogre"
- **thief_here → shadow_thief_here**: Thief becomes "Shadow Thief"

### Location Names
- **lld_flag → realm_of_dead_flag**: "Land of Living Dead" → "Realm of Eternal Torment"
- **loud_flag → screaming_chamber_flag**: "Loud Room" → "Chamber of Screams"

### Environmental States
- **low_tide → blood_drained**: Reservoir → Blood Lake
- **rainbow_flag → blood_rainbow_flag**: Rainbow → Blood Rainbow

### Object Names
- **lamp_battery → cursed_lantern_battery**: Brass Lantern → Cursed Lantern
- **mirror_mung → mirror_broken**: Mirror → Cursed Mirror
- **coffin_cure → sarcophagus_cure**: Coffin → Cursed Sarcophagus
- **kitchen_window_flag → broken_window_flag**: Kitchen Window → Broken Window

### Passage Names
- **magic_flag → dark_passage_flag**: Magic Passage → Cursed Passage

## Implementation Notes

### Code Compatibility
When porting original Zork logic, use a mapping dictionary:

```python
FLAG_MAPPING = {
    'cyclops_flag': 'ogre_flag',
    'troll_flag': 'ogre_defeated_flag',
    'lld_flag': 'realm_of_dead_flag',
    'low_tide': 'blood_drained',
    'magic_flag': 'dark_passage_flag',
    'rainbow_flag': 'blood_rainbow_flag',
    'thief_here': 'shadow_thief_here',
    'thief_engrossed': 'shadow_thief_engrossed',
    'lamp_battery': 'cursed_lantern_battery',
    'mirror_mung': 'mirror_broken',
    'grunlock': 'grate_unlocked',
    'coffin_cure': 'sarcophagus_cure',
    'kitchen_window_flag': 'broken_window_flag',
    'loud_flag': 'screaming_chamber_flag'
}

def get_flag(original_name):
    haunted_name = FLAG_MAPPING.get(original_name, original_name)
    return game_state[haunted_name]
```

### Dual-Mode Support
For games supporting both classic and haunted modes:

```python
def get_flag_name(flag, mode='haunted'):
    if mode == 'classic':
        return flag
    else:
        return FLAG_MAPPING.get(flag, flag)
```

### Save File Compatibility
Save files should store both versions or include mode metadata:

```json
{
  "mode": "haunted",
  "flags": {
    "ogre_flag": false,
    "blood_drained": false,
    "sanity": 82,
    "cursed": true
  }
}
```

## Testing Checklist

When implementing haunted flags, verify:

- [ ] All original game logic works with new flag names
- [ ] Creature defeat conditions trigger correct flags
- [ ] Environmental state changes update correct flags
- [ ] Object interactions reference correct flags
- [ ] Puzzle solutions check correct flags
- [ ] Win condition evaluates correct flags
- [ ] Save/load preserves all flag states
- [ ] Mode switching (if supported) maps flags correctly

## Summary

**14 flags renamed** to match haunted theme  
**13 flags unchanged** (technical/mechanical)  
**4 new flags added** (Halloween mechanics)  
**31 total flags** in haunted version

All original game logic is preserved - only the naming has changed to maintain thematic consistency with the haunted transformation.
