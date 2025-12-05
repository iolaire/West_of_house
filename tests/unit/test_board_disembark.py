"""
Unit Tests for BOARD and DISEMBARK Commands

Tests the basic functionality of boarding and disembarking from vehicles.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler'))

import pytest
from game_engine import GameEngine, ActionResult
from state_manager import GameState
from world_loader import WorldData
from command_parser import CommandParser


@pytest.fixture
def world_data():
    """Load world data for tests."""
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    return world


@pytest.fixture
def game_engine(world_data):
    """Create game engine instance."""
    return GameEngine(world_data)


@pytest.fixture
def parser():
    """Create command parser instance."""
    return CommandParser()


class TestBoardCommand:
    """Test BOARD command functionality."""
    
    def test_board_vehicle_success(self, game_engine, world_data):
        """Test successfully boarding a vehicle."""
        # Create a test vehicle object
        from world_loader import GameObject, Interaction
        
        vehicle = GameObject(
            id="boat",
            name="boat",
            name_spooky="ghostly boat",
            type="vehicle",
            is_takeable=False,
            is_treasure=False,
            treasure_value=0,
            capacity=0,
            state={"is_vehicle": True, "requires_water": False},
            interactions=[]
        )
        
        # Add vehicle to world data
        world_data.objects["boat"] = vehicle
        
        # Create game state with vehicle in room
        state = GameState.create_new_game()
        state.current_room = "west_of_house"
        
        # Add vehicle to room
        room = world_data.get_room("west_of_house")
        room.items.append("boat")
        
        # Board the vehicle
        result = game_engine.handle_board("boat", state)
        
        assert result.success is True
        assert state.current_vehicle == "boat"
        assert "boat" in result.message.lower()
    
    def test_board_vehicle_not_present(self, game_engine):
        """Test boarding a vehicle that's not in the room."""
        state = GameState.create_new_game()
        state.current_room = "west_of_house"
        
        # Use a vehicle that definitely doesn't exist
        result = game_engine.handle_board("nonexistent_vehicle", state)
        
        assert result.success is False
        assert "don't see" in result.message.lower()
    
    def test_board_non_vehicle(self, game_engine, world_data):
        """Test boarding an object that's not a vehicle."""
        state = GameState.create_new_game()
        state.current_room = "west_of_house"
        
        # Add a non-vehicle object to the room
        room = world_data.get_room("west_of_house")
        if "mailbox" not in room.items:
            room.items.append("mailbox")
        
        result = game_engine.handle_board("mailbox", state)
        
        assert result.success is False
        assert "can't board" in result.message.lower()
    
    def test_board_while_already_in_vehicle(self, game_engine, world_data):
        """Test boarding a vehicle while already in another vehicle."""
        # Create a test vehicle
        from world_loader import GameObject
        
        vehicle1 = GameObject(
            id="boat",
            name="boat",
            name_spooky="ghostly boat",
            type="vehicle",
            is_takeable=False,
            is_treasure=False,
            treasure_value=0,
            capacity=0,
            state={"is_vehicle": True},
            interactions=[]
        )
        
        vehicle2 = GameObject(
            id="basket",
            name="basket",
            name_spooky="wicker basket",
            type="vehicle",
            is_takeable=False,
            is_treasure=False,
            treasure_value=0,
            capacity=0,
            state={"is_vehicle": True},
            interactions=[]
        )
        
        world_data.objects["boat"] = vehicle1
        world_data.objects["basket"] = vehicle2
        
        state = GameState.create_new_game()
        state.current_room = "west_of_house"
        state.current_vehicle = "boat"
        
        # Add second vehicle to room
        room = world_data.get_room("west_of_house")
        room.items.append("basket")
        
        result = game_engine.handle_board("basket", state)
        
        assert result.success is False
        assert "already in" in result.message.lower()


class TestDisembarkCommand:
    """Test DISEMBARK command functionality."""
    
    def test_disembark_success(self, game_engine, world_data):
        """Test successfully disembarking from a vehicle."""
        state = GameState.create_new_game()
        state.current_room = "west_of_house"
        state.current_vehicle = "boat"
        
        result = game_engine.handle_disembark(None, state)
        
        assert result.success is True
        assert state.current_vehicle is None
        assert "boat" in result.message.lower()
    
    def test_disembark_not_in_vehicle(self, game_engine):
        """Test disembarking when not in a vehicle."""
        state = GameState.create_new_game()
        state.current_room = "west_of_house"
        state.current_vehicle = None
        
        result = game_engine.handle_disembark(None, state)
        
        assert result.success is False
        assert "not in any vehicle" in result.message.lower()
    
    def test_disembark_wrong_vehicle(self, game_engine):
        """Test disembarking from a specific vehicle when in a different one."""
        state = GameState.create_new_game()
        state.current_room = "west_of_house"
        state.current_vehicle = "boat"
        
        result = game_engine.handle_disembark("basket", state)
        
        assert result.success is False
        assert "not in the basket" in result.message.lower()
    
    def test_disembark_specific_vehicle(self, game_engine):
        """Test disembarking from a specific vehicle."""
        state = GameState.create_new_game()
        state.current_room = "west_of_house"
        state.current_vehicle = "boat"
        
        result = game_engine.handle_disembark("boat", state)
        
        assert result.success is True
        assert state.current_vehicle is None


class TestBoardDisembarkRoundTrip:
    """Test round-trip property of board/disembark."""
    
    def test_board_then_disembark(self, game_engine, world_data):
        """Test that boarding then disembarking returns to original state."""
        # Create a test vehicle
        from world_loader import GameObject
        
        vehicle = GameObject(
            id="boat",
            name="boat",
            name_spooky="ghostly boat",
            type="vehicle",
            is_takeable=False,
            is_treasure=False,
            treasure_value=0,
            capacity=0,
            state={"is_vehicle": True},
            interactions=[]
        )
        
        world_data.objects["boat"] = vehicle
        
        state = GameState.create_new_game()
        state.current_room = "west_of_house"
        
        # Add vehicle to room
        room = world_data.get_room("west_of_house")
        room.items.append("boat")
        
        # Original state
        original_vehicle = state.current_vehicle
        assert original_vehicle is None
        
        # Board
        board_result = game_engine.handle_board("boat", state)
        assert board_result.success is True
        assert state.current_vehicle == "boat"
        
        # Disembark
        disembark_result = game_engine.handle_disembark(None, state)
        assert disembark_result.success is True
        assert state.current_vehicle == original_vehicle


class TestCommandParsing:
    """Test command parser for BOARD and DISEMBARK."""
    
    def test_parse_board_command(self, parser):
        """Test parsing BOARD command."""
        result = parser.parse("board boat")
        
        assert result.verb == "BOARD"
        assert result.object == "boat"
    
    def test_parse_board_synonym(self, parser):
        """Test parsing BOARD synonym (embark)."""
        result = parser.parse("embark boat")
        
        assert result.verb == "BOARD"
        assert result.object == "boat"
    
    def test_parse_disembark_command(self, parser):
        """Test parsing DISEMBARK command."""
        result = parser.parse("disembark")
        
        assert result.verb == "DISEMBARK"
    
    def test_parse_disembark_with_object(self, parser):
        """Test parsing DISEMBARK with specific vehicle."""
        result = parser.parse("disembark boat")
        
        assert result.verb == "DISEMBARK"
        assert result.object == "boat"
    
    def test_parse_get_out(self, parser):
        """Test parsing GET OUT as synonym for DISEMBARK."""
        result = parser.parse("get out")
        
        assert result.verb == "GET_OUT"
