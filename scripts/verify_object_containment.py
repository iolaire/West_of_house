#!/usr/bin/env python3
"""
Verify object containment in rooms JSON against original Zork source.
Extracts object locations from 1dungeon.zil and compares with JSON files.
"""

import json
import re
from pathlib import Path

# Object locations from original Zork source (1dungeon.zil)
# Format: object_id: (room_id, description)
ORIGINAL_OBJECT_LOCATIONS = {
    # Objects with explicit (IN <ROOM>) declarations
    "skull": ("land_of_living_dead", "crystal skull"),
    "lowered_basket": ("lower_shaft", "basket (lowered)"),
    "raised_basket": ("shaft_room", "basket (raised)"),
    "lunch": ("sandwich_bag", "hot pepper sandwich - IN CONTAINER"),
    "bat": ("bat_room", "vampire bat"),
    "bell": ("north_temple", "brass bell"),
    "axe": ("troll", "bloody axe - CARRIED BY TROLL"),
    "bolt": ("dam_room", "bolt"),
    "bubble": ("dam_room", "green bubble"),
    "altar": ("south_temple", "altar"),
    "book": ("altar", "black book - ON ALTAR"),
    "sceptre": ("coffin", "sceptre - IN COFFIN"),
    "timbers": ("timber_room", "broken timbers"),
    "sandwich_bag": ("kitchen_table", "brown sack - ON TABLE"),
    "bottle": ("kitchen_table", "glass bottle - ON TABLE"),
    "water": ("bottle", "water - IN BOTTLE"),
    "coffin": ("egypt_room", "gold coffin"),
    "pump": ("reservoir_north", "hand pump"),
    "diamond": (None, "huge diamond - NO INITIAL LOCATION"),
    "jade": ("bat_room", "jade figurine"),
    "knife": ("attic_table", "nasty knife - ON TABLE"),
    "bones": ("maze_5", "skeleton"),
    "burned_out_lantern": ("maze_5", "burned-out lantern"),
    "bag_of_coins": ("maze_5", "bag of coins"),
    "lamp": ("living_room", "brass lantern"),
    "emerald": ("buoy", "large emerald - IN BUOY"),
    "advertisement": ("mailbox", "leaflet - IN MAILBOX"),
    "leak": ("maintenance_room", "leak"),
    "machine": ("machine_room", "machine"),
    "mailbox": ("west_of_house", "small mailbox"),
    "match": ("dam_lobby", "matchbook"),
    "mirror_2": ("mirror_room_2", "mirror"),
    "mirror_1": ("mirror_room_1", "mirror"),
    "painting": ("gallery", "painting"),
    "candles": ("south_temple", "pair of candles"),
    "gunk": (None, "vitreous slag - NO INITIAL LOCATION"),
    "leaves": ("grating_clearing", "pile of leaves"),
    "punctured_boat": (None, "punctured boat - NO INITIAL LOCATION"),
    "inflatable_boat": ("dam_base", "pile of plastic"),
    "bar": ("loud_room", "platinum bar"),
    "pot_of_gold": ("end_of_rainbow", "pot of gold"),
    "prayer": ("north_temple", "prayer inscription"),
    "railing": ("dome_room", "wooden railing"),
    "buoy": ("river_4", "red buoy"),
    "rope": ("attic", "large coil of rope"),
    "rusty_knife": ("maze_5", "rusty knife"),
    "sand": ("sandy_cave", "sand"),
    "bracelet": ("gas_room", "sapphire bracelet"),
    "screwdriver": ("maintenance_room", "screwdriver"),
    "keys": ("maze_5", "skeleton key"),
    "shovel": ("sandy_beach", "shovel"),
    "coal": ("dead_end_5", "small pile of coal"),
    "scarab": ("sandy_cave", "jeweled scarab"),
    "large_bag": ("thief", "large bag - CARRIED BY THIEF"),
    "stiletto": ("thief", "stiletto - CARRIED BY THIEF"),
    "machine_switch": ("machine_room", "switch"),
    "sword": ("living_room", "elvish sword"),
    "map": ("trophy_case", "ancient map - IN TROPHY CASE"),
    "boat_label": ("inflated_boat", "tan label - IN BOAT"),
    "thief": ("round_room", "thief"),
    "pedestal": ("torch_room", "pedestal"),
    "torch": ("pedestal", "ivory torch - ON PEDESTAL"),
    "guide": ("dam_lobby", "tour guidebook"),
    "troll": ("troll_room", "troll"),
    "trunk": ("reservoir", "trunk of jewels"),
    "tube": ("maintenance_room", "tube"),
    "putty": ("tube", "viscous material - IN TUBE"),
    "engravings": ("engravings_cave", "wall engravings"),
    "owners_manual": ("studio", "owner's manual"),
    "wrench": ("maintenance_room", "wrench"),
    "control_panel": ("dam_room", "control panel"),
    "nest": ("up_a_tree", "bird's nest"),
    "egg": ("nest", "jewel-encrusted egg - IN NEST"),
    "broken_egg": (None, "broken egg - NO INITIAL LOCATION"),
    "bauble": (None, "brass bauble - NO INITIAL LOCATION"),
    "canary": ("egg", "golden canary - IN EGG"),
    "broken_canary": ("broken_egg", "broken canary - IN BROKEN EGG"),
    "trophy_case": ("living_room", "trophy case"),
    "rug": ("living_room", "oriental rug"),
    "chalice": ("treasure_room", "silver chalice"),
    "garlic": ("sandwich_bag", "clove of garlic - IN BAG"),
    "trident": ("atlantis_room", "crystal trident"),
    "cyclops": ("cyclops_room", "cyclops"),
    "dam": ("dam_room", "dam"),
    "trap_door": ("living_room", "trap door"),
    "barrow_door": ("stone_barrow", "stone door"),
    "barrow": ("stone_barrow", "stone barrow"),
    "front_door": ("west_of_house", "front door"),
    "grate": ("grating_clearing", "grating - INITIALLY INVISIBLE"),
    "yellow_button": ("maintenance_room", "yellow button"),
    "brown_button": ("maintenance_room", "brown button"),
    "red_button": ("maintenance_room", "red button"),
    "blue_button": ("maintenance_room", "blue button"),
    "tool_chest": ("maintenance_room", "tool chests"),
    "ghosts": ("entrance_to_hades", "ghosts"),
}

