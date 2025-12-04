#!/usr/bin/env python3
"""
Merge extracted Zork interactions with haunted objects file.

This script:
1. Loads the extracted Zork interactions
2. Loads the existing haunted objects file
3. Merges interaction data, preserving existing spooky responses
4. Adds missing objects and interactions
5. Outputs enhanced haunted objects file
"""

import json
from pathlib import Path
from typing import Dict, Any, List


def load_json(filepath: Path) -> Dict:
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(filepath: Path, data: Dict):
    """Save JSON file with pretty formatting."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def merge_interactions(extracted: Dict, haunted: Dict) -> Dict:
    """Merge extracted interactions with haunted objects."""
    result = {}
    
    # Process all objects from extracted data
    for obj_key, extracted_obj in extracted.items():
        # Get existing haunted object if it exists
        haunted_obj = haunted.get(obj_key, {})
        
        # Start with extracted data
        merged_obj = {
            'name': haunted_obj.get('name', extracted_obj['name']),
            'type': extracted_obj['type'],
            'state': extracted_obj['state'].copy(),
            'interactions': []
        }
        
        # Merge interactions
        merged_obj['interactions'] = merge_object_interactions(
            extracted_obj.get('interactions', []),
            haunted_obj.get('interactions', [])
        )
        
        result[obj_key] = merged_obj
    
    # Add any haunted objects not in extracted data
    for obj_key, haunted_obj in haunted.items():
        if obj_key not in result:
            result[obj_key] = haunted_obj
    
    return result


def merge_object_interactions(extracted_interactions: List[Dict], 
                              haunted_interactions: List[Dict]) -> List[Dict]:
    """Merge interactions for a single object."""
    # Create a map of existing haunted interactions by verb
    haunted_map = {
        interaction['verb']: interaction 
        for interaction in haunted_interactions
    }
    
    merged = []
    
    # Process extracted interactions
    for extracted_int in extracted_interactions:
        verb = extracted_int['verb']
        
        # If we have a haunted version, use it
        if verb in haunted_map:
            haunted_int = haunted_map[verb]
            
            # Merge: keep haunted response_spooky, add extracted response_original
            merged_int = {
                'verb': verb,
                'response_original': extracted_int.get('response_original', ''),
            }
            
            # Add spooky response if it exists
            if 'response_spooky' in haunted_int:
                merged_int['response_spooky'] = haunted_int['response_spooky']
            
            # Add condition if it exists
            if 'condition' in extracted_int:
                merged_int['condition'] = extracted_int['condition']
            elif 'condition' in haunted_int:
                merged_int['condition'] = haunted_int['condition']
            
            # Add state_change if it exists
            if 'state_change' in extracted_int:
                merged_int['state_change'] = extracted_int['state_change']
            elif 'state_change' in haunted_int:
                merged_int['state_change'] = haunted_int['state_change']
            
            merged.append(merged_int)
            
            # Remove from haunted_map so we don't duplicate
            del haunted_map[verb]
        else:
            # No haunted version, use extracted with placeholder spooky
            merged_int = extracted_int.copy()
            # Add placeholder spooky response
            if 'response_original' in merged_int:
                merged_int['response_spooky'] = f"[NEEDS SPOOKY VERSION] {merged_int['response_original']}"
            merged.append(merged_int)
    
    # Add any remaining haunted interactions not in extracted
    for haunted_int in haunted_map.values():
        merged.append(haunted_int)
    
    return merged


def generate_report(extracted: Dict, haunted: Dict, merged: Dict) -> str:
    """Generate a report of the merge operation."""
    lines = []
    lines.append("=" * 70)
    lines.append("📊 Merge Report")
    lines.append("=" * 70)
    lines.append("")
    
    # Count objects
    lines.append(f"Objects in extracted data: {len(extracted)}")
    lines.append(f"Objects in haunted data:   {len(haunted)}")
    lines.append(f"Objects in merged data:    {len(merged)}")
    lines.append("")
    
    # Count interactions
    extracted_int_count = sum(len(obj.get('interactions', [])) for obj in extracted.values())
    haunted_int_count = sum(len(obj.get('interactions', [])) for obj in haunted.values())
    merged_int_count = sum(len(obj.get('interactions', [])) for obj in merged.values())
    
    lines.append(f"Interactions in extracted: {extracted_int_count}")
    lines.append(f"Interactions in haunted:   {haunted_int_count}")
    lines.append(f"Interactions in merged:    {merged_int_count}")
    lines.append("")
    
    # Count objects needing spooky versions
    needs_spooky = 0
    for obj in merged.values():
        for interaction in obj.get('interactions', []):
            if 'response_original' in interaction and 'response_spooky' not in interaction:
                needs_spooky += 1
    
    lines.append(f"Interactions needing spooky versions: {needs_spooky}")
    lines.append("")
    
    # List objects with most interactions
    lines.append("Top 10 objects by interaction count:")
    obj_int_counts = [
        (obj_key, len(obj.get('interactions', [])))
        for obj_key, obj in merged.items()
    ]
    obj_int_counts.sort(key=lambda x: x[1], reverse=True)
    
    for obj_key, count in obj_int_counts[:10]:
        lines.append(f"  {obj_key:20s}: {count:2d} interactions")
    
    lines.append("")
    lines.append("=" * 70)
    
    return "\n".join(lines)


def main():
    """Main merge process."""
    print("=" * 70)
    print("🎃 Haunted Interactions Merger")
    print("=" * 70)
    print()
    
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    extracted_file = project_root / "reference" / "json" / "zork_objects_extracted.json"
    haunted_file = project_root / "reference" / "west_of_house_json" / "west_of_house_objects_haunted.json"
    output_file = project_root / "reference" / "west_of_house_json" / "west_of_house_objects_haunted_merged.json"
    
    # Load files
    print(f"📖 Loading extracted data from {extracted_file.name}...")
    extracted = load_json(extracted_file)
    print(f"   Loaded {len(extracted)} objects")
    
    print(f"📖 Loading haunted data from {haunted_file.name}...")
    haunted = load_json(haunted_file)
    print(f"   Loaded {len(haunted)} objects")
    
    # Merge
    print("\n🔀 Merging interactions...")
    merged = merge_interactions(extracted, haunted)
    print(f"   Created {len(merged)} merged objects")
    
    # Save
    print(f"\n💾 Saving merged data to {output_file.name}...")
    save_json(output_file, merged)
    print("   ✅ Saved successfully")
    
    # Generate report
    print()
    report = generate_report(extracted, haunted, merged)
    print(report)
    
    # Save report
    report_file = output_file.with_suffix('.report.txt')
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\n📄 Report saved to {report_file.name}")
    
    print("\n✨ Merge complete!")
    print(f"   Output: {output_file}")
    print(f"   Report: {report_file}")
    
    return 0


if __name__ == '__main__':
    exit(main())
