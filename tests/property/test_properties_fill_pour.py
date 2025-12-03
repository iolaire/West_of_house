"""
Property-Based Tests for FILL and POUR Commands

Tests correctness properties related to the FILL and POUR commands,
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
def container_and_source_scenario(draw, world_data):
    """
    Generate a valid room with a container and a liquid source.
    
    Creates a test container and liquid source, places them in a random room.
    Returns tuple of (room_id, container_id, source_id, container_object, source_object).
    """
    # Get all room IDs
    room_ids = list(world_data.rooms.keys())
    room_id = draw(st.sampled_from(room_ids))
    
    # Generate container names
    container_names = ["bottle", "flask", "cup", "bucket", "jug", "vial"]
    container_id = draw(st.sampled_from(container_names))
    
    # Generate source names
    source_names = ["fountain", "well", "stream", "pool", "barrel", "tap"]
    source_id = draw(st.sampled_from(source_names))
    
    # Generate liquid type
    liquid_types = ["water", "oil", "wine", "blood", "potion"]
    liquid_type = draw(st.sampled_from(liquid_types))
    
    # Generate capacity
    capacity = draw(st.integers(min_value=50, max_value=200))
    
    # Create a container object
    container_object = GameObject(
        id=container_id,
        name=container_id,
        name_spooky=f"cursed {container_id}",
        type="container",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={
            "can_hold_liquid": True,
            "is_empty": True,
            "is_full": False,
            "liquid_level": 0,
            "liquid_capacity": capacity,
            "liquid_type": None
        },
        interactions=[]
    )
    
    # Create a liquid source object
    source_object = GameObject(
        id=source_id,
        name=source_id,
        name_spooky=f"ancient {source_id}",
        type="object",
        is_takeable=False,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={
            "has_liquid": True,
            "is_liquid_source": True,
            "liquid_type": liquid_type
        },
        interactions=[]
    )
    
    return (room_id, container_id, source_id, container_object, source_object, liquid_type, capacity)


# Feature: complete-zork-commands, Property 9: Fill/Pour inverse operations
@settings(max_examples=100)
@given(st.data())
def test_fill_pour_round_trip(data):
    """
    For any container and liquid source, filling then pouring should
    return the container to its original empty state (round-trip property).
    
    **Validates: Requirements 3.7, 3.8**
    
    This property ensures that:
    1. FILL changes container state to full
    2. POUR changes container state back to empty
    3. Round-trip preserves container state consistency
    4. Game state is updated correctly
    """
    # Load world data (fresh instance for each test)
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid container and source scenario
    room_id, container_id, source_id, container_object, source_object, liquid_type, capacity = \
        data.draw(container_and_source_scenario(world))
    
    # Add objects to world data
    world.objects[container_id] = container_object
    world.objects[source_id] = source_object
    
    # Create game state in the room with the source
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add source to room
    room = world.get_room(room_id)
    if source_id not in room.items:
        room.items.append(source_id)
    
    # Add container to inventory
    if container_id not in state.inventory:
        state.add_to_inventory(container_id)
    
    # Original state: empty
    original_is_empty = container_object.state.get('is_empty', True)
    original_is_full = container_object.state.get('is_full', False)
    original_liquid_level = container_object.state.get('liquid_level', 0)
    original_liquid_type = container_object.state.get('liquid_type', None)
    
    assert original_is_empty is True, "Should start empty"
    assert original_is_full is False, "Should not start full"
    assert original_liquid_level == 0, "Should have no liquid"
    assert original_liquid_type is None, "Should have no liquid type"
    
    # Fill the container from the source
    fill_result = engine.handle_fill(container_id, source_id, state)
    
    # Fill should succeed
    assert fill_result.success is True, \
        f"Filling {container_id} from {source_id} should succeed"
    
    # Should now be full
    assert container_object.state.get('is_empty', True) is False, \
        f"{container_id} should not be empty"
    assert container_object.state.get('is_full', False) is True, \
        f"{container_id} should be full"
    assert container_object.state.get('liquid_level', 0) == capacity, \
        f"{container_id} should have liquid level equal to capacity"
    assert container_object.state.get('liquid_type', None) == liquid_type, \
        f"{container_id} should contain {liquid_type}"
    
    # Pour the liquid out
    pour_result = engine.handle_pour(container_id, None, state)
    
    # Pour should succeed
    assert pour_result.success is True, \
        f"Pouring {container_id} should succeed"
    
    # Should be back to original state (empty)
    assert container_object.state.get('is_empty', False) == original_is_empty, \
        f"Round-trip should return to original empty state (True), got {container_object.state.get('is_empty', False)}"
    assert container_object.state.get('is_full', True) == original_is_full, \
        f"Round-trip should return to original full state (False), got {container_object.state.get('is_full', True)}"
    assert container_object.state.get('liquid_level', capacity) == original_liquid_level, \
        f"Round-trip should return to original liquid level (0), got {container_object.state.get('liquid_level', capacity)}"
    assert container_object.state.get('liquid_type', liquid_type) == original_liquid_type, \
        f"Round-trip should return to original liquid type (None), got {container_object.state.get('liquid_type', liquid_type)}"
    
    # Both operations should return messages
    assert fill_result.message is not None and len(fill_result.message) > 0, \
        "Fill result should contain a message"
    assert pour_result.message is not None and len(pour_result.message) > 0, \
        "Pour result should contain a message"
    
    # Fill message should mention the container
    assert container_id in fill_result.message.lower(), \
        f"Fill message should mention {container_id}"
    
    # Pour message should mention either the container or the liquid
    # (when pouring onto ground, message may focus on liquid rather than container)
    assert (container_id in pour_result.message.lower() or 
            liquid_type in pour_result.message.lower()), \
        f"Pour message should mention {container_id} or {liquid_type}"


@settings(max_examples=100)
@given(st.data())
def test_fill_fails_when_already_full(data):
    """
    For any container, attempting to fill when already full should fail.
    
    **Validates: Requirements 3.7**
    
    This property ensures that:
    1. Cannot fill an already full container
    2. State remains unchanged on failed fill
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid container and source scenario
    room_id, container_id, source_id, container_object, source_object, liquid_type, capacity = \
        data.draw(container_and_source_scenario(world))
    
    # Set container to already full
    container_object.state['is_full'] = True
    container_object.state['is_empty'] = False
    container_object.state['liquid_level'] = capacity
    container_object.state['liquid_type'] = liquid_type
    
    # Add objects to world data
    world.objects[container_id] = container_object
    world.objects[source_id] = source_object
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add source to room
    room = world.get_room(room_id)
    if source_id not in room.items:
        room.items.append(source_id)
    
    # Add container to inventory
    if container_id not in state.inventory:
        state.add_to_inventory(container_id)
    
    # Attempt to fill already full container
    result = engine.handle_fill(container_id, source_id, state)
    
    # Should fail
    assert result.success is False, \
        "Filling already full container should fail"
    
    # State should remain full
    assert container_object.state.get('is_full', False) is True, \
        f"{container_id} should remain full"
    
    # Error message should indicate already full
    assert "already full" in result.message.lower(), \
        "Error message should indicate container is already full"


