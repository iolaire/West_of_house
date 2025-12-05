"""
Unit Tests for AppSync Game Handler

Tests the AppSync Lambda resolver including:
- Valid command processing
- New game creation (auto-provisioning)
- Error handling (exceptions)
- State preservation

Requirements: 16.1, 16.3, 16.5
"""

import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler'))

from index import handler, initialize_game_components
from state_manager import GameState
from game_engine import ActionResult
from command_parser import ParsedCommand

@pytest.fixture(scope="module")
def mock_context():
    """Create a mock Lambda context."""
    context = Mock()
    context.request_id = "test-request-123"
    context.function_name = "gameHandler"
    context.memory_limit_in_mb = 128
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:gameHandler"
    return context

@pytest.fixture
def mock_session_manager():
    """Create a mock session manager."""
    manager = Mock()
    manager.save_session = Mock()
    manager.load_session = Mock()
    return manager

@pytest.fixture
def mock_world_data():
    """Create a mock world data."""
    world = Mock()
    # Mock get_room to return a basic room object
    room = Mock()
    room.exits = {"NORTH": "north_of_house"}
    room.items = []
    world.get_room.return_value = room
    world.get_room_description.return_value = "A spooky room."
    return world

class TestAppSyncHandler:
    
    def test_valid_command_execution(self, mock_context, mock_session_manager, mock_world_data):
        """Test successful execution of a valid command."""
        # Setup state
        state = GameState.create_new_game()
        state.session_id = "test-session-123"
        mock_session_manager.load_session.return_value = state
        
        # Setup event
        event = {
            "arguments": {
                "sessionId": "test-session-123",
                "command": "go north"
            }
        }
        
        # Mock dependencies
        with patch('index.session_manager', mock_session_manager):
            with patch('index.world_data', mock_world_data):
                with patch('index.game_engine') as mock_engine:
                    with patch('index.command_parser') as mock_parser:
                        # Mock execution
                        def update_state(command, state):
                            state.current_room = "north_of_house"
                            return ActionResult(
                                success=True, 
                                message="You go north.", 
                                new_room="north_of_house"
                            )
                        
                        mock_parser.parse.return_value = ParsedCommand("GO", "NORTH")
                        mock_engine.execute_command.side_effect = update_state
                        
                        # Execute
                        response = handler(event, mock_context)
                        
                        # Verify response structure
                        assert response["room"] == "north_of_house"
                        assert response["message"] == "You go north."
                        assert response["sanity"] == state.sanity
                        
                        # Verify state saved
                        mock_session_manager.save_session.assert_called_once()

    def test_auto_create_session_if_missing(self, mock_context, mock_session_manager, mock_world_data):
        """Test that a new session is created if the ID is not found."""
        # Setup session manager to return None (not found)
        mock_session_manager.load_session.return_value = None
        
        event = {
            "arguments": {
                "sessionId": "new-session-123",
                "command": "look"
            }
        }
        
        with patch('index.session_manager', mock_session_manager):
            with patch('index.world_data', mock_world_data):
                with patch('index.game_engine') as mock_engine:
                    with patch('index.command_parser') as mock_parser:
                        mock_parser.parse.return_value = ParsedCommand("LOOK")
                        mock_engine.execute_command.return_value = ActionResult(True, "You look around.")
                        
                        response = handler(event, mock_context)
                        
                        # Verify new session was created and saved
                        assert mock_session_manager.save_session.call_count >= 1
                        saved_state = mock_session_manager.save_session.call_args[0][0]
                        assert saved_state.session_id == "new-session-123"

    def test_missing_arguments_raises_error(self, mock_context):
        """Test that missing arguments raise ValueError."""
        event = {"arguments": {}}
        
        with pytest.raises(ValueError, match="Missing sessionId or command"):
            handler(event, mock_context)

    def test_database_error_propagates(self, mock_context, mock_session_manager):
        """Test that database errors are propagated as exceptions."""
        mock_session_manager.load_session.side_effect = Exception("DynamoDB Error")
        
        event = {
            "arguments": {
                "sessionId": "test-session",
                "command": "look"
            }
        }
        
        with patch('index.session_manager', mock_session_manager):
            with patch('index.initialize_game_components'):
                with pytest.raises(Exception, match="DynamoDB Error"):
                    handler(event, mock_context)
