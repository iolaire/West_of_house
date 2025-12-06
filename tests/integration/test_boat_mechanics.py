import unittest
import sys
import os

# Add game-handler to path
game_handler_path = os.path.join(os.getcwd(), 'amplify/functions/game-handler')
sys.path.append(game_handler_path)

from game_engine import GameEngine
from state_manager import GameState
from world_loader import WorldData

class TestBoatMechanics(unittest.TestCase):
    def setUp(self):
        # Clear cache to ensure fresh load
        WorldData.clear_cache()
        
        # Load world data
        data_path = "amplify/functions/game-handler/data"
        self.world_data = WorldData()
        self.world_data.load_from_json(data_path)
        self.engine = GameEngine(self.world_data)
        self.state = GameState("test_user", "west_of_house")

    def test_inflate_boat(self):
        # Start at Dam Base
        self.state.current_room = "dam_base"
        
        # Cheat: Give pump
        self.state.inventory.append("pump")
        
        # Verify initial state
        room = self.world_data.get_room("dam_base")
        if "inflatable_boat" not in room.items:
             room.items.append("inflatable_boat") # Ensure it's there
        
        # Action: INFLATE BOAT
        # Note: We call handle_inflate directly to test logic
        res = self.engine.handle_inflate("inflatable_boat", self.state)
        
        self.assertTrue(res.success, f"Inflate failed: {res.message}")
        self.assertIn("inflated_boat", self.world_data.get_room("dam_base").items)
        self.assertNotIn("inflatable_boat", self.world_data.get_room("dam_base").items)

    def test_puncture_boat(self):
        self.state.current_room = "dam_base"
        room = self.world_data.get_room("dam_base")
        # Ensure inflated boat is there
        if "inflated_boat" not in room.items:
            room.items.append("inflated_boat")
            if "inflatable_boat" in room.items: list(room.items).remove("inflatable_boat")
            
        # Give sharp item
        self.state.inventory.append("knife")
        
        # Action: BOARD BOAT
        res = self.engine.handle_board("inflated_boat", self.state)
        
        self.assertFalse(res.success)
        self.assertIn("punctured", res.message.lower())
        self.assertIn("punctured_boat", room.items)
        self.assertNotIn("inflated_boat", room.items)

    def test_repair_boat(self):
        self.state.current_room = "dam_base"
        room = self.world_data.get_room("dam_base")
        # Ensure punctured boat
        if "punctured_boat" not in room.items:
            room.items.append("punctured_boat")
            
        # Give repair kit (gunk)
        self.state.inventory.append("gunk")
        
        # Action: FIX BOAT
        res = self.engine.handle_fix("punctured_boat", self.state)
        
        self.assertTrue(res.success)
        self.assertIn("inflated_boat", room.items)
        self.assertNotIn("punctured_boat", room.items)

    def test_launch_boat(self):
        self.state.current_room = "dam_base"
        room = self.world_data.get_room("dam_base")
        # Ensure inflated boat
        if "inflated_boat" not in room.items: room.items.append("inflated_boat")
        
        # Board safely
        self.state.inventory = [] # No sharp items
        res_board = self.engine.handle_board("inflated_boat", self.state)
        self.assertTrue(res_board.success)
        self.assertEqual(self.state.current_vehicle, "inflated_boat")
        
        # Launch
        res_launch = self.engine.handle_launch(self.state)
        
        self.assertTrue(res_launch.success)
        self.assertEqual(self.state.current_room, "river_1")
        # Verify boat moved
        self.assertIn("inflated_boat", self.world_data.get_room("river_1").items)
        self.assertNotIn("inflated_boat", self.world_data.get_room("dam_base").items)

if __name__ == '__main__':
    unittest.main()
