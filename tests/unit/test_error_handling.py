"""
Unit Tests for Error Handling

Tests error handling scenarios for the Lambda handler including
invalid session IDs, malformed JSON, internal errors, and state preservation.

Requirements: 16.1, 16.2, 16.3, 16.5
"""

import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock
import copy

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler'))

import pytest
from index import (
    handler,
    handle_new_game,
    handle_command,
    handle_get_state,
    create_error_response,
    initialize_game_components
)
from state_manager import GameState
from game_engine import GameEngine
from world_loader import WorldData


@pytest.fixture(scope="module")
def mock_context():
    """Create a mock Lambda context."""
    context = Mock()
    context.request_id = "test-request-123"
    context.function_name = "gameHandler"
    context.memory_limit_in_mb = 128
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:gameHandler"
    return context


@pytest.fixture(scope="module")
def world_data():
    """Load world data once for all tests."""
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    return world


@pytest.fixture
def mock_session_manager():
    """Create a mock session manager."""
    manager = Mock()
    manager.save_session = Mock()
    manager.load_session = Mock()
    manager.delete_session = Mock()
    return manager


class TestInvalidSessionID:
    """
    Test error handling for invalid session IDs.
    
    Requirements: 16.1
    """
    
    def test_command_with_invalid_session_id(self, mock_context, mock_session_manager):
        """
        Test that invalid session ID returns 404 error.
        
        Requirements: 16.1
        """
        # Mock session manager to return None (session not found)
        mock_session_manager.load_session.return_value = None
        
        # Create event with invalid session ID
        event = {
            'httpMethod': 'POST',
            'path': '/api/game/command',
            'body': json.dumps({
                'session_id': 'invalid-session-id-12345',
                'command': 'go north'
            })
        }
        
        # Patch the global session_manager
        with patch('index.session_manager', mock_session_manager):
            with patch('index.world_data', Mock()):
                with patch('index.game_engine', Mock()):
                    with patch('index.command_parser', Mock()):
                        response = handler(event, mock_context)
        
        # Verify 404 response
        assert response['statusCode'] == 404
        
        # Parse response body
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error']['code'] == 'SESSION_NOT_FOUND'
        assert 'not found' in body['error']['message'].lower()
        assert 'invalid-session-id-12345' in body['error']['message']
    
    def test_get_state_with_invalid_session_id(self, mock_context, mock_session_manager):
        """
        Test that GET state with invalid session ID returns 404.
        
        Requirements: 16.1
        """
        # Mock session manager to return None
        mock_session_manager.load_session.return_value = None
        
        # Create event for GET state
        event = {
            'httpMethod': 'GET',
            'path': '/api/game/state/nonexistent-session-id'
        }
        
        # Patch the global session_manager
        with patch('index.session_manager', mock_session_manager):
            with patch('index.world_data', Mock()):
                response = handler(event, mock_context)
        
        # Verify 404 response
        assert response['statusCode'] == 404
        
        # Parse response body
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error']['code'] == 'SESSION_NOT_FOUND'
        assert 'not found' in body['error']['message'].lower()
    
    def test_command_with_missing_session_id(self, mock_context):
        """
        Test that missing session ID returns 400 error.
        
        Requirements: 16.1
        """
        # Create event without session_id
        event = {
            'httpMethod': 'POST',
            'path': '/api/game/command',
            'body': json.dumps({
                'command': 'go north'
            })
        }
        
        with patch('index.world_data', Mock()):
            with patch('index.game_engine', Mock()):
                with patch('index.command_parser', Mock()):
                    with patch('index.session_manager', Mock()):
                        response = handler(event, mock_context)
        
        # Verify 400 response
        assert response['statusCode'] == 400
        
        # Parse response body
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error']['code'] == 'MISSING_SESSION_ID'
        assert 'required' in body['error']['message'].lower()
    
    def test_get_state_with_empty_session_id(self, mock_context):
        """
        Test that empty session ID returns 400 error.
        
        Requirements: 16.1
        """
        # Create event with empty session_id in path
        event = {
            'httpMethod': 'GET',
            'path': '/api/game/state/'
        }
        
        with patch('index.world_data', Mock()):
            response = handler(event, mock_context)
        
        # Verify 400 response (missing session_id)
        assert response['statusCode'] == 400
        
        # Parse response body
        body = json.loads(response['body'])
        assert body['success'] is False


