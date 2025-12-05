"""
Manual test script for SMELL command implementation.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/lambda/game_handler'))

from game_engine import GameEngine
from state_manager import GameState
from world_loader import WorldData
from command_parser import CommandParser


def main():
    """Test SMELL command functionality."""
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), 'src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    # Create game engine
    engine = GameEngine(world)
    
    # Create game state
    state = GameState('test_session', 'west_of_house')
    
    print("=" * 60)
    print("SMELL Command Manual Tests")
    print("=" * 60)
    print()
    
    # Test 1: SMELL command without object (room)
    print("Test 1 - Smell room:")
    result = engine.handle_smell(None, state)
    print(f'Success: {result.success}')
    print(f'Message: {result.message}')
    print()
    
    # Test 2: SMELL command with object
    print("Test 2 - Smell lamp:")
    result = engine.handle_smell('lamp', state)
    print(f'Success: {result.success}')
    print(f'Message: {result.message}')
    print()
    
    # Test 3: SMELL command with missing object
    print("Test 3 - Smell missing object:")
    result = engine.handle_smell('sword', state)
    print(f'Success: {result.success}')
    print(f'Message: {result.message}')
    print()
    
    # Test 4: Command parser - smell
    print("Test 4 - Parse 'smell' command:")
    parser = CommandParser()
    cmd = parser.parse('smell')
    print(f'Verb: {cmd.verb}')
    print()
    
    # Test 5: Command parser - smell lamp
    print("Test 5 - Parse 'smell lamp':")
    cmd = parser.parse('smell lamp')
    print(f'Verb: {cmd.verb}')
    print(f'Object: {cmd.object}')
    print()
    
    # Test 6: Command parser - sniff synonym
    print("Test 6 - Parse 'sniff lamp' (synonym):")
    cmd = parser.parse('sniff lamp')
    print(f'Verb: {cmd.verb}')
    print(f'Object: {cmd.object}')
    print()
    
    # Test 7: Execute command through engine
    print("Test 7 - Execute 'smell' through engine:")
    cmd = parser.parse('smell')
    result = engine.execute_command(cmd, state)
    print(f'Success: {result.success}')
    print(f'Message: {result.message}')
    print()
    
    # Test 8: Test sanity variation
    print("Test 8 - Smell room at different sanity levels:")
    state.sanity = 90
    result_high = engine.handle_smell(None, state)
    print(f'High sanity (90): {result_high.message[:60]}...')
    
    state.sanity = 50
    result_mid = engine.handle_smell(None, state)
    print(f'Mid sanity (50): {result_mid.message[:60]}...')
    
    state.sanity = 20
    result_low = engine.handle_smell(None, state)
    print(f'Low sanity (20): {result_low.message[:60]}...')
    print()
    
    print("=" * 60)
    print("All manual tests completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
