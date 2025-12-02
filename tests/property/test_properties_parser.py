"""
Property-Based Tests for Command Parser

Tests correctness properties related to command parsing,
determinism, and synonym handling.
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler'))

import pytest
from hypothesis import given, strategies as st, settings
from command_parser import CommandParser, ParsedCommand


# Feature: game-backend-api, Property 4: Command parsing determinism
@settings(max_examples=100)
@given(command=st.text(min_size=1, max_size=100))
def test_command_parsing_determinism(command):
    """
    For any command string, parsing it multiple times should always produce the same result.
    
    **Validates: Requirements 2.2**
    
    This property ensures that command parsing is deterministic and consistent,
    which is critical for reliable game behavior.
    """
    parser = CommandParser()
    
    # Parse the command multiple times
    result1 = parser.parse(command)
    result2 = parser.parse(command)
    result3 = parser.parse(command)
    
    # All results should be identical
    assert result1 == result2
    assert result2 == result3
    assert result1 == result3
    
    # Verify all fields match
    assert result1.verb == result2.verb == result3.verb
    assert result1.object == result2.object == result3.object
    assert result1.target == result2.target == result3.target
    assert result1.instrument == result2.instrument == result3.instrument
    assert result1.direction == result2.direction == result3.direction
    assert result1.preposition == result2.preposition == result3.preposition


# Additional property: Parsing is case-insensitive
@settings(max_examples=100)
@given(
    command=st.sampled_from([
        "go north", "take lamp", "open mailbox", "examine sword",
        "drop keys", "inventory", "look", "quit"
    ])
)
def test_parsing_case_insensitive(command):
    """
    For any valid command, parsing should be case-insensitive.
    
    Commands in uppercase, lowercase, or mixed case should produce the same result.
    """
    parser = CommandParser()
    
    result_lower = parser.parse(command.lower())
    result_upper = parser.parse(command.upper())
    result_mixed = parser.parse(command.title())
    
    # All should produce the same verb
    assert result_lower.verb == result_upper.verb == result_mixed.verb
    
    # Objects should match (if present)
    if result_lower.object:
        assert result_lower.object.lower() == result_upper.object.lower()
        assert result_lower.object.lower() == result_mixed.object.lower()


# Additional property: Direction commands are recognized
@settings(max_examples=100)
@given(
    direction=st.sampled_from([
        "north", "south", "east", "west", "up", "down", "in", "out",
        "n", "s", "e", "w", "u", "d"
    ])
)
def test_direction_recognition(direction):
    """
    For any direction word, it should be recognized as a movement command.
    
    Both full names and abbreviations should work.
    """
    parser = CommandParser()
    
    # Parse direction alone (implicit GO)
    result = parser.parse(direction)
    
    assert result.verb == "GO"
    assert result.direction is not None
    assert result.direction in [
        "NORTH", "SOUTH", "EAST", "WEST", "UP", "DOWN", "IN", "OUT"
    ]


# Additional property: Synonyms produce same canonical verb
@settings(max_examples=100)
@given(
    synonym_pair=st.sampled_from([
        ("take lamp", "get lamp"),
        ("take lamp", "grab lamp"),
        ("examine sword", "look at sword"),
        ("examine sword", "inspect sword"),
        ("drop keys", "put keys"),
        ("inventory", "i"),
        ("quit", "exit"),
    ])
)
def test_synonyms_produce_same_verb(synonym_pair):
    """
    For any pair of synonym commands, they should produce the same canonical verb.
    
    This ensures synonym handling is consistent.
    """
    parser = CommandParser()
    
    command1, command2 = synonym_pair
    result1 = parser.parse(command1)
    result2 = parser.parse(command2)
    
    # Should produce the same canonical verb
    assert result1.verb == result2.verb


# Additional property: Empty or whitespace commands are handled
@settings(max_examples=100)
@given(
    whitespace=st.text(alphabet=" \t\n\r", min_size=0, max_size=20)
)
def test_empty_command_handling(whitespace):
    """
    For any empty or whitespace-only command, parsing should handle it gracefully.
    
    Should return UNKNOWN verb without crashing.
    """
    parser = CommandParser()
    
    result = parser.parse(whitespace)
    
    # Should not crash and should return a valid ParsedCommand
    assert isinstance(result, ParsedCommand)
    assert result.verb == "UNKNOWN"


# Additional property: Object commands preserve object names
@settings(max_examples=100)
@given(
    verb=st.sampled_from(["take", "drop", "examine", "open", "close", "read"]),
    obj=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Lu"), min_codepoint=97, max_codepoint=122),
        min_size=2,  # At least 2 characters to avoid single-letter articles
        max_size=20
    ).filter(lambda x: x.lower() not in ["a", "an", "the", "my", "some"])  # Exclude articles
)
def test_object_preservation(verb, obj):
    """
    For any object command, the object name should be preserved in the result.
    
    The parser should not lose or corrupt object names (except articles which are filtered).
    """
    parser = CommandParser()
    
    command = f"{verb} {obj}"
    result = parser.parse(command)
    
    # Object should be present and match (case-insensitive)
    assert result.object is not None
    assert result.object.lower() == obj.lower()
