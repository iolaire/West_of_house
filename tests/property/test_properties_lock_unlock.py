"""
Property-Based Tests for LOCK and UNLOCK Commands

Tests correctness properties related to the LOCK and UNLOCK commands,
ensuring round-trip consistency and proper state updates.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler'))

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
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    return world


@pytest.fixture(scope="module")
def game_engine(world_data):
    """Create game engine instance."""
    return GameEngine(world_data)


# Custom strategies for generating test data
@st.composite
def lockable_object_scenario(draw, world_data):
    """
    Generate a valid room with a lockable object and matching key.
    
    Creates a test lockable object and key, places them in a random room.
    Returns tuple of (room_id, object_id, key_id, lockable_object, key_object).
    """
    # Get all room IDs
    room_ids = list(world_data.rooms.keys())
    room_id = draw(st.sampled_from(room_ids))
    
    # Generate lockable object properties
    lockable_names = ["chest", "door", "gate", "box", "safe", "grate"]
    object_id = draw(st.sampled_from(lockable_names))
    
    # Generate key name
    key_names = ["key", "brass_key", "skeleton_key", "iron_key"]
    key_id = draw(st.sampled_from(key_names))
    
    # Create a lockable object
    lockable_object = GameObject(
        id=object_id,
        name=object_id,
        name_spooky=f"cursed {object_id}",
        type="object",
        is_takeable=False,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={
            "is_lockable": True,
            "is_locked": False,
            "required_key": key_id
        },
        interactions=[]
    )
    
    # Create a key object
    key_object = GameObject(
        id=key_id,
        name=key_id,
        name_spooky=f"ancient {key_id}",
        type="tool",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={},
        interactions=[]
    )
    
    return (room_id, object_id, key_id, lockable_object, key_object)


# Feature: complete-zork-commands, Property 5: Lock/Unlock inverse operations
@settings(max_examples=100)
@given(st.data())
def test_lock_unlock_round_trip(data):
    """
    For any lockable object and appropriate key, locking then unlocking should
    return the object to its original unlocked state (round-trip property).
    
    **Validates: Requirements 3.3**
    
    This property ensures that:
    1. LOCK changes object state to locked
    2. UNLOCK changes object state back to unlocked
    3. Round-trip preserves lock state consistency
    4. Game state is updated correctly
    """
    # Load world data (fresh instance for each test)
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid lockable object scenario
    room_id, object_id, key_id, lockable_object, key_object = data.draw(lockable_object_scenario(world))
    
    # Add objects to world data
    world.objects[object_id] = lockable_object
    world.objects[key_id] = key_object
    
    # Create game state in the room with the lockable object
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add lockable object to room
    room = world.get_room(room_id)
    if object_id not in room.items:
        room.items.append(object_id)
    
    # Add key to inventory
    if key_id not in state.inventory:
        state.add_to_inventory(key_id)
    
    # Original state: unlocked
    original_lock_state = lockable_object.state.get('is_locked', False)
    assert original_lock_state is False, "Should start unlocked"
    
    # Lock the object
    lock_result = engine.handle_lock(object_id, key_id, state)
    
    # Lock should succeed
    assert lock_result.success is True, \
        f"Locking {object_id} with {key_id} should succeed"
    
    # Should now be locked
    assert lockable_object.state.get('is_locked', False) is True, \
        f"{object_id} should be locked"
    
    # Unlock the object
    unlock_result = engine.handle_unlock(object_id, key_id, state)
    
    # Unlock should succeed
    assert unlock_result.success is True, \
        f"Unlocking {object_id} with {key_id} should succeed"
    
    # Should be back to original state (unlocked)
    assert lockable_object.state.get('is_locked', False) == original_lock_state, \
        f"Round-trip should return to original lock state (False), got {lockable_object.state.get('is_locked', False)}"
    
    # Both operations should return messages
    assert lock_result.message is not None and len(lock_result.message) > 0, \
        "Lock result should contain a message"
    assert unlock_result.message is not None and len(unlock_result.message) > 0, \
        "Unlock result should contain a message"
    
    # Messages should mention the object and key
    assert object_id in lock_result.message.lower(), \
        f"Lock message should mention {object_id}"
    assert key_id in lock_result.message.lower(), \
        f"Lock message should mention {key_id}"
    assert object_id in unlock_result.message.lower(), \
        f"Unlock message should mention {object_id}"
    assert key_id in unlock_result.message.lower(), \
        f"Unlock message should mention {key_id}"


@settings(max_examples=100)
@given(st.data())
def test_lock_fails_when_already_locked(data):
    """
    For any lockable object, attempting to lock when already locked should fail.
    
    **Validates: Requirements 3.3**
    
    This property ensures that:
    1. Cannot lock an already locked object
    2. State remains unchanged on failed lock
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid lockable object scenario
    room_id, object_id, key_id, lockable_object, key_object = data.draw(lockable_object_scenario(world))
    
    # Set object to already locked
    lockable_object.state['is_locked'] = True
    
    # Add objects to world data
    world.objects[object_id] = lockable_object
    world.objects[key_id] = key_object
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add lockable object to room
    room = world.get_room(room_id)
    if object_id not in room.items:
        room.items.append(object_id)
    
    # Add key to inventory
    if key_id not in state.inventory:
        state.add_to_inventory(key_id)
    
    # Attempt to lock already locked object
    result = engine.handle_lock(object_id, key_id, state)
    
    # Should fail
    assert result.success is False, \
        "Locking already locked object should fail"
    
    # State should remain locked
    assert lockable_object.state.get('is_locked', False) is True, \
        f"{object_id} should remain locked"
    
    # Error message should indicate already locked
    assert "already locked" in result.message.lower(), \
        "Error message should indicate object is already locked"


