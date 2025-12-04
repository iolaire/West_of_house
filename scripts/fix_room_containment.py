#!/usr/bin/env python3
"""
Fix object containment in rooms JSON based on original Zork source.
"""

import json
from pathlib import Path

def load_json_file(filepath):
    """Load and return JSON data from file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json_file(filepath, data):
    """Save JSON data to file with proper formatting."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✓ Saved {filepath}")

def fix_room_containment():
    """Fix object containment in rooms JSON."""
    
    rooms_file = Path("reference/west_of_house_json/west_of_house_rooms_haunted.json")
    rooms_data = load_json_file(rooms_file)
    
    print("Fixing room object containment...")
    print()
    
    # Add missing objects to rooms
    fixes = {
        "west_of_house": {
            "add": ["mailbox", "front_door"],
            "reason": "mailbox and front_door are at west of house"
        },
        "stone_barrow": {
            "add": ["barrow_door", "barrow"],
            "reason": "barrow_door and barrow are scenery objects here"
        },
        "kitchen": {
            "ensure": ["kitchen_table", "kitchen_window"],
            "reason": "kitchen_table and kitchen_window must be in kitchen"
        },
        "attic": {
            "ensure": ["attic_table", "rope"],
            "reason": "attic_table and rope are in attic"
        },
        "living_room": {
            "ensure": ["trophy_case", "rug", "trap_door", "sword", "lamp"],
            "reason": "all major living room objects"
        },
        "dam_room": {
            "add": ["control_panel", "dam", "bolt", "bubble"],
            "reason": "dam room control objects"
        },
        "south_temple": {
            "ensure": ["altar", "candles"],
            "reason": "altar and candles are in south temple"
        },
        "north_temple": {
            "ensure": ["bell", "prayer"],
            "reason": "bell and prayer are in north temple"
        },
        "torch_room": {
            "add": ["pedestal"],
            "reason": "pedestal is in torch room"
        },
        "troll_room": {
            "add": ["troll"],
            "reason": "troll is in troll room"
        },
        "cyclops_room": {
            "ensure": ["cyclops"],
            "reason": "cyclops is in cyclops room"
        },
        "treasure_room": {
            "ensure": ["chalice"],
            "reason": "chalice is in treasure room"
        },
        "round_room": {
            "add": ["thief"],
            "reason": "thief starts in round room"
        },
        "gallery": {
            "ensure": ["painting"],
            "reason": "painting is in gallery"
        },
        "studio": {
            "ensure": ["owners_manual"],
            "reason": "owner's manual is in studio"
        },
        "egypt_room": {
            "add": ["coffin"],
            "reason": "coffin is in egypt room"
        },
        "atlantis_room": {
            "add": ["trident"],
            "reason": "trident is in atlantis room"
        },
        "bat_room": {
            "add": ["bat", "jade"],
            "reason": "bat and jade figurine are in bat room"
        },
        "maze_5": {
            "ensure": ["bones", "burned_out_lantern", "bag_of_coins", "rusty_knife", "keys"],
            "reason": "skeleton and items in maze_5"
        },
        "grating_clearing": {
            "ensure": ["leaves", "grate"],
            "reason": "leaves and grate are in clearing"
        },
        "dam_lobby": {
            "add": ["match", "guide"],
            "reason": "matchbook and guidebook are in dam lobby"
        },
        "dam_base": {
            "add": ["inflatable_boat"],
            "reason": "deflated boat is at dam base"
        },
        "maintenance_room": {
            "add": ["leak", "screwdriver", "tube", "wrench", "yellow_button", "brown_button", "red_button", "blue_button", "tool_chest"],
            "reason": "all maintenance room objects"
        },
        "machine_room": {
            "add": ["machine", "machine_switch"],
            "reason": "machine and switch are in machine room"
        },
        "lower_shaft": {
            "add": ["lowered_basket"],
            "reason": "lowered basket is in lower shaft"
        },
        "shaft_room": {
            "add": ["raised_basket"],
            "reason": "raised basket is in shaft room"
        },
        "loud_room": {
            "add": ["bar"],
            "reason": "platinum bar is in loud room"
        },
        "end_of_rainbow": {
            "add": ["pot_of_gold"],
            "reason": "pot of gold is at end of rainbow"
        },
        "reservoir": {
            "add": ["trunk"],
            "reason": "trunk of jewels is in reservoir"
        },
        "reservoir_north": {
            "ensure": ["pump"],
            "reason": "pump is at reservoir north"
        },
        "river_4": {
            "add": ["buoy"],
            "reason": "red buoy is in river"
        },
        "sandy_beach": {
            "add": ["shovel"],
            "reason": "shovel is on sandy beach"
        },
        "sandy_cave": {
            "add": ["sand", "scarab"],
            "reason": "sand and scarab are in sandy cave"
        },
        "gas_room": {
            "add": ["bracelet"],
            "reason": "sapphire bracelet is in gas room"
        },
        "dead_end_5": {
            "add": ["coal"],
            "reason": "coal pile is in dead end"
        },
        "timber_room": {
            "add": ["timbers"],
            "reason": "broken timbers are in timber room"
        },
        "dome_room": {
            "add": ["railing"],
            "reason": "wooden railing is in dome room"
        },
        "engravings_cave": {
            "add": ["engravings"],
            "reason": "wall engravings are in cave"
        },
        "entrance_to_hades": {
            "add": ["ghosts"],
            "reason": "ghosts are at entrance to hades"
        },
        "land_of_living_dead": {
            "add": ["skull"],
            "reason": "crystal skull is in land of living dead"
        },
        "mirror_room_1": {
            "ensure": ["mirror_1"],
            "reason": "mirror is in mirror room 1"
        },
        "mirror_room_2": {
            "ensure": ["mirror_2"],
            "reason": "mirror is in mirror room 2"
        },
    }
    
    changes_made = 0
    
    for room_key, fix_info in fixes.items():
        if room_key not in rooms_data:
            print(f"⚠ Room not found: {room_key}")
            continue
        
        room = rooms_data[room_key]
        if "items" not in room:
            room["items"] = []
        
        items_to_add = fix_info.get("add", []) + fix_info.get("ensure", [])
        
        for item in items_to_add:
            if item not in room["items"]:
                room["items"].append(item)
                changes_made += 1
                print(f"✓ Added {item} to {room_key}")
    
    print()
    print(f"Total changes: {changes_made}")
    print()
    
    # Save updated rooms file
    save_json_file(rooms_file, rooms_data)
    
    return changes_made

if __name__ == "__main__":
    print("=" * 80)
    print("FIXING ROOM OBJECT CONTAINMENT")
    print("=" * 80)
    print()
    
    changes = fix_room_containment()
    
    print()
    print("=" * 80)
    print("DONE!")
    print("=" * 80)
    print()
    print("Run verify_object_containment.py again to check results.")