@settings(max_examples=100)
@given(st.data())
def test_pour_fails_when_empty(data):
    """
    For any container, attempting to pour when empty should fail.
    
    **Validates: Requirements 3.8**
    
    This property ensures that:
    1. Cannot pour from an empty container
    2. State remains unchanged on failed pour
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid container and source scenario
    room_id, container_id, source_id, container_object, source_object, liquid_type, capacity = \
        data.draw(container_and_source_scenario(world))
    
    # Ensure container is empty
    container_object.state['is_empty'] = True
    container_object.state['is_full'] = False
    container_object.state['liquid_level'] = 0
    container_object.state['liquid_type'] = None
    
    # Add objects to world data
    world.objects[container_id] = container_object
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add container to inventory
    if container_id not in state.inventory:
        state.add_to_inventory(container_id)
    
    # Attempt to pour from empty container
    result = engine.handle_pour(container_id, None, state)
    
    # Should fail
    assert result.success is False, \
        "Pouring from empty container should fail"
    
    # State should remain empty
    assert container_object.state.get('is_empty', False) is True, \
        f"{container_id} should remain empty"
    
    # Error message should indicate empty
    assert "empty" in result.message.lower(), \
        "Error message should indicate container is empty"


@settings(max_examples=100)
@given(st.data())
def test_fill_fails_with_non_liquid_container(data):
    """
    For any non-liquid container, attempting to fill should fail.
    
    **Validates: Requirements 3.7**
    
    This property ensures that:
    1. Only liquid containers can be filled
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
    
    # Create a non-liquid container
    non_liquid_names = ["box", "chest", "bag", "sack"]
    container_id = data.draw(st.sampled_from(non_liquid_names))
    
    non_liquid_container = GameObject(
        id=container_id,
        name=container_id,
        name_spooky=f"cursed {container_id}",
        type="container",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        capacity=10,
        state={
            "can_hold_liquid": False,
            "is_empty": True
        },
        interactions=[]
    )
    
    # Create a liquid source
    source_id = "test_fountain"
    source_object = GameObject(
        id=source_id,
        name=source_id,
        name_spooky=f"ancient {source_id}",
        type="object",
        is_takeable=False,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={
            "has_liquid": True,
            "is_liquid_source": True,
            "liquid_type": "water"
        },
        interactions=[]
    )
    
    # Add objects to world data
    world.objects[container_id] = non_liquid_container
    world.objects[source_id] = source_object
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add source to room
    room = world.get_room(room_id)
    if source_id not in room.items:
        room.items.append(source_id)
    
    # Add non-liquid container to inventory
    state.add_to_inventory(container_id)
    
    # Attempt to fill non-liquid container
    result = engine.handle_fill(container_id, source_id, state)
    
    # Should fail
    assert result.success is False, \
        f"Filling non-liquid container {container_id} should fail"
    
    # Error message should indicate can't fill
    assert "can't fill" in result.message.lower(), \
        "Error message should indicate container can't hold liquid"