@settings(max_examples=100)
@given(st.data())
def test_unlock_fails_when_already_unlocked(data):
    """
    For any lockable object, attempting to unlock when already unlocked should fail.
    
    **Validates: Requirements 3.3**
    
    This property ensures that:
    1. Cannot unlock an already unlocked object
    2. State remains unchanged on failed unlock
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid lockable object scenario
    room_id, object_id, key_id, lockable_object, key_object = data.draw(lockable_object_scenario(world))
    
    # Ensure object is unlocked
    lockable_object.state['is_locked'] = False
    
    # Add objects to world data
    world.objects[object_id] = lockable_object
    world.objects[key_id] = key_object
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add lockable object to room
    room = world.get_room(room_id)
    if object_id not in room.items:
        room.items.append(object_id)
    
    # Add key to inventory
    if key_id not in state.inventory:
        state.add_to_inventory(key_id)
    
    # Attempt to unlock already unlocked object
    result = engine.handle_unlock(object_id, key_id, state)
    
    # Should fail
    assert result.success is False, \
        "Unlocking already unlocked object should fail"
    
    # State should remain unlocked
    assert lockable_object.state.get('is_locked', False) is False, \
        f"{object_id} should remain unlocked"
    
    # Error message should indicate already unlocked
    assert "already unlocked" in result.message.lower(), \
        "Error message should indicate object is already unlocked"


@settings(max_examples=100)
@given(st.data())
def test_lock_fails_with_wrong_key(data):
    """
    For any lockable object, attempting to lock with wrong key should fail.
    
    **Validates: Requirements 3.3**
    
    This property ensures that:
    1. Only the correct key can lock an object
    2. State remains unchanged with wrong key
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid lockable object scenario
    room_id, object_id, correct_key_id, lockable_object, correct_key = data.draw(lockable_object_scenario(world))
    
    # Create a wrong key
    wrong_key_id = "wrong_key"
    wrong_key = GameObject(
        id=wrong_key_id,
        name=wrong_key_id,
        name_spooky=f"mysterious {wrong_key_id}",
        type="tool",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={},
        interactions=[]
    )
    
    # Add objects to world data
    world.objects[object_id] = lockable_object
    world.objects[correct_key_id] = correct_key
    world.objects[wrong_key_id] = wrong_key
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add lockable object to room
    room = world.get_room(room_id)
    if object_id not in room.items:
        room.items.append(object_id)
    
    # Add wrong key to inventory
    if wrong_key_id not in state.inventory:
        state.add_to_inventory(wrong_key_id)
    
    # Original state
    original_lock_state = lockable_object.state.get('is_locked', False)
    
    # Attempt to lock with wrong key
    result = engine.handle_lock(object_id, wrong_key_id, state)
    
    # Should fail
    assert result.success is False, \
        f"Locking {object_id} with wrong key should fail"
    
    # State should remain unchanged
    assert lockable_object.state.get('is_locked', False) == original_lock_state, \
        f"{object_id} lock state should remain unchanged"
    
    # Error message should indicate wrong key
    assert "doesn't fit" in result.message.lower(), \
        "Error message should indicate key doesn't fit"


