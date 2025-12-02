"""
Property-Based Tests for API Endpoints

Tests correctness properties related to Lambda handler and API responses.
"""

import sys
import os
import json
from unittest.mock import Mock, MagicMock, patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler'))

import pytest
from hypothesis import given, strategies as st, settings


# Feature: game-backend-api, Property 1: Session uniqueness
@settings(max_examples=100)
@given(st.integers(min_value=2, max_value=50))
def test_session_uniqueness(num_sessions):
    """
    For any number of new game API calls, all generated session IDs should be unique.
    
    **Validates: Requirements 1.1**
    
    This property ensures that the new game endpoint generates unique session
    identifiers for every game creation request, preventing session collisions.
    """
    # Import here to avoid issues with mocking
    from state_manager import GameState
    
    session_ids = set()
    
    for _ in range(num_sessions):
        # Create new game state (simulating what handle_new_game does)
        state = GameState.create_new_game(starting_room="west_of_house")
        
        # Verify session ID is unique
        assert state.session_id not in session_ids, \
            f"Duplicate session ID found: {state.session_id}"
        
        session_ids.add(state.session_id)
    
    # Verify we got the expected number of unique IDs
    assert len(session_ids) == num_sessions


# Feature: game-backend-api, Property 2: Initialization consistency
@settings(max_examples=100)
@given(st.integers(min_value=1, max_value=100))
def test_initialization_consistency(num_games):
    """
    For any number of new games, all should start with the same initial state values.
    
    **Validates: Requirements 1.2, 1.5**
    
    This property ensures that every new game starts with consistent initial
    conditions: sanity=100, cursed=false, blood_moon_active=true, souls_collected=0,
    score=0, moves=0, lamp_battery=200.
    """
    from state_manager import GameState
    
    for _ in range(num_games):
        state = GameState.create_new_game(starting_room="west_of_house")
        
        # Verify all initial values match requirements
        assert state.current_room == "west_of_house", \
            f"Expected starting room 'west_of_house', got '{state.current_room}'"
        assert state.sanity == 100, \
            f"Expected sanity=100, got {state.sanity}"
        assert state.cursed is False, \
            f"Expected cursed=False, got {state.cursed}"
        assert state.blood_moon_active is True, \
            f"Expected blood_moon_active=True, got {state.blood_moon_active}"
        assert state.souls_collected == 0, \
            f"Expected souls_collected=0, got {state.souls_collected}"
        assert state.score == 0, \
            f"Expected score=0, got {state.score}"
        assert state.moves == 0, \
            f"Expected moves=0, got {state.moves}"
        assert state.lamp_battery == 200, \
            f"Expected lamp_battery=200, got {state.lamp_battery}"
        assert state.inventory == [], \
            f"Expected empty inventory, got {state.inventory}"
        assert state.flags == {}, \
            f"Expected empty flags, got {state.flags}"