class TestMalformedJSON:
    """
    Test error handling for malformed JSON requests.
    
    Requirements: 16.2
    """
    
    def test_command_with_invalid_json(self, mock_context):
        """
        Test that malformed JSON returns 400 error.
        
        Requirements: 16.2
        """
        # Create event with invalid JSON
        event = {
            'httpMethod': 'POST',
            'path': '/api/game/command',
            'body': '{invalid json here'
        }
        
        with patch('index.world_data', Mock()):
            with patch('index.game_engine', Mock()):
                with patch('index.command_parser', Mock()):
                    with patch('index.session_manager', Mock()):
                        response = handler(event, mock_context)
        
        # Verify 400 response
        assert response['statusCode'] == 400
        
        # Parse response body
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error']['code'] == 'INVALID_JSON'
        assert 'valid json' in body['error']['message'].lower()
    
    def test_command_with_non_object_json(self, mock_context):
        """
        Test that JSON array instead of object returns 400 error.
        
        Requirements: 16.2
        """
        # Create event with JSON array instead of object
        event = {
            'httpMethod': 'POST',
            'path': '/api/game/command',
            'body': '["not", "an", "object"]'
        }
        
        with patch('index.world_data', Mock()):
            with patch('index.game_engine', Mock()):
                with patch('index.command_parser', Mock()):
                    with patch('index.session_manager', Mock()):
                        response = handler(event, mock_context)
        
        # Verify 400 response
        assert response['statusCode'] == 400
        
        # Parse response body
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error']['code'] == 'INVALID_REQUEST'
        assert 'json object' in body['error']['message'].lower()
    
    def test_command_with_missing_command_field(self, mock_context):
        """
        Test that missing command field returns 400 error.
        
        Requirements: 16.2
        """
        # Create event without command field
        event = {
            'httpMethod': 'POST',
            'path': '/api/game/command',
            'body': json.dumps({
                'session_id': 'test-session-123'
            })
        }
        
        with patch('index.world_data', Mock()):
            with patch('index.game_engine', Mock()):
                with patch('index.command_parser', Mock()):
                    with patch('index.session_manager', Mock()):
                        response = handler(event, mock_context)
        
        # Verify 400 response
        assert response['statusCode'] == 400
        
        # Parse response body
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error']['code'] == 'MISSING_COMMAND'
        assert 'required' in body['error']['message'].lower()
    
    def test_command_with_non_string_command(self, mock_context):
        """
        Test that non-string command returns 400 error.
        
        Requirements: 16.2
        """
        # Create event with numeric command
        event = {
            'httpMethod': 'POST',
            'path': '/api/game/command',
            'body': json.dumps({
                'session_id': 'test-session-123',
                'command': 12345
            })
        }
        
        with patch('index.world_data', Mock()):
            with patch('index.game_engine', Mock()):
                with patch('index.command_parser', Mock()):
                    with patch('index.session_manager', Mock()):
                        response = handler(event, mock_context)
        
        # Verify 400 response
        assert response['statusCode'] == 400
        
        # Parse response body
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error']['code'] == 'INVALID_COMMAND'
        assert 'string' in body['error']['message'].lower()
    
    def test_command_with_empty_command(self, mock_context):
        """
        Test that empty command string returns 400 error.
        
        Requirements: 16.2
        """
        # Create event with empty command
        event = {
            'httpMethod': 'POST',
            'path': '/api/game/command',
            'body': json.dumps({
                'session_id': 'test-session-123',
                'command': '   '
            })
        }
        
        with patch('index.world_data', Mock()):
            with patch('index.game_engine', Mock()):
                with patch('index.command_parser', Mock()):
                    with patch('index.session_manager', Mock()):
                        response = handler(event, mock_context)
        
        # Verify 400 response
        assert response['statusCode'] == 400
        
        # Parse response body
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error']['code'] == 'INVALID_COMMAND'
        assert 'empty' in body['error']['message'].lower()


