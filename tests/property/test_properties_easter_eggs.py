"""
Property-Based Tests for Easter Egg and Special Commands

Tests XYZZY, PLUGH, HELLO, PRAY, JUMP, YELL, ECHO commands.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler'))

import pytest
from hypothesis import given, strategies as st, settings
from game_engine import GameEngine
from state_manager import GameState
from world_loader import WorldData


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


# Feature: complete-zork-commands, Property: Easter eggs generate responses
@settings(max_examples=100)
@given(st.data())
def test_xyzzy_generates_response(data):
    """XYZZY should always generate a response. Validates: Requirements 8.1"""
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    state = GameState.create_new_game()
    
    result = engine.handle_xyzzy(state)
    
    assert result.success is True
    assert result.message is not None
    assert len(result.message) > 0


@settings(max_examples=100)
@given(st.data())
def test_plugh_generates_response(data):
    """PLUGH should always generate a response. Validates: Requirements 8.1"""
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    state = GameState.create_new_game()
    
    result = engine.handle_plugh(state)
    
    assert result.success is True
    assert result.message is not None
    assert len(result.message) > 0


@settings(max_examples=100)
@given(st.data())
def test_hello_generates_response(data):
    """HELLO should always generate a response. Validates: Requirements 8.2"""
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    state = GameState.create_new_game()
    
    result = engine.handle_hello(state)
    
    assert result.success is True
    assert result.message is not None
    assert len(result.message) > 0


@settings(max_examples=100)
@given(st.data())
def test_pray_generates_response(data):
    """PRAY should always generate a response. Validates: Requirements 8.4"""
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    state = GameState.create_new_game()
    
    result = engine.handle_pray(state)
    
    assert result.success is True
    assert result.message is not None
    assert len(result.message) > 0


@settings(max_examples=100)
@given(st.data())
def test_jump_generates_response(data):
    """JUMP should always generate a response. Validates: Requirements 8.5"""
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    state = GameState.create_new_game()
    
    result = engine.handle_jump(state)
    
    assert result.success is True
    assert result.message is not None
    assert len(result.message) > 0


@settings(max_examples=100)
@given(st.data())
def test_yell_generates_response(data):
    """YELL should always generate a response. Validates: Requirements 8.6"""
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    state = GameState.create_new_game()
    
    result = engine.handle_yell(state)
    
    assert result.success is True
    assert result.message is not None
    assert len(result.message) > 0


# Feature: complete-zork-commands, Property 34: Echo repeats input
@settings(max_examples=100)
@given(st.text(min_size=1, max_size=50))
def test_echo_repeats_input(text):
    """ECHO should repeat the input text. Validates: Requirements 8.7"""
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    
    engine = GameEngine(world)
    state = GameState.create_new_game()
    
    result = engine.handle_echo(text, state)
    
    assert result.success is True
    assert result.message is not None
    assert text in result.message
