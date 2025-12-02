"""
Unit Tests for Game Engine

Tests specific scenarios for game engine functionality including
movement, object interactions, and command processing.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler'))

import pytest
from game_engine import GameEngine, ActionResult
from state_manager import GameState
from world_loader import WorldData
from command_parser import CommandParser, ParsedCommand


@pytest.fixture(scope="module")
def world_data():
    """Load world data once for all tests."""
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    return world


@pytest.fixture(scope="module")
def game_engine(world_data):
    """Create game engine instance."""
    return GameEngine(world_data)


@pytest.fixture
def fresh_state():
    """Create a fresh game state for each test."""
    return GameState.create_new_game()


class TestMovement:
    """Test suite for room navigation."""
    
    def test_valid_movement_between_rooms(self, game_engine, fresh_state):
        """
        Test that valid movement between rooms works correctly.
        
        Requirements: 3.1, 3.2
        """
        # Start at west_of_house
        assert fresh_state.current_room == "west_of_house"
        
        # Move north
        result = game_engine.handle_movement("NORTH", fresh_state)
        
        # Verify movement succeeded
        assert result.success is True
        assert result.room_changed is True
        assert result.new_room == "north_of_house"
        assert fresh_state.current_room == "north_of_house"
        
        # Verify state updates
        assert "north_of_house" in fresh_state.rooms_visited
        assert fresh_state.moves == 1
        assert fresh_state.turn_count == 1
    
    def test_blocked_direction(self, game_engine, fresh_state):
        """
        Test that movement in a blocked direction fails appropriately.
        
        Requirements: 3.4
        """
        # Start at west_of_house
        fresh_state.current_room = "west_of_house"
        initial_room = fresh_state.current_room
        initial_moves = fresh_state.moves
        
        # Try to move UP (not a valid exit from west_of_house)
        result = game_engine.handle_movement("UP", fresh_state)
        
        # Verify movement failed
        assert result.success is False
        assert result.room_changed is False
        assert result.new_room is None
        
        # Verify state unchanged
        assert fresh_state.current_room == initial_room
        assert fresh_state.moves == initial_moves
        assert "blocked" in result.message.lower()
    
    def test_movement_returns_description(self, game_engine, world_data, fresh_state):
        """
        Test that movement returns the appropriate room description.
        
        Requirements: 3.3
        """
        # Move to a new room
        result = game_engine.handle_movement("NORTH", fresh_state)
        
        # Verify description is returned
        assert result.success is True
        assert result.message is not None
        assert len(result.message) > 0
        
        # Verify it's the spooky description
        expected_description = world_data.get_room_description("north_of_house", fresh_state.sanity)
        assert result.message == expected_description
    
    def test_movement_chain(self, game_engine, fresh_state):
        """
        Test a sequence of movements to verify state consistency.
        
        Requirements: 3.1, 3.2
        """
        # Start at west_of_house
        assert fresh_state.current_room == "west_of_house"
        
        # Move north
        result1 = game_engine.handle_movement("NORTH", fresh_state)
        assert result1.success is True
        assert fresh_state.current_room == "north_of_house"
        assert fresh_state.moves == 1
        
        # Move east
        result2 = game_engine.handle_movement("EAST", fresh_state)
        assert result2.success is True
        assert fresh_state.current_room == "east_of_house"
        assert fresh_state.moves == 2
        
        # Move south
        result3 = game_engine.handle_movement("SOUTH", fresh_state)
        assert result3.success is True
        assert fresh_state.current_room == "south_of_house"
        assert fresh_state.moves == 3
        
        # Verify all rooms visited
        assert "west_of_house" in fresh_state.rooms_visited
        assert "north_of_house" in fresh_state.rooms_visited
        assert "east_of_house" in fresh_state.rooms_visited
        assert "south_of_house" in fresh_state.rooms_visited
    
    def test_movement_to_same_room_multiple_times(self, game_engine, fresh_state):
        """
        Test that moving to a room multiple times doesn't duplicate in rooms_visited.
        
        Requirements: 3.2
        """
        # Move north and back
        game_engine.handle_movement("NORTH", fresh_state)
        assert fresh_state.current_room == "north_of_house"
        
        # Move back west (SW or WEST both go to west_of_house from north_of_house)
        game_engine.handle_movement("WEST", fresh_state)
        assert fresh_state.current_room == "west_of_house"
        
        # Move north again
        game_engine.handle_movement("NORTH", fresh_state)
        assert fresh_state.current_room == "north_of_house"
        
        # Verify rooms_visited is a set (no duplicates)
        assert isinstance(fresh_state.rooms_visited, set)
        assert len(fresh_state.rooms_visited) == 2  # west_of_house and north_of_house
    
    def test_movement_increments_counters(self, game_engine, fresh_state):
        """
        Test that movement properly increments turn and move counters.
        
        Requirements: 3.2
        """
        initial_moves = fresh_state.moves
        initial_turns = fresh_state.turn_count
        
        # Make several moves
        game_engine.handle_movement("NORTH", fresh_state)
        game_engine.handle_movement("EAST", fresh_state)
        game_engine.handle_movement("SOUTH", fresh_state)
        
        # Verify counters incremented
        assert fresh_state.moves == initial_moves + 3
        assert fresh_state.turn_count == initial_turns + 3
    
    def test_invalid_room_id_handling(self, game_engine, fresh_state):
        """
        Test that invalid room IDs are handled gracefully.
        
        Requirements: 3.1
        """
        # Set current room to invalid ID
        fresh_state.current_room = "nonexistent_room"
        
        # Try to move
        result = game_engine.handle_movement("NORTH", fresh_state)
        
        # Should fail gracefully
        assert result.success is False
        assert result.room_changed is False


class TestFlagGatedExits:
    """Test suite for conditional exits based on flags."""
    
    def test_flag_gated_exit_blocked(self, game_engine, world_data, fresh_state):
        """
        Test that exits requiring flags are blocked when flag is not set.
        
        Requirements: 3.5
        
        Note: This test will be more meaningful once we have rooms with
        flag-gated exits in the game data. For now, we test the mechanism.
        """
        # This is a placeholder test - actual flag-gated rooms will be tested
        # once we have specific examples in the game data
        
        # For now, just verify the flag checking mechanism exists
        # by checking that rooms can have flags_required
        room = world_data.get_room("west_of_house")
        assert hasattr(room, 'flags_required')
    
    def test_flag_gated_exit_allowed(self, game_engine, fresh_state):
        """
        Test that exits requiring flags are allowed when flag is set.
        
        Requirements: 3.5
        
        Note: This will be expanded once we have specific flag-gated rooms.
        """
        # Set a flag
        fresh_state.set_flag("test_flag", True)
        
        # Verify flag is set
        assert fresh_state.get_flag("test_flag") is True
        
        # This test will be expanded with actual flag-gated room examples


class TestRoomEffects:
    """Test suite for room-based effects like sanity changes."""
    
    def test_room_sanity_effect_applied(self, game_engine, world_data):
        """
        Test that rooms with sanity effects properly modify player sanity.
        
        Requirements: 3.2
        """
        # Create a state with known sanity
        state = GameState.create_new_game()
        state.sanity = 80
        
        # Find a room with sanity effect (if any exist in data)
        # For now, test the mechanism
        state.current_room = "west_of_house"
        
        # Move to another room
        result = game_engine.handle_movement("NORTH", state)
        
        # Sanity should be within valid bounds
        assert 0 <= state.sanity <= 100
    
    def test_sanity_bounds_maintained(self, game_engine, fresh_state):
        """
        Test that sanity never goes below 0 or above 100.
        
        Requirements: 3.2
        """
        # Set sanity to edge values and move
        fresh_state.sanity = 5
        game_engine.handle_movement("NORTH", fresh_state)
        assert fresh_state.sanity >= 0
        
        fresh_state.sanity = 95
        game_engine.handle_movement("SOUTH", fresh_state)
        assert fresh_state.sanity <= 100


class TestCommandExecution:
    """Test suite for command execution routing."""
    
    def test_execute_movement_command(self, game_engine, fresh_state):
        """
        Test that movement commands are properly routed to movement handler.
        
        Requirements: 3.1
        """
        # Create a movement command
        command = ParsedCommand(verb="GO", direction="NORTH")
        
        # Execute command
        result = game_engine.execute_command(command, fresh_state)
        
        # Verify it was handled as movement
        assert result.success is True
        assert result.room_changed is True
        assert fresh_state.current_room == "north_of_house"
    
    def test_execute_unknown_command(self, game_engine, fresh_state):
        """
        Test that unknown commands return appropriate error.
        
        Requirements: 2.5
        """
        # Create an unknown command
        command = ParsedCommand(verb="UNKNOWN", object="something")
        
        # Execute command
        result = game_engine.execute_command(command, fresh_state)
        
        # Verify error response
        assert result.success is False
        assert "don't understand" in result.message.lower()
    
    def test_execute_unimplemented_command(self, game_engine, fresh_state):
        """
        Test that unimplemented commands return appropriate message.
        """
        # Create a command that's recognized but not yet implemented
        command = ParsedCommand(verb="TAKE", object="lamp")
        
        # Execute command
        result = game_engine.execute_command(command, fresh_state)
        
        # Verify it indicates not implemented
        assert result.success is False
        assert "not yet implemented" in result.message.lower()
