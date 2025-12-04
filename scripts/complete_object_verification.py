#!/usr/bin/env python3
"""
Complete object verification showing rooms, containers, and nested objects.
"""

import json
from pathlib import Path

def load_json_file(filepath):
    """Load and return JSON data from file."""
    with open(filepath, 'r') as f:
        return json.load(f)

# Complete object location mapping from original Zork
OBJECT_LOCATIONS = {
    # Direct room containment
    "room_objects": {
        "west_of_house": ["mailbox", "front_door"],
        "stone_barrow": ["barrow_door", "barrow"],
        "kitchen": ["kitchen_table", "kitchen_window"],
        "attic": ["attic_table", "rope"],
        "living_room": ["trophy_case", "rug", "trap_door", "sword", "lamp"],
        "up_a_tree": ["nest"],
        "grating_clearing": ["leaves", "grate"],
        "troll_room": ["troll"],
        "east_of_chasm": [],
        "gallery": ["painting"],
        "studio": ["owners_manual"],
        "maze_5": ["bones", "burned_out_lantern", "bag_of_coins", "rusty_knife", "keys"],
        "cyclops_room": ["cyclops"],
        "treasure_room": ["chalice"],
        "reservoir_south": [],
        "reservoir": ["trunk"],
        "reservoir_north": ["pump"],
        "mirror_room_1": ["mirror_1"],
        "mirror_room_2": ["mirror_2"],
        "atlantis_room": ["trident"],
        "round_room": ["thief"],
        "loud_room": ["bar"],
        "entrance_to_hades": ["ghosts"],
        "land_of_living_dead": ["skull"],
        "engravings_cave": ["engravings"],
        "egypt_room": ["coffin"],
        "dome_room": ["railing"],
        "torch_room": ["pedestal"],
        "north_temple": ["bell", "prayer"],
        "south_temple": ["altar", "candles"],
        "dam_room": ["bolt", "bubble", "dam", "control_panel"],
        "dam_lobby": ["match", "guide"],
        "dam_base": ["inflatable_boat"],
        "river_4": ["buoy"],
        "sandy_beach": ["shovel"],
        "sandy_cave": ["sand", "scarab"],
        "bat_room": ["bat", "jade"],
        "shaft_room": ["raised_basket"],
        "gas_room": ["bracelet"],
        "ladder_bottom": [],
        "dead_end_5": ["coal"],
        "timber_room": ["timbers"],
        "lower_shaft": ["lowered_basket"],
        "machine_room": ["machine", "machine_switch"],
        "maintenance_room": ["leak", "screwdriver", "tube", "wrench", 
                            "yellow_button", "brown_button", "red_button", 
                            "blue_button", "tool_chest"],
        "end_of_rainbow": ["pot_of_gold"],
    },
    
    # Container objects and their contents
    "containers": {
        "mailbox": ["advertisement"],
        "kitchen_table": ["sandwich_bag", "bottle"],
        "sandwich_bag": ["lunch", "garlic"],
        "bottle": ["water"],
        "attic_table": ["knife"],
        "trophy_case": ["map"],
        "nest": ["egg"],
        "egg": ["canary"],
        "broken_egg": ["broken_canary"],
        "altar": ["book"],
        "pedestal": ["torch"],
        "coffin": ["sceptre"],
        "buoy": ["emerald"],
        "tube": ["putty"],
        "inflated_boat": ["boat_label"],
        "tool_chest": [],
        "raised_basket": [],
        "lowered_basket": [],
        "machine": [],
        "chalice": [],
    },
    
    # NPC inventory
    "npc_inventory": {
        "troll": ["axe"],
        "thief": ["large_bag", "stiletto"],
        "cyclops": [],
        "bat": [],
        "ghosts": [],
    }
}

def verify_complete_containment():
    """Verify complete object containment including containers."""
    
    print("=" * 80)
    print("COMPLETE OBJECT CONTAINMENT VERIFICATION")
    print("=" * 80)
    print()
    
    rooms_file = Path("reference/west_of_house_json/west_of_house_rooms_haunted.json")
    if not rooms_file.exists():
        print(f"ERROR: {rooms_file} not found!")
        return
    
    rooms_data = load_json_file(rooms_file)
    
    # Check room objects
    print("CHECKING ROOM OBJECT CONTAINMENT")
    print("-" * 80)
    
    room_issues = []
    rooms_ok = 0
    
    for room_key, expected_objects in OBJECT_LOCATIONS["room_objects"].items():
        if not expected_objects:
            continue
            
        if room_key not in rooms_data:
            room_issues.append(f"Room not found: {room_key}")
            continue
        
        room = rooms_data[room_key]
        actual_items = room.get("items", [])
        
        missing = [obj for obj in expected_objects if obj not in actual_items]
        
        if missing:
            room_issues.append(f"{room_key}: missing {', '.join(missing)}")
        else:
            rooms_ok += 1
    
    if room_issues:
        print(f"\n❌ Issues found in {len(room_issues)} rooms:")
        for issue in room_issues:
            print(f"   • {issue}")
    else:
        print(f"\n✅ All {rooms_ok} rooms have correct object containment!")
    
    # Show container hierarchy
    print()
    print("=" * 80)
    print("CONTAINER OBJECT HIERARCHY")
    print("=" * 80)
    print()
    
    for container, contents in sorted(OBJECT_LOCATIONS["containers"].items()):
        if contents:
            print(f"{container}:")
            for item in contents:
                print(f"  └─ {item}")
                # Check for nested containers
                if item in OBJECT_LOCATIONS["containers"]:
                    nested = OBJECT_LOCATIONS["containers"][item]
                    for nested_item in nested:
                        print(f"     └─ {nested_item}")
            print()
    
    # Show NPC inventory
    print("=" * 80)
    print("NPC INVENTORY")
    print("=" * 80)
    print()
    
    for npc, items in sorted(OBJECT_LOCATIONS["npc_inventory"].items()):
        if items:
            print(f"{npc}:")
            for item in items:
                print(f"  └─ {item}")
            print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Rooms checked: {len([r for r in OBJECT_LOCATIONS['room_objects'].values() if r])}")
    print(f"Rooms OK: {rooms_ok}")
    print(f"Room issues: {len(room_issues)}")
    print(f"Container objects: {len([c for c in OBJECT_LOCATIONS['containers'].values() if c])}")
    print(f"NPCs with inventory: {len([n for n in OBJECT_LOCATIONS['npc_inventory'].values() if n])}")
    print()
    
    if not room_issues:
        print("✅ ALL ROOM CONTAINMENT VERIFIED!")
        print()
        print("Note: Container objects (mailbox, tables, etc.) and NPC inventory")
        print("should be defined in the objects JSON file, not as separate rooms.")
    
    return len(room_issues) == 0

if __name__ == "__main__":
    success = verify_complete_containment()
    exit(0 if success else 1)