@settings(max_examples=100)
@given(st.data())
def test_fill_fails_with_non_liquid_source(data):
    """
    For any non-liquid source, attempting to fill from it should fail.
    
    **Validates: Requirements 3.7**
    
    This property ensures that:
    1. Can only fill from liquid sources
    2. State remains unchanged
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid container scenario
    room_id, container_id, _, container_object, _, _, _ = \
        data.draw(container_and_source_scenario(world))
    
    # Create a non-liquid source
    non_liquid_source_names = ["rock", "tree", "wall", "door"]
    source_id = data.draw(st.sampled_from(non_liquid_source_names))
    
    non_liquid_source = GameObject(
        id=source_id,
        name=source_id,
        name_spooky=f"ancient {source_id}",
        type="object",
        is_takeable=False,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={
            "has_liquid": False,
            "is_liquid_source": False
        },
        interactions=[]
    )
    
    # Add objects to world data
    world.objects[container_id] = container_object
    world.objects[source_id] = non_liquid_source
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add source to room
    room = world.get_room(room_id)
    if source_id not in room.items:
        room.items.append(source_id)
    
    # Add container to inventory
    state.add_to_inventory(container_id)
    
    # Attempt to fill from non-liquid source
    result = engine.handle_fill(container_id, source_id, state)
    
    # Should fail
    assert result.success is False, \
        f"Filling from non-liquid source {source_id} should fail"
    
    # Error message should indicate no liquid
    assert "no liquid" in result.message.lower(), \
        "Error message should indicate source has no liquid"


@settings(max_examples=100)
@given(st.data())
def test_pour_into_another_container(data):
    """
    For any two containers, pouring from one into another should transfer liquid.
    
    **Validates: Requirements 3.8**
    
    This property ensures that:
    1. Can pour from one container into another
    2. Source container becomes empty
    3. Target container becomes full
    4. Liquid type is preserved
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a room
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    # Generate liquid type and capacity
    liquid_types = ["water", "oil", "wine", "blood", "potion"]
    liquid_type = data.draw(st.sampled_from(liquid_types))
    capacity = data.draw(st.integers(min_value=50, max_value=200))
    
    # Create source container (full)
    source_container_id = "bottle"
    source_container = GameObject(
        id=source_container_id,
        name=source_container_id,
        name_spooky=f"cursed {source_container_id}",
        type="container",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={
            "can_hold_liquid": True,
            "is_empty": False,
            "is_full": True,
            "liquid_level": capacity,
            "liquid_capacity": capacity,
            "liquid_type": liquid_type
        },
        interactions=[]
    )
    
    # Create target container (empty)
    target_container_id = "flask"
    target_container = GameObject(
        id=target_container_id,
        name=target_container_id,
        name_spooky=f"ancient {target_container_id}",
        type="container",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        capacity=0,
        state={
            "can_hold_liquid": True,
            "is_empty": True,
            "is_full": False,
            "liquid_level": 0,
            "liquid_capacity": capacity,
            "liquid_type": None
        },
        interactions=[]
    )
    
    # Add objects to world data
    world.objects[source_container_id] = source_container
    world.objects[target_container_id] = target_container
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add both containers to inventory
    state.add_to_inventory(source_container_id)
    state.add_to_inventory(target_container_id)
    
    # Pour from source into target
    result = engine.handle_pour(source_container_id, target_container_id, state)
    
    # Should succeed
    assert result.success is True, \
        f"Pouring from {source_container_id} into {target_container_id} should succeed"
    
    # Source should be empty
    assert source_container.state.get('is_empty', False) is True, \
        f"{source_container_id} should be empty"
    assert source_container.state.get('is_full', True) is False, \
        f"{source_container_id} should not be full"
    assert source_container.state.get('liquid_level', capacity) == 0, \
        f"{source_container_id} should have no liquid"
    
    # Target should be full
    assert target_container.state.get('is_empty', True) is False, \
        f"{target_container_id} should not be empty"
    assert target_container.state.get('is_full', False) is True, \
        f"{target_container_id} should be full"
    assert target_container.state.get('liquid_level', 0) == capacity, \
        f"{target_container_id} should have liquid level equal to capacity"
    assert target_container.state.get('liquid_type', None) == liquid_type, \
        f"{target_container_id} should contain {liquid_type}"


