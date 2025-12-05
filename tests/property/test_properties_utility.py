"""
Property-Based Tests for Utility Commands

Tests correctness properties related to BURN, CUT, DIG, INFLATE, DEFLATE, WAVE, RUB, SHAKE, and SQUEEZE commands.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler'))

import pytest
from hypothesis import given, strategies as st, settings, assume
from game_engine import GameEngine, ActionResult
from state_manager import GameState
from world_loader import WorldData, GameObject


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


@st.composite
def flammable_object_scenario(draw, world_data):
    """Generate scenario with flammable object and fire source."""
    object_id = "test_flammable"
    flammable = GameObject(
        id=object_id,
        name="test object",
        name_spooky="cursed parchment",
        type="item",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        interactions=[],
        state={'is_flammable': True}
    )
    
    fire_source_id = "test_fire_source"
    fire_source = GameObject(
        id=fire_source_id,
        name="test fire source",
        name_spooky="spectral flame",
        type="item",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        interactions=[],
        state={'is_fire_source': True}
    )
    
    world_data.objects[object_id] = flammable
    world_data.objects[fire_source_id] = fire_source
    
    room_ids = list(world_data.rooms.keys())
    room_id = draw(st.sampled_from(room_ids))
    
    return (room_id, object_id, fire_source_id)


# Feature: complete-zork-commands, Property 23: Burn destroys flammable objects
@settings(max_examples=100)
@given(st.data())
def test_burn_destroys_flammable_objects(data):
    """
    For any flammable object and fire source, BURN should destroy the object.
    
    **Validates: Requirements 6.1**
    """
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    room_id, object_id, fire_source_id = data.draw(flammable_object_scenario(world))
    
    state = GameState.create_new_game()
    state.current_room = room_id
    
    room = world.get_room(room_id)
    room.items.append(object_id)
    state.add_to_inventory(fire_source_id)
    
    assert object_id in room.items
    
    result = engine.handle_burn(object_id, fire_source_id, state)
    
    assert result.success is True
    assert object_id not in room.items
    
    game_object = world.get_object(object_id)
    assert game_object.state.get('is_burned', False) is True
    assert game_object.state.get('is_destroyed', False) is True
    
    assert result.message is not None
    assert any(word in result.message.lower() for word in ['burn', 'fire', 'ash'])


@settings(max_examples=100)
@given(st.data())
def test_burn_fails_for_non_flammable_objects(data):
    """
    For non-flammable objects, burn should fail.
    
    **Validates: Requirements 6.1**
    """
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    non_flammable_objects = [obj_id for obj_id, obj in world.objects.items() 
                             if not obj.state.get('is_flammable', False)]
    
    if not non_flammable_objects:
        assume(False)
    
    object_id = data.draw(st.sampled_from(non_flammable_objects))
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    state = GameState.create_new_game()
    state.current_room = room_id
    
    room = world.get_room(room_id)
    if object_id not in room.items:
        room.items.append(object_id)
    
    result = engine.handle_burn(object_id, None, state)
    
    assert result.success is False
    assert result.message is not None
    assert "won't burn" in result.message.lower() or "can't burn" in result.message.lower()


@st.composite
def cuttable_object_scenario(draw, world_data):
    """Generate scenario with cuttable object and cutting tool."""
    object_id = "test_cuttable"
    cuttable = GameObject(
        id=object_id,
        name="test object",
        name_spooky="cursed rope",
        type="item",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        interactions=[],
        state={'is_cuttable': True}
    )
    
    tool_id = "test_cutting_tool"
    tool = GameObject(
        id=tool_id,
        name="test tool",
        name_spooky="spectral blade",
        type="item",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        interactions=[],
        state={'is_cutting_tool': True}
    )
    
    world_data.objects[object_id] = cuttable
    world_data.objects[tool_id] = tool
    
    room_ids = list(world_data.rooms.keys())
    room_id = draw(st.sampled_from(room_ids))
    
    return (room_id, object_id, tool_id)


# Feature: complete-zork-commands, Property 24: Cut modifies objects
@settings(max_examples=100)
@given(st.data())
def test_cut_modifies_objects(data):
    """
    For any cuttable object and cutting tool, CUT should modify the object.
    
    **Validates: Requirements 6.2**
    """
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    room_id, object_id, tool_id = data.draw(cuttable_object_scenario(world))
    
    state = GameState.create_new_game()
    state.current_room = room_id
    
    room = world.get_room(room_id)
    room.items.append(object_id)
    state.add_to_inventory(tool_id)
    
    result = engine.handle_cut(object_id, tool_id, state)
    
    assert result.success is True
    
    game_object = world.get_object(object_id)
    assert game_object.state.get('is_cut', False) is True
    
    assert result.message is not None


@settings(max_examples=100)
@given(st.data())
def test_cut_fails_for_non_cuttable_objects(data):
    """
    For non-cuttable objects, cut should fail.
    
    **Validates: Requirements 6.2**
    """
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    non_cuttable_objects = [obj_id for obj_id, obj in world.objects.items() 
                            if not obj.state.get('is_cuttable', False)]
    
    if not non_cuttable_objects:
        assume(False)
    
    object_id = data.draw(st.sampled_from(non_cuttable_objects))
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    state = GameState.create_new_game()
    state.current_room = room_id
    
    room = world.get_room(room_id)
    if object_id not in room.items:
        room.items.append(object_id)
    
    result = engine.handle_cut(object_id, None, state)
    
    assert result.success is False
    assert result.message is not None
    assert "can't cut" in result.message.lower()


@st.composite
def diggable_location_scenario(draw, world_data):
    """Generate scenario with diggable location and digging tool."""
    tool_id = "test_digging_tool"
    tool = GameObject(
        id=tool_id,
        name="test tool",
        name_spooky="cursed shovel",
        type="item",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        interactions=[],
        state={'is_digging_tool': True}
    )
    
    world_data.objects[tool_id] = tool
    
    room_ids = list(world_data.rooms.keys())
    room_id = draw(st.sampled_from(room_ids))
    
    return (room_id, tool_id)


# Feature: complete-zork-commands, Property 25: Dig reveals or modifies
@settings(max_examples=100)
@given(st.data())
def test_dig_reveals_or_modifies(data):
    """
    For any diggable location and digging tool, DIG should succeed.
    
    **Validates: Requirements 6.3**
    """
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    room_id, tool_id = data.draw(diggable_location_scenario(world))
    
    state = GameState.create_new_game()
    state.current_room = room_id
    state.add_to_inventory(tool_id)
    
    # Make room diggable via flag
    state.set_flag(f"room_{room_id}_diggable", True)
    
    result = engine.handle_dig(None, tool_id, state)
    
    assert result.success is True
    assert result.message is not None
    assert "dig" in result.message.lower()


@settings(max_examples=100)
@given(st.data())
def test_dig_fails_for_non_diggable_locations(data):
    """
    For non-diggable locations, dig should fail.
    
    **Validates: Requirements 6.3**
    """
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    state = GameState.create_new_game()
    state.current_room = room_id
    
    # Ensure room is NOT diggable (don't set flag)
    
    result = engine.handle_dig(None, None, state)
    
    assert result.success is False
    assert result.message is not None
    assert "hard" in result.message.lower() or "can't dig" in result.message.lower()


@st.composite
def inflatable_object_scenario(draw, world_data):
    """Generate scenario with inflatable object."""
    object_id = "test_inflatable"
    inflatable = GameObject(
        id=object_id,
        name="test object",
        name_spooky="cursed balloon",
        type="item",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        interactions=[],
        state={'is_inflatable': True, 'is_inflated': False}
    )
    
    world_data.objects[object_id] = inflatable
    
    room_ids = list(world_data.rooms.keys())
    room_id = draw(st.sampled_from(room_ids))
    
    return (room_id, object_id)


# Feature: complete-zork-commands, Property 26: Inflate/Deflate inverse operations
@settings(max_examples=100)
@given(st.data())
def test_inflate_deflate_round_trip(data):
    """
    For any inflatable object, INFLATE then DEFLATE should return to original state.
    
    **Validates: Requirements 6.4**
    """
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    room_id, object_id = data.draw(inflatable_object_scenario(world))
    
    state = GameState.create_new_game()
    state.current_room = room_id
    state.add_to_inventory(object_id)
    
    game_object = world.get_object(object_id)
    assert game_object.state['is_inflated'] is False
    
    result = engine.handle_inflate(object_id, state)
    assert result.success is True
    assert game_object.state['is_inflated'] is True
    
    result = engine.handle_deflate(object_id, state)
    assert result.success is True
    assert game_object.state['is_inflated'] is False


@settings(max_examples=100)
@given(st.data())
def test_inflate_fails_for_non_inflatable_objects(data):
    """
    For non-inflatable objects, inflate should fail.
    
    **Validates: Requirements 6.4**
    """
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    non_inflatable_objects = [obj_id for obj_id, obj in world.objects.items() 
                              if not obj.state.get('is_inflatable', False)]
    
    if not non_inflatable_objects:
        assume(False)
    
    object_id = data.draw(st.sampled_from(non_inflatable_objects))
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    state = GameState.create_new_game()
    state.current_room = room_id
    
    room = world.get_room(room_id)
    if object_id not in room.items:
        room.items.append(object_id)
    
    result = engine.handle_inflate(object_id, state)
    
    assert result.success is False
    assert result.message is not None
    assert "can't inflate" in result.message.lower()


# Feature: complete-zork-commands, Property 27: Wave generates response
@settings(max_examples=100)
@given(st.data())
def test_wave_generates_response(data):
    """WAVE should generate a response for any object in inventory. Validates: Requirements 6.5"""
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    # Create a test object
    object_id = "test_waveable"
    waveable = GameObject(
        id=object_id,
        name="test object",
        name_spooky="cursed wand",
        type="item",
        is_takeable=True,
        is_treasure=False,
        treasure_value=0,
        interactions=[],
        state={}
    )
    world.objects[object_id] = waveable
    
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    state = GameState.create_new_game()
    state.current_room = room_id
    state.add_to_inventory(object_id)
    
    result = engine.handle_wave(object_id, state)
    
    assert result.success is True
    assert result.message is not None


# Feature: complete-zork-commands, Property 28: Rub/Touch generates response
@settings(max_examples=100)
@given(st.data())
def test_rub_generates_response(data):
    """RUB should generate a response for any accessible object. Validates: Requirements 6.6"""
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    object_ids = list(world.objects.keys())
    if not object_ids:
        assume(False)
    
    object_id = data.draw(st.sampled_from(object_ids))
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    state = GameState.create_new_game()
    state.current_room = room_id
    
    room = world.get_room(room_id)
    room.items.append(object_id)
    
    result = engine.handle_rub(object_id, state)
    
    assert result.success is True
    assert result.message is not None


# Feature: complete-zork-commands, Property 29: Shake generates response or state change
@settings(max_examples=100)
@given(st.data())
def test_shake_generates_response(data):
    """SHAKE should generate a response for any accessible object. Validates: Requirements 6.7"""
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    object_ids = list(world.objects.keys())
    if not object_ids:
        assume(False)
    
    object_id = data.draw(st.sampled_from(object_ids))
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    state = GameState.create_new_game()
    state.current_room = room_id
    
    room = world.get_room(room_id)
    room.items.append(object_id)
    
    result = engine.handle_shake(object_id, state)
    
    assert result.success is True
    assert result.message is not None


# Feature: complete-zork-commands, Property 30: Squeeze generates response or state change
@settings(max_examples=100)
@given(st.data())
def test_squeeze_generates_response(data):
    """SQUEEZE should generate a response for any accessible object. Validates: Requirements 6.8"""
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    
    object_ids = list(world.objects.keys())
    if not object_ids:
        assume(False)
    
    object_id = data.draw(st.sampled_from(object_ids))
    room_ids = list(world.rooms.keys())
    room_id = data.draw(st.sampled_from(room_ids))
    
    state = GameState.create_new_game()
    state.current_room = room_id
    
    room = world.get_room(room_id)
    room.items.append(object_id)
    
    result = engine.handle_squeeze(object_id, state)
    
    assert result.success is True
    assert result.message is not None
