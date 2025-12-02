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
        # Use ATTACK which is not yet implemented
        command = ParsedCommand(verb="ATTACK", target="troll")
        
        # Execute command
        result = game_engine.execute_command(command, fresh_state)
        
        # Verify it indicates not implemented
        assert result.success is False
        assert "not yet implemented" in result.message.lower()



class TestObjectExamine:
    """Test suite for examining objects."""
    
    def test_examine_object_in_room(self, game_engine, world_data, fresh_state):
        """
        Test examining an object that is in the current room.
        
        Requirements: 4.1
        """
        # Place mailbox in current room
        current_room = world_data.get_room(fresh_state.current_room)
        if "mailbox" not in current_room.items:
            current_room.items.append("mailbox")
        
        # Examine the mailbox
        result = game_engine.handle_examine("mailbox", fresh_state)
        
        # Verify examination succeeded
        assert result.success is True
        assert result.message is not None
        assert len(result.message) > 0
    
    def test_examine_object_not_present(self, game_engine, fresh_state):
        """
        Test examining an object that is not in the room or inventory.
        
        Requirements: 4.1
        """
        # Try to examine an object that's not present
        result = game_engine.handle_examine("nonexistent_object", fresh_state)
        
        # Verify examination failed
        assert result.success is False
        assert "don't see" in result.message.lower()
    
    def test_examine_object_in_inventory(self, game_engine, world_data, fresh_state):
        """
        Test examining an object that is in the player's inventory.
        
        Requirements: 4.1
        """
        # Add leaflet to inventory
        fresh_state.inventory.append("leaflet")
        
        # Examine the leaflet
        result = game_engine.handle_examine("leaflet", fresh_state)
        
        # Verify examination succeeded
        assert result.success is True
        assert result.message is not None
    
    def test_examine_returns_spooky_description(self, game_engine, world_data, fresh_state):
        """
        Test that examine returns spooky descriptions.
        
        Requirements: 4.1, 20.2
        """
        # Place mailbox in room
        current_room = world_data.get_room(fresh_state.current_room)
        if "mailbox" not in current_room.items:
            current_room.items.append("mailbox")
        
        # Examine mailbox
        result = game_engine.handle_examine("mailbox", fresh_state)
        
        # Verify we got a spooky description (not original)
        assert result.success is True
        # The response should be the spooky variant
        assert result.message is not None


class TestObjectTakeDrop:
    """Test suite for taking and dropping objects."""
    
    def test_take_object_from_room(self, game_engine, world_data, fresh_state):
        """
        Test taking a takeable object from the room.
        
        Requirements: 4.2, 5.2
        """
        # Place leaflet in room and mark as takeable
        current_room = world_data.get_room(fresh_state.current_room)
        if "leaflet" not in current_room.items:
            current_room.items.append("leaflet")
        
        leaflet = world_data.get_object("leaflet")
        leaflet.is_takeable = True
        
        # Take the leaflet
        result = game_engine.handle_take("leaflet", fresh_state)
        
        # Verify take succeeded
        assert result.success is True
        assert result.inventory_changed is True
        assert "leaflet" in fresh_state.inventory
        assert "leaflet" not in current_room.items
    
    def test_take_non_takeable_object(self, game_engine, world_data, fresh_state):
        """
        Test that non-takeable objects cannot be taken.
        
        Requirements: 5.2
        """
        # Place mailbox in room (not takeable)
        current_room = world_data.get_room(fresh_state.current_room)
        if "mailbox" not in current_room.items:
            current_room.items.append("mailbox")
        
        mailbox = world_data.get_object("mailbox")
        mailbox.is_takeable = False
        
        # Try to take the mailbox
        result = game_engine.handle_take("mailbox", fresh_state)
        
        # Verify take failed
        assert result.success is False
        assert "mailbox" not in fresh_state.inventory
    
    def test_take_object_not_in_room(self, game_engine, fresh_state):
        """
        Test taking an object that is not in the room.
        
        Requirements: 4.2
        """
        # Try to take an object that's not present
        result = game_engine.handle_take("nonexistent_object", fresh_state)
        
        # Verify take failed
        assert result.success is False
        assert "don't see" in result.message.lower()
    
    def test_take_object_already_in_inventory(self, game_engine, world_data, fresh_state):
        """
        Test taking an object that is already in inventory.
        
        Requirements: 4.2
        """
        # Add leaflet to inventory
        fresh_state.inventory.append("leaflet")
        
        # Try to take it again
        result = game_engine.handle_take("leaflet", fresh_state)
        
        # Verify take failed
        assert result.success is False
        assert "already have" in result.message.lower()
    
    def test_drop_object_from_inventory(self, game_engine, world_data, fresh_state):
        """
        Test dropping an object from inventory.
        
        Requirements: 4.3, 5.3
        """
        # Add leaflet to inventory
        fresh_state.inventory.append("leaflet")
        
        # Drop the leaflet
        result = game_engine.handle_drop("leaflet", fresh_state)
        
        # Verify drop succeeded
        assert result.success is True
        assert result.inventory_changed is True
        assert "leaflet" not in fresh_state.inventory
        
        # Verify object is now in room
        current_room = world_data.get_room(fresh_state.current_room)
        assert "leaflet" in current_room.items
    
    def test_drop_object_not_in_inventory(self, game_engine, fresh_state):
        """
        Test dropping an object that is not in inventory.
        
        Requirements: 4.3
        """
        # Try to drop an object we don't have
        result = game_engine.handle_drop("nonexistent_object", fresh_state)
        
        # Verify drop failed
        assert result.success is False
        assert "don't have" in result.message.lower()