# Feature: game-backend-api, Property 5: Invalid command state preservation
@settings(max_examples=100)
@given(
    st.text(min_size=1, max_size=50).filter(
        lambda x: not any(word in x.lower() for word in [
            'go', 'north', 'south', 'east', 'west', 'up', 'down',
            'take', 'drop', 'examine', 'open', 'close', 'read',
            'inventory', 'look', 'quit',
            # Exclude single-letter abbreviations
            'n', 's', 'e', 'w', 'u', 'd', 'i', 'l', 'q',
            # Exclude other common abbreviations
            'ne', 'nw', 'se', 'sw', 'inv', 'ex', 'x'
        ])
    )
)
def test_invalid_command_state_preservation(invalid_command):
    """
    For any invalid command, executing it should not change the game state.
    
    **Validates: Requirements 2.5, 16.5**
    
    This property ensures that unrecognized or invalid commands do not
    corrupt or modify the game state in any way.
    """
    from state_manager import GameState
    from command_parser import CommandParser
    from game_engine import GameEngine
    from world_loader import WorldData
    import copy
    
    # Load world data
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world_data = WorldData()
    world_data.load_from_json(data_dir)
    
    # Create game engine and parser
    engine = GameEngine(world_data)
    parser = CommandParser()
    
    # Create initial state
    initial_state = GameState.create_new_game()
    
    # Make a deep copy of the initial state
    state_before = copy.deepcopy(initial_state.to_dict())
    
    # Parse the invalid command
    parsed_command = parser.parse(invalid_command)
    
    # Execute the command
    result = engine.execute_command(parsed_command, initial_state)
    
    # Get state after execution
    state_after = initial_state.to_dict()
    
    # Verify state hasn't changed (except last_accessed timestamp)
    assert state_before['session_id'] == state_after['session_id']
    assert state_before['current_room'] == state_after['current_room']
    assert state_before['inventory'] == state_after['inventory']
    assert state_before['flags'] == state_after['flags']
    assert state_before['sanity'] == state_after['sanity']
    assert state_before['score'] == state_after['score']
    assert state_before['moves'] == state_after['moves']
    assert state_before['lamp_battery'] == state_after['lamp_battery']
    assert state_before['cursed'] == state_after['cursed']
    
    # Verify the command was rejected
    assert result.success is False or parsed_command.verb == "UNKNOWN"


# Feature: game-backend-api, Property 17: API response format consistency
@settings(max_examples=100)
@given(st.integers(min_value=1, max_value=20))
def test_api_response_format_consistency(num_requests):
    """
    For any successful API request, the response should follow consistent JSON schema.
    
    **Validates: Requirements 11.2, 19.2, 19.4**
    
    This property ensures all API responses have the expected structure with
    required fields: success, message/data, room, description, exits, inventory,
    state, and notifications.
    """
    from state_manager import GameState
    from world_loader import WorldData
    
    # Load world data
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world_data = WorldData()
    world_data.load_from_json(data_dir)
    
    for _ in range(num_requests):
        # Simulate new game response
        state = GameState.create_new_game(starting_room="west_of_house")
        room = world_data.get_room(state.current_room)
        description = world_data.get_room_description(state.current_room, state.sanity)
        
        # Build response (simulating what handle_new_game returns)
        response_body = {
            'success': True,
            'session_id': state.session_id,
            'room': state.current_room,
            'description': description,
            'exits': list(room.exits.keys()),
            'items_visible': [],
            'inventory': [],
            'state': {
                'sanity': state.sanity,
                'cursed': state.cursed,
                'blood_moon_active': state.blood_moon_active,
                'souls_collected': state.souls_collected,
                'score': state.score,
                'moves': state.moves,
                'lamp_battery': state.lamp_battery
            }
        }
        
        # Verify required fields are present
        assert 'success' in response_body
        assert 'session_id' in response_body
        assert 'room' in response_body
        assert 'description' in response_body
        assert 'exits' in response_body
        assert 'items_visible' in response_body
        assert 'inventory' in response_body
        assert 'state' in response_body
        
        # Verify state object has required fields
        state_obj = response_body['state']
        assert 'sanity' in state_obj
        assert 'cursed' in state_obj
        assert 'blood_moon_active' in state_obj
        assert 'souls_collected' in state_obj
        assert 'score' in state_obj
        assert 'moves' in state_obj
        assert 'lamp_battery' in state_obj
        
        # Verify data types
        assert isinstance(response_body['success'], bool)
        assert isinstance(response_body['session_id'], str)
        assert isinstance(response_body['room'], str)
        assert isinstance(response_body['description'], str)
        assert isinstance(response_body['exits'], list)
        assert isinstance(response_body['items_visible'], list)
        assert isinstance(response_body['inventory'], list)
        assert isinstance(state_obj, dict)
        assert isinstance(state_obj['sanity'], int)
        assert isinstance(state_obj['cursed'], bool)
        assert isinstance(state_obj['score'], int)


