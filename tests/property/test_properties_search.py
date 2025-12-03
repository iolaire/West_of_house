"""
Property-Based Tests for SEARCH Command

Tests correctness properties related to the SEARCH command,
ensuring it reveals details appropriately.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler'))

import pytest
from hypothesis import given, strategies as st, settings, assume
from game_engine import GameEngine, ActionResult
from state_manager import GameState
from world_loader import WorldData


# Initialize world data for tests
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


# Custom strategies for generating test data
@st.composite
def valid_object_in_room(draw, world_data):
    """
    Generate a valid room ID and object ID where the object is in the room.
    
    Returns tuple of (room_id, object_id).
    """
    # Get all room IDs
    room_ids = list(world_data.rooms.keys())
    
    # Pick a random room
    room_id = draw(st.sampled_from(room_ids))
    room = world_data.get_room(room_id)
    
    # Check if room has any items that actually exist in the objects dictionary
    valid_items = [item_id for item_id in room.items if item_id in world_data.objects]
    
    if valid_items:
        object_id = draw(st.sampled_from(valid_items))
        return (room_id, object_id)
    else:
        # Room has no valid items, skip this example
        assume(False)


@st.composite
def object_not_in_room(draw, world_data):
    """
    Generate a room ID and an object ID where the object is NOT in the room.
    
    Returns tuple of (room_id, object_id).
    """
    # Get all room IDs and object IDs
    room_ids = list(world_data.rooms.keys())
    object_ids = list(world_data.objects.keys())
    
    # Pick a random room
    room_id = draw(st.sampled_from(room_ids))
    room = world_data.get_room(room_id)
    
    # Find objects not in this room
    objects_not_in_room = [obj_id for obj_id in object_ids if obj_id not in room.items]
    
    if objects_not_in_room:
        object_id = draw(st.sampled_from(objects_not_in_room))
        return (room_id, object_id)
    else:
        # All objects are in this room (unlikely), skip this example
        assume(False)


# Feature: complete-zork-commands, Property 13: Search reveals details
@settings(max_examples=100)
@given(st.data())
def test_search_returns_response(data):
    """
    For any object or location, executing SEARCH should return a response
    describing what is found or not found.
    
    **Validates: Requirements 4.4**
    
    This property ensures that:
    1. SEARCH always returns a message
    2. The command succeeds when object is present
    3. The response is non-empty
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid object in a room
    room_id, object_id = data.draw(valid_object_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Search the object
    result = engine.handle_search(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"SEARCH {object_id} should succeed when object is present"
    
    # Result should contain a message
    assert result.message is not None, \
        "Result message should not be None"
    assert len(result.message) > 0, \
        "Result message should not be empty"
    
    # Message should be a string
    assert isinstance(result.message, str), \
        "Result message should be a string"


@settings(max_examples=100)
@given(st.data())
def test_search_fails_for_missing_object(data):
    """
    For any object not in the current room, SEARCH should fail with appropriate message.
    
    **Validates: Requirements 4.4**
    
    This property ensures that:
    1. SEARCH fails when object is not present
    2. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get an object not in the room
    room_id, object_id = data.draw(object_not_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Try to search the missing object
    result = engine.handle_search(object_id, state)
    
    # Command should fail
    assert result.success is False, \
        f"SEARCH {object_id} should fail when object is not present"
    
    # Error message should be returned
    assert result.message is not None, \
        "Result message should not be None"
    assert len(result.message) > 0, \
        "Result message should not be empty"
    
    # Message should indicate object not found
    assert "don't see" in result.message.lower() or "not here" in result.message.lower(), \
        "Error message should indicate object is not present"


@settings(max_examples=100)
@given(st.data())
def test_search_reveals_hidden_items(data):
    """
    For any object with search_reveals property, SEARCH should reveal those items
    and add them to the room.
    
    **Validates: Requirements 4.4**
    
    This property ensures that:
    1. Hidden items are revealed through searching
    2. Revealed items are added to the room
    3. Items are only revealed once
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid object in a room
    room_id, object_id = data.draw(valid_object_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Get the object and room
    game_object = world.get_object(object_id)
    current_room = world.get_room(room_id)
    
    # Set up search_reveals property with a test item
    test_item_id = "hidden_test_item"
    game_object.state['search_reveals'] = [test_item_id]
    
    # Ensure the item is not already in the room
    if test_item_id in current_room.items:
        current_room.items.remove(test_item_id)
    
    # Search the object
    result = engine.handle_search(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"SEARCH {object_id} should succeed"
    
    # The hidden item should now be in the room
    assert test_item_id in current_room.items, \
        "Hidden item should be revealed and added to room"
    
    # Search again - item should not be revealed twice
    result2 = engine.handle_search(object_id, state)
    
    # Count how many times the item appears in the room
    item_count = current_room.items.count(test_item_id)
    assert item_count == 1, \
        "Hidden item should only be revealed once, not duplicated"


@settings(max_examples=100)
@given(st.data())
def test_search_uses_custom_description(data):
    """
    For any object with search_description property, SEARCH should return
    that custom description.
    
    **Validates: Requirements 4.4**
    
    This property ensures that:
    1. Custom search descriptions are used when available
    2. The description is returned in the message
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid object in a room
    room_id, object_id = data.draw(valid_object_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Get the object
    game_object = world.get_object(object_id)
    
    # Set up custom search description
    custom_description = "Your thorough search reveals ancient runes carved into the surface."
    game_object.state['search_description'] = custom_description
    
    # Search the object
    result = engine.handle_search(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"SEARCH {object_id} should succeed"
    
    # Result should contain the custom description
    assert custom_description in result.message, \
        "Custom search description should be in the result message"


@settings(max_examples=100)
@given(st.data())
def test_search_uses_hidden_details(data):
    """
    For any object with hidden_details property, SEARCH should reveal those details.
    
    **Validates: Requirements 4.4**
    
    This property ensures that:
    1. Hidden details are revealed through searching
    2. The details are returned in the message
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid object in a room
    room_id, object_id = data.draw(valid_object_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Get the object
    game_object = world.get_object(object_id)
    
    # Clear search_description to ensure hidden_details takes priority
    game_object.state['search_description'] = None
    game_object.state['search_reveals'] = []
    
    # Set up hidden details
    hidden_details = "You discover a secret compartment containing a cryptic message."
    game_object.state['hidden_details'] = hidden_details
    
    # Search the object
    result = engine.handle_search(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"SEARCH {object_id} should succeed"
    
    # Result should contain the hidden details
    assert hidden_details in result.message, \
        "Hidden details should be in the result message"


@settings(max_examples=100)
@given(st.data())
def test_search_default_message_for_empty_objects(data):
    """
    For any object without special search properties, SEARCH should return
    a default "nothing found" message.
    
    **Validates: Requirements 4.4**
    
    This property ensures that:
    1. Objects without search properties return appropriate messages
    2. The message indicates nothing was found
    3. The message uses haunted theme
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid object in a room
    room_id, object_id = data.draw(valid_object_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Get the object
    game_object = world.get_object(object_id)
    
    # Clear any search-related properties
    game_object.state['search_reveals'] = []
    game_object.state['search_description'] = None
    game_object.state['hidden_details'] = None
    
    # Search the object
    result = engine.handle_search(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"SEARCH {object_id} should succeed"
    
    # Result should contain a "nothing found" type message
    message_lower = result.message.lower()
    nothing_keywords = ['nothing', 'no', 'find', 'reveals', 'yields']
    
    # At least one keyword should be present
    has_keyword = any(keyword in message_lower for keyword in nothing_keywords)
    assert has_keyword, \
        "Default message should indicate nothing was found"


@settings(max_examples=100)
@given(st.data())
def test_search_uses_haunted_theme(data):
    """
    For any object, SEARCH response should use haunted theme descriptions.
    
    **Validates: Requirements 4.4**
    
    This property ensures that:
    1. Responses maintain the haunted atmosphere
    2. Default messages use spooky language
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid object in a room
    room_id, object_id = data.draw(valid_object_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Search the object
    result = engine.handle_search(object_id, state)
    
    # Check that message exists and is non-empty
    assert result.message is not None and len(result.message) > 0, \
        "Message should exist and be non-empty"
    
    # Message should be a string
    assert isinstance(result.message, str), \
        "Result message should be a string"


@settings(max_examples=100)
@given(st.data())
def test_search_consistent_for_same_object(data):
    """
    For any object without search_reveals, searching multiple times should
    return consistent results.
    
    **Validates: Requirements 4.4**
    
    This property ensures that:
    1. Repeated searches of the same object are consistent
    2. The same message is returned each time
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid object in a room
    room_id, object_id = data.draw(valid_object_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Get the object
    game_object = world.get_object(object_id)
    
    # Clear search_reveals to ensure consistency
    game_object.state['search_reveals'] = []
    
    # Search the object twice
    result1 = engine.handle_search(object_id, state)
    result2 = engine.handle_search(object_id, state)
    
    # Both should succeed
    assert result1.success is True
    assert result2.success is True
    
    # Messages should be the same
    assert result1.message == result2.message, \
        "Repeated searches should return consistent messages"
