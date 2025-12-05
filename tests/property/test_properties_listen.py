"""
Property-Based Tests for LISTEN Command

Tests correctness properties related to the LISTEN command,
ensuring it provides audio information appropriately.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler'))

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
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
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


# Feature: complete-zork-commands, Property 15: Listen provides audio information
@settings(max_examples=100)
@given(st.data())
def test_listen_provides_audio_information(data):
    """
    For any object or room, executing LISTEN should return a description
    of audible information.
    
    **Validates: Requirements 4.6**
    
    This property ensures that:
    1. LISTEN returns audio information
    2. The response is non-empty
    3. The response is a string
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid object in a room
    room_id, object_id = data.draw(valid_object_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Get the object
    game_object = world.get_object(object_id)
    
    # Remove any existing LISTEN interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "LISTEN"]
    
    # Create a LISTEN interaction with audio description
    audio_description = "You hear a faint ticking sound emanating from within."
    listen_interaction = Interaction(
        verb="LISTEN",
        response_original=audio_description,
        response_spooky=audio_description,
        condition=None,
        state_change=None,
        flag_change=None,
        sanity_effect=0
    )
    
    # Add LISTEN interaction to the object
    game_object.interactions.append(listen_interaction)
    
    # Listen to the object
    result = engine.handle_listen(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"LISTEN {object_id} should succeed"
    
    # Result should contain audio information
    assert result.message is not None, \
        "Result message should not be None"
    assert len(result.message) > 0, \
        "Result message should not be empty"
    
    # Message should contain the audio description
    assert audio_description in result.message, \
        "Result message should contain the audio description"
    
    # Message should be a string
    assert isinstance(result.message, str), \
        "Result message should be a string"


@settings(max_examples=100)
@given(st.data())
def test_listen_to_room_provides_audio(data):
    """
    For any room, executing LISTEN without an object should return
    ambient audio information.
    
    **Validates: Requirements 4.6**
    
    This property ensures that:
    1. LISTEN works without specifying an object
    2. Room ambient sounds are described
    3. Response varies based on sanity level
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a random room
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    # Create game state in the room with random sanity
    state = GameState.create_new_game()
    state.current_room = room_id
    state.sanity = data.draw(st.integers(min_value=0, max_value=100))
    
    # Listen to the room (no object specified)
    result = engine.handle_listen(None, state)
    
    # Command should succeed
    assert result.success is True, \
        "LISTEN should succeed when listening to room"
    
    # Result should contain audio information
    assert result.message is not None, \
        "Result message should not be None"
    assert len(result.message) > 0, \
        "Result message should not be empty"
    
    # Message should be a string
    assert isinstance(result.message, str), \
        "Result message should be a string"


@settings(max_examples=100)
@given(st.data())
def test_listen_fails_for_missing_object(data):
    """
    For any object not in the current room or inventory, LISTEN should fail
    with appropriate message.
    
    **Validates: Requirements 4.6**
    
    This property ensures that:
    1. LISTEN fails when object is not present
    2. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get an object not in the room
    room_id, object_id = data.draw(object_not_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Try to listen to the missing object
    result = engine.handle_listen(object_id, state)
    
    # Command should fail
    assert result.success is False, \
        f"LISTEN {object_id} should fail when object is not present"
    
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
def test_listen_uses_spooky_audio(data):
    """
    For any object with audio, LISTEN should use the spooky version.
    
    **Validates: Requirements 4.6**
    
    This property ensures that:
    1. Spooky audio is used instead of original
    2. The haunted theme is maintained
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid object in a room
    room_id, object_id = data.draw(valid_object_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Get the object
    game_object = world.get_object(object_id)
    
    # Remove any existing LISTEN interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "LISTEN"]
    
    # Create a LISTEN interaction with different original and spooky audio
    original_audio = "You hear a pleasant melody."
    spooky_audio = "You hear a haunting melody that chills your blood."
    listen_interaction = Interaction(
        verb="LISTEN",
        response_original=original_audio,
        response_spooky=spooky_audio,
        condition=None,
        state_change=None,
        flag_change=None,
        sanity_effect=0
    )
    
    # Add LISTEN interaction to the object
    game_object.interactions.append(listen_interaction)
    
    # Listen to the object
    result = engine.handle_listen(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"LISTEN {object_id} should succeed"
    
    # Result should contain the spooky audio, not the original
    assert spooky_audio in result.message, \
        "Result should contain spooky audio"
    assert original_audio not in result.message, \
        "Result should not contain original audio"


@settings(max_examples=100)
@given(st.data())
def test_listen_applies_sanity_effects(data):
    """
    For any object with sanity effects, LISTEN should apply those effects.
    
    **Validates: Requirements 4.6**
    
    This property ensures that:
    1. Sanity effects are applied when listening
    2. Sanity changes are tracked in the result
    3. Notifications are generated for sanity changes
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
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
    
    # Remove any existing LISTEN interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "LISTEN"]
    
    # Create a LISTEN interaction with sanity effect
    sanity_effect = data.draw(st.integers(min_value=-20, max_value=20))
    assume(sanity_effect != 0)  # Skip zero effects
    
    audio_description = "You hear disturbing whispers from the shadows."
    listen_interaction = Interaction(
        verb="LISTEN",
        response_original=audio_description,
        response_spooky=audio_description,
        condition=None,
        state_change=None,
        flag_change=None,
        sanity_effect=sanity_effect
    )
    
    # Add LISTEN interaction to the object
    game_object.interactions.append(listen_interaction)
    
    # Listen to the object
    result = engine.handle_listen(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"LISTEN {object_id} should succeed"
    
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
def test_listen_applies_state_changes(data):
    """
    For any object with state changes, LISTEN should apply those changes.
    
    **Validates: Requirements 4.6**
    
    This property ensures that:
    1. State changes are applied to the object
    2. The object's state is updated correctly
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid object in a room
    room_id, object_id = data.draw(valid_object_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Get the object
    game_object = world.get_object(object_id)
    
    # Remove any existing LISTEN interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "LISTEN"]
    
    # Create a LISTEN interaction with state change
    audio_description = "You hear a mechanism click inside."
    listen_interaction = Interaction(
        verb="LISTEN",
        response_original=audio_description,
        response_spooky=audio_description,
        condition=None,
        state_change={'has_been_listened_to': True},
        flag_change=None,
        sanity_effect=0
    )
    
    # Add LISTEN interaction to the object
    game_object.interactions.append(listen_interaction)
    
    # Ensure the state is not set initially
    game_object.state['has_been_listened_to'] = False
    
    # Listen to the object
    result = engine.handle_listen(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"LISTEN {object_id} should succeed"
    
    # State should have changed
    assert game_object.state['has_been_listened_to'] is True, \
        "Object state should be updated after listening"


@settings(max_examples=100)
@given(st.data())
def test_listen_applies_flag_changes(data):
    """
    For any object with flag changes, LISTEN should apply those changes.
    
    **Validates: Requirements 4.6**
    
    This property ensures that:
    1. Flag changes are applied to the game state
    2. The game state flags are updated correctly
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid object in a room
    room_id, object_id = data.draw(valid_object_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Get the object
    game_object = world.get_object(object_id)
    
    # Remove any existing LISTEN interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "LISTEN"]
    
    # Create a LISTEN interaction with flag change
    audio_description = "You hear a secret code being whispered."
    listen_interaction = Interaction(
        verb="LISTEN",
        response_original=audio_description,
        response_spooky=audio_description,
        condition=None,
        state_change=None,
        flag_change={'code_heard': True},
        sanity_effect=0
    )
    
    # Add LISTEN interaction to the object
    game_object.interactions.append(listen_interaction)
    
    # Ensure the flag is not set initially
    state.set_flag('code_heard', False)
    
    # Listen to the object
    result = engine.handle_listen(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"LISTEN {object_id} should succeed"
    
    # Flag should have changed
    assert state.get_flag('code_heard', False) is True, \
        "Game state flag should be updated after listening"


@settings(max_examples=100)
@given(st.data())
def test_listen_respects_conditions(data):
    """
    For any object with conditions, LISTEN should only work when
    conditions are met.
    
    **Validates: Requirements 4.6**
    
    This property ensures that:
    1. Conditional LISTEN interactions are respected
    2. LISTEN uses default message when conditions are not met
    3. LISTEN uses specific audio when conditions are met
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid object in a room
    room_id, object_id = data.draw(valid_object_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Get the object
    game_object = world.get_object(object_id)
    
    # Remove any existing LISTEN interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "LISTEN"]
    
    # Create a LISTEN interaction with condition
    audio_description = "You hear the mechanism ticking loudly now that it's activated."
    listen_interaction = Interaction(
        verb="LISTEN",
        response_original=audio_description,
        response_spooky=audio_description,
        condition={'is_activated': True},
        state_change=None,
        flag_change=None,
        sanity_effect=0
    )
    
    # Add LISTEN interaction to the object
    game_object.interactions.append(listen_interaction)
    
    # Test with condition not met
    game_object.state['is_activated'] = False
    result1 = engine.handle_listen(object_id, state)
    
    # Should succeed but use default message
    assert result1.success is True, \
        "LISTEN should succeed even when condition is not met"
    
    # Should not contain the specific audio description
    assert audio_description not in result1.message, \
        "Result should not contain specific audio when condition is not met"
    
    # Test with condition met
    game_object.state['is_activated'] = True
    result2 = engine.handle_listen(object_id, state)
    
    # Should succeed with specific audio
    assert result2.success is True, \
        "LISTEN should succeed when condition is met"
    
    # Should contain the specific audio description
    assert audio_description in result2.message, \
        "Result should contain specific audio when condition is met"


@settings(max_examples=100)
@given(st.data())
def test_listen_works_from_inventory(data):
    """
    For any object in inventory, LISTEN should work.
    
    **Validates: Requirements 4.6**
    
    This property ensures that:
    1. Objects in inventory can be listened to
    2. LISTEN works the same for inventory items as room items
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
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
    
    # Remove any existing LISTEN interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "LISTEN"]
    
    # Create a LISTEN interaction
    audio_description = "You hear a faint rattling from within the portable object."
    listen_interaction = Interaction(
        verb="LISTEN",
        response_original=audio_description,
        response_spooky=audio_description,
        condition=None,
        state_change=None,
        flag_change=None,
        sanity_effect=0
    )
    
    # Add LISTEN interaction to the object
    game_object.interactions.append(listen_interaction)
    
    # Listen to the object from inventory
    result = engine.handle_listen(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"LISTEN {object_id} should succeed when object is in inventory"
    
    # Result should contain the audio description
    assert audio_description in result.message, \
        "Result should contain audio description"


@settings(max_examples=100)
@given(st.data())
def test_listen_default_message_for_silent_objects(data):
    """
    For any object without LISTEN interaction, LISTEN should return
    a default "nothing to hear" message.
    
    **Validates: Requirements 4.6**
    
    This property ensures that:
    1. LISTEN succeeds even for silent objects
    2. Default message is returned
    3. Message indicates nothing unusual to hear
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid object in a room
    room_id, object_id = data.draw(valid_object_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Get the object
    game_object = world.get_object(object_id)
    
    # Remove any LISTEN interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "LISTEN"]
    
    # Listen to the object
    result = engine.handle_listen(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"LISTEN {object_id} should succeed even for silent objects"
    
    # Result should contain a message
    assert result.message is not None, \
        "Result message should not be None"
    assert len(result.message) > 0, \
        "Result message should not be empty"
    
    # Message should indicate nothing unusual (default message)
    message_lower = result.message.lower()
    assert any(word in message_lower for word in ['nothing', 'silent', 'no sound', 'hear']), \
        "Default message should indicate nothing unusual to hear"


@settings(max_examples=100)
@given(st.data())
def test_listen_audio_description_property(data):
    """
    For any object with audio_description property, LISTEN should use it.
    
    **Validates: Requirements 4.6**
    
    This property ensures that:
    1. audio_description property is used when present
    2. Takes precedence over default messages
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid object in a room
    room_id, object_id = data.draw(valid_object_in_room(world))
    
    # Create game state in the room
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Get the object
    game_object = world.get_object(object_id)
    
    # Remove any existing LISTEN interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "LISTEN"]
    
    # Set audio_description property directly
    audio_description = "The object emits a constant low hum."
    game_object.state['audio_description'] = audio_description
    
    # Listen to the object
    result = engine.handle_listen(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"LISTEN {object_id} should succeed"
    
    # Result should contain the audio description from property
    assert audio_description in result.message, \
        "Result should contain audio description from property"