@settings(max_examples=100)
@given(st.data())
def test_unlock_fails_with_wrong_key(data):
    """
    For any lockable object, attempting to unlock with wrong key should fail.
    
    **Validates: Requirements 3.3**
    
    This property ensures that:
    1. Only the correct key can unlock an object
    2. State remains unchanged with wrong key
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid lockable object scenario
    room_id, object_id, correct_key_id, lockable_object, correct_key = data.draw(lockable_object_scenario(world))
    
    # Set object to locked
    lockable_object.state['is_locked'] = True
    
    # Create a wrong key
    wrong_key_id = "wrong_key"
    wrong_key = GameObject(
        id=wrong_key_id,
        name=wrong_key_id,
        name_spooky=f"mysterious {wrong_key_id}",
        type="tool",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={},
        interactions=[]
    )
    
    # Add objects to world data
    world.objects[object_id] = lockable_object
    world.objects[correct_key_id] = correct_key
    world.objects[wrong_key_id] = wrong_key
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add lockable object to room
    room = world.get_room(room_id)
    if object_id not in room.items:
        room.items.append(object_id)
    
    # Add wrong key to inventory
    if wrong_key_id not in state.inventory:
        state.add_to_inventory(wrong_key_id)
    
    # Attempt to unlock with wrong key
    result = engine.handle_unlock(object_id, wrong_key_id, state)
    
    # Should fail
    assert result.success is False, \
        f"Unlocking {object_id} with wrong key should fail"
    
    # State should remain locked
    assert lockable_object.state.get('is_locked', False) is True, \
        f"{object_id} should remain locked"
    
    # Error message should indicate wrong key
    assert "doesn't fit" in result.message.lower(), \
        "Error message should indicate key doesn't fit"


@settings(max_examples=100)
@given(st.data())
def test_lock_fails_without_key_in_inventory(data):
    """
    For any lockable object, attempting to lock without key in inventory should fail.
    
    **Validates: Requirements 3.3**
    
    This property ensures that:
    1. Must have key in inventory to lock
    2. State remains unchanged
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid lockable object scenario
    room_id, object_id, key_id, lockable_object, key_object = data.draw(lockable_object_scenario(world))
    
    # Add objects to world data
    world.objects[object_id] = lockable_object
    world.objects[key_id] = key_object
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add lockable object to room
    room = world.get_room(room_id)
    if object_id not in room.items:
        room.items.append(object_id)
    
    # Do NOT add key to inventory
    
    # Original state
    original_lock_state = lockable_object.state.get('is_locked', False)
    
    # Attempt to lock without key
    result = engine.handle_lock(object_id, key_id, state)
    
    # Should fail
    assert result.success is False, \
        f"Locking {object_id} without key in inventory should fail"
    
    # State should remain unchanged
    assert lockable_object.state.get('is_locked', False) == original_lock_state, \
        f"{object_id} lock state should remain unchanged"
    
    # Error message should indicate don't have key
    assert "don't have" in result.message.lower(), \
        "Error message should indicate player doesn't have the key"


