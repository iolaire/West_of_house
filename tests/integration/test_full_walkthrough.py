import unittest
import sys
import os

# Add game-handler to path
game_handler_path = os.path.join(os.getcwd(), 'amplify/functions/game-handler')
sys.path.append(game_handler_path)

from game_engine import GameEngine
from world_loader import WorldData
from state_manager import GameState
from command_parser import CommandParser
from game_engine import ActionResult

class TestFullWalkthrough(unittest.TestCase):
    """
    Full game walkthrough test based on 1_WinGame.md.
    Follows the optimal route to complete the game.
    """
    
    def setUp(self):
        # Initialize components
        self.world_data = WorldData()
        self.world_data.load_from_json("amplify/functions/game-handler/data")
        self.state = GameState.create_new_game()
        self.engine = GameEngine(self.world_data)
        self.parser = CommandParser()
        
    def execute(self, command_text):
        """Helper to parse and execute a command."""
        cmd = self.parser.parse(command_text)
        result = self.engine.execute_command(cmd, self.state)
        # Uncomment to debug
        # print(f"\n> {command_text}")
        # print(result.message)
        if not result.success:
            print(f"COMMAND FAILED: {command_text} -> {result.message}")
        self.assertTrue(result.success, f"Command failed: {command_text}\nResponse: {result.message}")
        return result

    def test_win_game(self):
        print("\n=== STARTING FULL GAME WALKTHROUGH ===")
        
        # === Phase 1: Above Ground & The House ===
        print("\n--- Phase 1 ---")
        self.execute("OPEN MAILBOX")
        self.execute("TAKE CURSED PARCHMENT") # Leaflet
        self.execute("READ CURSED PARCHMENT")
        self.execute("DROP CURSED PARCHMENT")
        self.execute("NORTH")
        self.execute("NORTH") # Forest Path
        
        self.execute("CLIMB DEAD TREE") # Spooky tree
        self.execute("TAKE RAVEN'S EGG") # Egg
        self.execute("CLIMB DOWN")
        self.execute("SOUTH")
        self.execute("EAST") # Behind House
        
        self.execute("OPEN BROKEN WINDOW") # Spooky window
        self.execute("ENTER") # Kitchen
        
        self.execute("TAKE LEATHER POUCH") # Sack
        self.execute("TAKE VIAL OF POISON") # Bottle
        self.execute("WEST") # Living Room
        
        self.execute("TAKE TARNISHED LANTERN") # Lamp
        self.execute("TAKE SPECTRAL BLADE") # Sword
        self.execute("MOVE BLOODSTAINED RUG") # Rug
        self.execute("OPEN CURSED TRAP DOOR") # Trap Door
        self.execute("TURN ON TARNISHED LANTERN")
        self.execute("DOWN") # Cellar
        
        # === Phase 2: The Cellar, Troll, & Gallery ===
        print("\n--- Phase 2 ---")
        self.execute("NORTH") # Troll Room
        
        # Kill Troll (Loop until dead)
        troll_dead = False
        for _ in range(10):
            res = self.execute("KILL FLESH-EATING OGRE WITH SPECTRAL BLADE")
            # print(f"Combat: {res.message}")
            if "life force extinguished" in res.message or "dead" in res.message or "don't see any" in res.message:
                troll_dead = True
                break
        
        if not troll_dead:
            # Check if he's gone
            res = self.execute("LOOK")
            if "flesh-eating ogre" not in res.message:
                troll_dead = True
                
        self.assertTrue(troll_dead, "Troll must die.")
        
        self.execute("DROP SPECTRAL BLADE")
        self.execute("SOUTH")
        self.execute("EAST") # Gallery
        
        self.execute("TAKE PORTRAIT OF THE DAMNED") # Painting
        self.execute("NORTH") # Studio
        
        self.execute("UP")
        self.execute("WEST") # Living Room
        
        self.execute("OPEN CURSED TROPHY CASE") 
        self.execute("PUT PORTRAIT OF THE DAMNED IN CURSED TROPHY CASE")
        self.execute("DROP RAVEN'S EGG") # Drop egg for Thief
        self.execute("EAST") # Kitchen
        
        self.execute("UP") # Attic
        self.execute("TAKE RITUAL KNIFE") # Knife
        self.execute("TAKE HANGMAN'S ROPE") # Rope
        self.execute("DOWN")
        self.execute("WEST")
        self.execute("DOWN") # Cellar (via Trap Door)
        
        # === Phase 3: The Maze & The Cyclops ===
        print("\n--- Phase 3 ---")
        self.execute("NORTH") # Troll Room
        self.execute("WEST") # Maze 1
        
        self.execute("SOUTH")
        self.execute("EAST")
        self.execute("UP") # Maze 5 (Skeleton Key Room)
        
        self.execute("TAKE OLD BAG") # Bag of coins
        self.execute("TAKE KEYS") # Keys
        self.execute("SW") # Southwest
        self.execute("EAST")
        self.execute("SOUTH")
        self.execute("SE") # Cyclops Room
        
        self.execute("ULYSSES") # Scare Cyclops
        
        self.execute("UP") # Treasure Room
        
        self.execute("TAKE CHALICE OF SOULS")
        # Try taking Thief's bag - Thief name logic might differ
        res = self.execute("TAKE SHADOW THIEF") 
        # Ignoring fail here as it's optional path optimization or requires thief state
        if not res.success:
             print("Skipping Thief logic - probabilistic")

        # Canary logic
        res = self.execute("TAKE MECHANICAL RAVEN") # Canary Name
        if not res.success:
            self.execute("TAKE RAVEN'S EGG")
            print("Took Egg (Thief didn't open it).")
        else:
            print("Took Canary (Thief opened egg!).")
            
        self.execute("DOWN")
        self.execute("EAST")
        self.execute("EAST") # Living Room
        
        self.execute("PUT CHALICE OF SOULS IN CURSED TROPHY CASE")
        self.execute("PUT OLD BAG IN CURSED TROPHY CASE")
        # Put Canary or Egg
        self.execute("PUT MECHANICAL RAVEN IN CURSED TROPHY CASE")
        self.execute("PUT RAVEN'S EGG IN CURSED TROPHY CASE")
        
        self.execute("DROP KEYS")
        self.execute("DOWN") # Cellar
        
        # === Phase 4: The Dam & The Diamond ===
        print("\n--- Phase 4 ---")
        self.execute("NORTH")
        self.execute("EAST")
        self.execute("EAST")
        self.execute("SE")
        self.execute("EAST") # Dam
        
        self.execute("TIE HANGMAN'S ROPE TO RAIL")
        self.execute("CLIMB DOWN")
        self.execute("TAKE CURSED TORCH")
        self.execute("CLIMB UP")
        self.execute("NORTH")
        self.execute("NORTH") # Maintenance Room
        
        self.execute("TAKE RUSTY WRENCH")
        self.execute("TAKE SCREWDRIVER")
        self.execute("PUSH YELLOW SKULL BUTTON")
        self.execute("SOUTH")
        self.execute("SOUTH") # Dam
        
        self.execute("TURN IRON BOLT WITH RUSTY WRENCH")
        self.execute("DROP RUSTY WRENCH")
        self.execute("SOUTH") # Deep Canyon
        self.execute("DOWN") # Loud Room
        
        self.execute("ECHO")
        self.execute("TAKE CURSED PLATINUM BAR")
        self.execute("WEST")
        self.execute("WEST")
        self.execute("SOUTH")
        self.execute("UP")
        self.execute("WEST") # Living Room
        
        self.execute("PUT CURSED TORCH IN CURSED TROPHY CASE")
        self.execute("PUT CURSED PLATINUM BAR IN CURSED TROPHY CASE")
        self.execute("DOWN") # Cellar
        
        # === Phase 5: The Coal Mine & Hades ===
        print("\n--- Phase 5 ---")
        self.execute("NORTH")
        self.execute("EAST")
        self.execute("NORTH")
        self.execute("NE")
        self.execute("EAST")
        self.execute("NORTH")
        self.execute("UP")
        self.execute("NORTH") # Lobby
        
        self.execute("TAKE CURSED MATCHES")
        self.execute("NORTH")
        self.execute("EAST") # Shaft Room
        
        # Fetch Coal
        self.execute("SOUTH")
        self.execute("SOUTH") # Dead End
        self.execute("TAKE COAL")
        self.execute("NORTH")
        self.execute("NORTH") # Shaft Room
        
        self.execute("PUT COAL IN BASKET")
        self.execute("LOWER BASKET")
        self.execute("NORTH")
        self.execute("DOWN")
        self.execute("EAST")
        self.execute("NE")
        self.execute("SE")
        self.execute("SW")
        self.execute("DOWN") # Ladder Top
        
        self.execute("DOWN")
        self.execute("WEST") # Timber Room
        
        self.execute("DROP ALL EXCEPT SCREWDRIVER AND TARNISHED LANTERN")
        self.execute("WEST") # Drafty Room
        
        self.execute("TAKE COAL") # From basket
        self.execute("SOUTH") # Machine Room
        
        self.execute("OPEN LID")
        self.execute("PUT COAL IN TORTURE MACHINE")
        self.execute("CLOSE LID")
        self.execute("TURN SWITCH WITH SCREWDRIVER")
        self.execute("OPEN LID")
        self.execute("TAKE CURSED DIAMOND")
        self.execute("DROP SCREWDRIVER")
        self.execute("NORTH")
        
        self.execute("PUT CURSED DIAMOND IN BASKET")
        self.execute("EAST")
        
        self.execute("TAKE ALL")
        self.execute("EAST")
        self.execute("UP")
        self.execute("UP")
        self.execute("NORTH")
        self.execute("EAST")
        self.execute("SOUTH")
        self.execute("NORTH")
        self.execute("UP")
        self.execute("SOUTH") # Shaft Room
        
        self.execute("RAISE BASKET")
        self.execute("TAKE CURSED DIAMOND")
        self.execute("WEST")
        self.execute("SOUTH")
        self.execute("EAST")
        self.execute("SOUTH") # Hades Entrance
        
        self.execute("TAKE NECRONOMICON")
        self.execute("TAKE FUNERAL BELL")
        self.execute("SOUTH") # Land of Dead
        
        self.execute("TAKE SOUL CANDLES")
        self.execute("NORTH")
        
        self.execute("RING FUNERAL BELL")
        self.execute("TAKE SOUL CANDLES")
        self.execute("LIGHT CURSED MATCHES")
        self.execute("LIGHT SOUL CANDLES WITH CURSED MATCHES")
        self.execute("READ NECRONOMICON")
        self.execute("SOUTH")
        
        self.execute("TAKE CRYSTAL SKULL")
        self.execute("NORTH")
        self.execute("UP")
        self.execute("UP")
        self.execute("UP") # Living Room
        
        # === Phase 6: The Last Treasures ===
        print("\n--- Phase 6 ---")
        self.execute("PUT CURSED DIAMOND IN CURSED TROPHY CASE")
        self.execute("PUT CRYSTAL SKULL IN CURSED TROPHY CASE")
        self.execute("DROP ALL EXCEPT TARNISHED LANTERN")
        self.execute("DOWN")
        self.execute("NORTH")
        self.execute("EAST")
        self.execute("EAST")
        self.execute("SOUTH")
        self.execute("EAST")
        self.execute("DOWN")
        self.execute("SOUTH") # Altar
        
        self.execute("PRAY") # Forest
        self.execute("SOUTH")
        self.execute("NORTH") 
        self.execute("EAST")
        self.execute("DOWN")
        self.execute("DOWN")
        self.execute("DOWN") # Canyon Bottom
        
        self.execute("TAKE OBSIDIAN COFFIN")
        self.execute("OPEN OBSIDIAN COFFIN")
        self.execute("TAKE NECROMANCER'S SCEPTRE")
        self.execute("WAVE NECROMANCER'S SCEPTRE")
        self.execute("TAKE POT OF GOLD")
        self.execute("SW")
        self.execute("UP")
        self.execute("UP")
        self.execute("NW")
        self.execute("WEST") # Kitchen
        
        self.execute("OPEN LEATHER POUCH")
        self.execute("TAKE WITHERED GARLIC")
        self.execute("WEST")
        
        self.execute("PUT POT OF GOLD IN CURSED TROPHY CASE")
        self.execute("PUT NECROMANCER'S SCEPTRE IN CURSED TROPHY CASE")
        self.execute("PUT OBSIDIAN COFFIN IN CURSED TROPHY CASE")
        
        self.execute("TAKE TARNISHED LANTERN")
        self.execute("TAKE WITHERED GARLIC")
        self.execute("DOWN")
        self.execute("NORTH")
        self.execute("EAST")
        self.execute("SOUTH")
        self.execute("DOWN") # Bat Room
        
        self.execute("TAKE JADE DEATH MASK")
        self.execute("SOUTH")
        self.execute("EAST")
        self.execute("SOUTH")
        self.execute("DOWN")
        self.execute("UP") # Living Room
        
        self.execute("PUT JADE DEATH MASK IN CURSED TROPHY CASE")
        
        # === Phase 7: The Endgame ===
        print("\n--- Phase 7 ---")
        print(f"Final Score: {self.state.score}")
        
        self.execute("TAKE TARNISHED LANTERN")
        self.execute("TAKE SPECTRAL BLADE")
        self.execute("DROP ALL EXCEPT TARNISHED LANTERN AND SPECTRAL BLADE")
        
        self.execute("LOOK")
        self.execute("TAKE ANCIENT MAP") # Assuming Map Name? Or "TAKE MAP"
        
        self.execute("WEST")
        self.execute("SW")
        self.execute("ENTER")
        
        self.execute("TURN OFF TARNISHED LANTERN")
        self.execute("PLUGH")
        self.execute("DROP SPECTRAL BLADE")
        self.execute("DROP TARNISHED LANTERN")
        print("Done.")

if __name__ == "__main__":
    unittest.main(verbosity=2)
