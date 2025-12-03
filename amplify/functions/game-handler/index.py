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
        
    Requirements: 11.1, 11.2, 11.3, 2.1, 2.3, 2.4, 16.1, 16.2, 16.3, 16.5
    """
    request_id = context.request_id if context else 'unknown'
    
    try:
        # Initialize game components
        initialize_game_components()
        
        # Log incoming request with context
        print(f"[{request_id}] Received event: {json.dumps(event)}")
        
        # Validate event structure
        if not isinstance(event, dict):
            print(f"[{request_id}] ERROR: Invalid event structure - not a dictionary")
            return create_error_response(
                400,
                'INVALID_REQUEST',
                'Invalid request format'
            )
        
        # Extract HTTP method and path
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        # Validate required fields
        if not http_method or not path:
            print(f"[{request_id}] ERROR: Missing httpMethod or path in event")
            return create_error_response(
                400,
                'INVALID_REQUEST',
                'Missing required request fields'
            )
        
        # Handle OPTIONS requests for CORS
        if http_method == 'OPTIONS':
            return create_response(200, {'message': 'OK'})
        
        # Route to appropriate handler based on path and method
        if path == '/api/game/new' and http_method == 'POST':
            return handle_new_game(event, request_id)
        
        elif path == '/api/game/command' and http_method == 'POST':
            return handle_command(event, request_id)
        
        elif path.startswith('/api/game/state/') and http_method == 'GET':
            # Extract session_id from path
            session_id = path.split('/')[-1]
            if not session_id:
                print(f"[{request_id}] ERROR: Missing session_id in path")
                return create_error_response(
                    400,
                    'MISSING_SESSION_ID',
                    'Session ID is required in path'
                )
            return handle_get_state(session_id, request_id)
        
        else:
            # Unknown endpoint
            print(f"[{request_id}] ERROR: Unknown endpoint - {http_method} {path}")
            return create_error_response(
                404,
                'ENDPOINT_NOT_FOUND',
                f'Endpoint not found: {http_method} {path}'
            )
    
    except json.JSONDecodeError as e:
        # JSON parsing error
        print(f"[{request_id}] ERROR: JSON decode error - {str(e)}")
        print(traceback.format_exc())
        return create_error_response(
            400,
            'INVALID_JSON',
            'Request body must be valid JSON',
            str(e)
        )
    
    except Exception as e:
        # Log the full error for debugging with context
        print(f"[{request_id}] CRITICAL ERROR: Unexpected error in handler - {str(e)}")
        print(f"[{request_id}] Stack trace:")
        print(traceback.format_exc())
        
        # Return generic error to client (don't expose internals)
        return create_error_response(
            500,
            'INTERNAL_ERROR',
            'An unexpected error occurred. Please try again.'
        )


def handle_new_game(event: Dict[str, Any], request_id: str = 'unknown') -> Dict[str, Any]:
    """
    Handle POST /api/game/new - Create a new game session.
    
    Generates unique session ID, initializes game state with starting values,
    saves to DynamoDB, and returns initial room description and state.
    
    Args:
        event: API Gateway event
        request_id: Request identifier for logging
        
    Returns:
        API Gateway response with new game data
        
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 16.1, 16.2, 16.3, 16.5
    """
    state = None
    
    try:
        print(f"[{request_id}] Creating new game session")
        
        # Create new game state with default starting values
        state = GameState.create_new_game(starting_room="west_of_house")
        
        print(f"[{request_id}] Created new game session: {state.session_id}")
        
        # Validate state was created correctly
        if not state.session_id:
            raise ValueError("Failed to generate session ID")
        
        if not state.current_room:
            raise ValueError("Failed to set starting room")
        
        # Get initial room to validate it exists
        try:
            room = world_data.get_room(state.current_room)
        except ValueError as e:
            print(f"[{request_id}] ERROR: Starting room not found - {state.current_room}")
            raise ValueError(f"Starting room '{state.current_room}' not found in world data")
        
        # Save to DynamoDB
        try:
            session_manager.save_session(state)
            print(f"[{request_id}] Saved session {state.session_id} to DynamoDB")
        except Exception as e:
            print(f"[{request_id}] ERROR: Failed to save session to DynamoDB - {str(e)}")
            raise Exception(f"Database error: Failed to save session")
        
        # Get initial room description
        try:
            description = world_data.get_room_description(state.current_room, state.sanity)
        except Exception as e:
            print(f"[{request_id}] ERROR: Failed to get room description - {str(e)}")
            # Use fallback description
            description = "You are standing in an open field west of a white house."
        
        # Get visible items in room
        items_visible = []
        for item_id in room.items:
            try:
                obj = world_data.get_object(item_id)
                # Only show visible items (not hidden by puzzles)
                if obj.state.get('is_visible', True):
                    display_name = obj.name_spooky if obj.name_spooky else obj.name
                    items_visible.append(display_name)
            except ValueError as e:
                print(f"[{request_id}] WARNING: Object {item_id} not found in world data")
                continue
            except Exception as e:
                print(f"[{request_id}] WARNING: Error processing object {item_id} - {str(e)}")
                continue
        
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
        
        print(f"[{request_id}] Successfully created new game session {state.session_id}")
        return create_response(200, response_body)
    
    except ValueError as e:
        # Validation error - client or data error
        print(f"[{request_id}] ERROR: Validation error in handle_new_game - {str(e)}")
        print(traceback.format_exc())
        return create_error_response(
            500,
            'GAME_INITIALIZATION_ERROR',
            'Failed to initialize game',
            str(e)
        )
    
    except Exception as e:
        # Unexpected error
        print(f"[{request_id}] CRITICAL ERROR: Unexpected error in handle_new_game - {str(e)}")
        print(traceback.format_exc())
        
        # If we created a state but failed later, try to clean up
        if state and state.session_id:
            try:
                session_manager.delete_session(state.session_id)
                print(f"[{request_id}] Cleaned up failed session {state.session_id}")
            except Exception as cleanup_error:
                print(f"[{request_id}] WARNING: Failed to clean up session - {str(cleanup_error)}")
        
        return create_error_response(
            500,
            'INTERNAL_ERROR',
            'Failed to create new game'
        )


def handle_command(event: Dict[str, Any], request_id: str = 'unknown') -> Dict[str, Any]:
    """
    Handle POST /api/game/command - Execute a game command.
    
    Loads session from DynamoDB, parses command, executes via game engine,
    updates state, saves to DynamoDB, and returns response with updated state.
    
    Args:
        event: API Gateway event
        request_id: Request identifier for logging
        
    Returns:
        API Gateway response with command result
        
    Requirements: 2.1, 2.3, 2.4, 11.1, 16.1, 16.2, 16.3, 16.5
    """
    original_state = None
    state = None
    
    try:
        # Parse request body
        body = event.get('body', '{}')
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError as e:
                print(f"[{request_id}] ERROR: Invalid JSON in request body - {str(e)}")
                return create_error_response(
                    400,
                    'INVALID_JSON',
                    'Request body must be valid JSON',
                    str(e)
                )
        
        # Validate body is a dictionary
        if not isinstance(body, dict):
            print(f"[{request_id}] ERROR: Request body is not a JSON object")
            return create_error_response(
                400,
                'INVALID_REQUEST',
                'Request body must be a JSON object'
            )
        
        # Extract session_id and command
        session_id = body.get('session_id')
        command_text = body.get('command')
        
        # Validate required fields
        if not session_id:
            print(f"[{request_id}] ERROR: Missing session_id in request")
            return create_error_response(
                400,
                'MISSING_SESSION_ID',
                'session_id is required'
            )
        
        if not command_text:
            print(f"[{request_id}] ERROR: Missing command in request")
            return create_error_response(
                400,
                'MISSING_COMMAND',
                'command is required'
            )
        
        # Validate command is a string
        if not isinstance(command_text, str):
            print(f"[{request_id}] ERROR: Command is not a string")
            return create_error_response(
                400,
                'INVALID_COMMAND',
                'command must be a string'
            )
        
        # Validate command is not empty after stripping
        if not command_text.strip():
            print(f"[{request_id}] ERROR: Command is empty")
            return create_error_response(
                400,
                'INVALID_COMMAND',
                'command cannot be empty'
            )
        
        print(f"[{request_id}] Processing command for session {session_id}: {command_text}")
        
        # Load session from DynamoDB
        try:
            state = session_manager.load_session(session_id)
        except Exception as e:
            print(f"[{request_id}] ERROR: Failed to load session from DynamoDB - {str(e)}")
            return create_error_response(
                500,
                'DATABASE_ERROR',
                'Failed to load game session'
            )
        
        if state is None:
            print(f"[{request_id}] ERROR: Session not found - {session_id}")
            return create_error_response(
                404,
                'SESSION_NOT_FOUND',
                f'Session not found or expired: {session_id}'
            )
        
        # Create a backup of the original state for rollback
        import copy
        original_state = copy.deepcopy(state)
        
        # Parse command
        try:
            parsed_command = command_parser.parse(command_text)
            print(f"[{request_id}] Parsed command: {parsed_command}")
        except Exception as e:
            print(f"[{request_id}] ERROR: Failed to parse command - {str(e)}")
            # Command parsing should not fail, but if it does, return error
            return create_error_response(
                400,
                'INVALID_COMMAND',
                'Failed to parse command',
                str(e)
            )
        
        # Execute command via game engine
        try:
            result = game_engine.execute_command(parsed_command, state)
            print(f"[{request_id}] Command result: success={result.success}, message={result.message[:50]}...")
        except Exception as e:
            print(f"[{request_id}] ERROR: Failed to execute command - {str(e)}")
            print(traceback.format_exc())
            
            # Restore original state on error (state consistency requirement 16.5)
            state = original_state
            
            return create_error_response(
                500,
                'COMMAND_EXECUTION_ERROR',
                'Failed to execute command'
            )
        
        # Save updated state to DynamoDB
        try:
            session_manager.save_session(state)
            print(f"[{request_id}] Saved updated session {session_id}")
        except Exception as e:
            print(f"[{request_id}] ERROR: Failed to save session to DynamoDB - {str(e)}")
            
            # State was modified but not saved - this is a critical error
            # We cannot rollback the in-memory state at this point
            return create_error_response(
                500,
                'DATABASE_ERROR',
                'Failed to save game state. Your progress may not be saved.'
            )
        
        # Get current room information
        try:
            room = world_data.get_room(state.current_room)
        except ValueError as e:
            print(f"[{request_id}] ERROR: Current room not found - {state.current_room}")
            # This is a critical error - state is corrupted
            return create_error_response(
                500,
                'GAME_STATE_ERROR',
                'Game state is corrupted. Please start a new game.'
            )
        
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
            except ValueError as e:
                print(f"[{request_id}] WARNING: Object {item_id} not found in world data")
                continue
            except Exception as e:
                print(f"[{request_id}] WARNING: Error processing object {item_id} - {str(e)}")
                continue
        
        # Get inventory display names
        inventory_display = []
        for item_id in state.inventory:
            try:
                obj = world_data.get_object(item_id)
                display_name = obj.name_spooky if obj.name_spooky else obj.name
                inventory_display.append(display_name)
            except ValueError:
                print(f"[{request_id}] WARNING: Inventory object {item_id} not found in world data")
                inventory_display.append(item_id)
            except Exception as e:
                print(f"[{request_id}] WARNING: Error processing inventory object {item_id} - {str(e)}")
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
        
        print(f"[{request_id}] Successfully executed command for session {session_id}")
        return create_response(200, response_body)
    
    except json.JSONDecodeError as e:
        print(f"[{request_id}] ERROR: JSON decode error - {str(e)}")
        return create_error_response(
            400,
            'INVALID_JSON',
            'Request body must be valid JSON',
            str(e)
        )
    
    except Exception as e:
        print(f"[{request_id}] CRITICAL ERROR: Unexpected error in handle_command - {str(e)}")
        print(traceback.format_exc())
        
        # If we have original state and current state differs, try to restore
        if original_state and state and original_state != state:
            try:
                session_manager.save_session(original_state)
                print(f"[{request_id}] Restored original state after error")
            except Exception as restore_error:
                print(f"[{request_id}] WARNING: Failed to restore original state - {str(restore_error)}")
        
        return create_error_response(
            500,
            'INTERNAL_ERROR',
            'Failed to execute command'
        )


def handle_get_state(session_id: str, request_id: str = 'unknown') -> Dict[str, Any]:
    """
    Handle GET /api/game/state/{session_id} - Get current game state.
    
    Loads session from DynamoDB and returns complete game state.
    
    Args:
        session_id: The session identifier
        request_id: Request identifier for logging
        
    Returns:
        API Gateway response with game state
        
    Requirements: 19.1, 19.2, 19.3, 16.1, 16.2, 16.3
    """
    try:
        print(f"[{request_id}] Retrieving state for session {session_id}")
        
        # Validate session_id format
        if not session_id or not isinstance(session_id, str):
            print(f"[{request_id}] ERROR: Invalid session_id format")
            return create_error_response(
                400,
                'INVALID_SESSION_ID',
                'Session ID must be a non-empty string'
            )
        
        # Load session from DynamoDB
        try:
            state = session_manager.load_session(session_id)
        except Exception as e:
            print(f"[{request_id}] ERROR: Failed to load session from DynamoDB - {str(e)}")
            return create_error_response(
                500,
                'DATABASE_ERROR',
                'Failed to load game session'
            )
        
        if state is None:
            print(f"[{request_id}] ERROR: Session not found - {session_id}")
            return create_error_response(
                404,
                'SESSION_NOT_FOUND',
                f'Session not found or expired: {session_id}'
            )
        
        # Update last accessed timestamp and TTL
        state.update_ttl(hours=1)
        
        # Save updated session to extend TTL
        try:
            session_manager.save_session(state)
            print(f"[{request_id}] Updated TTL for session {session_id}")
        except Exception as e:
            print(f"[{request_id}] WARNING: Failed to update session TTL - {str(e)}")
            # Continue anyway - this is not critical for read operations
        
        # Get current room information
        try:
            room = world_data.get_room(state.current_room)
        except ValueError as e:
            print(f"[{request_id}] ERROR: Current room not found - {state.current_room}")
            return create_error_response(
                500,
                'GAME_STATE_ERROR',
                'Game state is corrupted. Please start a new game.'
            )
        
        try:
            description = world_data.get_room_description(state.current_room, state.sanity)
        except Exception as e:
            print(f"[{request_id}] WARNING: Failed to get room description - {str(e)}")
            description = "You are in a mysterious location."
        
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
                print(f"[{request_id}] WARNING: Object {item_id} not found in world data")
                continue
            except Exception as e:
                print(f"[{request_id}] WARNING: Error processing object {item_id} - {str(e)}")
                continue
        
        # Get inventory display names
        inventory_display = []
        for item_id in state.inventory:
            try:
                obj = world_data.get_object(item_id)
                display_name = obj.name_spooky if obj.name_spooky else obj.name
                inventory_display.append(display_name)
            except ValueError:
                print(f"[{request_id}] WARNING: Inventory object {item_id} not found in world data")
                inventory_display.append(item_id)
            except Exception as e:
                print(f"[{request_id}] WARNING: Error processing inventory object {item_id} - {str(e)}")
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
        
        print(f"[{request_id}] Successfully retrieved state for session {session_id}")
        return create_response(200, response_body)
    
    except Exception as e:
        print(f"[{request_id}] CRITICAL ERROR: Unexpected error in handle_get_state - {str(e)}")
        print(traceback.format_exc())
        return create_error_response(
            500,
            'INTERNAL_ERROR',
            'Failed to retrieve game state'
        )
