"""
Property-Based Tests for TIE and UNTIE Commands

Tests correctness properties related to the TIE and UNTIE commands,
ensuring round-trip consistency and proper state updates.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler'))

import pytest
from hypothesis import given, strategies as st, settings, assume
from game_engine import GameEngine, ActionResult
from state_manager import GameState
from world_loader import WorldData, GameObject


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
def rope_and_target_scenario(draw, world_data):
    """
    Generate a valid room with a rope-like object and a target to tie to.
    
    Creates a test rope object and target, places them in a random room.
    Returns tuple of (room_id, rope_id, target_id, rope_object, target_object).
    """
    # Get all room IDs
    room_ids = list(world_data.rooms.keys())
    room_id = draw(st.sampled_from(room_ids))
    
    # Generate rope object properties
    rope_names = ["rope", "chain", "cord", "cable", "string", "wire"]
    rope_id = draw(st.sampled_from(rope_names))
    
    # Generate target names
    target_names = ["hook", "railing", "post", "beam", "ring", "anchor"]
    target_id = draw(st.sampled_from(target_names))
    
    # Create a rope object
    rope_object = GameObject(
        id=rope_id,
        name=rope_id,
        name_spooky=f"cursed {rope_id}",
        type="tool",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={
            "is_rope": True,
            "can_tie": True,
            "is_tied": False,
            "tied_to": None,
            "tie_targets": [target_id]
        },
        interactions=[]
    )
    
    # Create a target object
    target_object = GameObject(
        id=target_id,
        name=target_id,
        name_spooky=f"ancient {target_id}",
        type="object",
        is_takeable=False,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={
            "can_be_tied_to": True,
            "tied_objects": []
        },
        interactions=[]
    )
    
    return (room_id, rope_id, target_id, rope_object, target_object)


# Feature: complete-zork-commands, Property 8: Tie/Untie inverse operations
@settings(max_examples=100)
@given(st.data())
def test_tie_untie_round_trip(data):
    """
    For any rope-like object and valid target, tying then untying should
    return objects to their original unbound state (round-trip property).
    
    **Validates: Requirements 3.6**
    
    This property ensures that:
    1. TIE changes rope state to tied
    2. UNTIE changes rope state back to untied
    3. Round-trip preserves tie state consistency
    4. Game state is updated correctly
    """
    # Load world data (fresh instance for each test)
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid rope and target scenario
    room_id, rope_id, target_id, rope_object, target_object = data.draw(rope_and_target_scenario(world))
    
    # Add objects to world data
    world.objects[rope_id] = rope_object
    world.objects[target_id] = target_object
    
    # Create game state in the room with the target
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add target to room
    room = world.get_room(room_id)
    if target_id not in room.items:
        room.items.append(target_id)
    
    # Add rope to inventory
    if rope_id not in state.inventory:
        state.add_to_inventory(rope_id)
    
    # Original state: untied
    original_tie_state = rope_object.state.get('is_tied', False)
    original_tied_to = rope_object.state.get('tied_to', None)
    assert original_tie_state is False, "Should start untied"
    assert original_tied_to is None, "Should not be tied to anything"
    
    # Tie the rope to the target
    tie_result = engine.handle_tie(rope_id, target_id, state)
    
    # Tie should succeed
    assert tie_result.success is True, \
        f"Tying {rope_id} to {target_id} should succeed"
    
    # Should now be tied
    assert rope_object.state.get('is_tied', False) is True, \
        f"{rope_id} should be tied"
    assert rope_object.state.get('tied_to', None) == target_id, \
        f"{rope_id} should be tied to {target_id}"
    
    # Target should track the rope
    assert rope_id in target_object.state.get('tied_objects', []), \
        f"{target_id} should track {rope_id} as tied to it"
    
    # Untie the rope
    untie_result = engine.handle_untie(rope_id, state)
    
    # Untie should succeed
    assert untie_result.success is True, \
        f"Untying {rope_id} should succeed"
    
    # Should be back to original state (untied)
    assert rope_object.state.get('is_tied', False) == original_tie_state, \
        f"Round-trip should return to original tie state (False), got {rope_object.state.get('is_tied', False)}"
    assert rope_object.state.get('tied_to', None) == original_tied_to, \
        f"Round-trip should return to original tied_to state (None), got {rope_object.state.get('tied_to', None)}"
    
    # Target should no longer track the rope
    assert rope_id not in target_object.state.get('tied_objects', []), \
        f"{target_id} should no longer track {rope_id}"
    
    # Both operations should return messages
    assert tie_result.message is not None and len(tie_result.message) > 0, \
        "Tie result should contain a message"
    assert untie_result.message is not None and len(untie_result.message) > 0, \
        "Untie result should contain a message"
    
    # Messages should mention the rope and target
    assert rope_id in tie_result.message.lower(), \
        f"Tie message should mention {rope_id}"
    assert target_id in tie_result.message.lower(), \
        f"Tie message should mention {target_id}"
    assert rope_id in untie_result.message.lower(), \
        f"Untie message should mention {rope_id}"


@settings(max_examples=100)
@given(st.data())
def test_tie_fails_when_already_tied(data):
    """
    For any rope-like object, attempting to tie when already tied should fail.
    
    **Validates: Requirements 3.6**
    
    This property ensures that:
    1. Cannot tie an already tied rope
    2. State remains unchanged on failed tie
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid rope and target scenario
    room_id, rope_id, target_id, rope_object, target_object = data.draw(rope_and_target_scenario(world))
    
    # Set rope to already tied
    rope_object.state['is_tied'] = True
    rope_object.state['tied_to'] = target_id
    
    # Add objects to world data
    world.objects[rope_id] = rope_object
    world.objects[target_id] = target_object
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add target to room
    room = world.get_room(room_id)
    if target_id not in room.items:
        room.items.append(target_id)
    
    # Add rope to inventory
    if rope_id not in state.inventory:
        state.add_to_inventory(rope_id)
    
    # Attempt to tie already tied rope
    result = engine.handle_tie(rope_id, target_id, state)
    
    # Should fail
    assert result.success is False, \
        "Tying already tied rope should fail"
    
    # State should remain tied
    assert rope_object.state.get('is_tied', False) is True, \
        f"{rope_id} should remain tied"
    
    # Error message should indicate already tied
    assert "already tied" in result.message.lower(), \
        "Error message should indicate rope is already tied"


