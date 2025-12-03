"""
Property-Based Tests for Enhanced Command Parser

Tests synonym equivalence, abbreviation expansion, variation mapping, 
preposition parsing, and article handling.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler'))

import pytest
from hypothesis import given, strategies as st, settings
from command_parser import CommandParser


@pytest.fixture(scope="module")
def parser():
    """Create parser instance."""
    return CommandParser()


# Feature: complete-zork-commands, Property 40: Synonym equivalence
@settings(max_examples=100)
@given(st.sampled_from(['take', 'get', 'grab', 'pick', 'pickup']))
def test_synonym_equivalence(synonym):
    """All synonyms for TAKE should parse to same verb. Validates: Requirements 10.1"""
    parser = CommandParser()
    
    result = parser.parse(f"{synonym} lamp")
    
    assert result.verb == "TAKE"
    assert result.object == "lamp"


# Feature: complete-zork-commands, Property 41: Abbreviation expansion
@settings(max_examples=100)
@given(st.sampled_from([
    ('n', 'NORTH'), ('s', 'SOUTH'), ('e', 'EAST'), ('w', 'WEST'),
    ('u', 'UP'), ('d', 'DOWN'), ('i', 'INVENTORY'), ('x', 'EXAMINE'),
    ('l', 'LOOK'), ('q', 'QUIT')
]))
def test_abbreviation_expansion(abbrev_pair):
    """Abbreviations should expand to full commands. Validates: Requirements 10.2"""
    parser = CommandParser()
    abbrev, expected = abbrev_pair
    
    if expected in ['NORTH', 'SOUTH', 'EAST', 'WEST', 'UP', 'DOWN']:
        result = parser.parse(abbrev)
        assert result.verb == "GO"
        assert result.direction == expected
    elif expected == 'EXAMINE':
        result = parser.parse(f"{abbrev} lamp")
        assert result.verb == expected
    else:
        result = parser.parse(abbrev)
        assert result.verb == expected


# Feature: complete-zork-commands, Property 42: Variation mapping
@settings(max_examples=100)
@given(st.sampled_from([
    ('take', 'TAKE'), ('get', 'TAKE'),
    ('look', 'EXAMINE'), ('examine', 'EXAMINE'),
    ('drop', 'DROP'), ('release', 'DROP'),
    ('open', 'OPEN'), ('close', 'CLOSE'), ('shut', 'CLOSE')
]))
def test_variation_mapping(variation_pair):
    """Command variations should map to canonical forms. Validates: Requirements 10.3"""
    parser = CommandParser()
    variation, expected = variation_pair
    
    if variation in ['look', 'examine']:
        result = parser.parse(f"{variation} at lamp")
        assert result.verb == expected
    else:
        result = parser.parse(f"{variation} lamp")
        assert result.verb == expected


# Feature: complete-zork-commands, Property 43: Preposition parsing
@settings(max_examples=100)
@given(st.sampled_from(['with', 'using', 'at', 'to', 'in', 'into', 'on', 'from', 'under', 'behind']))
def test_preposition_parsing(preposition):
    """Prepositions should be correctly parsed. Validates: Requirements 10.4"""
    parser = CommandParser()
    
    result = parser.parse(f"attack troll {preposition} sword")
    
    assert result.verb == "ATTACK"
    assert result.object == "troll"
    assert result.target == "sword" or result.instrument == "sword"
    assert result.preposition == preposition.upper()


# Feature: complete-zork-commands, Property 44: Article handling
@settings(max_examples=100)
@given(st.sampled_from(['the', 'a', 'an', 'my', 'some']))
def test_article_handling(article):
    """Articles should be ignored. Validates: Requirements 10.5"""
    parser = CommandParser()
    
    result_with = parser.parse(f"take {article} lamp")
    result_without = parser.parse("take lamp")
    
    assert result_with.verb == result_without.verb
    assert result_with.object == result_without.object


@settings(max_examples=100)
@given(st.text(min_size=2, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
def test_multiple_articles(object_name):
    """Multiple articles should all be ignored. Validates: Requirements 10.5"""
    parser = CommandParser()
    
    # Skip if object name is an article itself
    if object_name.lower() in ['the', 'an', 'my', 'some']:
        return
    
    result = parser.parse(f"take the a an {object_name}")
    
    assert result.verb == "TAKE"
    assert result.object == object_name.lower()