class TestInternalErrors:
    """
    Test error handling for internal server errors.
    
    Requirements: 16.3
    """
    
    def test_database_error_on_save(self, mock_context, mock_session_manager, world_data):
        """
        Test that database save error returns 500 error.
        
        Requirements: 16.3
        """
        # Create a valid game state
        state = GameState.create_new_game()
        
        # Mock session manager to fail on save
        mock_session_manager.load_session.return_value = state
        mock_session_manager.save_session.side_effect = Exception("DynamoDB connection error")
        
        # Create valid command event
        event = {
            'httpMethod': 'POST',
            'path': '/api/game/command',
            'body': json.dumps({
                'session_id': state.session_id,
                'command': 'go north'
            })
        }
        
        # Patch components
        with patch('index.session_manager', mock_session_manager):
            with patch('index.world_data', world_data):
                with patch('index.game_engine') as mock_engine:
                    with patch('index.command_parser') as mock_parser:
                        # Mock successful command execution
                        from game_engine import ActionResult
                        mock_result = ActionResult(
                            success=True,
                            message="You move north.",
                            room_changed=True,
                            new_room="north_of_house"
                        )
                        mock_engine.execute_command.return_value = mock_result
                        
                        from command_parser import ParsedCommand
                        mock_parser.parse.return_value = ParsedCommand(verb="GO", direction="NORTH")
                        
                        response = handler(event, mock_context)
        
        # Verify 500 response
        assert response['statusCode'] == 500
        
        # Parse response body
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error']['code'] == 'DATABASE_ERROR'
        assert 'save' in body['error']['message'].lower()
    
    def test_database_error_on_load(self, mock_context, mock_session_manager):
        """
        Test that database load error returns 500 error.
        
        Requirements: 16.3
        """
        # Mock session manager to fail on load
        mock_session_manager.load_session.side_effect = Exception("DynamoDB connection timeout")
        
        # Create command event
        event = {
            'httpMethod': 'POST',
            'path': '/api/game/command',
            'body': json.dumps({
                'session_id': 'test-session-123',
                'command': 'go north'
            })
        }
        
        with patch('index.session_manager', mock_session_manager):
            with patch('index.world_data', Mock()):
                with patch('index.game_engine', Mock()):
                    with patch('index.command_parser', Mock()):
                        response = handler(event, mock_context)
        
        # Verify 500 response
        assert response['statusCode'] == 500
        
        # Parse response body
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error']['code'] == 'DATABASE_ERROR'
        assert 'load' in body['error']['message'].lower()
    
    def test_command_execution_error(self, mock_context, mock_session_manager, world_data):
        """
        Test that command execution error returns 500 error.
        
        Requirements: 16.3
        """
        # Create a valid game state
        state = GameState.create_new_game()
        
        # Mock session manager to return valid state
        mock_session_manager.load_session.return_value = state
        
        # Create command event
        event = {
            'httpMethod': 'POST',
            'path': '/api/game/command',
            'body': json.dumps({
                'session_id': state.session_id,
                'command': 'go north'
            })
        }
        
        # Patch components
        with patch('index.session_manager', mock_session_manager):
            with patch('index.world_data', world_data):
                with patch('index.game_engine') as mock_engine:
                    with patch('index.command_parser') as mock_parser:
                        # Mock command execution to raise exception
                        mock_engine.execute_command.side_effect = Exception("Unexpected game engine error")
                        
                        from command_parser import ParsedCommand
                        mock_parser.parse.return_value = ParsedCommand(verb="GO", direction="NORTH")
                        
                        response = handler(event, mock_context)
        
        # Verify 500 response
        assert response['statusCode'] == 500
        
        # Parse response body
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error']['code'] == 'COMMAND_EXECUTION_ERROR'
    
    def test_new_game_initialization_error(self, mock_context):
        """
        Test that new game initialization error returns 500 error.
        
        Requirements: 16.3
        """
        # Create new game event
        event = {
            'httpMethod': 'POST',
            'path': '/api/game/new',
            'body': '{}'
        }
        
        # Patch GameState.create_new_game to raise exception
        with patch('index.world_data', Mock()):
            with patch('index.session_manager', Mock()):
                with patch('state_manager.GameState.create_new_game') as mock_create:
                    mock_create.side_effect = Exception("Failed to generate session ID")
                    
                    response = handler(event, mock_context)
        
        # Verify 500 response
        assert response['statusCode'] == 500
        
        # Parse response body
        body = json.loads(response['body'])
        assert body['success'] is False
        # Could be GAME_INITIALIZATION_ERROR or INTERNAL_ERROR
        assert 'error' in body['error']['code'].lower()
    
    def test_unexpected_handler_error(self, mock_context):
        """
        Test that unexpected errors in handler return 500 error.
        
        Requirements: 16.3
        """
        # Create event that will cause unexpected error
        event = {
            'httpMethod': 'POST',
            'path': '/api/game/command',
            'body': json.dumps({
                'session_id': 'test-session',
                'command': 'test'
            })
        }
        
        # Patch to raise unexpected exception
        with patch('index.initialize_game_components') as mock_init:
            mock_init.side_effect = RuntimeError("Unexpected runtime error")
            
            response = handler(event, mock_context)
        
        # Verify 500 response
        assert response['statusCode'] == 500
        
        # Parse response body
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error']['code'] == 'INTERNAL_ERROR'
        # Should not expose internal error details
        assert 'unexpected' in body['error']['message'].lower()
        assert 'RuntimeError' not in body['error']['message']


