#!/usr/bin/env python3
"""
Test script to verify wonFlag mapping fix
"""
import sys
sys.path.insert(0, 'src/lambda/game_handler')

from state_manager import GameState

def test_camelcase_to_snakecase():
    """Test that camelCase fields from frontend are properly mapped"""
    print("Testing camelCase to snake_case mapping...")
    
    # Simulate data coming from DynamoDB/GraphQL (camelCase)
    frontend_data = {
        'sessionId': 'test-session-123',
        'currentRoom': 'west_of_house',
        'wonFlag': True,
        'lampBattery': 150,
        'roomsVisited': ['west_of_house', 'north_of_house'],
        'bloodMoonActive': False,
        'soulsCollected': 5,
        'curseDuration': 10,
        'thiefHere': True,
        'inventory': ['lamp', 'sword'],
        'sanity': 85,
        'score': 100,
        'moves': 25,
    }
    
    # Load state from frontend data
    try:
        state = GameState.from_dict(frontend_data)
        
        # Verify all fields are correctly mapped
        assert state.session_id == 'test-session-123', "session_id not mapped"
        assert state.current_room == 'west_of_house', "current_room not mapped"
        assert state.won_flag == True, "won_flag not mapped"
        assert state.lamp_battery == 150, "lamp_battery not mapped"
        assert 'west_of_house' in state.rooms_visited, "rooms_visited not mapped"
        assert state.blood_moon_active == False, "blood_moon_active not mapped"
        assert state.souls_collected == 5, "souls_collected not mapped"
        assert state.curse_duration == 10, "curse_duration not mapped"
        assert state.thief_here == True, "thief_here not mapped"
        
        print("✅ All camelCase fields correctly mapped to snake_case")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_no_unexpected_kwargs():
    """Test that no unexpected keyword arguments are passed"""
    print("\nTesting that wonFlag doesn't cause unexpected keyword error...")
    
    data_with_wonflag = {
        'sessionId': 'test-456',
        'currentRoom': 'test_room',
        'wonFlag': False,  # This should be mapped, not skipped
    }
    
    try:
        state = GameState.from_dict(data_with_wonflag)
        assert state.won_flag == False
        print("✅ wonFlag properly mapped without errors")
        return True
    except TypeError as e:
        if "unexpected keyword argument 'wonFlag'" in str(e):
            print(f"❌ FAILED: {e}")
            print("   wonFlag is being passed directly instead of being mapped!")
            return False
        raise

if __name__ == '__main__':
    print("=" * 60)
    print("Testing wonFlag Mapping Fix")
    print("=" * 60)
    
    test1 = test_camelcase_to_snakecase()
    test2 = test_no_unexpected_kwargs()
    
    print("\n" + "=" * 60)
    if test1 and test2:
        print("✅ ALL TESTS PASSED - Fix is working!")
    else:
        print("❌ SOME TESTS FAILED - Fix needs more work")
    print("=" * 60)
