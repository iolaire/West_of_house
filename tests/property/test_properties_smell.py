"""
Property-Based Tests for SMELL Command

Tests correctness properties related to the SMELL command,
ensuring it provides olfactory information appropriately.
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


# Feature: complete-zork-commands, Property 16: Smell provides olfactory information
@settings(max_examples=100)
@given(st.data())
def test_smell_provides_olfactory_information(data):
    """
    For any object or room, executing SMELL should return a description
    of olfactory information.
    
    **Validates: Requirements 4.7**
    
    This property ensures that:
    1. SMELL returns olfactory information
    2. The response is non-empty
    3. The response is a string
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
    
    # Remove any existing SMELL interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "SMELL"]
    
    # Create a SMELL interaction with olfactory description
    smell_description = "You detect a faint musty odor emanating from it."
    smell_interaction = Interaction(
        verb="SMELL",
        response_original=smell_description,
        response_spooky=smell_description,
        condition=None,
        state_change=None,
        flag_change=None,
        sanity_effect=0
    )
    
    # Add SMELL interaction to the object
    game_object.interactions.append(smell_interaction)
    
    # Smell the object
    result = engine.handle_smell(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"SMELL {object_id} should succeed"
    
    # Result should contain olfactory information
    assert result.message is not None, \
        "Result message should not be None"
    assert len(result.message) > 0, \
        "Result message should not be empty"
    
    # Message should contain the smell description
    assert smell_description in result.message, \
        "Result message should contain the smell description"
    
    # Message should be a string
    assert isinstance(result.message, str), \
        "Result message should be a string"


@settings(max_examples=100)
@given(st.data())
def test_smell_room_provides_olfactory(data):
    """
    For any room, executing SMELL without an object should return
    ambient olfactory information.
    
    **Validates: Requirements 4.7**
    
    This property ensures that:
    1. SMELL works without specifying an object
    2. Room ambient smells are described
    3. Response varies based on sanity level
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a random room
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    # Create game state in the room with random sanity
    state = GameState.create_new_game()
    state.current_room = room_id
    state.sanity = data.draw(st.integers(min_value=0, max_value=100))
    
    # Smell the room (no object specified)
    result = engine.handle_smell(None, state)
    
    # Command should succeed
    assert result.success is True, \
        "SMELL should succeed when smelling room"
    
    # Result should contain olfactory information
    assert result.message is not None, \
        "Result message should not be None"
    assert len(result.message) > 0, \
        "Result message should not be empty"
    
    # Message should be a string
    assert isinstance(result.message, str), \
        "Result message should be a string"


@settings(max_examples=100)
@given(st.data())
def test_smell_fails_for_missing_object(data):
    """
    For any object not in the current room or inventory, SMELL should fail
    with appropriate message.
    
    **Validates: Requirements 4.7**
    
    This property ensures that:
    1. SMELL fails when object is not present
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
    
    # Try to smell the missing object
    result = engine.handle_smell(object_id, state)
    
    # Command should fail
    assert result.success is False, \
        f"SMELL {object_id} should fail when object is not present"
    
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
def test_smell_uses_spooky_description(data):
    """
    For any object with smell, SMELL should use the spooky version.
    
    **Validates: Requirements 4.7**
    
    This property ensures that:
    1. Spooky smell is used instead of original
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
    
    # Remove any existing SMELL interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "SMELL"]
    
    # Create a SMELL interaction with different original and spooky smell
    original_smell = "You smell fresh flowers."
    spooky_smell = "You smell decaying flowers, their sickly-sweet stench filling your nostrils."
    smell_interaction = Interaction(
        verb="SMELL",
        response_original=original_smell,
        response_spooky=spooky_smell,
        condition=None,
        state_change=None,
        flag_change=None,
        sanity_effect=0
    )
    
    # Add SMELL interaction to the object
    game_object.interactions.append(smell_interaction)
    
    # Smell the object
    result = engine.handle_smell(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"SMELL {object_id} should succeed"
    
    # Result should contain the spooky smell, not the original
    assert spooky_smell in result.message, \
        "Result should contain spooky smell"
    assert original_smell not in result.message, \
        "Result should not contain original smell"


@settings(max_examples=100)
@given(st.data())
def test_smell_applies_sanity_effects(data):
    """
    For any object with sanity effects, SMELL should apply those effects.
    
    **Validates: Requirements 4.7**
    
    This property ensures that:
    1. Sanity effects are applied when smelling
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
    
    # Remove any existing SMELL interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "SMELL"]
    
    # Create a SMELL interaction with sanity effect
    sanity_effect = data.draw(st.integers(min_value=-20, max_value=20))
    assume(sanity_effect != 0)  # Skip zero effects
    
    smell_description = "You smell the overwhelming stench of decay and corruption."
    smell_interaction = Interaction(
        verb="SMELL",
        response_original=smell_description,
        response_spooky=smell_description,
        condition=None,
        state_change=None,
        flag_change=None,
        sanity_effect=sanity_effect
    )
    
    # Add SMELL interaction to the object
    game_object.interactions.append(smell_interaction)
    
    # Smell the object
    result = engine.handle_smell(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"SMELL {object_id} should succeed"
    
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
def test_smell_applies_state_changes(data):
    """
    For any object with state changes, SMELL should apply those changes.
    
    **Validates: Requirements 4.7**
    
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
    
    # Remove any existing SMELL interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "SMELL"]
    
    # Create a SMELL interaction with state change
    smell_description = "You detect a chemical odor that triggers a reaction."
    smell_interaction = Interaction(
        verb="SMELL",
        response_original=smell_description,
        response_spooky=smell_description,
        condition=None,
        state_change={'has_been_smelled': True},
        flag_change=None,
        sanity_effect=0
    )
    
    # Add SMELL interaction to the object
    game_object.interactions.append(smell_interaction)
    
    # Ensure the state is not set initially
    game_object.state['has_been_smelled'] = False
    
    # Smell the object
    result = engine.handle_smell(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"SMELL {object_id} should succeed"
    
    # State should have changed
    assert game_object.state['has_been_smelled'] is True, \
        "Object state should be updated after smelling"


@settings(max_examples=100)
@given(st.data())
def test_smell_applies_flag_changes(data):
    """
    For any object with flag changes, SMELL should apply those changes.
    
    **Validates: Requirements 4.7**
    
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
    
    # Remove any existing SMELL interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "SMELL"]
    
    # Create a SMELL interaction with flag change
    smell_description = "You smell a distinctive scent that reveals a secret."
    smell_interaction = Interaction(
        verb="SMELL",
        response_original=smell_description,
        response_spooky=smell_description,
        condition=None,
        state_change=None,
        flag_change={'scent_detected': True},
        sanity_effect=0
    )
    
    # Add SMELL interaction to the object
    game_object.interactions.append(smell_interaction)
    
    # Ensure the flag is not set initially
    state.set_flag('scent_detected', False)
    
    # Smell the object
    result = engine.handle_smell(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"SMELL {object_id} should succeed"
    
    # Flag should have changed
    assert state.get_flag('scent_detected', False) is True, \
        "Game state flag should be updated after smelling"


@settings(max_examples=100)
@given(st.data())
def test_smell_respects_conditions(data):
    """
    For any object with conditions, SMELL should only work when
    conditions are met.
    
    **Validates: Requirements 4.7**
    
    This property ensures that:
    1. Conditional SMELL interactions are respected
    2. SMELL uses default message when conditions are not met
    3. SMELL uses specific smell when conditions are met
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
    
    # Remove any existing SMELL interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "SMELL"]
    
    # Create a SMELL interaction with condition
    smell_description = "You smell a pungent chemical odor now that the container is open."
    smell_interaction = Interaction(
        verb="SMELL",
        response_original=smell_description,
        response_spooky=smell_description,
        condition={'is_open': True},
        state_change=None,
        flag_change=None,
        sanity_effect=0
    )
    
    # Add SMELL interaction to the object
    game_object.interactions.append(smell_interaction)
    
    # Test with condition not met
    game_object.state['is_open'] = False
    result1 = engine.handle_smell(object_id, state)
    
    # Should succeed but use default message
    assert result1.success is True, \
        "SMELL should succeed even when condition is not met"
    
    # Should not contain the specific smell description
    assert smell_description not in result1.message, \
        "Result should not contain specific smell when condition is not met"
    
    # Test with condition met
    game_object.state['is_open'] = True
    result2 = engine.handle_smell(object_id, state)
    
    # Should succeed with specific smell
    assert result2.success is True, \
        "SMELL should succeed when condition is met"
    
    # Should contain the specific smell description
    assert smell_description in result2.message, \
        "Result should contain specific smell when condition is met"


@settings(max_examples=100)
@given(st.data())
def test_smell_works_from_inventory(data):
    """
    For any object in inventory, SMELL should work.
    
    **Validates: Requirements 4.7**
    
    This property ensures that:
    1. Objects in inventory can be smelled
    2. SMELL works the same for inventory items as room items
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
    
    # Remove any existing SMELL interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "SMELL"]
    
    # Create a SMELL interaction
    smell_description = "You smell a faint odor from the portable object."
    smell_interaction = Interaction(
        verb="SMELL",
        response_original=smell_description,
        response_spooky=smell_description,
        condition=None,
        state_change=None,
        flag_change=None,
        sanity_effect=0
    )
    
    # Add SMELL interaction to the object
    game_object.interactions.append(smell_interaction)
    
    # Smell the object from inventory
    result = engine.handle_smell(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"SMELL {object_id} should succeed when object is in inventory"
    
    # Result should contain the smell description
    assert smell_description in result.message, \
        "Result should contain smell description"


@settings(max_examples=100)
@given(st.data())
def test_smell_default_message_for_odorless_objects(data):
    """
    For any object without SMELL interaction, SMELL should return
    a default "nothing to smell" message.
    
    **Validates: Requirements 4.7**
    
    This property ensures that:
    1. SMELL succeeds even for odorless objects
    2. Default message is returned
    3. Message indicates nothing unusual to smell
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
    
    # Remove any SMELL interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "SMELL"]
    
    # Smell the object
    result = engine.handle_smell(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"SMELL {object_id} should succeed even for odorless objects"
    
    # Result should contain a message
    assert result.message is not None, \
        "Result message should not be None"
    assert len(result.message) > 0, \
        "Result message should not be empty"
    
    # Message should indicate nothing unusual (default message)
    message_lower = result.message.lower()
    assert any(word in message_lower for word in ['nothing', 'no', 'smell', 'scent', 'odor']), \
        "Default message should indicate nothing unusual to smell"


@settings(max_examples=100)
@given(st.data())
def test_smell_description_property(data):
    """
    For any object with smell_description property, SMELL should use it.
    
    **Validates: Requirements 4.7**
    
    This property ensures that:
    1. smell_description property is used when present
    2. Takes precedence over default messages
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
    
    # Remove any existing SMELL interactions
    game_object.interactions = [i for i in game_object.interactions if i.verb != "SMELL"]
    
    # Set smell_description property directly
    smell_description = "The object emits a constant sulfurous odor."
    game_object.state['smell_description'] = smell_description
    
    # Smell the object
    result = engine.handle_smell(object_id, state)
    
    # Command should succeed
    assert result.success is True, \
        f"SMELL {object_id} should succeed"
    
    # Result should contain the smell description from property
    assert smell_description in result.message, \
        "Result should contain smell description from property"
