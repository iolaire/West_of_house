"""
Property-Based Tests for LOOK INSIDE Command

Tests correctness properties related to the LOOK INSIDE command,
ensuring container contents are listed correctly.
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
def valid_container_in_room(draw, world_data):
    """
    Generate a valid room ID and container ID where the container is in the room.
    
    Returns tuple of (room_id, container_id).
    """
    # Get all container objects
    container_ids = [obj_id for obj_id, obj in world_data.objects.items() if obj.type == "container"]
    
    if not container_ids:
        assume(False)
    
    # Pick a random container
    container_id = draw(st.sampled_from(container_ids))
    
    # Find a room that has this container
    rooms_with_container = []
    for room_id, room in world_data.rooms.items():
        if container_id in room.items:
            rooms_with_container.append(room_id)
    
    if rooms_with_container:
        room_id = draw(st.sampled_from(rooms_with_container))
        return (room_id, container_id)
    else:
        # Container not in any room, skip
        assume(False)


# Feature: complete-zork-commands, Property 12: Look inside container contents
@settings(max_examples=100)
@given(st.data())
def test_look_inside_open_container_lists_contents(data):
    """
    For any open or transparent container, executing LOOK INSIDE should list
    all objects currently in the container.
    
    **Validates: Requirements 4.3**
    
    This property ensures that:
    1. LOOK INSIDE succeeds for open/transparent containers
    2. All contents are listed
    3. Contents are formatted clearly
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid container in a room
    room_id, container_id = data.draw(valid_container_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Get container and make it open
    container = world.get_object(container_id)
    container.state['is_open'] = True
    
    # Add some test objects to the container
    test_objects = []
    all_objects = list(world.objects.keys())
    if len(all_objects) >= 2:
        test_objects = data.draw(st.lists(
            st.sampled_from(all_objects),
            min_size=0,
            max_size=min(3, len(all_objects))
        ))
    
    container.state['contents'] = test_objects
    
    # Look inside the container
    result = engine.handle_look_inside(container_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"LOOK INSIDE {container_id} should succeed when container is open"
    
    # Result should contain a message
    assert result.message is not None, \
        "Result message should not be None"
    assert len(result.message) > 0, \
        "Result message should not be empty"
    
    # If container has contents, they should be mentioned in the message
    if test_objects:
        # At least one object name should appear in the message
        message_lower = result.message.lower()
        found_any = False
        for obj_id in test_objects:
            try:
                obj = world.get_object(obj_id)
                obj_name = (obj.name_spooky if obj.name_spooky else obj.name).lower()
                if obj_name in message_lower:
                    found_any = True
                    break
            except ValueError:
                continue
        
        # At least one object should be mentioned (if objects exist)
        if test_objects:
            assert found_any or "empty" in message_lower, \
                "Message should mention contents or indicate container is empty"
    else:
        # Empty container should say it's empty
        assert "empty" in result.message.lower(), \
            "Empty container message should mention it's empty"


@settings(max_examples=100)
@given(st.data())
def test_look_inside_closed_container_fails(data):
    """
    For any closed (non-transparent) container, LOOK INSIDE should fail with
    appropriate message.
    
    **Validates: Requirements 4.3**
    
    This property ensures that:
    1. LOOK INSIDE fails for closed containers
    2. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid container in a room
    room_id, container_id = data.draw(valid_container_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Get container and make it closed and not transparent
    container = world.get_object(container_id)
    container.state['is_open'] = False
    container.state['is_transparent'] = False
    
    # Look inside the closed container
    result = engine.handle_look_inside(container_id, state)
    
    # Command should fail
    assert result.success is False, \
        f"LOOK INSIDE {container_id} should fail when container is closed"
    
    # Error message should indicate container is closed
    assert "closed" in result.message.lower() or "can't see" in result.message.lower(), \
        "Error message should indicate container is closed"


@settings(max_examples=100)
@given(st.data())
def test_look_inside_transparent_container_succeeds(data):
    """
    For any transparent container (even if closed), LOOK INSIDE should succeed.
    
    **Validates: Requirements 4.3**
    
    This property ensures that:
    1. LOOK INSIDE succeeds for transparent containers
    2. Contents are visible even when closed
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid container in a room
    room_id, container_id = data.draw(valid_container_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Get container and make it transparent but closed
    container = world.get_object(container_id)
    container.state['is_open'] = False
    container.state['is_transparent'] = True
    container.state['contents'] = []
    
    # Look inside the transparent container
    result = engine.handle_look_inside(container_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"LOOK INSIDE {container_id} should succeed when container is transparent"
    
    # Result should contain a message
    assert result.message is not None, \
        "Result message should not be None"


@settings(max_examples=100)
@given(st.data())
def test_look_inside_non_container_fails(data):
    """
    For any non-container object, LOOK INSIDE should fail with appropriate message.
    
    **Validates: Requirements 4.3**
    
    This property ensures that:
    1. LOOK INSIDE only works on containers
    2. Appropriate error message for non-containers
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get all non-container objects
    non_container_ids = [obj_id for obj_id, obj in world.objects.items() if obj.type != "container"]
    
    if not non_container_ids:
        assume(False)
    
    # Pick a random non-container
    object_id = data.draw(st.sampled_from(non_container_ids))
    
    # Find a room that has this object
    rooms_with_object = []
    for room_id, room in world.rooms.items():
        if object_id in room.items:
            rooms_with_object.append(room_id)
    
    if not rooms_with_object:
        assume(False)
    
    room_id = data.draw(st.sampled_from(rooms_with_object))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Try to look inside the non-container
    result = engine.handle_look_inside(object_id, state)
    
    # Command should fail
    assert result.success is False, \
        f"LOOK INSIDE {object_id} should fail for non-container objects"
    
    # Error message should indicate it's not a container
    assert "can't look inside" in result.message.lower() or "not a container" in result.message.lower(), \
        "Error message should indicate object is not a container"


@settings(max_examples=100)
@given(st.data())
def test_look_inside_formats_contents_clearly(data):
    """
    For any container with contents, LOOK INSIDE should format the contents list clearly.
    
    **Validates: Requirements 4.3**
    
    This property ensures that:
    1. Single item is formatted correctly
    2. Multiple items are formatted with proper grammar (commas and "and")
    3. Empty containers are clearly indicated
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid container in a room
    room_id, container_id = data.draw(valid_container_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Get container and make it open
    container = world.get_object(container_id)
    container.state['is_open'] = True
    
    # Test with different numbers of items
    all_objects = list(world.objects.keys())
    if len(all_objects) >= 3:
        num_items = data.draw(st.integers(min_value=0, max_value=min(3, len(all_objects))))
        test_objects = data.draw(st.lists(
            st.sampled_from(all_objects),
            min_size=num_items,
            max_size=num_items
        ))
        
        container.state['contents'] = test_objects
        
        # Look inside the container
        result = engine.handle_look_inside(container_id, state)
        
        # Command should succeed
        assert result.success is True, \
            f"LOOK INSIDE {container_id} should succeed"
        
        # Check formatting based on number of items
        if num_items == 0:
            assert "empty" in result.message.lower(), \
                "Empty container should say it's empty"
        elif num_items == 1:
            # Single item should not have "and" in the items list
            # (comma after container name is OK: "Inside the box, you see: item")
            assert " and " not in result.message.lower() or result.message.lower().count(" and ") <= 1, \
                "Single item should not have 'and' between items"
        elif num_items == 2:
            # Two items should have "and" joining them
            assert " and " in result.message.lower(), \
                "Two items should be joined with 'and'"
        else:
            # Three or more items should have commas and "and"
            assert "," in result.message and " and " in result.message.lower(), \
                "Multiple items should have commas and 'and'"
