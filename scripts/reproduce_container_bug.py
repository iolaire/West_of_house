
import sys
import os
import pytest

# Add amplify directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../amplify/functions/game-handler'))

from game_engine import GameEngine
from state_manager import GameState
from world_loader import WorldData
from command_parser import ParsedCommand

def test_container_interaction_bug():
    # Initialize game
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    engine = GameEngine(world)
    state = GameState.create_new_game()
    
    # Ensure we are in west_of_house where mailbox is
    state.current_room = "west_of_house"
    
    print("\n--- Step 1: Open Mailbox ---")
    cmd_open = ParsedCommand(verb="OPEN", object="mailbox")
    result_open = engine.execute_command(cmd_open, state)
    print(f"Result: {result_open.message}")
    assert result_open.success
    
    # Verify mailbox is open in state
    is_open = state.get_object_state("mailbox", "is_open")
    contents = state.get_object_state("mailbox", "contents")
    print(f"Mailbox Open: {is_open}")
    print(f"Mailbox Contents: {contents}")
    
    print("\n--- Step 2: Examine Mailbox ---")
    cmd_examine = ParsedCommand(verb="EXAMINE", object="mailbox")
    result_examine = engine.execute_command(cmd_examine, state)
    print(f"Result: {result_examine.message}")
    
    # Check if "cursed parchment" or "leaflet" is mentioned
    has_parchment = "cursed parchment" in result_examine.message.lower() or "leaflet" in result_examine.message.lower()
    print(f"Mentions contents: {has_parchment}")
    
    print("\n--- Step 3: Examine Cursed Parchment ---")
    cmd_examine_item = ParsedCommand(verb="EXAMINE", object="cursed parchment")
    result_examine_item = engine.execute_command(cmd_examine_item, state)
    print(f"Result: {result_examine_item.message}")
    print(f"Success: {result_examine_item.success}")
    
    print("\n--- Step 4: Take Cursed Parchment ---")
    cmd_take = ParsedCommand(verb="TAKE", object="cursed parchment")
    result_take = engine.execute_command(cmd_take, state)
    print(f"Result: {result_take.message}")
    print(f"Success: {result_take.success}")

    print("\n--- Step 5: Read Cursed Parchment ---")
    cmd_read = ParsedCommand(verb="READ", object="cursed parchment")
    result_read = engine.execute_command(cmd_read, state)
    print(f"Result: {result_read.message}")
    print(f"Success: {result_read.success}")

if __name__ == "__main__":
    test_container_interaction_bug()
