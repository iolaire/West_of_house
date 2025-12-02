"""
Lambda Handler for West of Haunted House

AWS Lambda entry point that handles API Gateway events, routes requests
to appropriate game engine functions, and formats JSON responses.

Requirements: 11.1, 11.2, 11.3, 2.1, 2.3, 2.4
"""

import json
import os
import sys
import traceback
import boto3
from typing import Dict, Any, Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from game_engine import GameEngine, ActionResult
from state_manager import GameState, SessionManager
from command_parser import CommandParser
from world_loader import WorldData


# Initialize global objects for Lambda warm starts
world_data = None
game_engine = None
command_parser = None
session_manager = None


def initialize_game_components():
    """
    Initialize game components (world data, engine, parser, session manager).
    Uses global variables for Lambda warm start optimization.
    """
    global world_data, game_engine, command_parser, session_manager
    
    if world_data is None:
        # Load world data from bundled JSON files
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        world_data = WorldData()
        world_data.load_from_json(data_dir)
        print(f"Loaded world data from {data_dir}")
    
    if game_engine is None:
        game_engine = GameEngine(world_data)
        print("Initialized game engine")
    
    if command_parser is None:
        command_parser = CommandParser()
        print("Initialized command parser")
    
    if session_manager is None:
        # Initialize DynamoDB client
        dynamodb_client = boto3.client('dynamodb')
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'GameSessions')
        session_manager = SessionManager(dynamodb_client, table_name)
        print(f"Initialized session manager with table: {table_name}")


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a properly formatted API Gateway response.
    
    Args:
        status_code: HTTP status code
        body: Response body dictionary
        
    Returns:
        API Gateway response dictionary
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }


