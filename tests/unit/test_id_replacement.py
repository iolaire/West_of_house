import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler'))

from game_engine import GameEngine, ActionResult
from state_manager import GameState
from world_loader import WorldData, Room, GameObject, Interaction

class TestIdReplacement(unittest.TestCase):
    def setUp(self):
        self.world = WorldData()
        # Mock data loading or load actual data
        data_dir = os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler/data')
        self.world.load_from_json(data_dir)
        self.engine = GameEngine(self.world)
        self.state = GameState.create_new_game()

    def test_examine_missing_object_uses_name(self):
        # We can't easily test "missing object uses name" because if it's missing, we can't look up its name!
        # Unless we try to examine something that exists in world but not in room.
        
        # 'kitchen_window' is in 'east_of_house'. Let's be in 'west_of_house'.
        self.state.current_room = "west_of_house"
        
        # Try to examine kitchen_window
        result = self.engine.handle_examine("kitchen_window", self.state)
        
        # Should fail
        self.assertFalse(result.success)
        # Should use display name "broken window" (or similar) instead of "kitchen_window"
        # Note: The fix for handle_examine was done previously.
        # But let's verify it doesn't say "kitchen_window".
        self.assertNotIn("kitchen_window", result.message)
        self.assertIn("broken window", result.message.lower())

    def test_take_missing_object_uses_name(self):
        # Try to take kitchen_window from west_of_house
        self.state.current_room = "west_of_house"
        result = self.engine.handle_take("kitchen_window", self.state)
        
        self.assertFalse(result.success)
        self.assertNotIn("kitchen_window", result.message)
        self.assertIn("broken window", result.message.lower())

    def test_open_already_open_uses_name(self):
        # Move to east_of_house where window is
        self.state.current_room = "east_of_house"
        
        # Open window
        self.engine.handle_object_interaction("OPEN", "kitchen_window", self.state)
        
        # Try to open again
        result = self.engine.handle_object_interaction("OPEN", "kitchen_window", self.state)
        
        self.assertFalse(result.success)
        self.assertNotIn("kitchen_window", result.message)
        self.assertIn("broken window", result.message.lower())
        self.assertIn("already open", result.message)



class TestHandlerIdReplacement(unittest.TestCase):
    def setUp(self):
        self.world = MagicMock(spec=WorldData)
        self.engine = GameEngine(self.world)
        self.state = MagicMock(spec=GameState)
        self.state.inventory = []
        self.state.current_room = "start_room"
        self.state.sanity = 100
        
        # Mock _get_object_names to return a predictable name
        self.engine._get_object_names = MagicMock(return_value="Display Name")
        
        # Setup common objects
        self.room = MagicMock(spec=Room)
        self.room.items = []
        self.world.get_room.return_value = self.room
        
        self.obj = MagicMock(spec=GameObject)
        self.obj.name = "Test Object"
        self.obj.interactions = []
        self.obj.state = {}
        self.world.get_object.return_value = self.obj

    def test_handle_listen_missing_object(self):
        result = self.engine.handle_listen("missing_obj", self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("missing_obj")

    def test_handle_smell_missing_object(self):
        result = self.engine.handle_smell("missing_obj", self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("missing_obj")

    def test_handle_burn_missing_object(self):
        result = self.engine.handle_burn("missing_obj", None, self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("missing_obj")

    def test_handle_burn_not_flammable(self):
        self.room.items = ["obj"]
        self.obj.state = {'is_flammable': False}
        result = self.engine.handle_burn("obj", None, self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("obj")

    def test_handle_cut_missing_object(self):
        result = self.engine.handle_cut("missing_obj", None, self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("missing_obj")

    def test_handle_cut_not_cuttable(self):
        self.room.items = ["obj"]
        self.obj.state = {'is_cuttable': False}
        result = self.engine.handle_cut("obj", None, self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("obj")

    def test_handle_dig_missing_location(self):
        result = self.engine.handle_dig("missing_loc", None, self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("missing_loc")

    def test_handle_dig_not_diggable(self):
        self.room.items = ["loc"]
        self.obj.state = {'is_diggable': False}
        result = self.engine.handle_dig("loc", None, self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("loc")

    def test_handle_destroy_missing_object(self):
        result = self.engine.handle_destroy("missing_obj", self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("missing_obj")

    def test_handle_inflate_missing_object(self):
        result = self.engine.handle_inflate("missing_obj", self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("missing_obj")

    def test_handle_inflate_not_inflatable(self):
        self.room.items = ["obj"]
        self.obj.state = {'is_inflatable': False}
        result = self.engine.handle_inflate("obj", self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("obj")

    def test_handle_deflate_missing_object(self):
        result = self.engine.handle_deflate("missing_obj", self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("missing_obj")

    def test_handle_wave_missing_object(self):
        result = self.engine.handle_wave("missing_obj", self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("missing_obj")

    def test_handle_rub_missing_object(self):
        result = self.engine.handle_rub("missing_obj", self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("missing_obj")

    def test_handle_shake_missing_object(self):
        result = self.engine.handle_shake("missing_obj", self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("missing_obj")

    def test_handle_ring_missing_object(self):
        result = self.engine.handle_ring("missing_obj", self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("missing_obj")

    def test_handle_cross_missing_object(self):
        result = self.engine.handle_cross("missing_obj", self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("missing_obj")

    def test_handle_enter_missing_object(self):
        result = self.engine.handle_enter("missing_obj", self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("missing_obj")

    def test_handle_climb_missing_object(self):
        # Must be in room with valid exit for "climb UP/DOWN" first, 
        # or we just test the object not found logic.
        # Logic says: if object_id specified, check if in room. If not, error.
        result = self.engine.handle_climb("UP", "missing_obj", self.state)
        self.assertFalse(result.success)
        # The logic validates direction first (needs to be in exits).
        # Let's assume start_room has UP exit? By default mock room has empty exits.
        # We need to setup room exits for this test if we want to reach object check.
        # But actually "There's nothing to climb up here" fails first.
        # Let's add exit.
        self.room.exits = {"UP": "some_room"}
        result = self.engine.handle_climb("UP", "missing_obj", self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("missing_obj")
    
    def test_handle_squeeze_missing_object(self):
        result = self.engine.handle_squeeze("missing_obj", self.state)
        self.assertFalse(result.success)
        self.assertIn("Display Name", result.message)
        self.engine._get_object_names.assert_called_with("missing_obj")

if __name__ == '__main__':
    unittest.main()
