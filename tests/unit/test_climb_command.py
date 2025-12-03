"""
Unit tests for CLIMB command handler.

Tests the handle_climb method in GameEngine to ensure it properly:
- Validates direction (UP/DOWN only)
- Checks for valid exits in the specified direction
- Validates climbable objects when specified
- Moves player to connected room
- Returns appropriate success/failure messages with haunted theme
"""

import pytest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler'))

from game_engine import GameEngine, ActionResult
from state_manager import GameState
from world_loader import WorldData, Room, GameObject, Interaction
from command_parser import CommandParser


@pytest.fixture
def world_data():
    """Create a minimal world data for testing."""
    world = WorldData()
    
    # Create test rooms with UP/DOWN exits
    world.rooms = {
        'ladder_bottom': Room(
            id='ladder_bottom',
            name='Ladder Bottom',
            description_original='Bottom of a ladder.',
            description_spooky='The bone ladder ends here in a chamber of darkness.',
            exits={'UP': 'ladder_top', 'WEST': 'timber_room'},
            items=[],
            is_dark=False
        ),
        'ladder_top': Room(
            id='ladder_top',
            name='Ladder Top',
            description_original='Top of a ladder.',
            description_spooky='A ladder of bones descends into darkness.',
            exits={'DOWN': 'ladder_bottom', 'UP': 'mine_4'},
            items=[],
            is_dark=False
        ),
        'mine_4': Room(
            id='mine_4',
            name='Mine Entrance',
            description_original='A mine entrance.',
            description_spooky='The cursed mine entrance looms before you.',
            exits={'DOWN': 'ladder_top'},
            items=[],
            is_dark=False
        ),
        'timber_room': Room(
            id='timber_room',
            name='Timber Room',
            description_original='A room with timber.',
            description_spooky='Rotted timber fills this cursed chamber.',
            exits={'EAST': 'ladder_bottom'},
            items=[],
            is_dark=False
        )
    }
    
    # Create a climbable object for testing
    world.objects = {
        'ladder': GameObject(
            id='ladder',
            name='ladder',
            name_spooky='bone ladder',
            type='scenery',
            state={'is_climbable': True},
            interactions=[],
            is_takeable=False
        ),
        'wall': GameObject(
            id='wall',
            name='wall',
            name_spooky='cursed wall',
            type='scenery',
            state={'is_climbable': False},
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
    state = GameState(session_id='test-session', current_room='ladder_bottom')
    return state


def test_climb_up_success(game_engine, game_state):
    """Test successful climb up."""
    result = game_engine.handle_climb('UP', None, game_state)
    
    assert result.success is True
    assert result.room_changed is True
    assert result.new_room == 'ladder_top'
    assert game_state.current_room == 'ladder_top'
    assert 'climb up' in result.message.lower()


def test_climb_down_success(game_engine, game_state):
    """Test successful climb down."""
    game_state.current_room = 'ladder_top'
    result = game_engine.handle_climb('DOWN', None, game_state)
    
    assert result.success is True
    assert result.room_changed is True
    assert result.new_room == 'ladder_bottom'
    assert game_state.current_room == 'ladder_bottom'
    assert 'climb down' in result.message.lower()


def test_climb_invalid_direction(game_engine, game_state):
    """Test climb with invalid direction (not UP or DOWN)."""
    result = game_engine.handle_climb('NORTH', None, game_state)
    
    assert result.success is False
    assert result.room_changed is False
    assert 'only climb up or down' in result.message.lower()


def test_climb_no_exit(game_engine, game_state):
    """Test climb when there's no exit in that direction."""
    game_state.current_room = 'timber_room'
    result = game_engine.handle_climb('UP', None, game_state)
    
    assert result.success is False
    assert result.room_changed is False
    assert 'nothing to climb' in result.message.lower()


def test_climb_with_climbable_object(game_engine, game_state):
    """Test climb with a climbable object specified."""
    # Add ladder to the room
    game_engine.world.rooms['ladder_bottom'].items.append('ladder')
    
    result = game_engine.handle_climb('UP', 'ladder', game_state)
    
    assert result.success is True
    assert result.room_changed is True
    assert result.new_room == 'ladder_top'


def test_climb_with_non_climbable_object(game_engine, game_state):
    """Test climb with a non-climbable object specified."""
    # Add wall to the room
    game_engine.world.rooms['ladder_bottom'].items.append('wall')
    
    result = game_engine.handle_climb('UP', 'wall', game_state)
    
    assert result.success is False
    assert result.room_changed is False
    assert "can't climb" in result.message.lower()


def test_climb_with_missing_object(game_engine, game_state):
    """Test climb with an object that doesn't exist in the room."""
    result = game_engine.handle_climb('UP', 'ladder', game_state)
    
    assert result.success is False
    assert result.room_changed is False
    assert "don't see" in result.message.lower()


def test_command_parser_climb_up():
    """Test command parser recognizes 'climb up'."""
    parser = CommandParser()
    command = parser.parse('climb up')
    
    assert command.verb == 'CLIMB'
    assert command.direction == 'UP'
    assert command.object is None


def test_command_parser_climb_down():
    """Test command parser recognizes 'climb down'."""
    parser = CommandParser()
    command = parser.parse('climb down')
    
    assert command.verb == 'CLIMB'
    assert command.direction == 'DOWN'
    assert command.object is None


def test_command_parser_climb_up_ladder():
    """Test command parser recognizes 'climb up ladder'."""
    parser = CommandParser()
    command = parser.parse('climb up ladder')
    
    assert command.verb == 'CLIMB'
    assert command.direction == 'UP'
    assert command.object == 'ladder'


def test_command_parser_climb_ladder():
    """Test command parser recognizes 'climb ladder' (implicit UP)."""
    parser = CommandParser()
    command = parser.parse('climb ladder')
    
    assert command.verb == 'CLIMB'
    assert command.direction == 'UP'
    assert command.object == 'ladder'


def test_command_parser_climb_synonyms():
    """Test command parser recognizes climb synonyms."""
    parser = CommandParser()
    
    # Test 'scale'
    command = parser.parse('scale up')
    assert command.verb == 'CLIMB'
    assert command.direction == 'UP'
    
    # Test 'ascend'
    command = parser.parse('ascend')
    assert command.verb == 'CLIMB'
    
    # Test 'descend'
    command = parser.parse('descend')
    assert command.verb == 'CLIMB'