def create_error_response(status_code: int, error_code: str, message: str, details: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a properly formatted error response.
    
    Args:
        status_code: HTTP status code
        error_code: Error code identifier
        message: User-friendly error message
        details: Optional additional details
        
    Returns:
        API Gateway error response dictionary
        
    Requirements: 16.1, 16.2, 16.3
    """
    error_body = {
        'success': False,
        'error': {
            'code': error_code,
            'message': message
        }
    }
    
    if details:
        error_body['error']['details'] = details
    
    return create_response(status_code, error_body)


def handler(event, context):
    """
    Main Lambda handler function.
    
    Processes API Gateway events, routes to appropriate handlers,
    and returns formatted JSON responses.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
        
    Requirements: 11.1, 11.2, 11.3, 2.1, 2.3, 2.4
    """
    try:
        # Initialize game components
        initialize_game_components()
        
        # Log incoming request
        print(f"Received event: {json.dumps(event)}")
        
        # Extract HTTP method and path
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        # Handle OPTIONS requests for CORS
        if http_method == 'OPTIONS':
            return create_response(200, {'message': 'OK'})
        
        # Route to appropriate handler based on path and method
        if path == '/api/game/new' and http_method == 'POST':
            return handle_new_game(event)
        
        elif path == '/api/game/command' and http_method == 'POST':
            return handle_command(event)
        
        elif path.startswith('/api/game/state/') and http_method == 'GET':
            # Extract session_id from path
            session_id = path.split('/')[-1]
            return handle_get_state(session_id)
        
        else:
            # Unknown endpoint
            return create_error_response(
                404,
                'ENDPOINT_NOT_FOUND',
                f'Endpoint not found: {http_method} {path}'
            )
    
    except Exception as e:
        # Log the full error for debugging
        print(f"Unexpected error: {str(e)}")
        print(traceback.format_exc())
        
        # Return generic error to client (don't expose internals)
        return create_error_response(
            500,
            'INTERNAL_ERROR',
            'An unexpected error occurred. Please try again.'
        )


def handle_new_game(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST /api/game/new - Create a new game session.
    
    Generates unique session ID, initializes game state with starting values,
    saves to DynamoDB, and returns initial room description and state.
    
    Args:
        event: API Gateway event
        
    Returns:
        API Gateway response with new game data
        
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
    """
    try:
        # Create new game state with default starting values
        state = GameState.create_new_game(starting_room="west_of_house")
        
        print(f"Created new game session: {state.session_id}")
        
        # Save to DynamoDB
        session_manager.save_session(state)
        print(f"Saved session {state.session_id} to DynamoDB")
        
        # Get initial room description
        room = world_data.get_room(state.current_room)
        description = world_data.get_room_description(state.current_room, state.sanity)
        
        # Get visible items in room
        items_visible = []
        for item_id in room.items:
            try:
                obj = world_data.get_object(item_id)
                # Only show visible items (not hidden by puzzles)
                if obj.state.get('is_visible', True):
                    display_name = obj.name_spooky if obj.name_spooky else obj.name
                    items_visible.append(display_name)
            except ValueError:
                pass
        
        # Build response
        response_body = {
            'success': True,
            'session_id': state.session_id,
            'room': state.current_room,
            'description': description,
            'exits': list(room.exits.keys()),
            'items_visible': items_visible,
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
        
        return create_response(200, response_body)
    
    except Exception as e:
        print(f"Error in handle_new_game: {str(e)}")
        print(traceback.format_exc())
        return create_error_response(
            500,
            'INTERNAL_ERROR',
            'Failed to create new game'
        )


def handle_command(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST /api/game/command - Execute a game command.
    
    Loads session from DynamoDB, parses command, executes via game engine,
    updates state, saves to DynamoDB, and returns response with updated state.
    
    Args:
        event: API Gateway event
        
    Returns:
        API Gateway response with command result
        
    Requirements: 2.1, 2.3, 2.4, 11.1
    """
    try:
        # Parse request body
        body = event.get('body', '{}')
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                return create_error_response(
                    400,
                    'INVALID_JSON',
                    'Request body must be valid JSON'
                )
        
        # Extract session_id and command
        session_id = body.get('session_id')
        command_text = body.get('command')
        
        if not session_id:
            return create_error_response(
                400,
                'MISSING_SESSION_ID',
                'session_id is required'
            )
        
        if not command_text:
            return create_error_response(
                400,
                'MISSING_COMMAND',
                'command is required'
            )
        
        print(f"Processing command for session {session_id}: {command_text}")
        
        # Load session from DynamoDB
        state = session_manager.load_session(session_id)
        
        if state is None:
            return create_error_response(
                404,
                'SESSION_NOT_FOUND',
                f'Session not found or expired: {session_id}'
            )
        
        # Parse command
        parsed_command = command_parser.parse(command_text)
        print(f"Parsed command: {parsed_command}")
        
        # Execute command via game engine
        result = game_engine.execute_command(parsed_command, state)
        print(f"Command result: success={result.success}, message={result.message[:50]}...")
        
        # Save updated state to DynamoDB
        session_manager.save_session(state)
        print(f"Saved updated session {session_id}")
        
        # Get current room information
        room = world_data.get_room(state.current_room)
        description = result.message if result.success else result.message
        
        # Get visible items in room
        items_visible = []
        for item_id in room.items:
            try:
                obj = world_data.get_object(item_id)
                # Only show visible items (not hidden by puzzles)
                if obj.state.get('is_visible', True):
                    display_name = obj.name_spooky if obj.name_spooky else obj.name
                    items_visible.append(display_name)
            except ValueError:
                pass
        
        # Get inventory display names
        inventory_display = []
        for item_id in state.inventory:
            try:
                obj = world_data.get_object(item_id)
                display_name = obj.name_spooky if obj.name_spooky else obj.name
                inventory_display.append(display_name)
            except ValueError:
                inventory_display.append(item_id)
        
        # Build response
        response_body = {
            'success': result.success,
            'message': result.message,
            'room': state.current_room,
            'description': world_data.get_room_description(state.current_room, state.sanity) if result.room_changed else description,
            'exits': list(room.exits.keys()),
            'items_visible': items_visible,
            'inventory': inventory_display,
            'state': {
                'sanity': state.sanity,
                'cursed': state.cursed,
                'blood_moon_active': state.blood_moon_active,
                'souls_collected': state.souls_collected,
                'score': state.score,
                'moves': state.moves,
                'lamp_battery': state.lamp_battery,
                'turn_count': state.turn_count
            },
            'notifications': result.notifications
        }
        
        return create_response(200, response_body)
    
    except json.JSONDecodeError as e:
        return create_error_response(
            400,
            'INVALID_JSON',
            'Request body must be valid JSON',
            str(e)
        )
    except Exception as e:
        print(f"Error in handle_command: {str(e)}")
        print(traceback.format_exc())
        return create_error_response(
            500,
            'INTERNAL_ERROR',
            'Failed to execute command'
        )


def handle_get_state(session_id: str) -> Dict[str, Any]:
    """
    Handle GET /api/game/state/{session_id} - Get current game state.
    
    Loads session from DynamoDB and returns complete game state.
    
    Args:
        session_id: The session identifier
        
    Returns:
        API Gateway response with game state
        
    Requirements: 19.1, 19.2, 19.3
    """
    try:
        print(f"Retrieving state for session {session_id}")
        
        # Load session from DynamoDB
        state = session_manager.load_session(session_id)
        
        if state is None:
            return create_error_response(
                404,
                'SESSION_NOT_FOUND',
                f'Session not found or expired: {session_id}'
            )
        
        # Get current room information
        room = world_data.get_room(state.current_room)
        description = world_data.get_room_description(state.current_room, state.sanity)
        
        # Get visible items in room
        items_visible = []
        for item_id in room.items:
            try:
                obj = world_data.get_object(item_id)
                # Only show visible items (not hidden by puzzles)
                if obj.state.get('is_visible', True):
                    display_name = obj.name_spooky if obj.name_spooky else obj.name
                    items_visible.append(display_name)
            except ValueError:
                pass
        
        # Get inventory display names
        inventory_display = []
        for item_id in state.inventory:
            try:
                obj = world_data.get_object(item_id)
                display_name = obj.name_spooky if obj.name_spooky else obj.name
                inventory_display.append(display_name)
            except ValueError:
                inventory_display.append(item_id)
        
        # Build response with complete game state
        response_body = {
            'success': True,
            'session_id': state.session_id,
            'current_room': state.current_room,
            'description': description,
            'exits': list(room.exits.keys()),
            'items_visible': items_visible,
            'inventory': inventory_display,
            'flags': state.flags,
            'state': {
                'sanity': state.sanity,
                'cursed': state.cursed,
                'blood_moon_active': state.blood_moon_active,
                'souls_collected': state.souls_collected,
                'curse_duration': state.curse_duration,
                'score': state.score,
                'moves': state.moves,
                'lamp_battery': state.lamp_battery,
                'turn_count': state.turn_count,
                'lucky': state.lucky,
                'thief_here': state.thief_here
            },
            'rooms_visited': list(state.rooms_visited),
            'created_at': state.created_at,
            'last_accessed': state.last_accessed
        }
        
        return create_response(200, response_body)
    
    except Exception as e:
        print(f"Error in handle_get_state: {str(e)}")
        print(traceback.format_exc())
        return create_error_response(
            500,
            'INTERNAL_ERROR',
            'Failed to retrieve game state'
        )
