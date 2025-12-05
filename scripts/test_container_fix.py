#!/usr/bin/env python3
"""
Test script to verify container contents bug fix.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../amplify/functions/game-handler'))

from state_manager import GameState
from world_loader import WorldData
from game_engine import GameEngine

def test_mailbox_container():
    """Test that mailbox contents become accessible after opening."""

    print("=== Testing Mailbox Container Fix ===\n")

    # Load game data
    world = WorldData()
    world.load_from_json("amplify/functions/game-handler/data")

    # Create game engine and initial state
    engine = GameEngine(world)
    state = GameState(
        session_id="test",
        current_room="west_of_house",
        inventory=[],
        flags={},
        sanity=100
    )

    # Get initial room state
    room = engine.world.get_room("west_of_house")
    print(f"Initial room items: {room.items}")

    # Try to read advertisement before opening mailbox (should fail)
    print("\n--- Trying to READ advertisement before opening mailbox ---")
    result = engine.handle_command("read advertisement", state)
    print(f"Result: {result.message}")
    print(f"Success: {result.success}")

    # Open the mailbox
    print("\n--- Opening mailbox ---")
    result = engine.handle_command("open mailbox", state)
    print(f"Result: {result.message}")
    print(f"Success: {result.success}")
    if result.notifications:
        print(f"Notifications: {result.notifications}")

    # Check room items after opening
    print(f"\nRoom items after opening mailbox: {room.items}")

    # Try to read advertisement after opening mailbox (should succeed)
    print("\n--- Trying to READ advertisement after opening mailbox ---")
    result = engine.handle_command("read advertisement", state)
    print(f"Result: {result.message}")
    print(f"Success: {result.success}")

    # Try to take advertisement
    print("\n--- Trying to TAKE advertisement ---")
    result = engine.handle_command("take advertisement", state)
    print(f"Result: {result.message}")
    print(f"Success: {result.success}")
    print(f"Inventory: {state.inventory}")

    # Close the mailbox
    print("\n--- Closing mailbox ---")
    result = engine.handle_command("close mailbox", state)
    print(f"Result: {result.message}")
    print(f"Success: {result.success}")
    if result.notifications:
        print(f"Notifications: {result.notifications}")

    # Check room items after closing
    print(f"\nRoom items after closing mailbox: {room.items}")

    # Check mailbox state
    mailbox = engine.world.get_object("mailbox")
    print(f"Mailbox contents: {mailbox.state.get('contents', [])}")
    print(f"Mailbox is_open: {mailbox.state.get('is_open', False)}")

def test_bag_of_coins():
    """Test that bag_of_coins contents become accessible after opening."""

    print("\n\n=== Testing Bag of Coins Container Fix ===\n")

    # Load game data
    world = WorldData()
    world.load_from_json("amplify/functions/game-handler/data")

    # Create game engine and initial state in maze_5
    engine = GameEngine(world)
    state = GameState(
        session_id="test",
        current_room="maze_5",
        inventory=[],
        flags={},
        sanity=100
    )

    # Get room state
    room = engine.world.get_room("maze_5")
    print(f"Initial room items: {room.items}")

    # Try to take coins before opening bag (should fail)
    print("\n--- Trying to TAKE coins before opening bag ---")
    result = engine.handle_command("take coins", state)
    print(f"Result: {result.message}")
    print(f"Success: {result.success}")

    # Open the bag of coins
    print("\n--- Opening bag of coins ---")
    result = engine.handle_command("open bag_of_coins", state)
    print(f"Result: {result.message}")
    print(f"Success: {result.success}")
    if result.notifications:
        print(f"Notifications: {result.notifications}")

    # Check room items after opening
    print(f"\nRoom items after opening bag: {room.items}")

    # Try to take coins after opening (should succeed)
    print("\n--- Trying to TAKE coins after opening bag ---")
    result = engine.handle_command("take coins", state)
    print(f"Result: {result.message}")
    print(f"Success: {result.success}")
    print(f"Inventory: {state.inventory}")

if __name__ == "__main__":
    test_mailbox_container()
    test_bag_of_coins()