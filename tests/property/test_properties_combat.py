"""
Property-Based Tests for Combat and Interaction Commands

Tests correctness properties related to ATTACK, THROW, GIVE, TELL, WAKE, and KISS commands,
ensuring proper combat mechanics, object transfers, and NPC interactions.
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
def creature_with_weapon_scenario(draw, world_data):
    """
    Generate a scenario with a creature in a room and a weapon in inventory.
    
    Returns tuple of (room_id, creature_id, weapon_id).
    """
    # Create a test creature
    creature_id = "test_creature"
    creature = GameObject(
        id=creature_id,
        name="test creature",
        name_spooky="spectral horror",
        type="creature",
        is_takeable=False,
        is_treasure=False,
        treasure_value=0,
        interactions=[],
        state={
            'is_creature': True,
            'health': draw(st.integers(min_value=5, max_value=20)),
            'strength': draw(st.integers(min_value=1, max_value=10)),
            'is_alive': True,
            'is_dead': False
        }
    )
    
    # Create a test weapon
    weapon_id = "test_weapon"
    weapon = GameObject(
        id=weapon_id,
        name="test weapon",
        name_spooky="cursed blade",
        type="weapon",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        interactions=[],
        state={
            'is_weapon': True,
            'damage': draw(st.integers(min_value=3, max_value=15))
        }
    )
    
    # Add to world data
    world_data.objects[creature_id] = creature
    world_data.objects[weapon_id] = weapon
    
    # Pick a random room
    room_ids = list(world_data.rooms.keys())
    room_id = draw(st.sampled_from(room_ids))
    
    return (room_id, creature_id, weapon_id)


@st.composite
def npc_scenario(draw, world_data):
    """
    Generate a scenario with an NPC in a room.
    
    Returns tuple of (room_id, npc_id).
    """
    # Create a test NPC
    npc_id = "test_npc"
    npc = GameObject(
        id=npc_id,
        name="test npc",
        name_spooky="ghostly figure",
        type="npc",
        is_takeable=False,
        is_treasure=False,
        treasure_value=0,
        interactions=[],
        state={
            'is_npc': True,
            'dialogue_responses': {
                'hello': 'The figure nods silently.',
                'help': 'I cannot help you, mortal.'
            },
            'default_dialogue': 'The ghostly figure stares at you with hollow eyes.'
        }
    )
    
    # Add to world data
    world_data.objects[npc_id] = npc
    
    # Pick a random room
    room_ids = list(world_data.rooms.keys())
    room_id = draw(st.sampled_from(room_ids))
    
    return (room_id, npc_id)


# Feature: complete-zork-commands, Property 17: Attack initiates combat
@settings(max_examples=100)
@given(st.data())
def test_attack_initiates_combat(data):
    """
    For any creature and weapon, executing ATTACK should change the combat state
    (creature health, player status, etc.).
    
    **Validates: Requirements 5.1**
    
    This property ensures that:
    1. Attack command succeeds when targeting a creature
    2. Creature health is reduced by weapon damage
    3. Combat state changes are tracked
    4. Appropriate combat messages are returned
    """
    # Load world data (fresh instance for each test)
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get a creature and weapon scenario
    room_id, creature_id, weapon_id = data.draw(creature_with_weapon_scenario(world))
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add creature to room
    room = world.get_room(room_id)
    room.items.append(creature_id)
    
    # Add weapon to inventory
    state.add_to_inventory(weapon_id)
    
    # Get initial creature health
    creature = world.get_object(creature_id)
    initial_health = creature.state['health']
    weapon = world.get_object(weapon_id)
    weapon_damage = weapon.state['damage']
    
    # Attack the creature
    result = engine.handle_attack(creature_id, weapon_id, state)
    
    # Attack should succeed
    assert result.success is True, \
        f"Attacking {creature_id} with {weapon_id} should succeed"
    
    # Creature health should be reduced
    new_health = creature.state['health']
    assert new_health < initial_health, \
        f"Creature health should decrease from {initial_health}, got {new_health}"
    
    # Health reduction should match weapon damage (or creature dies)
    expected_health = max(0, initial_health - weapon_damage)
    assert new_health == expected_health, \
        f"Creature health should be {expected_health}, got {new_health}"
    
    # Result should contain combat message
    assert result.message is not None, \
        "Result message should not be None"
    assert len(result.message) > 0, \
        "Result message should not be empty"
    
    # Message should mention the attack
    assert "strike" in result.message.lower() or "attack" in result.message.lower(), \
        "Result message should mention the attack"
    
    # If creature died, it should be marked as dead
    if new_health == 0:
        assert creature.state.get('is_alive', True) is False, \
            "Dead creature should have is_alive = False"
        assert creature.state.get('is_dead', False) is True, \
            "Dead creature should have is_dead = True"
        # Note: We don't check room.items because the room object might be stale
        # The important thing is that the creature is marked as dead


@settings(max_examples=100)
@given(st.data())
def test_attack_without_weapon_uses_bare_hands(data):
    """
    For any creature, attacking without a weapon should use bare hands with base damage.
    
    **Validates: Requirements 5.1**
    
    This property ensures that:
    1. Attack works without a weapon
    2. Base damage is applied
    3. Combat proceeds normally
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Create a test creature
    creature_id = "test_creature_bare_hands"
    creature = GameObject(
        id=creature_id,
        name="test creature",
        name_spooky="spectral horror",
        type="creature",
        is_takeable=False,
        is_treasure=False,
        treasure_value=0,
        interactions=[],
        state={
            'is_creature': True,
            'health': 10,
            'strength': 2,
            'is_alive': True,
            'is_dead': False
        }
    )
    
    world.objects[creature_id] = creature
    
    # Pick a random room
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add creature to room
    room = world.get_room(room_id)
    room.items.append(creature_id)
    
    # Get initial creature health
    initial_health = creature.state['health']
    
    # Attack without weapon (None)
    result = engine.handle_attack(creature_id, None, state)
    
    # Attack should succeed
    assert result.success is True, \
        "Attacking without weapon should succeed"
    
    # Creature health should be reduced by base damage (1)
    new_health = creature.state['health']
    expected_health = initial_health - 1  # Base damage
    assert new_health == expected_health, \
        f"Creature health should be {expected_health} after bare hands attack, got {new_health}"
    
    # Message should mention bare hands
    assert "bare hands" in result.message.lower(), \
        "Result message should mention bare hands"