@settings(max_examples=100)
@given(st.data())
def test_untie_fails_when_not_tied(data):
    """
    For any rope-like object, attempting to untie when not tied should fail.
    
    **Validates: Requirements 3.6**
    
    This property ensures that:
    1. Cannot untie a rope that is not tied
    2. State remains unchanged on failed untie
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid rope and target scenario
    room_id, rope_id, target_id, rope_object, target_object = data.draw(rope_and_target_scenario(world))
    
    # Ensure rope is not tied
    rope_object.state['is_tied'] = False
    rope_object.state['tied_to'] = None
    
    # Add objects to world data
    world.objects[rope_id] = rope_object
    world.objects[target_id] = target_object
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add target to room
    room = world.get_room(room_id)
    if target_id not in room.items:
        room.items.append(target_id)
    
    # Add rope to inventory
    if rope_id not in state.inventory:
        state.add_to_inventory(rope_id)
    
    # Attempt to untie rope that is not tied
    result = engine.handle_untie(rope_id, state)
    
    # Should fail
    assert result.success is False, \
        "Untying rope that is not tied should fail"
    
    # State should remain untied
    assert rope_object.state.get('is_tied', False) is False, \
        f"{rope_id} should remain untied"
    
    # Error message should indicate not tied
    assert "not tied" in result.message.lower(), \
        "Error message should indicate rope is not tied"


@settings(max_examples=100)
@given(st.data())
def test_tie_fails_with_invalid_target(data):
    """
    For any rope-like object, attempting to tie to invalid target should fail.
    
    **Validates: Requirements 3.6**
    
    This property ensures that:
    1. Can only tie to valid targets
    2. State remains unchanged with invalid target
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid rope and target scenario
    room_id, rope_id, valid_target_id, rope_object, valid_target = data.draw(rope_and_target_scenario(world))
    
    # Create an invalid target (not in tie_targets list)
    invalid_target_id = "invalid_target"
    invalid_target = GameObject(
        id=invalid_target_id,
        name=invalid_target_id,
        name_spooky=f"mysterious {invalid_target_id}",
        type="object",
        is_takeable=False,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={
            "can_be_tied_to": True,
            "tied_objects": []
        },
        interactions=[]
    )
    
    # Add objects to world data
    world.objects[rope_id] = rope_object
    world.objects[valid_target_id] = valid_target
    world.objects[invalid_target_id] = invalid_target
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add invalid target to room
    room = world.get_room(room_id)
    if invalid_target_id not in room.items:
        room.items.append(invalid_target_id)
    
    # Add rope to inventory
    if rope_id not in state.inventory:
        state.add_to_inventory(rope_id)
    
    # Original state
    original_tie_state = rope_object.state.get('is_tied', False)
    
    # Attempt to tie to invalid target
    result = engine.handle_tie(rope_id, invalid_target_id, state)
    
    # Should fail
    assert result.success is False, \
        f"Tying {rope_id} to invalid target should fail"
    
    # State should remain unchanged
    assert rope_object.state.get('is_tied', False) == original_tie_state, \
        f"{rope_id} tie state should remain unchanged"
    
    # Error message should indicate can't tie to target
    assert "can't tie" in result.message.lower(), \
        "Error message should indicate can't tie to that target"