def load_json_file(filepath):
    """Load and return JSON data from file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def check_room_containment():
    """Check if rooms JSON has correct object containment."""
    print("=" * 80)
    print("OBJECT CONTAINMENT VERIFICATION")
    print("=" * 80)
    print()
    
    # Load rooms JSON
    rooms_file = Path("reference/west_of_house_json/west_of_house_rooms_haunted.json")
    if not rooms_file.exists():
        print(f"ERROR: {rooms_file} not found!")
        return
    
    rooms_data = load_json_file(rooms_file)
    
    # Build reverse mapping: room -> objects that should be there
    room_to_objects = {}
    for obj_id, (room_id, desc) in ORIGINAL_OBJECT_LOCATIONS.items():
        if room_id and not room_id.startswith("_"):  # Skip None and special cases
            # Convert room_id to match JSON format
            room_key = room_id.lower()
            if room_key not in room_to_objects:
                room_to_objects[room_key] = []
            room_to_objects[room_key].append((obj_id, desc))
    
    # Check each room
    issues_found = []
    rooms_checked = 0
    
    for room_key, expected_objects in sorted(room_to_objects.items()):
        rooms_checked += 1
        
        if room_key not in rooms_data:
            issues_found.append(f"MISSING ROOM: {room_key}")
            continue
        
        room = rooms_data[room_key]
        actual_items = room.get("items", [])
        
        # Check for missing objects
        for obj_id, desc in expected_objects:
            if obj_id not in actual_items:
                issues_found.append(
                    f"MISSING OBJECT in {room_key}: {obj_id} ({desc})"
                )
    
    # Print results
    print(f"Rooms checked: {rooms_checked}")
    print(f"Issues found: {len(issues_found)}")
    print()
    
    if issues_found:
        print("ISSUES FOUND:")
        print("-" * 80)
        for issue in issues_found:
            print(f"  • {issue}")
    else:
        print("✓ All object containment verified correctly!")
    
    print()
    print("=" * 80)
    print("SUMMARY OF OBJECT LOCATIONS FROM ORIGINAL ZORK")
    print("=" * 80)
    print()
    
    # Group by room
    for room_key in sorted(room_to_objects.keys()):
        objects = room_to_objects[room_key]
        print(f"\n{room_key}:")
        for obj_id, desc in objects:
            print(f"  - {obj_id}: {desc}")

if __name__ == "__main__":
    check_room_containment()