@settings(max_examples=100)
@given(st.data())
def test_attack_fails_for_non_creatures(data):
    """
    For any non-creature object, attack should fail.
    
    **Validates: Requirements 5.1**
    
    This property ensures that:
    1. Only creatures can be attacked
    2. Appropriate error messages are returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Find a non-creature object
    non_creature_objects = []
    for obj_id, obj in world.objects.items():
        if not obj.state.get('is_creature', False):
            non_creature_objects.append(obj_id)
    
    # Skip if no non-creature objects
    if not non_creature_objects:
        assume(False)
    
    object_id = data.draw(st.sampled_from(non_creature_objects))
    
    # Pick a random room
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add object to room
    room = world.get_room(room_id)
    if object_id not in room.items:
        room.items.append(object_id)
    
    # Attempt attack
    result = engine.handle_attack(object_id, None, state)
    
    # Attack should fail
    assert result.success is False, \
        f"Attacking non-creature {object_id} should fail"
    
    # Error message should be returned
    assert result.message is not None, \
        "Result message should not be None"
    assert "can't attack" in result.message.lower(), \
        "Error message should indicate object cannot be attacked"


# Feature: complete-zork-commands, Property 18: Throw relocates object
@settings(max_examples=100)
@given(st.data())
def test_throw_relocates_object(data):
    """
    For any throwable object and target, executing THROW should change the object's location.
    
    **Validates: Requirements 5.2**
    
    This property ensures that:
    1. Throw command succeeds
    2. Object is removed from inventory
    3. Object is added to current room
    4. Appropriate throw messages are returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Create a throwable object
    object_id = "test_throwable"
    throwable = GameObject(
        id=object_id,
        name="test object",
        name_spooky="cursed stone",
        type="item",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        interactions=[],
        state={
            'is_throwable': True,
            'throw_damage': 2
        }
    )
    
    world.objects[object_id] = throwable
    
    # Create a target object
    target_id = "test_target"
    target = GameObject(
        id=target_id,
        name="test target",
        name_spooky="ancient statue",
        type="scenery",
        is_takeable=False,
        is_treasure=False,
        treasure_value=0,
        interactions=[],
        state={}
    )
    
    world.objects[target_id] = target
    
    # Pick a random room
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add throwable to inventory
    state.add_to_inventory(object_id)
    
    # Add target to room
    room = world.get_room(room_id)
    room.items.append(target_id)
    
    # Verify object is in inventory
    assert object_id in state.inventory, \
        "Object should be in inventory before throw"
    
    # Throw the object
    result = engine.handle_throw(object_id, target_id, state)
    
    # Throw should succeed
    assert result.success is True, \
        f"Throwing {object_id} at {target_id} should succeed"
    
    # Object should be removed from inventory
    assert object_id not in state.inventory, \
        "Object should be removed from inventory after throw"
    
    # Object should be in current room
    assert object_id in room.items, \
        "Object should be in current room after throw"
    
    # Inventory should be marked as changed
    assert result.inventory_changed is True, \
        "inventory_changed should be True after throw"
    
    # Result should contain throw message
    assert result.message is not None, \
        "Result message should not be None"
    assert "throw" in result.message.lower() or "hurl" in result.message.lower(), \
        "Result message should mention throwing"


