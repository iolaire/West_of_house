#!/usr/bin/env python3
"""
Extract object interactions from Zork I source code.

This script parses the ZIL (Zork Implementation Language) files to extract:
- Object definitions
- Verb handlers (ACTION routines)
- Response text
- State changes
- Conditions

Output: Enhanced JSON with all interaction data for haunted transformation.
"""

import re
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional


class ZorkInteractionExtractor:
    """Extract object interactions from Zork ZIL source files."""
    
    def __init__(self, zork_source_dir: str):
        self.zork_source_dir = Path(zork_source_dir)
        self.objects = {}
        self.action_routines = {}
        self.global_messages = {}
        
    def extract_all(self) -> Dict[str, Any]:
        """Extract all object interactions from Zork source."""
        print("🔍 Scanning Zork source files...")
        
        # Parse all ZIL files
        zil_files = list(self.zork_source_dir.glob("*.zil"))
        print(f"Found {len(zil_files)} ZIL files")
        
        for zil_file in zil_files:
            print(f"  📄 Parsing {zil_file.name}...")
            self._parse_zil_file(zil_file)
        
        # Build interaction data
        print("\n🔨 Building interaction data...")
        interactions = self._build_interactions()
        
        print(f"\n✅ Extracted {len(interactions)} objects with interactions")
        return interactions
    
    def _parse_zil_file(self, filepath: Path):
        """Parse a single ZIL file for objects and routines."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"    ⚠️  Error reading {filepath.name}: {e}")
            return
        
        # Extract object definitions
        self._extract_objects(content)
        
        # Extract action routines
        self._extract_action_routines(content)
        
        # Extract global messages
        self._extract_messages(content)
    
    def _extract_objects(self, content: str):
        """Extract OBJECT definitions from ZIL content."""
        # Pattern: <OBJECT NAME ... (ACTION ROUTINE-NAME) ...>
        object_pattern = r'<OBJECT\s+([A-Z0-9\-]+)\s+(.*?)(?=<OBJECT|<ROOM|<ROUTINE|$)'
        
        for match in re.finditer(object_pattern, content, re.DOTALL):
            obj_name = match.group(1)
            obj_body = match.group(2)
            
            obj_data = {
                'name': obj_name,
                'synonyms': self._extract_synonyms(obj_body),
                'adjectives': self._extract_adjectives(obj_body),
                'description': self._extract_description(obj_body),
                'flags': self._extract_flags(obj_body),
                'action': self._extract_action(obj_body),
                'text': self._extract_text(obj_body),
                'location': self._extract_location(obj_body),
                'capacity': self._extract_capacity(obj_body),
                'value': self._extract_value(obj_body),
            }
            
            self.objects[obj_name.lower().replace('-', '_')] = obj_data
    
    def _extract_synonyms(self, obj_body: str) -> List[str]:
        """Extract SYNONYM list."""
        match = re.search(r'\(SYNONYM\s+([^)]+)\)', obj_body)
        if match:
            return match.group(1).split()
        return []
    
    def _extract_adjectives(self, obj_body: str) -> List[str]:
        """Extract ADJECTIVE list."""
        match = re.search(r'\(ADJECTIVE\s+([^)]+)\)', obj_body)
        if match:
            return match.group(1).split()
        return []
    
    def _extract_description(self, obj_body: str) -> Optional[str]:
        """Extract DESC or LDESC."""
        # Try LDESC first (long description)
        match = re.search(r'\(LDESC\s+"([^"]+)"\)', obj_body)
        if match:
            return match.group(1)
        
        # Try DESC
        match = re.search(r'\(DESC\s+"([^"]+)"\)', obj_body)
        if match:
            return match.group(1)
        
        # Try FDESC (first description)
        match = re.search(r'\(FDESC\s+"([^"]+)"\)', obj_body)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_flags(self, obj_body: str) -> List[str]:
        """Extract FLAGS."""
        match = re.search(r'\(FLAGS\s+([^)]+)\)', obj_body)
        if match:
            return match.group(1).split()
        return []
    
    def _extract_action(self, obj_body: str) -> Optional[str]:
        """Extract ACTION routine name."""
        match = re.search(r'\(ACTION\s+([A-Z0-9\-]+)\)', obj_body)
        if match:
            return match.group(1)
        return None
    
    def _extract_text(self, obj_body: str) -> Optional[str]:
        """Extract TEXT (for readable objects)."""
        match = re.search(r'\(TEXT\s+"([^"]+(?:"\s*\|[^"]*)*)"', obj_body, re.DOTALL)
        if match:
            text = match.group(1)
            # Clean up ZIL formatting
            text = text.replace('|', '\n')
            return text.strip()
        return None
    
    def _extract_location(self, obj_body: str) -> Optional[str]:
        """Extract IN (initial location)."""
        match = re.search(r'\(IN\s+([A-Z0-9\-]+)\)', obj_body)
        if match:
            return match.group(1)
        return None
    
    def _extract_capacity(self, obj_body: str) -> Optional[int]:
        """Extract CAPACITY (for containers)."""
        match = re.search(r'\(CAPACITY\s+(\d+)\)', obj_body)
        if match:
            return int(match.group(1))
        return None
    
    def _extract_value(self, obj_body: str) -> Optional[int]:
        """Extract VALUE (treasure value)."""
        match = re.search(r'\(VALUE\s+(\d+)\)', obj_body)
        if match:
            return int(match.group(1))
        return None
    
    def _extract_action_routines(self, content: str):
        """Extract ROUTINE definitions (action handlers)."""
        # Pattern: <ROUTINE NAME (ARGS) BODY>
        routine_pattern = r'<ROUTINE\s+([A-Z0-9\-]+)\s*\((.*?)\)(.*?)(?=<ROUTINE|<OBJECT|$)'
        
        for match in re.finditer(routine_pattern, content, re.DOTALL):
            routine_name = match.group(1)
            routine_body = match.group(3)
            
            # Extract verb handlers from routine
            verb_handlers = self._extract_verb_handlers(routine_body)
            
            if verb_handlers:
                self.action_routines[routine_name] = verb_handlers
    
    def _extract_verb_handlers(self, routine_body: str) -> Dict[str, Any]:
        """Extract verb handlers from routine body."""
        handlers = {}
        
        # Pattern: <COND (<VERB? VERB-NAME> ... <TELL "response"> ...)>
        verb_pattern = r'<VERB\?\s+([A-Z\-]+)>'
        tell_pattern = r'<TELL\s+"([^"]+(?:"\s*CR\s*"[^"]*)*)"'
        
        # Find all VERB? checks
        for verb_match in re.finditer(verb_pattern, routine_body):
            verb = verb_match.group(1)
            
            # Find TELL statements near this verb
            # Look ahead up to 500 chars for the response
            start_pos = verb_match.start()
            search_area = routine_body[start_pos:start_pos + 500]
            
            tell_matches = list(re.finditer(tell_pattern, search_area))
            if tell_matches:
                # Take the first TELL as the response
                response = tell_matches[0].group(1)
                # Clean up ZIL formatting
                response = response.replace('CR', '\n').strip()
                
                handlers[verb] = {
                    'response': response,
                    'conditions': [],  # TODO: Extract conditions
                    'state_changes': []  # TODO: Extract state changes
                }
        
        return handlers
    
    def _extract_messages(self, content: str):
        """Extract global message strings."""
        # Pattern: <CONSTANT MESSAGE-NAME "text">
        msg_pattern = r'<CONSTANT\s+([A-Z0-9\-]+)\s+"([^"]+)"'
        
        for match in re.finditer(msg_pattern, content):
            msg_name = match.group(1)
            msg_text = match.group(2)
            self.global_messages[msg_name] = msg_text
    
    def _build_interactions(self) -> Dict[str, Any]:
        """Build final interaction data structure."""
        result = {}
        
        for obj_key, obj_data in self.objects.items():
            # Determine object type
            obj_type = self._determine_type(obj_data)
            
            # Build state
            state = self._build_state(obj_data)
            
            # Build interactions
            interactions = self._build_object_interactions(obj_data)
            
            result[obj_key] = {
                'name': self._format_name(obj_data),
                'type': obj_type,
                'state': state,
                'interactions': interactions,
                'metadata': {
                    'synonyms': obj_data['synonyms'],
                    'adjectives': obj_data['adjectives'],
                    'flags': obj_data['flags'],
                    'location': obj_data['location'],
                    'capacity': obj_data['capacity'],
                    'value': obj_data['value'],
                }
            }
        
        return result
    
    def _determine_type(self, obj_data: Dict) -> str:
        """Determine object type from flags."""
        flags = obj_data['flags']
        
        if 'CONTBIT' in flags:
            return 'container'
        elif 'TAKEBIT' in flags:
            return 'item'
        elif 'ACTORBIT' in flags:
            return 'npc'
        elif 'DOORBIT' in flags:
            return 'door'
        else:
            return 'scenery'
    
    def _build_state(self, obj_data: Dict) -> Dict[str, Any]:
        """Build initial state from flags."""
        state = {}
        flags = obj_data['flags']
        
        if 'CONTBIT' in flags:
            state['is_open'] = 'OPENBIT' in flags
            state['is_locked'] = False  # Default
        
        if 'TAKEBIT' in flags:
            state['is_taken'] = False
        
        if 'LIGHTBIT' in flags:
            state['is_on'] = 'ONBIT' in flags
            if obj_data['name'] == 'LAMP':
                state['battery_life'] = 200  # Default lamp battery
        
        if 'READBIT' in flags:
            state['is_read'] = False
        
        return state
    
    def _build_object_interactions(self, obj_data: Dict) -> List[Dict]:
        """Build interactions list for an object."""
        interactions = []
        
        # Get action routine if exists
        action_name = obj_data['action']
        if action_name and action_name in self.action_routines:
            verb_handlers = self.action_routines[action_name]
            
            for verb, handler in verb_handlers.items():
                interaction = {
                    'verb': verb,
                    'response_original': handler['response']
                }
                
                if handler['conditions']:
                    interaction['condition'] = handler['conditions']
                
                if handler['state_changes']:
                    interaction['state_change'] = handler['state_changes']
                
                interactions.append(interaction)
        
        # Add common interactions based on flags
        interactions.extend(self._add_common_interactions(obj_data))
        
        return interactions
    
    def _add_common_interactions(self, obj_data: Dict) -> List[Dict]:
        """Add common interactions based on object flags."""
        interactions = []
        flags = obj_data['flags']
        
        # TAKE interaction
        if 'TAKEBIT' in flags:
            interactions.append({
                'verb': 'TAKE',
                'response_original': 'Taken.',
                'state_change': {'is_taken': True}
            })
            interactions.append({
                'verb': 'DROP',
                'condition': {'is_taken': True},
                'response_original': 'Dropped.',
                'state_change': {'is_taken': False}
            })
        
        # EXAMINE interaction (all objects)
        if obj_data['description']:
            interactions.append({
                'verb': 'EXAMINE',
                'response_original': obj_data['description']
            })
        
        # READ interaction
        if 'READBIT' in flags and obj_data['text']:
            interactions.append({
                'verb': 'READ',
                'response_original': obj_data['text'],
                'state_change': {'is_read': True}
            })
        
        # OPEN/CLOSE for containers
        if 'CONTBIT' in flags:
            interactions.append({
                'verb': 'OPEN',
                'condition': {'is_open': False},
                'response_original': 'Opened.',
                'state_change': {'is_open': True}
            })
            interactions.append({
                'verb': 'CLOSE',
                'condition': {'is_open': True},
                'response_original': 'Closed.',
                'state_change': {'is_open': False}
            })
        
        # TURN ON/OFF for lights
        if 'LIGHTBIT' in flags:
            interactions.append({
                'verb': 'TURN_ON',
                'condition': {'is_on': False},
                'response_original': f'The {self._format_name(obj_data)} is now on.',
                'state_change': {'is_on': True}
            })
            interactions.append({
                'verb': 'TURN_OFF',
                'condition': {'is_on': True},
                'response_original': f'The {self._format_name(obj_data)} is now off.',
                'state_change': {'is_on': False}
            })
        
        return interactions
    
    def _format_name(self, obj_data: Dict) -> str:
        """Format object name from synonyms and adjectives."""
        synonyms = obj_data['synonyms']
        adjectives = obj_data['adjectives']
        
        if not synonyms:
            return obj_data['name'].lower().replace('-', ' ')
        
        # Use first adjective + first synonym
        if adjectives:
            return f"{adjectives[0].lower()} {synonyms[0].lower()}"
        else:
            return synonyms[0].lower()


def main():
    """Main extraction process."""
    print("=" * 60)
    print("🎮 Zork I Interaction Extractor")
    print("=" * 60)
    print()
    
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    zork_source = project_root / "reference" / "zork1-master"
    output_file = project_root / "reference" / "json" / "zork_objects_extracted.json"
    
    # Check if source exists
    if not zork_source.exists():
        print(f"❌ Error: Zork source not found at {zork_source}")
        print("   Expected: reference/zork1-master/")
        return 1
    
    # Extract interactions
    extractor = ZorkInteractionExtractor(str(zork_source))
    interactions = extractor.extract_all()
    
    # Save to JSON
    print(f"\n💾 Saving to {output_file.name}...")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(interactions, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(interactions)} objects")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Extraction Summary")
    print("=" * 60)
    
    type_counts = {}
    for obj_data in interactions.values():
        obj_type = obj_data['type']
        type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
    
    for obj_type, count in sorted(type_counts.items()):
        print(f"  {obj_type:12s}: {count:3d} objects")
    
    # Count objects with interactions
    with_interactions = sum(1 for obj in interactions.values() if obj['interactions'])
    print(f"\n  Objects with interactions: {with_interactions}/{len(interactions)}")
    
    print("\n✨ Extraction complete!")
    print(f"   Output: {output_file}")
    
    return 0


if __name__ == '__main__':
    exit(main())
