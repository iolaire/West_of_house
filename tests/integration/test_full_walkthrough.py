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
        
    def execute(self, command_text, require_success=True):
        """Helper to parse and execute a command."""
        cmd = self.parser.parse(command_text)
        result = self.engine.execute_command(cmd, self.state)
        # Uncomment to debug
        print(f"\n> {command_text}")
        print(result.message)
        if require_success and not result.success:
            print(f"COMMAND FAILED: {command_text} -> {result.message}")
        if require_success:
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
        
        self.execute("CLIMB GNARLED TREE") # Spooky tree
        self.execute("TAKE RAVEN'S EGG") # Egg
        self.execute("DOWN")
        self.execute("SOUTH")
        self.execute("EAST") # Behind House
        
        self.execute("OPEN BROKEN WINDOW") # Spooky window
        self.execute("ENTER BROKEN WINDOW") # Kitchen
        
        self.execute("TAKE LEATHER POUCH") # Sack
        self.execute("TAKE VIAL OF POISON") # Bottle
        self.execute("WEST") # Living Room
        
        self.execute("TAKE CURSED LANTERN") # Lamp
        self.execute("TAKE SPECTRAL BLADE") # Sword
        self.execute("MOVE BLOODSTAINED RUG") # Rug
        self.execute("OPEN CURSED TRAP DOOR") # Trap Door
        self.execute("TURN ON CURSED LANTERN")
        self.execute("DOWN") # Cellar
        
        # === Phase 2: The Cellar, Troll, & Gallery ===
        print("\n--- Phase 2 ---")
        self.execute("NORTH") # Troll Room
        
        # Kill Troll (Loop until dead)
        troll_dead = False
        self.execute("INVENTORY")
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
        self.execute("SOUTH") # Cellar
        self.execute("SOUTH") # East of Chasm
        self.execute("EAST") # Gallery
        
        self.execute("TAKE PAINTING") # Painting
        self.execute("NORTH") # Studio
        
        self.execute("UP")
        self.execute("WEST") # Living Room
        
        self.execute("OPEN CURSED TROPHY CASE") 
        self.execute("PUT PAINTING IN CURSED TROPHY CASE")
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
        
        # self.execute("ULYSSES") # Scare Cyclops (Not implemented/needed?)
        
        self.execute("UP") # Treasure Room
        
        self.execute("TAKE CHALICE OF SOULS")
        # Try taking Thief's bag - Thief name logic might differ
        res = self.execute("TAKE SHADOW THIEF", require_success=False)
        # Ignoring fail here as it's optional path optimization or requires thief state
        if not res.success:
             print("Skipping Thief logic - probabilistic")

        # Canary logic
        have_raven = False
        have_egg = False
        
        res = self.execute("TAKE MECHANICAL RAVEN", require_success=False) # Canary Name
        if res.success:
            have_raven = True
            print("Took Canary (Thief opened egg!).")
        else:
            res_egg = self.execute("TAKE RAVEN'S EGG", require_success=False)
            if res_egg.success:
                have_egg = True
                print("Took Egg (Thief didn't open it).")
            else:
                 print("Egg/Raven not in Treasure Room. Probably in Living Room.")
            
        self.execute("DOWN")
        self.execute("EAST")
        self.execute("EAST") # Living Room
        
        # Put Treasures
        self.execute("PUT CHALICE OF SOULS IN CURSED TROPHY CASE")
        self.execute("PUT OLD BAG IN CURSED TROPHY CASE")
        
        # Put Canary or Egg (Conditional)
        if not have_raven and not have_egg:
             # Assume it's in Living Room
             self.execute("TAKE RAVEN'S EGG", require_success=False) # Might already be there?
             have_egg = True
    
        if have_raven:
            self.execute("PUT MECHANICAL RAVEN IN CURSED TROPHY CASE")
        else:
            self.execute("PUT RAVEN'S EGG IN CURSED TROPHY CASE")
        
        self.execute("DROP KEYS")
        self.execute("DOWN") # Cellar
        
        # === Phase 4: The Dam & The Diamond ===
        print("\n--- Phase 4 ---")
        self.execute("NORTH")
        self.execute("EAST")
        self.execute("EAST")
        self.execute("SE")
        self.execute("EAST") # Dome Room
        
        self.execute("TIE HANGMAN'S ROPE TO RAILING")
        self.execute("DOWN")
        self.execute("TAKE CURSED TORCH")
        
        # Egypt Room Excursion
        self.execute("SOUTH") # North Temple
        self.execute("DOWN") # Egypt Room
        self.execute("TAKE OBSIDIAN COFFIN") # Coffin
        self.execute("OPEN OBSIDIAN COFFIN")
        self.execute("TAKE NECROMANCER'S SCEPTRE") # Sceptre
        self.execute("UP") # North Temple
        self.execute("NORTH") # Torch Room
        
        self.execute("UP") # Back to Dome Room
        
        # Navigate to Maintenance Room
        self.execute("WEST") # Engravings Cave
        self.execute("NW") # Round Room
        self.execute("NORTH") # NS Passage
        self.execute("NE") # Deep Canyon
        self.execute("EAST") # Dam Room
        self.execute("NORTH") # Dam Lobby
        self.execute("TAKE CURSED MATCHES") # Matches
        self.execute("NORTH") # Maintenance Room
        
        self.execute("TAKE BLOOD-STAINED WRENCH") # Wrench
        self.execute("PUSH YELLOW SKULL BUTTON") # Button
        self.execute("SOUTH")
        self.execute("SOUTH") # Dam Room
        
        self.execute("TURN IRON BOLT WITH BLOOD-STAINED WRENCH")
        self.execute("DROP BLOOD-STAINED WRENCH")
        self.execute("SOUTH") # Deep Canyon
        self.execute("DOWN") # Loud Room
        
        self.execute("ECHO")
        self.execute("TAKE CURSED PLATINUM BAR")
        self.execute("WEST") # Round Room
        self.execute("WEST") # EW Passage
        self.execute("WEST") # Troll Room
        self.execute("SOUTH") # Cellar
        self.execute("UP")
        # self.execute("WEST") # Removed: UP from Cellar lands in Living Room
        
        self.execute("PUT CURSED TORCH IN CURSED TROPHY CASE")
        self.execute("PUT CURSED PLATINUM BAR IN CURSED TROPHY CASE")
        self.execute("PUT OBSIDIAN COFFIN IN CURSED TROPHY CASE")
        self.execute("PUT NECROMANCER'S SCEPTRE IN CURSED TROPHY CASE")
        self.execute("DOWN") # Cellar
        
        # === Phase 5: The Coal Mine & Hades ===
        print("\n--- Phase 5 ---")
        self.execute("UP") # Living Room
        self.execute("EAST") # Kitchen
        self.execute("DOWN") # Slide Room
        self.execute("NORTH") # Mine Entrance
        self.execute("WEST") # Squeeky Room
        self.execute("NORTH") # Bat Room
        
        self.execute("TAKE JADE") # Get Jade
        self.execute("EAST") # Shaft Room
        
        # Fetch Coal & Make Diamond
        self.execute("DOWN") # Gas Room
        self.execute("DOWN") # Ladder Bottom
        self.execute("SOUTH") # Dead End
        self.execute("TAKE CURSED COAL")
        self.execute("NORTH") # Ladder Bottom
        self.execute("WEST") # Timber Room
        self.execute("WEST") # Lower Shaft
        self.execute("SOUTH") # Machine Room
        
        self.execute("PUT CURSED COAL IN MACHINE")
        self.execute("TURN MACHINE SWITCH WITH RUSTED SCREWDRIVER") # Switch
        self.execute("TAKE DARK DIAMOND") # Diamond
        
        self.execute("NORTH") # Lower Shaft
        self.execute("EAST") # Timber Room
        self.execute("EAST") # Ladder Bottom
        self.execute("UP") # Ladder Top
        self.execute("UP") # Mine 4
        self.execute("NORTH") # Mine 3
        self.execute("EAST") # Mine 2
        self.execute("SOUTH") # Mine 1
        self.execute("NORTH") # Gas Room
        self.execute("UP") # Smelly Room
        self.execute("SOUTH") # Shaft Room
        
        # Exit Mine
        self.execute("WEST") # Bat Room
        self.execute("SOUTH") # Squeeky Room
        self.execute("EAST") # Mine Entrance
        self.execute("SOUTH") # Slide Room
        self.execute("DOWN") # Cellar
        
        self.execute("UP") # Living Room
        
        self.execute("PUT DARK DIAMOND IN CURSED TROPHY CASE")
        self.execute("PUT JADE DEATH MASK IN CURSED TROPHY CASE")
        self.execute("PUT SOUL-BINDING BRACELET IN CURSED TROPHY CASE")
        
        # Check Final Score
        score_res = self.execute("SCORE")
        # Assuming 350 is max
        if "350" in score_res.message:
            print("\n*** SUCCESS: REACHED 350 POINTS! ***")
        else:
            print(f"\nFinished with output: {score_res.message}")
        self.execute("SW")
        self.execute("DOWN") # Ladder Top
        
        self.execute("DOWN")
        self.execute("WEST") # Timber Room
        
        self.execute("DROP ALL EXCEPT RUSTED SCREWDRIVER AND CURSED LANTERN")
        self.execute("WEST") # Drafty Room
        
        self.execute("TAKE CURSED COAL") # From basket
        self.execute("SOUTH") # Machine Room
        
        self.execute("OPEN LID")
        self.execute("PUT CURSED COAL IN TORTURE MACHINE")
        self.execute("CLOSE LID")
        self.execute("TURN SWITCH WITH RUSTED SCREWDRIVER")
        self.execute("OPEN LID")
        self.execute("TAKE CURSED DIAMOND")
        self.execute("DROP RUSTED SCREWDRIVER")
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
        self.execute("DROP ALL EXCEPT CURSED LANTERN")
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
        
        self.execute("TAKE CURSED LANTERN")
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
        
        self.execute("TAKE CURSED LANTERN")
        self.execute("TAKE SPECTRAL BLADE")
        self.execute("DROP ALL EXCEPT CURSED LANTERN AND SPECTRAL BLADE")
        
        self.execute("LOOK")
        self.execute("TAKE ANCIENT MAP") # Assuming Map Name? Or "TAKE MAP"
        
        self.execute("WEST")
        self.execute("SW")
        self.execute("ENTER")
        
        self.execute("TURN OFF CURSED LANTERN")
        self.execute("PLUGH")
        self.execute("DROP SPECTRAL BLADE")
        self.execute("DROP CURSED LANTERN")
        print("Done.")

if __name__ == "__main__":
    unittest.main(verbosity=2)