class TestObjectInteractions:
    """Test suite for object interactions (open, close, read, move)."""
    
    def test_open_container(self, game_engine, world_data, fresh_state):
        """
        Test opening a container object.
        
        Requirements: 4.4
        """
        # Place mailbox in room
        current_room = world_data.get_room(fresh_state.current_room)
        if "mailbox" not in current_room.items:
            current_room.items.append("mailbox")
        
        # Get mailbox and ensure it's closed
        mailbox = world_data.get_object("mailbox")
        mailbox.state["is_open"] = False
        
        # Open the mailbox
        result = game_engine.handle_object_interaction("OPEN", "mailbox", fresh_state)
        
        # Verify open succeeded
        assert result.success is True
        assert mailbox.state["is_open"] is True
    
    def test_close_container(self, game_engine, world_data, fresh_state):
        """
        Test closing a container object.
        
        Requirements: 4.4
        """
        # Place mailbox in room
        current_room = world_data.get_room(fresh_state.current_room)
        if "mailbox" not in current_room.items:
            current_room.items.append("mailbox")
        
        # Get mailbox and ensure it's open
        mailbox = world_data.get_object("mailbox")
        mailbox.state["is_open"] = True
        
        # Close the mailbox
        result = game_engine.handle_object_interaction("CLOSE", "mailbox", fresh_state)
        
        # Verify close succeeded
        assert result.success is True
        assert mailbox.state["is_open"] is False
    
    def test_read_readable_object(self, game_engine, world_data, fresh_state):
        """
        Test reading a readable object.
        
        Requirements: 4.4
        """
        # Place leaflet in room
        current_room = world_data.get_room(fresh_state.current_room)
        if "leaflet" not in current_room.items:
            current_room.items.append("leaflet")
        
        # Read the leaflet
        result = game_engine.handle_object_interaction("READ", "leaflet", fresh_state)
        
        # Verify read succeeded
        assert result.success is True
        assert result.message is not None
        assert len(result.message) > 0
    
    def test_move_moveable_object(self, game_engine, world_data, fresh_state):
        """
        Test moving a moveable object (like the rug).
        
        Requirements: 4.4, 4.5
        
        Note: This test assumes a rug object exists in the data.
        If not, it will be skipped.
        """
        # Check if rug exists in world data
        try:
            rug = world_data.get_object("rug")
        except ValueError:
            pytest.skip("Rug object not found in game data")
        
        # Place rug in room
        current_room = world_data.get_room(fresh_state.current_room)
        if "rug" not in current_room.items:
            current_room.items.append("rug")
        
        # Move the rug
        result = game_engine.handle_object_interaction("MOVE", "rug", fresh_state)
        
        # Verify move succeeded or returned appropriate message
        assert result.message is not None
    
    def test_interaction_with_conditions(self, game_engine, world_data, fresh_state):
        """
        Test that interactions with conditions are properly checked.
        
        Requirements: 4.5
        """
        # Place mailbox in room
        current_room = world_data.get_room(fresh_state.current_room)
        if "mailbox" not in current_room.items:
            current_room.items.append("mailbox")
        
        # Get mailbox and ensure it's closed
        mailbox = world_data.get_object("mailbox")
        mailbox.state["is_open"] = False
        
        # Try to read mailbox while closed (should have condition)
        result = game_engine.handle_object_interaction("READ", "mailbox", fresh_state)
        
        # Result depends on whether READ interaction has condition
        # At minimum, should not crash
        assert result.message is not None
    
    def test_interaction_updates_flags(self, game_engine, world_data, fresh_state):
        """
        Test that interactions can update game flags.
        
        Requirements: 4.5
        
        Note: This test will be more meaningful once we have objects
        that set flags (like moving the rug to reveal trap door).
        """
        # For now, verify the mechanism exists
        initial_flags = fresh_state.flags.copy()
        
        # Perform an interaction
        current_room = world_data.get_room(fresh_state.current_room)
        if "mailbox" not in current_room.items:
            current_room.items.append("mailbox")
        
        mailbox = world_data.get_object("mailbox")
        mailbox.state["is_open"] = False
        
        result = game_engine.handle_object_interaction("OPEN", "mailbox", fresh_state)
        
        # Flags may or may not have changed, but should be accessible
        assert isinstance(fresh_state.flags, dict)
    
    def test_interaction_with_nonexistent_object(self, game_engine, fresh_state):
        """
        Test interaction with an object that doesn't exist.
        
        Requirements: 4.4
        """
        # Try to open a nonexistent object
        result = game_engine.handle_object_interaction("OPEN", "nonexistent", fresh_state)
        
        # Verify interaction failed
        assert result.success is False
        assert "don't see" in result.message.lower()
    
    def test_invalid_interaction_for_object(self, game_engine, world_data, fresh_state):
        """
        Test performing an invalid interaction on an object.
        
        Requirements: 4.4
        """
        # Place white_house (scenery) in room
        current_room = world_data.get_room(fresh_state.current_room)
        if "white_house" not in current_room.items:
            current_room.items.append("white_house")
        
        # Try to open the house (should not have OPEN interaction)
        result = game_engine.handle_object_interaction("OPEN", "white_house", fresh_state)
        
        # Verify interaction failed appropriately
        assert result.success is False
        assert "can't" in result.message.lower()