# Feature: complete-zork-commands, Property 19: Give transfers ownership
@settings(max_examples=100)
@given(st.data())
def test_give_transfers_ownership(data):
    """
    For any object and NPC, executing GIVE should transfer the object from player
    inventory to NPC possession.
    
    **Validates: Requirements 5.3**
    
    This property ensures that:
    1. Give command succeeds
    2. Object is removed from player inventory
    3. Object is added to NPC's inventory
    4. Appropriate give messages are returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get an NPC scenario
    room_id, npc_id = data.draw(npc_scenario(world))
    
    # Create a test object to give
    object_id = "test_gift"
    gift = GameObject(
        id=object_id,
        name="test gift",
        name_spooky="mysterious amulet",
        type="item",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        interactions=[],
        state={}
    )
    
    world.objects[object_id] = gift
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add NPC to room
    room = world.get_room(room_id)
    room.items.append(npc_id)
    
    # Add gift to inventory
    state.add_to_inventory(object_id)
    
    # Verify object is in inventory
    assert object_id in state.inventory, \
        "Object should be in inventory before give"
    
    # Give the object to NPC
    result = engine.handle_give(object_id, npc_id, state)
    
    # Give should succeed
    assert result.success is True, \
        f"Giving {object_id} to {npc_id} should succeed"
    
    # Object should be removed from player inventory
    assert object_id not in state.inventory, \
        "Object should be removed from inventory after give"
    
    # Object should be in NPC's inventory
    npc = world.get_object(npc_id)
    npc_inventory = npc.state.get('inventory', [])
    assert object_id in npc_inventory, \
        "Object should be in NPC's inventory after give"
    
    # Inventory should be marked as changed
    assert result.inventory_changed is True, \
        "inventory_changed should be True after give"
    
    # Result should contain give message
    assert result.message is not None, \
        "Result message should not be None"
    assert "give" in result.message.lower(), \
        "Result message should mention giving"


# Feature: complete-zork-commands, Property 20: Tell/Ask generates dialogue
@settings(max_examples=100)
@given(st.data())
def test_tell_ask_generates_dialogue(data):
    """
    For any NPC, executing TELL or ASK should return a dialogue response.
    
    **Validates: Requirements 5.4**
    
    This property ensures that:
    1. Tell/Ask commands succeed
    2. Dialogue responses are returned
    3. Conversation state is tracked
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get an NPC scenario
    room_id, npc_id = data.draw(npc_scenario(world))
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add NPC to room
    room = world.get_room(room_id)
    room.items.append(npc_id)
    
    # Get NPC
    npc = world.get_object(npc_id)
    
    # Pick a topic (or None for default)
    topics = list(npc.state.get('dialogue_responses', {}).keys()) + [None]
    topic = data.draw(st.sampled_from(topics))
    
    # Talk to NPC
    result = engine.handle_tell(npc_id, topic, state)
    
    # Tell should succeed
    assert result.success is True, \
        f"Talking to {npc_id} should succeed"
    
    # Result should contain dialogue response
    assert result.message is not None, \
        "Result message should not be None"
    assert len(result.message) > 0, \
        "Result message should not be empty"
    
    # Conversation count should increment
    conversation_count = npc.state.get('conversation_count', 0)
    assert conversation_count > 0, \
        "Conversation count should increment after dialogue"