class TestStatePreservation:
    """
    Test that game state is preserved on errors.
    
    Requirements: 16.5
    """
    
    def test_state_preserved_on_command_execution_error(self, mock_context, mock_session_manager, world_data):
        """
        Test that state is not modified when command execution fails.
        
        Requirements: 16.5
        """
        # Create initial game state
        initial_state = GameState.create_new_game()
        initial_state.current_room = "west_of_house"
        initial_state.sanity = 100
        initial_state.score = 0
        initial_state.moves = 5
        
        # Create a copy to verify state preservation
        state_copy = copy.deepcopy(initial_state)
        
        # Mock session manager to return state
        mock_session_manager.load_session.return_value = initial_state
        
        # Create command event
        event = {
            'httpMethod': 'POST',
            'path': '/api/game/command',
            'body': json.dumps({
                'session_id': initial_state.session_id,
                'command': 'go north'
            })
        }
        
        # Patch components to simulate error during execution
        with patch('index.session_manager', mock_session_manager):
            with patch('index.world_data', world_data):
                with patch('index.game_engine') as mock_engine:
                    with patch('index.command_parser') as mock_parser:
                        # Mock command execution to raise exception
                        mock_engine.execute_command.side_effect = Exception("Command execution failed")
                        
                        from command_parser import ParsedCommand
                        mock_parser.parse.return_value = ParsedCommand(verb="GO", direction="NORTH")
                        
                        response = handler(event, mock_context)
        
        # Verify error response
        assert response['statusCode'] == 500
        
        # Verify state was not saved (save_session should not be called on error)
        # The handler should restore original state
        assert mock_session_manager.save_session.call_count == 0
    
    def test_state_rollback_on_save_error(self, mock_context, mock_session_manager, world_data):
        """
        Test that state changes are rolled back when save fails.
        
        Requirements: 16.5
        """
        # Create initial game state
        initial_state = GameState.create_new_game()
        initial_state.current_room = "west_of_house"
        initial_state.moves = 5
        
        # Mock session manager
        mock_session_manager.load_session.return_value = initial_state
        mock_session_manager.save_session.side_effect = Exception("DynamoDB save failed")
        
        # Create command event
        event = {
            'httpMethod': 'POST',
            'path': '/api/game/command',
            'body': json.dumps({
                'session_id': initial_state.session_id,
                'command': 'go north'
            })
        }
        
        # Patch components
        with patch('index.session_manager', mock_session_manager):
            with patch('index.world_data', world_data):
                with patch('index.game_engine') as mock_engine:
                    with patch('index.command_parser') as mock_parser:
                        # Mock successful command execution
                        from game_engine import ActionResult
                        mock_result = ActionResult(
                            success=True,
                            message="You move north.",
                            room_changed=True,
                            new_room="north_of_house"
                        )
                        mock_engine.execute_command.return_value = mock_result
                        
                        from command_parser import ParsedCommand
                        mock_parser.parse.return_value = ParsedCommand(verb="GO", direction="NORTH")
                        
                        response = handler(event, mock_context)
        
        # Verify error response
        assert response['statusCode'] == 500
        
        # Parse response body
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'save' in body['error']['message'].lower()
    
    def test_invalid_command_does_not_modify_state(self, mock_context, mock_session_manager, world_data):
        """
        Test that invalid commands do not modify game state.
        
        Requirements: 16.5, 2.5
        """
        # Create initial game state
        initial_state = GameState.create_new_game()
        initial_state.current_room = "west_of_house"
        initial_state.sanity = 100
        initial_state.score = 0
        initial_state.moves = 5
        initial_inventory = initial_state.inventory.copy()
        
        # Mock session manager to return state
        mock_session_manager.load_session.return_value = initial_state
        
        # Create command event with invalid command
        event = {
            'httpMethod': 'POST',
            'path': '/api/game/command',
            'body': json.dumps({
                'session_id': initial_state.session_id,
                'command': 'xyzzy invalid command'
            })
        }
        
        # Patch components
        with patch('index.session_manager', mock_session_manager):
            with patch('index.world_data', world_data):
                with patch('index.game_engine') as mock_engine:
                    with patch('index.command_parser') as mock_parser:
                        # Mock command execution to return failure
                        from game_engine import ActionResult
                        mock_result = ActionResult(
                            success=False,
                            message="I don't understand that command."
                        )
                        mock_engine.execute_command.return_value = mock_result
                        
                        from command_parser import ParsedCommand
                        mock_parser.parse.return_value = ParsedCommand(verb="UNKNOWN")
                        
                        response = handler(event, mock_context)
        
        # Verify response indicates failure but is not an error
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is False
        
        # Verify state was saved (even though command failed, we still save)
        assert mock_session_manager.save_session.called
        
        # Verify critical state fields were not modified
        saved_state = mock_session_manager.save_session.call_args[0][0]
        assert saved_state.current_room == "west_of_house"
        assert saved_state.sanity == 100
        assert saved_state.score == 0
        assert saved_state.inventory == initial_inventory


