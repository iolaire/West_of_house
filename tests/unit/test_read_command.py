"""
Unit tests for READ command implementation.

Tests the handle_read method in GameEngine to ensure it properly:
- Reads readable objects and displays their text content
- Returns "nothing to read" if object is not readable
- Handles objects in room and inventory
- Applies state changes and sanity effects
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler'))

import pytest
from game_engine import GameEngine, ActionResult
from state_manager import GameState
from world_loader import WorldData
from command_parser import CommandParser


@pytest.fixture
def world_data():
    """Load world data for testing."""
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    return world


@pytest.fixture
def game_engine(world_data):
    """Create a game engine instance."""
    return GameEngine(world_data)


@pytest.fixture
def game_state():
    """Create a fresh game state."""
    state = GameState(session_id='test-session', current_room='west_of_house')
    return state


class TestReadCommand:
    """Test READ command functionality."""
    
    def test_read_readable_object_in_room(self, game_engine, game_state):
        """Test reading a readable object (leaflet) in the room."""
        # Add leaflet to room
        room = game_engine.world.get_room("west_of_house")
        room.items.append("leaflet")
        
        # Read the leaflet
        result = game_engine.handle_read("leaflet", game_state)
        
        assert result.success
        assert "ABANDON HOPE" in result.message
        assert "nightmare" in result.message.lower()
    
    def test_read_readable_object_in_inventory(self, game_engine, game_state):
        """Test reading a readable object in inventory."""
        # Add leaflet to inventory
        game_state.add_to_inventory("leaflet")
        
        # Read the leaflet
        result = game_engine.handle_read("leaflet", game_state)
        
        assert result.success
        assert "ABANDON HOPE" in result.message
    
    def test_read_non_readable_object(self, game_engine, game_state):
        """Test reading an object that is not readable."""
        # Add lamp to room (lamp has no READ interaction)
        room = game_engine.world.get_room("west_of_house")
        room.items.append("lamp")
        
        # Try to read the lamp
        result = game_engine.handle_read("lamp", game_state)
        
        assert not result.success
        assert "nothing to read" in result.message.lower()
    
    def test_read_object_not_present(self, game_engine, game_state):
        """Test reading an object that is not in room or inventory."""
        # Try to read an object that doesn't exist in current location
        # Use an object that's definitely not in west_of_house
        result = game_engine.handle_read("sword", game_state)
        
        assert not result.success
        assert "don't see" in result.message.lower()
    
    def test_read_updates_object_state(self, game_engine, game_state):
        """Test that reading updates object state (is_read flag)."""
        # Add leaflet to room
        room = game_engine.world.get_room("west_of_house")
        room.items.append("leaflet")
        
        # Get leaflet object
        leaflet = game_engine.world.get_object("leaflet")
        
        # Reset the state to ensure clean test
        leaflet.state["is_read"] = False
        
        # Verify initial state
        assert leaflet.state.get("is_read", False) == False
        
        # Read the leaflet
        result = game_engine.handle_read("leaflet", game_state)
        
        assert result.success
        # Verify state was updated
        assert leaflet.state.get("is_read", False) == True
    
    def test_read_with_conditional_interaction(self, game_engine, game_state):
        """Test reading with conditional interactions (mailbox)."""
        # Add mailbox to room
        room = game_engine.world.get_room("west_of_house")
        room.items.append("mailbox")
        
        # Get mailbox object
        mailbox = game_engine.world.get_object("mailbox")
        
        # Mailbox is closed, so READ should return closed message
        result = game_engine.handle_read("mailbox", game_state)
        
        assert result.success
        assert "sealed shut" in result.message.lower() or "closed" in result.message.lower()


class TestReadCommandParsing:
    """Test that READ commands are parsed correctly."""
    
    def test_parse_read_command(self):
        """Test parsing 'read leaflet'."""
        parser = CommandParser()
        command = parser.parse("read leaflet")
        
        assert command.verb == "READ"
        assert command.object == "leaflet"
    
    def test_parse_read_with_article(self):
        """Test parsing 'read the leaflet'."""
        parser = CommandParser()
        command = parser.parse("read the leaflet")
        
        assert command.verb == "READ"
        assert command.object == "leaflet"
    
    def test_parse_read_multi_word_object(self):
        """Test parsing 'read cursed parchment'."""
        parser = CommandParser()
        command = parser.parse("read cursed parchment")
        
        assert command.verb == "READ"
        # Parser handles multi-word objects with spaces
        assert command.object == "cursed parchment"


class TestReadCommandIntegration:
    """Test READ command through execute_command."""
    
    def test_execute_read_command(self, game_engine, game_state):
        """Test executing READ command through execute_command."""
        # Add leaflet to room
        room = game_engine.world.get_room("west_of_house")
        room.items.append("leaflet")
        
        # Parse and execute command
        parser = CommandParser()
        command = parser.parse("read leaflet")
        result = game_engine.execute_command(command, game_state)
        
        assert result.success
        assert "ABANDON HOPE" in result.message
    
    def test_execute_read_non_readable(self, game_engine, game_state):
        """Test executing READ on non-readable object."""
        # Add lamp to room
        room = game_engine.world.get_room("west_of_house")
        room.items.append("lamp")
        
        # Parse and execute command
        parser = CommandParser()
        command = parser.parse("read lamp")
        result = game_engine.execute_command(command, game_state)
        
        assert not result.success
        assert "nothing to read" in result.message.lower()
