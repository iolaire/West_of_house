"""
Unit tests for ENTER and EXIT command handlers.

Tests the handle_enter and handle_exit methods in GameEngine to ensure they properly:
- Support entering objects (vehicles, buildings, passages)
- Support exiting current location or object
- Validate entry/exit points exist
- Update player location appropriately
- Return thematic descriptions with haunted theme
"""

import pytest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler'))

from game_engine import GameEngine, ActionResult
from state_manager import GameState
from world_loader import WorldData, Room, GameObject, Interaction
from command_parser import CommandParser


@pytest.fixture
def world_data():
    """Create a minimal world data for testing."""
    world = WorldData()
    
    # Create test rooms with IN/OUT exits
    world.rooms = {
        'outside': Room(
            id='outside',
            name='Outside',
            description_original='You are outside a building.',
            description_spooky='You stand before a cursed structure, its entrance beckoning.',
            exits={'IN': 'inside', 'NORTH': 'forest'},
            items=['building'],
            is_dark=False
        ),
        'inside': Room(
            id='inside',
            name='Inside',
            description_original='You are inside a building.',
            description_spooky='The interior is dark and foreboding, shadows dancing on the walls.',
            exits={'OUT': 'outside'},
            items=[],
            is_dark=False
        ),
        'forest': Room(
            id='forest',
            name='Forest',
            description_original='A dense forest.',
            description_spooky='Twisted trees surround you, their branches reaching like skeletal fingers.',
            exits={'SOUTH': 'outside'},
            items=[],
            is_dark=False
        ),
        'vehicle_room': Room(
            id='vehicle_room',
            name='Vehicle Room',
            description_original='A room with a vehicle.',
            description_spooky='A cursed carriage sits here, waiting.',
            exits={'NORTH': 'outside'},
            items=['carriage'],
            is_dark=False
        ),
        'inside_vehicle': Room(
            id='inside_vehicle',
            name='Inside Vehicle',
            description_original='Inside the vehicle.',
            description_spooky='The interior of the carriage is cramped and smells of decay.',
            exits={},
            items=[],
            is_dark=False
        )
    }
    
    # Create enterable objects for testing
    world.objects = {
        'building': GameObject(
            id='building',
            name='building',
            name_spooky='cursed building',
            type='scenery',
            state={
                'is_enterable': True,
                'entry_destination': 'inside',
                'exit_destination': 'outside'
            },
            interactions=[],
            is_takeable=False
        ),
        'carriage': GameObject(
            id='carriage',
            name='carriage',
            name_spooky='cursed carriage',
            type='vehicle',
            state={
                'is_enterable': True,
                'entry_destination': 'inside_vehicle',
                'exit_destination': 'vehicle_room'
            },
            interactions=[],
            is_takeable=False
        ),
        'wall': GameObject(
            id='wall',
            name='wall',
            name_spooky='stone wall',
            type='scenery',
            state={'is_enterable': False},
            interactions=[],
            is_takeable=False
        ),
        'door': GameObject(
            id='door',
            name='door',
            name_spooky='locked door',
            type='scenery',
            state={
                'is_enterable': True,
                'entry_destination': 'inside',
                'entry_condition': 'door_unlocked'
            },
            interactions=[],
            is_takeable=False
        )
    }
    
    world.initial_flags = {}
    world._loaded = True
    
    return world


@pytest.fixture
def game_engine(world_data):
    """Create a game engine with test world data."""
    return GameEngine(world_data)


@pytest.fixture
def game_state():
    """Create a fresh game state."""
    state = GameState(session_id='test-session', current_room='outside')
    return state


# ENTER command tests

def test_enter_no_object_uses_in_direction(game_engine, game_state):
    """Test ENTER with no object specified uses IN direction."""
    result = game_engine.handle_enter(None, game_state)
    
    assert result.success is True
    assert result.room_changed is True
    assert result.new_room == 'inside'
    assert game_state.current_room == 'inside'


def test_enter_enterable_object_success(game_engine, game_state):
    """Test successful entry into an enterable object."""
    result = game_engine.handle_enter('building', game_state)
    
    assert result.success is True
    assert result.room_changed is True
    assert result.new_room == 'inside'
    assert game_state.current_room == 'inside'
    assert 'enter' in result.message.lower()


def test_enter_vehicle_success(game_engine, game_state):
    """Test successful entry into a vehicle."""
    game_state.current_room = 'vehicle_room'
    result = game_engine.handle_enter('carriage', game_state)
    
    assert result.success is True
    assert result.room_changed is True
    assert result.new_room == 'inside_vehicle'
    assert game_state.current_room == 'inside_vehicle'


def test_enter_non_enterable_object(game_engine, game_state):
    """Test entering a non-enterable object fails."""
    game_state.current_room = 'outside'
    game_engine.world.rooms['outside'].items.append('wall')
    
    result = game_engine.handle_enter('wall', game_state)
    
    assert result.success is False
    assert result.room_changed is False
    assert "can't enter" in result.message.lower()


def test_enter_missing_object(game_engine, game_state):
    """Test entering an object that doesn't exist in the room."""
    result = game_engine.handle_enter('carriage', game_state)
    
    assert result.success is False
    assert result.room_changed is False
    assert "don't see" in result.message.lower()


def test_enter_object_without_destination(game_engine, game_state):
    """Test entering an object that has no entry destination."""
    # Create an enterable object without a destination
    game_engine.world.objects['building'].state['entry_destination'] = None
    
    result = game_engine.handle_enter('building', game_state)
    
    assert result.success is False
    assert result.room_changed is False
    assert "nowhere to go" in result.message.lower()