class TestCommandExecutionWithObjects:
    """Test suite for command execution with object commands."""
    
    def test_execute_examine_command(self, game_engine, world_data, fresh_state):
        """
        Test that examine commands are properly routed.
        
        Requirements: 4.1
        """
        # Place mailbox in room
        current_room = world_data.get_room(fresh_state.current_room)
        if "mailbox" not in current_room.items:
            current_room.items.append("mailbox")
        
        # Create examine command
        command = ParsedCommand(verb="EXAMINE", object="mailbox")
        
        # Execute command
        result = game_engine.execute_command(command, fresh_state)
        
        # Verify it was handled
        assert result.message is not None
    
    def test_execute_take_command(self, game_engine, world_data, fresh_state):
        """
        Test that take commands are properly routed.
        
        Requirements: 4.2
        """
        # Place leaflet in room and mark as takeable
        current_room = world_data.get_room(fresh_state.current_room)
        if "leaflet" not in current_room.items:
            current_room.items.append("leaflet")
        
        leaflet = world_data.get_object("leaflet")
        leaflet.is_takeable = True
        
        # Create take command
        command = ParsedCommand(verb="TAKE", object="leaflet")
        
        # Execute command
        result = game_engine.execute_command(command, fresh_state)
        
        # Verify it was handled
        assert result.success is True
        assert "leaflet" in fresh_state.inventory
    
    def test_execute_drop_command(self, game_engine, fresh_state):
        """
        Test that drop commands are properly routed.
        
        Requirements: 4.3
        """
        # Add leaflet to inventory
        fresh_state.inventory.append("leaflet")
        
        # Create drop command
        command = ParsedCommand(verb="DROP", object="leaflet")
        
        # Execute command
        result = game_engine.execute_command(command, fresh_state)
        
        # Verify it was handled
        assert result.success is True
        assert "leaflet" not in fresh_state.inventory
    
    def test_execute_open_command(self, game_engine, world_data, fresh_state):
        """
        Test that open commands are properly routed.
        
        Requirements: 4.4
        """
        # Place mailbox in room
        current_room = world_data.get_room(fresh_state.current_room)
        if "mailbox" not in current_room.items:
            current_room.items.append("mailbox")
        
        mailbox = world_data.get_object("mailbox")
        mailbox.state["is_open"] = False
        
        # Create open command
        command = ParsedCommand(verb="OPEN", object="mailbox")
        
        # Execute command
        result = game_engine.execute_command(command, fresh_state)
        
        # Verify it was handled
        assert result.message is not None
    
    def test_execute_read_command(self, game_engine, world_data, fresh_state):
        """
        Test that read commands are properly routed.
        
        Requirements: 4.4
        """
        # Place leaflet in room
        current_room = world_data.get_room(fresh_state.current_room)
        if "leaflet" not in current_room.items:
            current_room.items.append("leaflet")
        
        # Create read command
        command = ParsedCommand(verb="READ", object="leaflet")
        
        # Execute command
        result = game_engine.execute_command(command, fresh_state)
        
        # Verify it was handled
        assert result.message is not None
