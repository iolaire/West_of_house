#!/usr/bin/env python3
"""
Generate spooky/haunted versions of Zork responses.

This script applies Halloween-themed transformations to original Zork responses:
- Word substitutions (house → manor, door → coffin lid, etc.)
- Atmospheric additions (cold, dark, blood, screaming, etc.)
- Sensory enhancements (sounds, smells, textures)
- Gothic horror themes
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple


class SpookyTransformer:
    """Transform original Zork responses into haunted versions."""
    
    def __init__(self):
        # Word substitutions: original → spooky
        self.word_map = {
            # Buildings & structures
            'house': 'manor',
            'white house': 'haunted manor',
            'door': 'coffin lid',
            'window': 'broken window',
            'boards': 'coffin boards',
            'mailbox': 'rusted mailbox',
            'trophy case': 'cursed trophy case',
            'rug': 'bloodstained rug',
            'carpet': 'bloodstained carpet',
            'trap door': 'cursed trap door',
            'table': 'bloodstained table',
            'altar': 'sacrificial altar',
            'chimney': 'crematorium chimney',
            
            # Objects
            'lantern': 'cursed lantern',
            'lamp': 'cursed lantern',
            'brass lantern': 'tarnished lantern',
            'sword': 'spectral blade',
            'leaflet': 'cursed parchment',
            'advertisement': 'death notice',
            'bottle': 'vial',
            'water': 'tainted water',
            'book': 'necronomicon',
            'prayer': 'dark prayer',
            'candles': 'black candles',
            'bell': 'funeral bell',
            'torch': 'cursed torch',
            'rope': "hangman's rope",
            'knife': 'ritual knife',
            'axe': "executioner's axe",
            'coffin': 'obsidian coffin',
            'sceptre': "necromancer's sceptre",
            'skull': 'crystal skull',
            'painting': 'portrait of the damned',
            'egg': "raven's egg",
            'nest': "raven's nest",
            'canary': 'mechanical raven',
            'bird': 'death raven',
            'songbird': 'death raven',
            
            # Creatures
            'troll': 'flesh-eating ogre',
            'thief': 'shadow thief',
            'cyclops': 'one-eyed demon',
            'bat': 'vampire bat',
            'grue': 'shadow demon',
            
            # Nature
            'forest': 'dead forest',
            'tree': 'dead tree',
            'leaves': 'pile of bones',
            'river': 'river of blood',
            'water': 'dark water',
            'rainbow': 'spectral bridge',
            'sand': 'grave dirt',
            
            # Actions & states
            'open': 'creak open',
            'opened': 'creaked open',
            'close': 'slam shut',
            'closed': 'slammed shut',
            'taken': 'grasped',
            'dropped': 'released',
            'beautiful': 'grotesque',
            'bright': 'dim',
            'light': 'flickering light',
            'dark': 'absolute darkness',
            'clean': 'blood-stained',
            'white': 'bone-white',
            'clear': 'murky',
            'fresh': 'rotting',
            'warm': 'cold',
            'pleasant': 'disturbing',
        }
        
        # Atmospheric additions by verb type
        self.verb_atmospherics = {
            'TAKE': [
                "It's cold to the touch.",
                "Your fingers tingle with dark energy.",
                "The object seems to writhe in your grasp.",
                "A chill runs down your spine.",
                "You feel its cursed weight.",
            ],
            'DROP': [
                "It falls with a wet sound.",
                "The object lands with an unnatural thud.",
                "You feel relief as it leaves your hands.",
                "It hits the ground and seems to pulse.",
            ],
            'OPEN': [
                "The hinges scream in protest.",
                "Cold air flows from within.",
                "You hear whispers from inside.",
                "A smell of decay wafts out.",
                "Darkness spills forth.",
            ],
            'CLOSE': [
                "It slams shut with a sound like breaking bones.",
                "The closure echoes through the darkness.",
                "You hear a click like a coffin sealing.",
                "It shuts with finality.",
            ],
            'EXAMINE': [
                "It's covered in strange symbols.",
                "Dark stains mar its surface.",
                "It seems to pulse with malevolent energy.",
                "Shadows cling to it unnaturally.",
            ],
            'READ': [
                "The words seem to writhe on the page.",
                "Reading it fills you with dread.",
                "The text is written in something dark.",
                "Ancient curses fill the pages.",
            ],
            'TURN_ON': [
                "It flickers to life with sickly green light.",
                "The flame casts dancing shadows.",
                "An unnatural glow emanates from it.",
                "It illuminates the darkness with cold fire.",
            ],
            'TURN_OFF': [
                "The light dies, leaving you in darkness.",
                "Shadows rush in to fill the void.",
                "You hear breathing in the darkness.",
                "The flame gutters and dies.",
            ],
        }
        
        # Sensory enhancements
        self.sensory_additions = {
            'sound': [
                'You hear distant screaming.',
                'A low moan echoes through the halls.',
                'Chains rattle in the distance.',
                'Something scratches at the walls.',
                'Whispers fill the air.',
            ],
            'smell': [
                'The smell of decay is overwhelming.',
                'You smell sulfur and rot.',
                'The air reeks of death.',
                'A coppery smell fills your nostrils.',
            ],
            'touch': [
                "It's cold as ice.",
                "It's slick with something dark.",
                'Your skin crawls at the touch.',
                'It feels wrong somehow.',
            ],
            'sight': [
                'Shadows move in the corners of your vision.',
                'The darkness seems alive.',
                'You see movement that shouldn\'t be there.',
                'Everything is tinged with an unnatural hue.',
            ],
        }
        
        # Object-specific transformations
        self.object_specific = {
            'mailbox': {
                'OPEN': 'The rusted mailbox creaks open, its hinges screaming. Inside, a blood-stained parchment awaits.',
                'CLOSE': 'The mailbox slams shut with a sound like breaking bones.',
                'TAKE': 'The mailbox is fused to the ground by dark magic. It will not budge.',
            },
            'leaflet': {
                'READ': '"ABANDON HOPE, ALL YE WHO ENTER HERE. You have been chosen to explore the Haunted Manor and its cursed depths. Few who enter ever leave, and those who do are forever changed. The treasures you seek are cursed, the paths are treacherous, and death is only the beginning of your suffering. Welcome to your nightmare."',
                'TAKE': 'You grasp the parchment. It\'s cold to the touch and seems to writhe in your hands.',
            },
            'lamp': {
                'TURN_ON': 'The lantern flickers to life with a sickly green flame that casts dancing shadows.',
                'TURN_OFF': 'The cursed flame dies, leaving you in darkness. You hear breathing nearby.',
                'EXAMINE': 'The tarnished lantern is covered in strange symbols. Its flame burns with an unnatural color.',
            },
            'sword': {
                'TAKE': 'You grasp the spectral blade. It\'s cold as ice and seems to drink in the light. Runes along its length glow with pale fire.',
                'EXAMINE': 'The blade is forged from some otherworldly metal that seems to shift between solid and ethereal. Ancient runes carved along its length speak of death and damnation.',
                'WAVE': 'The blade cuts through the air with a sound like screaming. Ghostly afterimages trail behind it.',
            },
            'rug': {
                'MOVE': 'With great effort, you drag the heavy rug aside. Its underside is soaked with old blood. Beneath it, a trap door is revealed, its surface carved with warnings in dead languages.',
                'TAKE': 'The rug is impossibly heavy, as if weighted down by the souls of the dead.',
            },
            'trap_door': {
                'OPEN': 'The trap door opens with a groan of tortured wood. Below, a staircase of bones descends into absolute darkness. Cold air and the smell of death flow upward.',
                'CLOSE': 'The trap door slams shut with a sound like a coffin closing.',
            },
        }
    
    def transform_response(self, original: str, verb: str, obj_key: str) -> str:
        """Transform an original response into a spooky version."""
        # Check for object-specific transformation first
        if obj_key in self.object_specific:
            if verb in self.object_specific[obj_key]:
                return self.object_specific[obj_key][verb]
        
        # Start with the original text
        spooky = original
        
        # Apply word substitutions (case-insensitive)
        for orig_word, spooky_word in self.word_map.items():
            # Word boundary replacement
            pattern = r'\b' + re.escape(orig_word) + r'\b'
            spooky = re.sub(pattern, spooky_word, spooky, flags=re.IGNORECASE)
        
        # Add atmospheric details based on verb
        if verb in self.verb_atmospherics:
            atmospherics = self.verb_atmospherics[verb]
            # Pick based on object key hash for consistency
            idx = hash(obj_key) % len(atmospherics)
            atmospheric = atmospherics[idx]
            
            # Add to end if not already atmospheric
            if not self._is_atmospheric(spooky):
                spooky = f"{spooky} {atmospheric}"
        
        # Enhance generic responses
        spooky = self._enhance_generic(spooky, verb)
        
        return spooky.strip()
    
    def _is_atmospheric(self, text: str) -> bool:
        """Check if text already has atmospheric elements."""
        atmospheric_words = [
            'cold', 'dark', 'blood', 'scream', 'whisper', 'shadow',
            'death', 'curse', 'rot', 'decay', 'bone', 'skull', 'grave'
        ]
        text_lower = text.lower()
        return any(word in text_lower for word in atmospheric_words)
    
    def _enhance_generic(self, text: str, verb: str) -> str:
        """Enhance generic responses like 'Taken.' or 'Opened.'"""
        enhancements = {
            'Taken.': 'You grasp it with trembling hands.',
            'Dropped.': 'It falls to the ground with a dull thud.',
            'Opened.': 'It opens with a creak of protest.',
            'Closed.': 'It closes with an ominous click.',
            'Done.': 'It is done.',
            'Okay.': 'Very well.',
            'You can\'t see any such thing.': 'The shadows hide it from view.',
            'I don\'t understand that.': 'Your words echo meaninglessly in the darkness.',
        }
        
        for generic, enhanced in enhancements.items():
            if text.strip() == generic:
                return enhanced
        
        return text
    
    def transform_object(self, obj_key: str, obj_data: Dict) -> Dict:
        """Transform all interactions for an object."""
        transformed = obj_data.copy()
        transformed_interactions = []
        
        for interaction in obj_data.get('interactions', []):
            transformed_int = interaction.copy()
            
            # Transform response if it needs it
            if 'response_original' in interaction:
                if 'response_spooky' not in interaction or \
                   interaction['response_spooky'].startswith('[NEEDS SPOOKY VERSION]'):
                    
                    verb = interaction['verb']
                    original = interaction['response_original']
                    
                    spooky = self.transform_response(original, verb, obj_key)
                    transformed_int['response_spooky'] = spooky
            
            transformed_interactions.append(transformed_int)
        
        transformed['interactions'] = transformed_interactions
        return transformed


def main():
    """Main transformation process."""
    print("=" * 70)
    print("🎃 Spooky Response Generator")
    print("=" * 70)
    print()
    
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    input_file = project_root / "reference" / "west_of_house_json" / "west_of_house_objects_haunted_merged.json"
    output_file = project_root / "reference" / "west_of_house_json" / "west_of_house_objects_haunted_complete.json"
    
    # Load merged data
    print(f"📖 Loading merged data from {input_file.name}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"   Loaded {len(data)} objects")
    
    # Count interactions needing transformation
    needs_transform = 0
    for obj_data in data.values():
        for interaction in obj_data.get('interactions', []):
            if 'response_original' in interaction:
                if 'response_spooky' not in interaction or \
                   interaction['response_spooky'].startswith('[NEEDS SPOOKY VERSION]'):
                    needs_transform += 1
    
    print(f"   Found {needs_transform} interactions needing spooky versions")
    
    # Transform
    print("\n🎭 Generating spooky responses...")
    transformer = SpookyTransformer()
    
    transformed_data = {}
    transformed_count = 0
    
    for obj_key, obj_data in data.items():
        transformed_obj = transformer.transform_object(obj_key, obj_data)
        transformed_data[obj_key] = transformed_obj
        
        # Count transformations
        for interaction in transformed_obj.get('interactions', []):
            if 'response_spooky' in interaction and \
               not interaction['response_spooky'].startswith('[NEEDS SPOOKY VERSION]'):
                transformed_count += 1
    
    print(f"   Generated {transformed_count} spooky responses")
    
    # Save
    print(f"\n💾 Saving to {output_file.name}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(transformed_data, f, indent=2, ensure_ascii=False)
    print("   ✅ Saved successfully")
    
    # Generate report
    print("\n" + "=" * 70)
    print("📊 Transformation Report")
    print("=" * 70)
    print(f"Total objects:              {len(transformed_data)}")
    print(f"Total interactions:         {sum(len(obj.get('interactions', [])) for obj in transformed_data.values())}")
    print(f"Spooky responses generated: {transformed_count}")
    
    # Check for any remaining placeholders
    remaining = 0
    for obj_data in transformed_data.values():
        for interaction in obj_data.get('interactions', []):
            if 'response_spooky' in interaction and \
               interaction['response_spooky'].startswith('[NEEDS SPOOKY VERSION]'):
                remaining += 1
    
    if remaining > 0:
        print(f"\n⚠️  {remaining} interactions still need manual review")
    else:
        print(f"\n✅ All interactions have spooky versions!")
    
    print("\n✨ Transformation complete!")
    print(f"   Output: {output_file}")
    
    return 0


if __name__ == '__main__':
    exit(main())