@settings(max_examples=100)
@given(st.data())
def test_fill_fails_without_container_in_inventory(data):
    """
    For any container, attempting to fill without it in inventory should fail.
    
    **Validates: Requirements 3.7**
    
    This property ensures that:
    1. Must have container in inventory to fill
    2. State remains unchanged
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid container and source scenario
    room_id, container_id, source_id, container_object, source_object, liquid_type, capacity = \
        data.draw(container_and_source_scenario(world))
    
    # Add objects to world data
    world.objects[container_id] = container_object
    world.objects[source_id] = source_object
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add source to room
    room = world.get_room(room_id)
    if source_id not in room.items:
        room.items.append(source_id)
    
    # Do NOT add container to inventory
    
    # Original state
    original_is_empty = container_object.state.get('is_empty', True)
    
    # Attempt to fill without container
    result = engine.handle_fill(container_id, source_id, state)
    
    # Should fail
    assert result.success is False, \
        f"Filling {container_id} without it in inventory should fail"
    
    # State should remain unchanged
    assert container_object.state.get('is_empty', False) == original_is_empty, \
        f"{container_id} empty state should remain unchanged"
    
    # Error message should indicate don't have container
    assert "don't have" in result.message.lower(), \
        "Error message should indicate player doesn't have the container"


@settings(max_examples=100)
@given(st.data())
def test_pour_fails_without_container_in_inventory(data):
    """
    For any container, attempting to pour without it in inventory should fail.
    
    **Validates: Requirements 3.8**
    
    This property ensures that:
    1. Must have container in inventory to pour
    2. State remains unchanged
    3. Appropriate error message is returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a valid container scenario
    room_id, container_id, _, container_object, _, liquid_type, capacity = \
        data.draw(container_and_source_scenario(world))
    
    # Set container to full
    container_object.state['is_full'] = True
    container_object.state['is_empty'] = False
    container_object.state['liquid_level'] = capacity
    container_object.state['liquid_type'] = liquid_type
    
    # Add objects to world data
    world.objects[container_id] = container_object
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Do NOT add container to inventory
    
    # Attempt to pour without container
    result = engine.handle_pour(container_id, None, state)
    
    # Should fail
    assert result.success is False, \
        f"Pouring {container_id} without it in inventory should fail"
    
    # State should remain full
    assert container_object.state.get('is_full', False) is True, \
        f"{container_id} should remain full"
    
    # Error message should indicate don't have container
    assert "don't have" in result.message.lower(), \
        "Error message should indicate player doesn't have the container"
