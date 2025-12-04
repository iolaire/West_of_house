#!/usr/bin/env python3
import json

# Container contents from Zork source
container_contents = {
    "altar": ["book"],
    "attic_table": ["knife"],
    "bottle": ["water"],
    "broken_egg": ["broken_canary"],
    "buoy": ["emerald"],
    "coffin": ["sceptre"],
    "egg": ["canary"],
    "inflated_boat": ["boat_label"],
    "kitchen_table": ["sandwich_bag", "bottle"],
    "mailbox": ["advertisement"],
    "nest": ["egg"],
    "pedestal": ["torch"],
    "sandwich_bag": ["lunch", "garlic"],
    "thief": ["large_bag", "stiletto"],
    "troll": ["axe"],
    "trophy_case": ["map"],
    "tube": ["putty"]
}

# Load objects JSON
with open('/Volumes/Gold/vedfolnir/West_of_house/data/west_of_house_objects_haunted.json', 'r') as f:
    objects = json.load(f)

# Update containers with contents
updated = 0
for container_id, contents in container_contents.items():
    if container_id in objects:
        if 'state' not in objects[container_id]:
            objects[container_id]['state'] = {}
        objects[container_id]['state']['contents'] = contents
        updated += 1
        print(f"Updated {container_id} with contents: {contents}")

# Save updated JSON
with open('/Volumes/Gold/vedfolnir/West_of_house/data/west_of_house_objects_haunted.json', 'w') as f:
    json.dump(objects, f, indent=2)

print(f"\nUpdated {updated} containers")