def test_enter_with_condition_not_met(game_engine, game_state):
    """Test entering an object when entry condition is not met."""
    game_state.current_room = 'outside'
    game_engine.world.rooms['outside'].items.append('door')
    
    # Condition not met (door_unlocked flag is False)
    result = game_engine.handle_enter('door', game_state)
    
    assert result.success is False
    assert result.room_changed is False
    assert "can't enter" in result.message.lower()


def test_enter_with_condition_met(game_engine, game_state):
    """Test entering an object when entry condition is met."""
    game_state.current_room = 'outside'
    game_engine.world.rooms['outside'].items.append('door')
    game_state.set_flag('door_unlocked', True)
    
    result = game_engine.handle_enter('door', game_state)
    
    assert result.success is True
    assert result.room_changed is True
    assert result.new_room == 'inside'


# EXIT command tests

def test_exit_no_object_uses_out_direction(game_engine, game_state):
    """Test EXIT with no object specified uses OUT direction."""
    game_state.current_room = 'inside'
    result = game_engine.handle_exit(None, game_state)
    
    assert result.success is True
    assert result.room_changed is True
    assert result.new_room == 'outside'
    assert game_state.current_room == 'outside'


def test_exit_from_vehicle(game_engine, game_state):
    """Test exiting from a vehicle."""
    game_state.current_room = 'inside_vehicle'
    # Add carriage to the room (representing we're in it)
    game_engine.world.rooms['inside_vehicle'].items.append('carriage')
    
    result = game_engine.handle_exit('carriage', game_state)
    
    assert result.success is True
    assert result.room_changed is True
    assert result.new_room == 'vehicle_room'
    assert game_state.current_room == 'vehicle_room'


def test_exit_object_not_in_room(game_engine, game_state):
    """Test exiting an object that's not in the current room."""
    game_state.current_room = 'inside'
    result = game_engine.handle_exit('carriage', game_state)
    
    assert result.success is False
    assert result.room_changed is False
    assert "not in" in result.message.lower()


def test_exit_object_without_destination(game_engine, game_state):
    """Test exiting an object without exit destination falls back to OUT."""
    game_state.current_room = 'inside'
    game_engine.world.rooms['inside'].items.append('building')
    game_engine.world.objects['building'].state['exit_destination'] = None
    
    result = game_engine.handle_exit('building', game_state)
    
    # Should fall back to OUT direction
    assert result.success is True
    assert result.room_changed is True
    assert result.new_room == 'outside'


# Command parser tests

def test_command_parser_enter():
    """Test command parser recognizes 'enter'."""
    parser = CommandParser()
    command = parser.parse('enter')
    
    assert command.verb == 'ENTER'
    assert command.object is None


def test_command_parser_enter_building():
    """Test command parser recognizes 'enter building'."""
    parser = CommandParser()
    command = parser.parse('enter building')
    
    assert command.verb == 'ENTER'
    assert command.object == 'building'


def test_command_parser_enter_the_carriage():
    """Test command parser recognizes 'enter the carriage' (ignores article)."""
    parser = CommandParser()
    command = parser.parse('enter the carriage')
    
    assert command.verb == 'ENTER'
    assert command.object == 'carriage'


def test_command_parser_exit():
    """Test command parser recognizes 'exit'."""
    parser = CommandParser()
    command = parser.parse('exit')
    
    assert command.verb == 'EXIT'
    assert command.object is None


def test_command_parser_exit_building():
    """Test command parser recognizes 'exit building'."""
    parser = CommandParser()
    command = parser.parse('exit building')
    
    assert command.verb == 'EXIT'
    assert command.object == 'building'


def test_command_parser_leave():
    """Test command parser recognizes 'leave' as EXIT synonym."""
    parser = CommandParser()
    command = parser.parse('leave')
    
    assert command.verb == 'EXIT'
    assert command.object is None


def test_command_parser_leave_carriage():
    """Test command parser recognizes 'leave carriage'."""
    parser = CommandParser()
    command = parser.parse('leave carriage')
    
    assert command.verb == 'EXIT'
    assert command.object == 'carriage'


# Integration tests with game engine

def test_enter_exit_round_trip(game_engine, game_state):
    """Test entering and then exiting returns to original location."""
    original_room = game_state.current_room
    
    # Enter building
    enter_result = game_engine.handle_enter('building', game_state)
    assert enter_result.success is True
    assert game_state.current_room == 'inside'
    
    # Exit building
    exit_result = game_engine.handle_exit(None, game_state)
    assert exit_result.success is True
    assert game_state.current_room == original_room


def test_enter_increments_turn_counter(game_engine, game_state):
    """Test that entering increments the turn counter."""
    initial_turns = game_state.turn_count
    
    game_engine.handle_enter('building', game_state)
    
    assert game_state.turn_count == initial_turns + 1


def test_exit_increments_turn_counter(game_engine, game_state):
    """Test that exiting increments the turn counter."""
    game_state.current_room = 'inside'
    initial_turns = game_state.turn_count
    
    game_engine.handle_exit(None, game_state)
    
    assert game_state.turn_count == initial_turns + 1


def test_enter_applies_room_sanity_effects(game_engine, game_state):
    """Test that entering a room applies sanity effects."""
    # Set up a room with sanity effect
    game_engine.world.rooms['inside'].sanity_effect = -5
    initial_sanity = game_state.sanity
    
    game_engine.handle_enter('building', game_state)
    
    assert game_state.sanity == initial_sanity - 5


def test_exit_applies_room_sanity_effects(game_engine, game_state):
    """Test that exiting to a room applies sanity effects."""
    game_state.current_room = 'inside'
    # Set up a room with sanity effect and lower initial sanity
    game_state.sanity = 50
    game_engine.world.rooms['outside'].sanity_effect = 5
    initial_sanity = game_state.sanity
    
    game_engine.handle_exit(None, game_state)
    
    assert game_state.sanity == initial_sanity + 5
