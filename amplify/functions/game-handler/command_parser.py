"""
Command Parser for West of Haunted House

Parses natural language commands into structured ParsedCommand objects.
Handles movement, object interaction, and utility commands with synonym support.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Set


@dataclass
class ParsedCommand:
    """Structured representation of a parsed command."""
    verb: str
    object: Optional[str] = None
    target: Optional[str] = None
    instrument: Optional[str] = None
    direction: Optional[str] = None
    preposition: Optional[str] = None


class CommandParser:
    """
    Parses natural language text commands into structured ParsedCommand objects.
    
    Supports:
    - Movement commands (GO, NORTH, SOUTH, EAST, WEST, UP, DOWN, IN, OUT)
    - Object commands (TAKE, DROP, EXAMINE, OPEN, CLOSE, READ, MOVE)
    - Utility commands (INVENTORY, LOOK, QUIT)
    - Synonyms and variations
    """
    
    def __init__(self):
        """Initialize the command parser with verb and synonym mappings."""
        # Movement verbs and their synonyms
        self.movement_verbs: Dict[str, str] = {
            'go': 'GO',
            'walk': 'GO',
            'run': 'GO',
            'travel': 'GO',
            'head': 'GO',
            'climb': 'CLIMB',
            'scale': 'CLIMB',
            'ascend': 'CLIMB',
            'descend': 'CLIMB',
            'enter': 'ENTER',
            'exit': 'EXIT',
            'leave': 'EXIT',
        }
        
        # Direction words (can be used alone or with GO)
        self.directions: Dict[str, str] = {
            'north': 'NORTH',
            'n': 'NORTH',
            'south': 'SOUTH',
            's': 'SOUTH',
            'east': 'EAST',
            'e': 'EAST',
            'west': 'WEST',
            'w': 'WEST',
            'up': 'UP',
            'u': 'UP',
            'down': 'DOWN',
            'd': 'DOWN',
            'in': 'IN',
            'inside': 'IN',
            'out': 'OUT',
            'outside': 'OUT',
            'northeast': 'NORTHEAST',
            'ne': 'NORTHEAST',
            'northwest': 'NORTHWEST',
            'nw': 'NORTHWEST',
            'southeast': 'SOUTHEAST',
            'se': 'SOUTHEAST',
            'southwest': 'SOUTHWEST',
            'sw': 'SOUTHWEST',
        }
        
        # Object manipulation verbs
        self.object_verbs: Dict[str, str] = {
            'take': 'TAKE',
            'get': 'TAKE',
            'grab': 'TAKE',
            'pick': 'TAKE',
            'pickup': 'TAKE',
            'drop': 'DROP',
            'release': 'DROP',
            'put': 'PUT',
            'place': 'PUT',
            'insert': 'PUT',
            'examine': 'EXAMINE',
            'look': 'EXAMINE',
            'inspect': 'EXAMINE',
            'check': 'EXAMINE',
            'x': 'EXAMINE',
            'open': 'OPEN',
            'close': 'CLOSE',
            'shut': 'CLOSE',
            'read': 'READ',
            'move': 'MOVE',
            'push': 'MOVE',
            'pull': 'MOVE',
            'light': 'LIGHT',
            'ignite': 'LIGHT',
            'extinguish': 'EXTINGUISH',
            'douse': 'EXTINGUISH',
        }
        
        # Utility verbs
        self.utility_verbs: Dict[str, str] = {
            'inventory': 'INVENTORY',
            'i': 'INVENTORY',
            'inv': 'INVENTORY',
            'items': 'INVENTORY',
            'look': 'LOOK',
            'l': 'LOOK',
            'quit': 'QUIT',
            'q': 'QUIT',
        }
        
        # Prepositions to recognize
        self.prepositions: Set[str] = {
            'with', 'using', 'at', 'to', 'in', 'into', 'on', 'onto', 'from'
        }
        
        # Words to ignore (articles, etc.)
        self.ignore_words: Set[str] = {
            'the', 'a', 'an', 'my', 'some'
        }
    
    def parse(self, command: str) -> ParsedCommand:
        """
        Parse a natural language command into a structured ParsedCommand.
        
        Args:
            command: The raw text command from the player
            
        Returns:
            ParsedCommand object with parsed verb, objects, and modifiers
            
        Examples:
            "go north" -> ParsedCommand(verb="GO", direction="NORTH")
            "take lamp" -> ParsedCommand(verb="TAKE", object="lamp")
            "open mailbox" -> ParsedCommand(verb="OPEN", object="mailbox")
            "attack troll with sword" -> ParsedCommand(
                verb="ATTACK", 
                target="troll", 
                instrument="sword"
            )
        """
        # Normalize: lowercase and split into words
        words = command.lower().strip().split()
        
        if not words:
            return ParsedCommand(verb="UNKNOWN")
        
        # Remove ignored words
        words = [w for w in words if w not in self.ignore_words]
        
        if not words:
            return ParsedCommand(verb="UNKNOWN")
        
        # Handle multi-word verbs like "turn on" and "turn off"
        if len(words) >= 2:
            two_word = f"{words[0]} {words[1]}"
            if two_word == "turn on":
                obj = " ".join(words[2:]) if len(words) > 2 else None
                return ParsedCommand(verb="TURN_ON", object=obj)
            elif two_word == "turn off":
                obj = " ".join(words[2:]) if len(words) > 2 else None
                return ParsedCommand(verb="TURN_OFF", object=obj)
            elif two_word == "switch on":
                obj = " ".join(words[2:]) if len(words) > 2 else None
                return ParsedCommand(verb="TURN_ON", object=obj)
            elif two_word == "switch off":
                obj = " ".join(words[2:]) if len(words) > 2 else None
                return ParsedCommand(verb="TURN_OFF", object=obj)
        
        first_word = words[0]
        
        # Check if first word is a direction (implicit GO)
        if first_word in self.directions:
            return ParsedCommand(
                verb="GO",
                direction=self.directions[first_word]
            )
        
        # Check if first word is a utility command (often standalone)
        if first_word in self.utility_verbs:
            verb = self.utility_verbs[first_word]
            
            # Special case: "look at <object>" becomes EXAMINE
            if verb == "LOOK" and len(words) > 1:
                if words[1] == "at" and len(words) > 2:
                    return ParsedCommand(
                        verb="EXAMINE",
                        object=" ".join(words[2:])
                    )
                # "look <object>" also becomes EXAMINE
                return ParsedCommand(
                    verb="EXAMINE",
                    object=" ".join(words[1:])
                )
            
            return ParsedCommand(verb=verb)
        
        # Check if first word is a movement verb
        if first_word in self.movement_verbs:
            verb = self.movement_verbs[first_word]
            
            # Special handling for CLIMB command
            if verb == "CLIMB":
                # Look for direction (UP or DOWN)
                direction = None
                obj = None
                
                if len(words) > 1:
                    # Check if second word is a direction
                    if words[1] in self.directions and self.directions[words[1]] in ['UP', 'DOWN']:
                        direction = self.directions[words[1]]
                        # Check if there's an object after the direction
                        if len(words) > 2:
                            obj = " ".join(words[2:])
                    # Check if second word is an object (implicit UP)
                    else:
                        obj = " ".join(words[1:])
                        # Default to UP if no direction specified
                        direction = "UP"
                
                return ParsedCommand(
                    verb=verb,
                    direction=direction,
                    object=obj
                )
            
            # Special handling for ENTER command
            if verb == "ENTER":
                # Get object to enter (if specified)
                obj = None
                if len(words) > 1:
                    obj = " ".join(words[1:])
                
                return ParsedCommand(
                    verb=verb,
                    object=obj
                )
            
            # Special handling for EXIT command
            if verb == "EXIT":
                # Get object to exit from (if specified)
                obj = None
                if len(words) > 1:
                    obj = " ".join(words[1:])
                
                return ParsedCommand(
                    verb=verb,
                    object=obj
                )
            
            # Look for direction in remaining words
            if len(words) > 1 and words[1] in self.directions:
                return ParsedCommand(
                    verb=verb,
                    direction=self.directions[words[1]]
                )
            
            return ParsedCommand(verb=verb)
        
        # Check if first word is an object verb
        if first_word in self.object_verbs:
            verb = self.object_verbs[first_word]
            
            if len(words) == 1:
                # Verb with no object
                return ParsedCommand(verb=verb)
            
            # Find preposition if present
            preposition_idx = None
            preposition = None
            for i, word in enumerate(words[1:], start=1):
                if word in self.prepositions:
                    preposition_idx = i
                    preposition = word
                    break
            
            if preposition_idx:
                # Split into object and instrument/target
                obj = " ".join(words[1:preposition_idx])
                remaining = " ".join(words[preposition_idx + 1:])
                
                return ParsedCommand(
                    verb=verb,
                    object=obj if obj else None,
                    target=remaining if remaining else None,
                    instrument=remaining if remaining else None,
                    preposition=preposition.upper()
                )
            else:
                # No preposition, everything after verb is the object
                obj = " ".join(words[1:])
                return ParsedCommand(
                    verb=verb,
                    object=obj if obj else None
                )
        
        # Unknown command
        return ParsedCommand(verb="UNKNOWN", object=" ".join(words))
    
    def get_synonyms(self, word: str) -> List[str]:
        """
        Return list of synonyms for a word.
        
        Args:
            word: The word to find synonyms for
            
        Returns:
            List of synonym strings (including the original word)
        """
        word_lower = word.lower()
        synonyms = [word_lower]
        
        # Check all verb dictionaries
        for verb_dict in [self.movement_verbs, self.object_verbs, self.utility_verbs]:
            if word_lower in verb_dict:
                canonical = verb_dict[word_lower]
                # Find all words that map to the same canonical form
                for key, value in verb_dict.items():
                    if value == canonical and key not in synonyms:
                        synonyms.append(key)
        
        # Check directions
        if word_lower in self.directions:
            canonical = self.directions[word_lower]
            for key, value in self.directions.items():
                if value == canonical and key not in synonyms:
                    synonyms.append(key)
        
        return synonyms
