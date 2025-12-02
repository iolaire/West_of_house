"""
Property-Based Tests for Light System

Tests correctness properties related to lamp battery drain,
automatic shutoff, and darkness mechanics.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler'))

import pytest
from hypothesis import given, strategies as st, settings, assume
from state_manager import GameState
from game_engine import GameEngine
from world_loader import WorldData


# Feature: game-backend-api, Property 21: Lamp battery drain
@settings(max_examples=100)
@given(
    initial_battery=st.integers(min_value=1, max_value=200),
    num_turns=st.integers(min_value=1, max_value=50),
    cursed=st.booleans()
)
def test_lamp_battery_drain(initial_battery, num_turns, cursed):
    """
    For any turn where the lamp is on, battery should decrease by 1 per turn
    (or 2 per turn if cursed).
    
    **Validates: Requirements 14.2**
    
    This property ensures lamp battery drains correctly based on curse status.
    """
    # Create game state with lamp in inventory and lamp on
    state = GameState.create_new_game()
    state.inventory = ["lamp"]
    state.set_flag("lamp_on", True)
    state.lamp_battery = initial_battery
    state.cursed = cursed
    
    # Load world data
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world = WorldData()
    world.load_from_json(data_dir)
    
    # Create game engine
    engine = GameEngine(world)
    
    # Calculate expected drain per turn
    drain_per_turn = 2 if cursed else 1
    
    # Apply battery drain for each turn
    for turn in range(num_turns):
        # Calculate expected battery before drain
        expected_battery_before = max(0, initial_battery - (turn * drain_per_turn))
        
        # If battery would be 0 or less, lamp should be off
        if expected_battery_before <= 0:
            break
        
        # Apply drain
        notifications = engine.apply_lamp_battery_drain(state)
        
        # Calculate expected battery after drain
        expected_battery_after = max(0, initial_battery - ((turn + 1) * drain_per_turn))
        
        # Verify battery decreased correctly
        assert state.lamp_battery == expected_battery_after, \
            f"Turn {turn + 1}: Expected battery {expected_battery_after}, got {state.lamp_battery}"
        
        # If battery reached 0, lamp should be off
        if state.lamp_battery == 0:
            assert state.get_flag("lamp_on", False) is False, \
                "Lamp should be off when battery reaches 0"
            assert any("gone out" in n.lower() or "darkness" in n.lower() for n in notifications), \
                "Should notify when lamp goes out"


# Feature: game-backend-api, Property 22: Lamp auto-shutoff
@settings(max_examples=100)
@given(
    initial_battery=st.integers(min_value=0, max_value=10),
    cursed=st.booleans()
)
def test_lamp_auto_shutoff(initial_battery, cursed):
    """
    For any game state where lamp_battery reaches 0, the lamp should
    automatically turn off.
    
    **Validates: Requirements 14.3**
    
    This property ensures the lamp turns off automatically when battery is depleted.
    """
    # Create game state with lamp in inventory and lamp on
    state = GameState.create_new_game()
    state.inventory = ["lamp"]
    state.set_flag("lamp_on", True)
    state.lamp_battery = initial_battery
    state.cursed = cursed
    
    # Load world data
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world = WorldData()
    world.load_from_json(data_dir)
    
    # Create game engine
    engine = GameEngine(world)
    
    # If battery is already 0, lamp should turn off immediately
    if initial_battery == 0:
        notifications = engine.apply_lamp_battery_drain(state)
        assert state.get_flag("lamp_on", False) is False, \
            "Lamp should be off when battery is 0"
        return
    
    # Apply battery drain until battery reaches 0
    drain_per_turn = 2 if cursed else 1
    turns_until_empty = (initial_battery + drain_per_turn - 1) // drain_per_turn
    
    for turn in range(turns_until_empty):
        notifications = engine.apply_lamp_battery_drain(state)
        
        # Check if battery reached 0
        if state.lamp_battery == 0:
            # Lamp should be off
            assert state.get_flag("lamp_on", False) is False, \
                f"Lamp should be off when battery reaches 0 (turn {turn + 1})"
            # Should have notification about lamp going out
            assert any("gone out" in n.lower() or "darkness" in n.lower() for n in notifications), \
                "Should notify when lamp goes out"
            break
    
    # Final check: if we drained all the way, lamp should be off
    if state.lamp_battery == 0:
        assert state.get_flag("lamp_on", False) is False, \
            "Lamp should be off after battery fully drained"


# Additional property: Battery never goes negative
@settings(max_examples=100)
@given(
    initial_battery=st.integers(min_value=0, max_value=200),
    num_turns=st.integers(min_value=1, max_value=100),
    cursed=st.booleans()
)
def test_battery_never_negative(initial_battery, num_turns, cursed):
    """
    For any sequence of battery drains, battery should never go below 0.
    
    This ensures battery is properly bounded.
    """
    # Create game state with lamp in inventory and lamp on
    state = GameState.create_new_game()
    state.inventory = ["lamp"]
    state.set_flag("lamp_on", True)
    state.lamp_battery = initial_battery
    state.cursed = cursed
    
    # Load world data
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world = WorldData()
    world.load_from_json(data_dir)
    
    # Create game engine
    engine = GameEngine(world)
    
    # Apply battery drain for many turns
    for _ in range(num_turns):
        engine.apply_lamp_battery_drain(state)
        
        # Battery should never be negative
        assert state.lamp_battery >= 0, \
            f"Battery should never be negative, got {state.lamp_battery}"


# Additional property: Lamp off means no battery drain
@settings(max_examples=100)
@given(
    initial_battery=st.integers(min_value=1, max_value=200),
    num_turns=st.integers(min_value=1, max_value=50)
)
def test_lamp_off_no_drain(initial_battery, num_turns):
    """
    For any game state where lamp is off, battery should not drain.
    
    This ensures battery only drains when lamp is actively on.
    """
    # Create game state with lamp in inventory but lamp OFF
    state = GameState.create_new_game()
    state.inventory = ["lamp"]
    state.set_flag("lamp_on", False)
    state.lamp_battery = initial_battery
    
    # Load world data
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world = WorldData()
    world.load_from_json(data_dir)
    
    # Create game engine
    engine = GameEngine(world)
    
    # Apply battery drain for many turns
    for _ in range(num_turns):
        engine.apply_lamp_battery_drain(state)
        
        # Battery should remain unchanged
        assert state.lamp_battery == initial_battery, \
            f"Battery should not drain when lamp is off, expected {initial_battery}, got {state.lamp_battery}"


# Additional property: No lamp means no drain
@settings(max_examples=100)
@given(
    initial_battery=st.integers(min_value=1, max_value=200),
    num_turns=st.integers(min_value=1, max_value=50)
)
def test_no_lamp_no_drain(initial_battery, num_turns):
    """
    For any game state where player doesn't have lamp, battery should not drain.
    
    This ensures battery only drains when player has the lamp.
    """
    # Create game state WITHOUT lamp in inventory
    state = GameState.create_new_game()
    state.inventory = []  # No lamp
    state.set_flag("lamp_on", True)  # Flag is on but no lamp
    state.lamp_battery = initial_battery
    
    # Load world data
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world = WorldData()
    world.load_from_json(data_dir)
    
    # Create game engine
    engine = GameEngine(world)
    
    # Apply battery drain for many turns
    for _ in range(num_turns):
        engine.apply_lamp_battery_drain(state)
        
        # Battery should remain unchanged
        assert state.lamp_battery == initial_battery, \
            f"Battery should not drain when player doesn't have lamp, expected {initial_battery}, got {state.lamp_battery}"
