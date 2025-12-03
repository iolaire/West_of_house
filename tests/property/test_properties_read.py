"""
Property-Based Tests for READ Command

Tests correctness properties related to the READ command,
ensuring it displays text content appropriately.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler'))

import pytest
from hypothesis import given, strategies as st, settings, assume
from game_engine import GameEngine, ActionResult
from state_manager import GameState
from world_loader import WorldData, Interaction


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


# Feature: complete-zork-commands, Property 14: Read displays text
@settings(max_examples=100)
@given(st.data())
def test_read_displays_text(data):
    """
    For any readable object, executing READ should return the text content
    of that object.
    
    **Validates: Requirements 4.5**
    
    This property ensures that:
    1. READ returns text content for readable objects
    2. The text is non-empty
    3. The text is returned in the message
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
    
    # Remove any existing READ interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "READ"]
    
    # Create a READ interaction with text content
    text_content = "The ancient text reads: 'Beware the shadows that lurk in forgotten corners.'"
    read_interaction = Interaction(
        verb="READ",
        response_original=text_content,
        response_spooky=text_content,
        condition=None,
        state_change=None,
        flag_change=None,
        sanity_effect=0
    )
    
    # Add READ interaction to the object
    game_object.interactions.append(read_interaction)
    
    # Read the object
    result = engine.handle_read(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"READ {object_id} should succeed when object is readable"
    
    # Result should contain the text content
    assert result.message is not None, \
        "Result message should not be None"
    assert len(result.message) > 0, \
        "Result message should not be empty"
    
    # Message should contain the text content
    assert text_content in result.message, \
        "Result message should contain the text content"
    
    # Message should be a string
    assert isinstance(result.message, str), \
        "Result message should be a string"


@settings(max_examples=100)
@given(st.data())
def test_read_fails_for_non_readable_objects(data):
    """
    For any object without READ interaction, READ should fail with appropriate message.
    
    **Validates: Requirements 4.5**
    
    This property ensures that:
    1. READ fails when object is not readable
    2. Appropriate error message is returned
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
    
    # Remove any READ interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "READ"]
    
    # Try to read the object
    result = engine.handle_read(object_id, state)
    
    # Command should fail
    assert result.success is False, \
        f"READ {object_id} should fail when object is not readable"
    
    # Error message should be returned
    assert result.message is not None, \
        "Result message should not be None"
    assert len(result.message) > 0, \
        "Result message should not be empty"
    
    # Message should indicate nothing to read
    assert "nothing to read" in result.message.lower() or "can't read" in result.message.lower(), \
        "Error message should indicate object is not readable"


@settings(max_examples=100)
@given(st.data())
def test_read_fails_for_missing_object(data):
    """
    For any object not in the current room or inventory, READ should fail
    with appropriate message.
    
    **Validates: Requirements 4.5**
    
    This property ensures that:
    1. READ fails when object is not present
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
    
    # Try to read the missing object
    result = engine.handle_read(object_id, state)
    
    # Command should fail
    assert result.success is False, \
        f"READ {object_id} should fail when object is not present"
    
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
def test_read_uses_spooky_text(data):
    """
    For any readable object, READ should use the spooky version of the text.
    
    **Validates: Requirements 4.5**
    
    This property ensures that:
    1. Spooky text is used instead of original text
    2. The haunted theme is maintained
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
    
    # Remove any existing READ interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "READ"]
    
    # Create a READ interaction with different original and spooky text
    original_text = "Welcome to the house."
    spooky_text = "The blood-stained words whisper: 'Welcome to your doom.'"
    read_interaction = Interaction(
        verb="READ",
        response_original=original_text,
        response_spooky=spooky_text,
        condition=None,
        state_change=None,
        flag_change=None,
        sanity_effect=0
    )
    
    # Add READ interaction to the object
    game_object.interactions.append(read_interaction)
    
    # Read the object
    result = engine.handle_read(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"READ {object_id} should succeed"
    
    # Result should contain the spooky text, not the original
    assert spooky_text in result.message, \
        "Result should contain spooky text"
    assert original_text not in result.message, \
        "Result should not contain original text"


@settings(max_examples=100)
@given(st.data())
def test_read_applies_sanity_effects(data):
    """
    For any readable object with sanity effects, READ should apply those effects.
    
    **Validates: Requirements 4.5**
    
    This property ensures that:
    1. Sanity effects are applied when reading
    2. Sanity changes are tracked in the result
    3. Notifications are generated for sanity changes
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
    initial_sanity = state.sanity
    
    # Get the object
    game_object = world.get_object(object_id)
    
    # Remove any existing READ interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "READ"]
    
    # Create a READ interaction with sanity effect
    sanity_effect = data.draw(st.integers(min_value=-20, max_value=20))
    assume(sanity_effect != 0)  # Skip zero effects
    
    text_content = "The cursed text fills you with dread."
    read_interaction = Interaction(
        verb="READ",
        response_original=text_content,
        response_spooky=text_content,
        condition=None,
        state_change=None,
        flag_change=None,
        sanity_effect=sanity_effect
    )
    
    # Add READ interaction to the object
    game_object.interactions.append(read_interaction)
    
    # Read the object
    result = engine.handle_read(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"READ {object_id} should succeed"
    
    # Sanity should have changed
    expected_sanity = max(0, min(100, initial_sanity + sanity_effect))
    assert state.sanity == expected_sanity, \
        f"Sanity should change from {initial_sanity} to {expected_sanity}"
    
    # Result should track sanity change
    assert result.sanity_change == sanity_effect, \
        "Result should track sanity change"
    
    # Notifications should be present for sanity changes
    if sanity_effect != 0:
        assert len(result.notifications) > 0, \
            "Notifications should be present for sanity changes"


@settings(max_examples=100)
@given(st.data())
def test_read_applies_state_changes(data):
    """
    For any readable object with state changes, READ should apply those changes.
    
    **Validates: Requirements 4.5**
    
    This property ensures that:
    1. State changes are applied to the object
    2. The object's state is updated correctly
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
    
    # Remove any existing READ interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "READ"]
    
    # Create a READ interaction with state change
    text_content = "You read the ancient scroll."
    read_interaction = Interaction(
        verb="READ",
        response_original=text_content,
        response_spooky=text_content,
        condition=None,
        state_change={'has_been_read': True},
        flag_change=None,
        sanity_effect=0
    )
    
    # Add READ interaction to the object
    game_object.interactions.append(read_interaction)
    
    # Ensure the state is not set initially
    game_object.state['has_been_read'] = False
    
    # Read the object
    result = engine.handle_read(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"READ {object_id} should succeed"
    
    # State should have changed
    assert game_object.state['has_been_read'] is True, \
        "Object state should be updated after reading"


@settings(max_examples=100)
@given(st.data())
def test_read_applies_flag_changes(data):
    """
    For any readable object with flag changes, READ should apply those changes.
    
    **Validates: Requirements 4.5**
    
    This property ensures that:
    1. Flag changes are applied to the game state
    2. The game state flags are updated correctly
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
    
    # Remove any existing READ interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "READ"]
    
    # Create a READ interaction with flag change
    text_content = "The scroll reveals a secret."
    read_interaction = Interaction(
        verb="READ",
        response_original=text_content,
        response_spooky=text_content,
        condition=None,
        state_change=None,
        flag_change={'secret_revealed': True},
        sanity_effect=0
    )
    
    # Add READ interaction to the object
    game_object.interactions.append(read_interaction)
    
    # Ensure the flag is not set initially
    state.set_flag('secret_revealed', False)
    
    # Read the object
    result = engine.handle_read(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"READ {object_id} should succeed"
    
    # Flag should have changed
    assert state.get_flag('secret_revealed', False) is True, \
        "Game state flag should be updated after reading"


@settings(max_examples=100)
@given(st.data())
def test_read_respects_conditions(data):
    """
    For any readable object with conditions, READ should only work when
    conditions are met.
    
    **Validates: Requirements 4.5**
    
    This property ensures that:
    1. Conditional READ interactions are respected
    2. READ fails when conditions are not met
    3. READ succeeds when conditions are met
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
    
    # Remove any existing READ interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "READ"]
    
    # Create a READ interaction with condition
    text_content = "The text becomes visible only in the light."
    read_interaction = Interaction(
        verb="READ",
        response_original=text_content,
        response_spooky=text_content,
        condition={'is_illuminated': True},
        state_change=None,
        flag_change=None,
        sanity_effect=0
    )
    
    # Add READ interaction to the object
    game_object.interactions.append(read_interaction)
    
    # Test with condition not met
    game_object.state['is_illuminated'] = False
    result1 = engine.handle_read(object_id, state)
    
    # Should fail when condition not met
    assert result1.success is False, \
        "READ should fail when condition is not met"
    
    # Test with condition met
    game_object.state['is_illuminated'] = True
    result2 = engine.handle_read(object_id, state)
    
    # Should succeed when condition is met
    assert result2.success is True, \
        "READ should succeed when condition is met"
    
    # Should contain the text content
    assert text_content in result2.message, \
        "Result should contain text content when condition is met"


@settings(max_examples=100)
@given(st.data())
def test_read_works_from_inventory(data):
    """
    For any readable object in inventory, READ should work.
    
    **Validates: Requirements 4.5**
    
    This property ensures that:
    1. Objects in inventory can be read
    2. READ works the same for inventory items as room items
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid object
    object_ids = list(world.objects.keys())
    object_id = data.draw(st.sampled_from(object_ids))
    
    # Create game state
    state = GameState.create_new_game()
    
    # Add object to inventory
    state.inventory.append(object_id)
    
    # Get the object
    game_object = world.get_object(object_id)
    
    # Remove any existing READ interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "READ"]
    
    # Create a READ interaction
    text_content = "The portable text reads clearly."
    read_interaction = Interaction(
        verb="READ",
        response_original=text_content,
        response_spooky=text_content,
        condition=None,
        state_change=None,
        flag_change=None,
        sanity_effect=0
    )
    
    # Add READ interaction to the object
    game_object.interactions.append(read_interaction)
    
    # Read the object from inventory
    result = engine.handle_read(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"READ {object_id} should succeed when object is in inventory"
    
    # Result should contain the text content
    assert text_content in result.message, \
        "Result should contain text content"
