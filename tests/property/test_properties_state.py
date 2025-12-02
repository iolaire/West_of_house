"""
Property-Based Tests for Game State Management

Tests correctness properties related to game state persistence,
serialization, and session management.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler'))

import pytest
from hypothesis import given, strategies as st, settings
from state_manager import GameState
import json


# Custom strategies for generating test data
@st.composite
def game_state_strategy(draw):
    """
    Generate arbitrary GameState instances for property testing.
    
    Creates valid game states with random but realistic values.
    """
    session_id = draw(st.uuids()).hex
    current_room = draw(st.sampled_from([
        "west_of_house", "north_of_house", "south_of_house", 
        "kitchen", "living_room", "attic", "cellar"
    ]))
    
    # Generate inventory (0-10 items)
    inventory = draw(st.lists(
        st.sampled_from(["lamp", "sword", "rope", "keys", "mailbox", "leaflet"]),
        min_size=0,
        max_size=10,
        unique=True
    ))
    
    # Generate flags (0-20 flags)
    flag_names = ["rug_moved", "trap_door_open", "window_open", "grate_unlocked"]
    flags = {}
    for flag in draw(st.lists(st.sampled_from(flag_names), max_size=20)):
        flags[flag] = draw(st.booleans() | st.integers(min_value=0, max_value=100))
    
    # Generate rooms visited
    rooms_visited = set([current_room])
    for room in draw(st.lists(st.sampled_from([
        "west_of_house", "north_of_house", "kitchen", "living_room"
    ]), max_size=10)):
        rooms_visited.add(room)
    
    # Generate statistics
    turn_count = draw(st.integers(min_value=0, max_value=1000))
    sanity = draw(st.integers(min_value=0, max_value=100))
    score = draw(st.integers(min_value=0, max_value=350))
    moves = draw(st.integers(min_value=0, max_value=1000))
    lamp_battery = draw(st.integers(min_value=0, max_value=200))
    souls_collected = draw(st.integers(min_value=0, max_value=100))
    curse_duration = draw(st.integers(min_value=0, max_value=50))
    
    # Generate boolean flags
    cursed = draw(st.booleans())
    blood_moon_active = draw(st.booleans())
    lucky = draw(st.booleans())
    thief_here = draw(st.booleans())
    
    return GameState(
        session_id=session_id,
        current_room=current_room,
        inventory=inventory,
        flags=flags,
        rooms_visited=rooms_visited,
        turn_count=turn_count,
        sanity=sanity,
        cursed=cursed,
        blood_moon_active=blood_moon_active,
        souls_collected=souls_collected,
        curse_duration=curse_duration,
        score=score,
        moves=moves,
        lamp_battery=lamp_battery,
        lucky=lucky,
        thief_here=thief_here
    )


# Feature: game-backend-api, Property 16: Save/load round trip
@settings(max_examples=100)
@given(state=game_state_strategy())
def test_save_load_round_trip(state):
    """
    For any game state, serializing to dict and deserializing should preserve all fields.
    
    **Validates: Requirements 1.2, 1.5**
    
    This property ensures that game state can be reliably persisted and restored
    without data loss or corruption.
    """
    # Serialize to dictionary
    state_dict = state.to_dict()
    
    # Deserialize back to GameState
    restored_state = GameState.from_dict(state_dict)
    
    # Verify all critical fields are preserved
    assert restored_state.session_id == state.session_id
    assert restored_state.current_room == state.current_room
    assert restored_state.inventory == state.inventory
    assert restored_state.flags == state.flags
    assert restored_state.rooms_visited == state.rooms_visited
    assert restored_state.turn_count == state.turn_count
    assert restored_state.sanity == state.sanity
    assert restored_state.cursed == state.cursed
    assert restored_state.blood_moon_active == state.blood_moon_active
    assert restored_state.souls_collected == state.souls_collected
    assert restored_state.curse_duration == state.curse_duration
    assert restored_state.score == state.score
    assert restored_state.moves == state.moves
    assert restored_state.lamp_battery == state.lamp_battery
    assert restored_state.lucky == state.lucky
    assert restored_state.thief_here == state.thief_here


# Feature: game-backend-api, Property 16: Save/load round trip (JSON variant)
@settings(max_examples=100)
@given(state=game_state_strategy())
def test_json_round_trip(state):
    """
    For any game state, serializing to JSON and deserializing should preserve all fields.
    
    **Validates: Requirements 1.2, 1.5**
    
    This property ensures JSON serialization maintains data integrity.
    """
    # Serialize to JSON
    json_str = state.to_json()
    
    # Verify it's valid JSON
    json.loads(json_str)
    
    # Deserialize back to GameState
    restored_state = GameState.from_json(json_str)
    
    # Verify all critical fields are preserved
    assert restored_state.session_id == state.session_id
    assert restored_state.current_room == state.current_room
    assert set(restored_state.inventory) == set(state.inventory)
    assert restored_state.flags == state.flags
    assert restored_state.rooms_visited == state.rooms_visited
    assert restored_state.sanity == state.sanity
    assert restored_state.score == state.score
    assert restored_state.moves == state.moves
    assert restored_state.lamp_battery == state.lamp_battery


# Additional property: Serialization preserves data types
@settings(max_examples=100)
@given(state=game_state_strategy())
def test_serialization_preserves_types(state):
    """
    For any game state, serialization should preserve data types.
    
    Ensures that integers remain integers, booleans remain booleans, etc.
    """
    state_dict = state.to_dict()
    restored_state = GameState.from_dict(state_dict)
    
    # Check type preservation
    assert isinstance(restored_state.sanity, int)
    assert isinstance(restored_state.cursed, bool)
    assert isinstance(restored_state.score, int)
    assert isinstance(restored_state.inventory, list)
    assert isinstance(restored_state.flags, dict)
    assert isinstance(restored_state.rooms_visited, set)


# Additional property: New game initialization consistency
@settings(max_examples=100)
@given(st.integers(min_value=1, max_value=100))
def test_new_game_initialization_consistency(num_games):
    """
    For any number of new games, all should start with consistent initial values.
    
    **Validates: Requirements 1.2, 1.5**
    
    This ensures all players start with the same initial conditions.
    """
    for _ in range(num_games):
        state = GameState.create_new_game()
        
        # Verify initial values
        assert state.current_room == "west_of_house"
        assert state.inventory == []
        assert state.flags == {}
        assert state.rooms_visited == {"west_of_house"}
        assert state.turn_count == 0
        assert state.sanity == 100
        assert state.cursed is False
        assert state.blood_moon_active is True
        assert state.souls_collected == 0
        assert state.curse_duration == 0
        assert state.score == 0
        assert state.moves == 0
        assert state.lamp_battery == 200
        assert state.lucky is False
        assert state.thief_here is False


# Additional property: Session IDs are unique
@settings(max_examples=100)
@given(st.integers(min_value=2, max_value=50))
def test_session_id_uniqueness(num_sessions):
    """
    For any number of new games, all session IDs should be unique.
    
    **Validates: Requirements 1.1**
    
    This ensures no session ID collisions occur.
    """
    session_ids = set()
    
    for _ in range(num_sessions):
        state = GameState.create_new_game()
        assert state.session_id not in session_ids
        session_ids.add(state.session_id)
    
    # Verify we got the expected number of unique IDs
    assert len(session_ids) == num_sessions