@settings(max_examples=100)
@given(st.data())
def test_unlock_fails_without_key_in_inventory(data):
    """
    For any lockable object, attempting to unlock without key in inventory should fail.
    
    **Validates: Requirements 3.3**
    
    This property ensures that:
    1. Must have key in inventory to unlock
    2. State remains unchanged
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid lockable object scenario
    room_id, object_id, key_id, lockable_object, key_object = data.draw(lockable_object_scenario(world))
    
    # Set object to locked
    lockable_object.state['is_locked'] = True
    
    # Add objects to world data
    world.objects[object_id] = lockable_object
    world.objects[key_id] = key_object
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add lockable object to room
    room = world.get_room(room_id)
    if object_id not in room.items:
        room.items.append(object_id)
    
    # Do NOT add key to inventory
    
    # Attempt to unlock without key
    result = engine.handle_unlock(object_id, key_id, state)
    
    # Should fail
    assert result.success is False, \
        f"Unlocking {object_id} without key in inventory should fail"
    
    # State should remain locked
    assert lockable_object.state.get('is_locked', False) is True, \
        f"{object_id} should remain locked"
    
    # Error message should indicate don't have key
    assert "don't have" in result.message.lower(), \
        "Error message should indicate player doesn't have the key"


@settings(max_examples=100)
@given(st.data())
def test_lock_fails_for_non_lockable_object(data):
    """
    For any non-lockable object, attempting to lock should fail.
    
    **Validates: Requirements 3.3**
    
    This property ensures that:
    1. Only lockable objects can be locked
    2. State remains unchanged
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a room with objects
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    room = world.get_room(room_id)
    
    # Find a non-lockable object in the room
    non_lockable_objects = []
    for item_id in room.items:
        try:
            obj = world.get_object(item_id)
            if not obj.state.get('is_lockable', False):
                non_lockable_objects.append(item_id)
        except ValueError:
            continue
    
    # Skip if no non-lockable objects
    if not non_lockable_objects:
        assume(False)
    
    object_id = data.draw(st.sampled_from(non_lockable_objects))
    
    # Create a key
    key_id = "test_key"
    key_object = GameObject(
        id=key_id,
        name=key_id,
        name_spooky=f"ancient {key_id}",
        type="tool",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={},
        interactions=[]
    )
    world.objects[key_id] = key_object
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add key to inventory
    state.add_to_inventory(key_id)
    
    # Attempt to lock non-lockable object
    result = engine.handle_lock(object_id, key_id, state)
    
    # Should fail
    assert result.success is False, \
        f"Locking non-lockable object {object_id} should fail"
    
    # Error message should indicate can't lock
    assert "cannot be locked" in result.message.lower(), \
        "Error message should indicate object cannot be locked"


@settings(max_examples=100)
@given(st.data())
def test_lock_fails_for_absent_object(data):
    """
    For any object not in the current room, locking should fail.
    
    **Validates: Requirements 3.3**
    
    This property ensures that:
    1. Can only lock objects that are present
    2. State remains unchanged
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a room
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Create a key
    key_id = "test_key"
    key_object = GameObject(
        id=key_id,
        name=key_id,
        name_spooky=f"ancient {key_id}",
        type="tool",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={},
        interactions=[]
    )
    world.objects[key_id] = key_object
    state.add_to_inventory(key_id)
    
    # Use an object ID that doesn't exist in the room
    absent_object_id = "nonexistent_object_xyz"
    
    # Attempt to lock absent object
    result = engine.handle_lock(absent_object_id, key_id, state)
    
    # Should fail
    assert result.success is False, \
        "Locking absent object should fail"
    
    # Error message should indicate object not present
    assert "don't see" in result.message.lower(), \
        "Error message should indicate object is not present"