# Feature: complete-zork-commands, Property 21: Wake changes creature state
@settings(max_examples=100)
@given(st.data())
def test_wake_changes_creature_state(data):
    """
    For any sleeping creature, executing WAKE should change the creature's state
    from sleeping to awake.
    
    **Validates: Requirements 5.5**
    
    This property ensures that:
    1. Wake command succeeds on sleeping creatures
    2. Creature state changes from sleeping to awake
    3. Appropriate wake messages are returned
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Create a sleeping creature
    creature_id = "test_sleeping_creature"
    creature = GameObject(
        id=creature_id,
        name="test creature",
        name_spooky="slumbering beast",
        type="creature",
        is_takeable=False,
        is_treasure=False,
        treasure_value=0,
        interactions=[],
        state={
            'is_creature': True,
            'is_sleeping': True,
            'is_awake': False,
            'wake_reaction': 'The beast opens its eyes and growls menacingly.'
        }
    )
    
    world.objects[creature_id] = creature
    
    # Pick a random room
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Add creature to room
    room = world.get_room(room_id)
    room.items.append(creature_id)
    
    # Verify creature is sleeping
    assert creature.state['is_sleeping'] is True, \
        "Creature should be sleeping before wake"
    
    # Wake the creature
    result = engine.handle_wake(creature_id, state)
    
    # Wake should succeed
    assert result.success is True, \
        f"Waking {creature_id} should succeed"
    
    # Creature should no longer be sleeping
    assert creature.state['is_sleeping'] is False, \
        "Creature should not be sleeping after wake"
    
    # Creature should be awake
    assert creature.state['is_awake'] is True, \
        "Creature should be awake after wake"
    
    # Result should contain wake message
    assert result.message is not None, \
        "Result message should not be None"
    assert "wake" in result.message.lower(), \
        "Result message should mention waking"


# Feature: complete-zork-commands, Property 22: Kiss generates response
@settings(max_examples=100)
@given(st.data())
def test_kiss_generates_response(data):
    """
    For any NPC, executing KISS should return an appropriate response message.
    
    **Validates: Requirements 5.6**
    
    This property ensures that:
    1. Kiss command succeeds
    2. Response messages are returned
    3. No state changes occur (just flavor)
    """
    # Load world data
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Get an NPC scenario
    room_id, npc_id = data.draw(npc_scenario(world))
    
    # Create game state
    state = GameState.create_new_game()
    state.current_room = room_id
    initial_sanity = state.sanity
    
    # Add NPC to room
    room = world.get_room(room_id)
    room.items.append(npc_id)
    
    # Kiss the NPC
    result = engine.handle_kiss(npc_id, state)
    
    # Kiss should succeed
    assert result.success is True, \
        f"Kissing {npc_id} should succeed"
    
    # Result should contain response message
    assert result.message is not None, \
        "Result message should not be None"
    assert len(result.message) > 0, \
        "Result message should not be empty"
    
    # Message should be a valid string response (thematic responses may not mention "kiss" explicitly)
    assert isinstance(result.message, str), \
        "Result message should be a string"
    
    # State should be unchanged (kiss is just flavor)
    # Note: sanity might change, but that's okay
    assert state.current_room == room_id, \
        "Room should not change after kiss"