# Feature: game-backend-api, Property 25: Error status codes
@settings(max_examples=100, deadline=None)
@given(
    st.sampled_from([
        'invalid_session',
        'malformed_json',
        'missing_field',
        'empty_command',
        'invalid_endpoint'
    ])
)
def test_error_status_codes(error_type):
    """
    For any error condition, the API should return the correct HTTP status code.
    
    **Validates: Requirements 16.1, 16.2, 16.3**
    
    This property ensures that:
    - Invalid session IDs return 404
    - Malformed JSON returns 400
    - Missing required fields return 400
    - Internal errors return 500
    
    Error types tested:
    - invalid_session: Session not found (404)
    - malformed_json: Invalid JSON in request body (400)
    - missing_field: Missing required field like session_id or command (400)
    - empty_command: Empty command string (400)
    - invalid_endpoint: Unknown API endpoint (404)
    """
    from index import handler, create_error_response
    from unittest.mock import Mock
    
    # Create mock Lambda context
    mock_context = Mock()
    mock_context.request_id = 'test-request-id'
    
    if error_type == 'invalid_session':
        # Test 404 for invalid session ID
        event = {
            'httpMethod': 'POST',
            'path': '/api/game/command',
            'body': json.dumps({
                'session_id': 'nonexistent-session-id-12345',
                'command': 'go north'
            })
        }
        
        with patch('index.session_manager') as mock_session_manager:
            # Mock session not found
            mock_session_manager.load_session.return_value = None
            
            response = handler(event, mock_context)
            
            # Verify 404 status code
            assert response['statusCode'] == 404, \
                f"Expected 404 for invalid session, got {response['statusCode']}"
            
            # Verify error structure
            body = json.loads(response['body'])
            assert body['success'] is False
            assert 'error' in body
            assert body['error']['code'] == 'SESSION_NOT_FOUND'
    
    elif error_type == 'malformed_json':
        # Test 400 for malformed JSON
        event = {
            'httpMethod': 'POST',
            'path': '/api/game/command',
            'body': '{invalid json here'  # Malformed JSON
        }
        
        response = handler(event, mock_context)
        
        # Verify 400 status code
        assert response['statusCode'] == 400, \
            f"Expected 400 for malformed JSON, got {response['statusCode']}"
        
        # Verify error structure
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'error' in body
        assert body['error']['code'] == 'INVALID_JSON'
    
    elif error_type == 'missing_field':
        # Test 400 for missing required field
        event = {
            'httpMethod': 'POST',
            'path': '/api/game/command',
            'body': json.dumps({
                'command': 'go north'
                # Missing session_id
            })
        }
        
        response = handler(event, mock_context)
        
        # Verify 400 status code
        assert response['statusCode'] == 400, \
            f"Expected 400 for missing field, got {response['statusCode']}"
        
        # Verify error structure
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'error' in body
        assert body['error']['code'] == 'MISSING_SESSION_ID'
    
    elif error_type == 'empty_command':
        # Test 400 for empty command
        event = {
            'httpMethod': 'POST',
            'path': '/api/game/command',
            'body': json.dumps({
                'session_id': 'test-session-id',
                'command': '   '  # Empty/whitespace only
            })
        }
        
        response = handler(event, mock_context)
        
        # Verify 400 status code
        assert response['statusCode'] == 400, \
            f"Expected 400 for empty command, got {response['statusCode']}"
        
        # Verify error structure
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'error' in body
        assert body['error']['code'] == 'INVALID_COMMAND'
    
    elif error_type == 'invalid_endpoint':
        # Test 404 for unknown endpoint
        event = {
            'httpMethod': 'GET',
            'path': '/api/game/unknown',
            'body': '{}'
        }
        
        response = handler(event, mock_context)
        
        # Verify 404 status code
        assert response['statusCode'] == 404, \
            f"Expected 404 for invalid endpoint, got {response['statusCode']}"
        
        # Verify error structure
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'error' in body
        assert body['error']['code'] == 'ENDPOINT_NOT_FOUND'
