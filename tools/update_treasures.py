import json
import os

FILE_PATH = "amplify/functions/game-handler/data/objects_haunted.json"

TREASURES = [
    "bag_of_coins", "chalice", "canary", "diamond", "jade", "skull", 
    "bar", "pot_of_gold", "sceptre", "coffin", "painting", "egg", 
    "torch", "emerald", "trident", "bracelet", "trunk", "bauble",
    "coins"
]

def update_treasures():
    with open(FILE_PATH, 'r') as f:
        data = json.load(f)
        
    updated_count = 0
    for t_id in TREASURES:
        if t_id in data:
            print(f"Updating {t_id}")
            if "state" not in data[t_id]:
                data[t_id]["state"] = {}
            
            data[t_id]["state"]["treasure"] = True
            data[t_id]["state"]["value"] = 15 # Flat value for now
            
            # Special values if needed (Zork standard)
            if t_id == "egg": data[t_id]["state"]["value"] = 5 # +5 for opening?
            # Adjust as needed
            
            updated_count += 1
        else:
            print(f"Warning: {t_id} not found")
            
    with open(FILE_PATH, 'w') as f:
        json.dump(data, f, indent=2) 
        # Note: Original file indentation seems to be 2 spaces based on previous views.
        # But some lines looked deeper. 
        # `json.dump` will reformat the whole file. 
        # This might cause massive diffs.
        # But strict JSON is fine.
        
    print(f"Updated {updated_count} items.")

if __name__ == "__main__":
    update_treasures()