class TestErrorResponseFormat:
    """
    Test that error responses follow consistent format.
    
    Requirements: 16.1, 16.2, 16.3
    """
    
    def test_error_response_structure(self):
        """
        Test that error responses have consistent structure.
        
        Requirements: 16.1, 16.2, 16.3
        """
        # Create error response
        response = create_error_response(
            404,
            'TEST_ERROR',
            'This is a test error',
            'Additional details here'
        )
        
        # Verify structure
        assert response['statusCode'] == 404
        assert 'headers' in response
        assert 'body' in response
        
        # Parse body
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'error' in body
        assert body['error']['code'] == 'TEST_ERROR'
        assert body['error']['message'] == 'This is a test error'
        assert body['error']['details'] == 'Additional details here'
    
    def test_error_response_without_details(self):
        """
        Test error response without optional details field.
        
        Requirements: 16.1, 16.2, 16.3
        """
        # Create error response without details
        response = create_error_response(
            500,
            'INTERNAL_ERROR',
            'An error occurred'
        )
        
        # Parse body
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'error' in body
        assert body['error']['code'] == 'INTERNAL_ERROR'
        assert body['error']['message'] == 'An error occurred'
        assert 'details' not in body['error']
    
    def test_cors_headers_in_error_response(self):
        """
        Test that error responses include CORS headers.
        
        Requirements: 16.1, 16.2, 16.3
        """
        # Create error response
        response = create_error_response(
            400,
            'TEST_ERROR',
            'Test error message'
        )
        
        # Verify CORS headers
        assert 'headers' in response
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        assert 'Access-Control-Allow-Headers' in response['headers']
        assert 'Access-Control-Allow-Methods' in response['headers']
        assert 'Content-Type' in response['headers']
        assert response['headers']['Content-Type'] == 'application/json'
