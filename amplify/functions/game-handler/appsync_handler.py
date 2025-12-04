"""
AppSync Lambda Resolver for West of Haunted House

This handler is specifically designed for AppSync GraphQL resolvers.
It processes the processCommand query and returns game state.
"""

import json
import os
import sys
import traceback
import boto3
from typing import Dict, Any

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
    """Initialize game components for Lambda warm starts."""
    global world_data, game_engine, command_parser, session_manager
    
    if world_data is None:
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
        dynamodb_client = boto3.client('dynamodb')
        table_name = os.environ.get('GAME_SESSIONS_TABLE_NAME', 'GameSessions')
        session_manager = SessionManager(dynamodb_client, table_name)
        print(f"Initialized session manager with table: {table_name}")


def handler(event, context):
    """
    AppSync Lambda resolver handler.
    
    Event structure:
    {
        "arguments": {
            "sessionId": "...",
            "command": "..."
        },
        "identity": {...},
        ...
    }
    """
    request_id = getattr(context, 'aws_request_id', 'unknown') if context else 'unknown'
    
    try:
        print(f"[{request_id}] AppSync event: {json.dumps(event)}")
        
        # Initialize components
        initialize_game_components()
        
        # Extract arguments
        arguments = event.get('arguments', {})
        session_id = arguments.get('sessionId')
        command_text = arguments.get('command')
        
        if not session_id or not command_text:
            raise ValueError("Missing sessionId or command")
        
        print(f"[{request_id}] Processing command '{command_text}' for session {session_id}")
        
        # Load or create session
        state = session_manager.load_session(session_id)
        if state is None:
            # Create new session
            state = GameState.create_new_game(starting_room="west_of_house")
            # Set session_id after creation
            state.session_id = session_id
            session_manager.save_session(state)
            print(f"[{request_id}] Created new session {session_id}")
        else:
            # Ensure session_id is set for loaded sessions
            state.session_id = session_id
        
        # Parse and execute command
        parsed_command = command_parser.parse(command_text)
        result = game_engine.execute_command(parsed_command, state)
        
        # Save updated state
        session_manager.save_session(state)
        
        # Get current room info
        room = world_data.get_room(state.current_room)
        description = world_data.get_room_description(state.current_room, state.sanity)
        
        # Get visible objects
        objects_visible = []
        for item_id in room.items:
            try:
                obj = world_data.get_object(item_id)
                if obj.state.get('is_visible', True):
                    objects_visible.append(obj.name_spooky or obj.name)
            except:
                pass
        
        # Get inventory display names
        inventory_display = []
        for item_id in state.inventory:
            try:
                obj = world_data.get_object(item_id)
                inventory_display.append(obj.name_spooky or obj.name)
            except:
                inventory_display.append(item_id)
        
        # Return AppSync response
        return {
            "room": state.current_room,
            "description_spooky": description,
            "exits": list(room.exits.keys()),
            "objects": objects_visible,
            "inventory": inventory_display,
            "sanity": state.sanity,
            "score": state.score,
            "moves": state.moves,
            "lampBattery": state.lamp_battery,
            "message": result.message
        }
        
    except Exception as e:
        print(f"[{request_id}] ERROR: {str(e)}")
        print(traceback.format_exc())
        raise
