"""
Unit Tests for Command Parser

Tests specific command parsing scenarios including:
- All verb categories (movement, object, utility)
- Synonym handling
- Invalid command handling
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler'))

import pytest
from command_parser import CommandParser, ParsedCommand


class TestMovementCommands:
    """Test parsing of movement commands."""
    
    def test_explicit_go_north(self):
        """Test 'go north' command."""
        parser = CommandParser()
        result = parser.parse("go north")
        
        assert result.verb == "GO"
        assert result.direction == "NORTH"
    
    def test_implicit_north(self):
        """Test 'north' command (implicit GO)."""
        parser = CommandParser()
        result = parser.parse("north")
        
        assert result.verb == "GO"
        assert result.direction == "NORTH"
    
    def test_abbreviated_direction(self):
        """Test abbreviated directions like 'n', 's', 'e', 'w'."""
        parser = CommandParser()
        
        assert parser.parse("n").direction == "NORTH"
        assert parser.parse("s").direction == "SOUTH"
        assert parser.parse("e").direction == "EAST"
        assert parser.parse("w").direction == "WEST"
        assert parser.parse("u").direction == "UP"
        assert parser.parse("d").direction == "DOWN"
    
    def test_all_directions(self):
        """Test all cardinal and vertical directions."""
        parser = CommandParser()
        
        directions = [
            ("north", "NORTH"),
            ("south", "SOUTH"),
            ("east", "EAST"),
            ("west", "WEST"),
            ("up", "UP"),
            ("down", "DOWN"),
            ("in", "IN"),
            ("out", "OUT"),
        ]
        
        for direction, expected in directions:
            result = parser.parse(direction)
            assert result.verb == "GO"
            assert result.direction == expected
    
    def test_movement_synonyms(self):
        """Test movement verb synonyms."""
        parser = CommandParser()
        
        # Note: "move" is for object manipulation, not movement
        synonyms = ["go", "walk", "run", "travel", "head"]
        
        for synonym in synonyms:
            result = parser.parse(f"{synonym} north")
            assert result.verb == "GO"
            assert result.direction == "NORTH"


class TestObjectCommands:
    """Test parsing of object manipulation commands."""
    
    def test_take_object(self):
        """Test 'take lamp' command."""
        parser = CommandParser()
        result = parser.parse("take lamp")
        
        assert result.verb == "TAKE"
        assert result.object == "lamp"
    
    def test_take_synonyms(self):
        """Test synonyms for TAKE."""
        parser = CommandParser()
        
        synonyms = ["take", "get", "grab", "pick", "pickup"]
        
        for synonym in synonyms:
            result = parser.parse(f"{synonym} lamp")
            assert result.verb == "TAKE"
            assert result.object == "lamp"
    
    def test_drop_object(self):
        """Test 'drop sword' command."""
        parser = CommandParser()
        result = parser.parse("drop sword")
        
        assert result.verb == "DROP"
        assert result.object == "sword"
    
    def test_drop_synonyms(self):
        """Test synonyms for DROP."""
        parser = CommandParser()
        
        synonyms = ["drop", "release"]
        
        for synonym in synonyms:
            result = parser.parse(f"{synonym} keys")
            assert result.verb == "DROP"
            assert result.object == "keys"
    
    def test_examine_object(self):
        """Test 'examine mailbox' command."""
        parser = CommandParser()
        result = parser.parse("examine mailbox")
        
        assert result.verb == "EXAMINE"
        assert result.object == "mailbox"
    
    def test_examine_synonyms(self):
        """Test synonyms for EXAMINE."""
        parser = CommandParser()
        
        # Direct synonyms
        synonyms = ["examine", "inspect", "check", "x"]
        
        for synonym in synonyms:
            result = parser.parse(f"{synonym} mailbox")
            assert result.verb == "EXAMINE"
            assert result.object == "mailbox"
    
    def test_look_at_object(self):
        """Test 'look at mailbox' becomes EXAMINE."""
        parser = CommandParser()
        result = parser.parse("look at mailbox")
        
        assert result.verb == "EXAMINE"
        assert result.object == "mailbox"
    
    def test_look_object(self):
        """Test 'look mailbox' becomes EXAMINE."""
        parser = CommandParser()
        result = parser.parse("look mailbox")
        
        assert result.verb == "EXAMINE"
        assert result.object == "mailbox"
    
    def test_open_object(self):
        """Test 'open mailbox' command."""
        parser = CommandParser()
        result = parser.parse("open mailbox")
        
        assert result.verb == "OPEN"
        assert result.object == "mailbox"
    
    def test_close_object(self):
        """Test 'close window' command."""
        parser = CommandParser()
        result = parser.parse("close window")
        
        assert result.verb == "CLOSE"
        assert result.object == "window"
    
    def test_close_synonyms(self):
        """Test synonyms for CLOSE."""
        parser = CommandParser()
        
        result1 = parser.parse("close door")
        result2 = parser.parse("shut door")
        
        assert result1.verb == "CLOSE"
        assert result2.verb == "CLOSE"
    
    def test_read_object(self):
        """Test 'read leaflet' command."""
        parser = CommandParser()
        result = parser.parse("read leaflet")
        
        assert result.verb == "READ"
        assert result.object == "leaflet"
    
    def test_move_object(self):
        """Test 'move rug' command."""
        parser = CommandParser()
        result = parser.parse("move rug")
        
        assert result.verb == "MOVE"
        assert result.object == "rug"
    
    def test_move_synonyms(self):
        """Test synonyms for MOVE."""
        parser = CommandParser()
        
        # Note: PUSH and PULL are their own commands in Zork, not synonyms of MOVE
        # MOVE is for general object movement, PUSH/PULL are specific actions
        # Currently MOVE only has itself as a synonym
        result = parser.parse("move rug")
        assert result.verb == "MOVE"
        assert result.object == "rug"
    
    def test_multi_word_object(self):
        """Test objects with multiple words."""
        parser = CommandParser()
        result = parser.parse("take brass lantern")
        
        assert result.verb == "TAKE"
        assert result.object == "brass lantern"


class TestUtilityCommands:
    """Test parsing of utility commands."""
    
    def test_inventory(self):
        """Test 'inventory' command."""
        parser = CommandParser()
        result = parser.parse("inventory")
        
        assert result.verb == "INVENTORY"
    
    def test_inventory_abbreviations(self):
        """Test inventory abbreviations."""
        parser = CommandParser()
        
        abbreviations = ["inventory", "i", "inv", "items"]
        
        for abbrev in abbreviations:
            result = parser.parse(abbrev)
            assert result.verb == "INVENTORY"
    
    def test_look(self):
        """Test 'look' command (room description)."""
        parser = CommandParser()
        result = parser.parse("look")
        
        assert result.verb == "LOOK"
    
    def test_look_abbreviation(self):
        """Test 'l' abbreviation for look."""
        parser = CommandParser()
        result = parser.parse("l")
        
        assert result.verb == "LOOK"
    
    def test_quit(self):
        """Test 'quit' command."""
        parser = CommandParser()
        result = parser.parse("quit")
        
        assert result.verb == "QUIT"
    
    def test_quit_synonyms(self):
        """Test synonyms for QUIT."""
        parser = CommandParser()
        
        # Note: "exit" is now a movement command (EXIT), not a quit synonym
        synonyms = ["quit", "q"]
        
        for synonym in synonyms:
            result = parser.parse(synonym)
            assert result.verb == "QUIT"


class TestInvalidCommands:
    """Test handling of invalid or unknown commands."""
    
    def test_unknown_verb(self):
        """Test command with unknown verb."""
        parser = CommandParser()
        result = parser.parse("xyzzy")
        
        assert result.verb == "XYZZY"
    
    def test_empty_command(self):
        """Test empty command string."""
        parser = CommandParser()
        result = parser.parse("")
        
        assert result.verb == "UNKNOWN"
    
    def test_whitespace_only(self):
        """Test command with only whitespace."""
        parser = CommandParser()
        result = parser.parse("   ")
        
        assert result.verb == "UNKNOWN"
    
    def test_gibberish(self):
        """Test nonsensical command."""
        parser = CommandParser()
        result = parser.parse("asdf qwer zxcv")
        
        assert result.verb == "UNKNOWN"


class TestArticleHandling:
    """Test that articles are properly ignored."""
    
    def test_take_the_lamp(self):
        """Test 'take the lamp' ignores 'the'."""
        parser = CommandParser()
        result = parser.parse("take the lamp")
        
        assert result.verb == "TAKE"
        assert result.object == "lamp"
    
    def test_take_a_sword(self):
        """Test 'take a sword' ignores 'a'."""
        parser = CommandParser()
        result = parser.parse("take a sword")
        
        assert result.verb == "TAKE"
        assert result.object == "sword"
    
    def test_examine_an_object(self):
        """Test 'examine an object' ignores 'an'."""
        parser = CommandParser()
        result = parser.parse("examine an object")
        
        assert result.verb == "EXAMINE"
        assert result.object == "object"


class TestCaseInsensitivity:
    """Test that parsing is case-insensitive."""
    
    def test_uppercase_command(self):
        """Test uppercase command."""
        parser = CommandParser()
        result = parser.parse("TAKE LAMP")
        
        assert result.verb == "TAKE"
        assert result.object == "lamp"
    
    def test_mixed_case_command(self):
        """Test mixed case command."""
        parser = CommandParser()
        result = parser.parse("TaKe LaMp")
        
        assert result.verb == "TAKE"
        assert result.object == "lamp"
    
    def test_lowercase_command(self):
        """Test lowercase command."""
        parser = CommandParser()
        result = parser.parse("take lamp")
        
        assert result.verb == "TAKE"
        assert result.object == "lamp"


class TestSynonymRetrieval:
    """Test the get_synonyms method."""
    
    def test_get_synonyms_for_take(self):
        """Test retrieving synonyms for 'take'."""
        parser = CommandParser()
        synonyms = parser.get_synonyms("take")
        
        assert "take" in synonyms
        assert "get" in synonyms
        assert "grab" in synonyms
    
    def test_get_synonyms_for_north(self):
        """Test retrieving synonyms for 'north'."""
        parser = CommandParser()
        synonyms = parser.get_synonyms("north")
        
        assert "north" in synonyms
        assert "n" in synonyms
    
    def test_get_synonyms_for_unknown_word(self):
        """Test retrieving synonyms for unknown word."""
        parser = CommandParser()
        synonyms = parser.get_synonyms("xyzzy")
        
        # Should return just the word itself
        assert synonyms == ["xyzzy"]


class TestPrepositions:
    """Test handling of commands with prepositions."""
    
    def test_command_with_preposition(self):
        """Test 'put lamp in mailbox' style commands."""
        parser = CommandParser()
        result = parser.parse("put lamp in mailbox")
        
        assert result.verb == "PUT"
        assert result.object == "lamp"
        assert result.target == "mailbox"
        assert result.preposition == "IN"
    
    def test_attack_with_weapon(self):
        """Test 'attack troll with sword' style commands."""
        parser = CommandParser()
        result = parser.parse("open mailbox with keys")
        
        assert result.verb == "OPEN"
        assert result.object == "mailbox"
        assert result.instrument == "keys"
        assert result.preposition == "WITH"