@settings(max_examples=100)
@given(st.data())
def test_tie_fails_without_rope_in_inventory(data):
    """
    For any rope-like object, attempting to tie without rope in inventory should fail.
    
    **Validates: Requirements 3.6**
    
    This property ensures that:
    1. Must have rope in inventory to tie
    2. State remains unchanged
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid rope and target scenario
    room_id, rope_id, target_id, rope_object, target_object = data.draw(rope_and_target_scenario(world))
    
    # Add objects to world data
    world.objects[rope_id] = rope_object
    world.objects[target_id] = target_object
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add target to room
    room = world.get_room(room_id)
    if target_id not in room.items:
        room.items.append(target_id)
    
    # Do NOT add rope to inventory
    
    # Original state
    original_tie_state = rope_object.state.get('is_tied', False)
    
    # Attempt to tie without rope
    result = engine.handle_tie(rope_id, target_id, state)
    
    # Should fail
    assert result.success is False, \
        f"Tying {rope_id} without it in inventory should fail"
    
    # State should remain unchanged
    assert rope_object.state.get('is_tied', False) == original_tie_state, \
        f"{rope_id} tie state should remain unchanged"
    
    # Error message should indicate don't have rope
    assert "don't have" in result.message.lower(), \
        "Error message should indicate player doesn't have the rope"


@settings(max_examples=100)
@given(st.data())
def test_tie_fails_for_non_rope_object(data):
    """
    For any non-rope object, attempting to tie should fail.
    
    **Validates: Requirements 3.6**
    
    This property ensures that:
    1. Only rope-like objects can be tied
    2. State remains unchanged
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a room
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    # Create a non-rope object
    non_rope_names = ["book", "lamp", "sword", "shield", "bottle"]
    object_id = data.draw(st.sampled_from(non_rope_names))
    
    non_rope_object = GameObject(
        id=object_id,
        name=object_id,
        name_spooky=f"cursed {object_id}",
        type="object",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={
            "is_rope": False,
            "can_tie": False
        },
        interactions=[]
    )
    
    # Create a target
    target_id = "test_target"
    target_object = GameObject(
        id=target_id,
        name=target_id,
        name_spooky=f"ancient {target_id}",
        type="object",
        is_takeable=False,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={
            "can_be_tied_to": True,
            "tied_objects": []
        },
        interactions=[]
    )
    
    # Add objects to world data
    world.objects[object_id] = non_rope_object
    world.objects[target_id] = target_object
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add target to room
    room = world.get_room(room_id)
    if target_id not in room.items:
        room.items.append(target_id)
    
    # Add non-rope object to inventory
    state.add_to_inventory(object_id)
    
    # Attempt to tie non-rope object
    result = engine.handle_tie(object_id, target_id, state)
    
    # Should fail
    assert result.success is False, \
        f"Tying non-rope object {object_id} should fail"
    
    # Error message should indicate can't tie
    assert "can't tie" in result.message.lower(), \
        "Error message should indicate object can't be tied"


@settings(max_examples=100)
@given(st.data())
def test_untie_fails_for_non_rope_object(data):
    """
    For any non-rope object, attempting to untie should fail.
    
    **Validates: Requirements 3.6**
    
    This property ensures that:
    1. Only rope-like objects can be untied
    2. State remains unchanged
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a room with objects
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    room = world.get_room(room_id)
    
    # Find a non-rope object in the room
    non_rope_objects = []
    for item_id in room.items:
        try:
            obj = world.get_object(item_id)
            if not obj.state.get('is_rope', False):
                non_rope_objects.append(item_id)
        except ValueError:
            continue
    
    # Skip if no non-rope objects
    if not non_rope_objects:
        assume(False)
    
    object_id = data.draw(st.sampled_from(non_rope_objects))
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add non-rope object to inventory
    state.add_to_inventory(object_id)
    
    # Attempt to untie non-rope object
    result = engine.handle_untie(object_id, state)
    
    # Should fail
    assert result.success is False, \
        f"Untying non-rope object {object_id} should fail"
    
    # Error message should indicate can't untie
    assert "can't untie" in result.message.lower(), \
        "Error message should indicate object can't be untied"


@settings(max_examples=100)
@given(st.data())
def test_tie_fails_for_absent_target(data):
    """
    For any target not in the current room, tying should fail.
    
    **Validates: Requirements 3.6**
    
    This property ensures that:
    1. Can only tie to targets that are present
    2. State remains unchanged
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid rope scenario
    room_id, rope_id, target_id, rope_object, target_object = data.draw(rope_and_target_scenario(world))
    
    # Add rope to world data
    world.objects[rope_id] = rope_object
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add rope to inventory
    state.add_to_inventory(rope_id)
    
    # Use a target ID that doesn't exist in the room
    absent_target_id = "nonexistent_target_xyz"
    
    # Attempt to tie to absent target
    result = engine.handle_tie(rope_id, absent_target_id, state)
    
    # Should fail
    assert result.success is False, \
        "Tying to absent target should fail"
    
    # Error message should indicate target not present
    assert "don't see" in result.message.lower(), \
        "Error message should indicate target is not present"
