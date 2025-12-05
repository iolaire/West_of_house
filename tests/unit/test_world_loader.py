"""
Unit tests for world_loader.py

Tests JSON loading, parsing, error handling, and caching behavior.
"""

import pytest
import json
import os
import tempfile
import shutil
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../amplify/functions/game-handler'))

from world_loader import WorldData, Room, GameObject, Interaction


class TestWorldDataLoading:
    """Test basic loading functionality."""
    
    @pytest.fixture
    def data_dir(self):
        """Fixture providing path to actual game data."""
        return os.path.join(
            os.path.dirname(__file__),
            '../../amplify/functions/game-handler/data'
        )
    
    @pytest.fixture
    def world_data(self):
        """Fixture providing a fresh WorldData instance."""
        # Clear cache before each test
        WorldData.clear_cache()
        return WorldData()
    
    def test_load_from_json_success(self, world_data, data_dir):
        """Test successful loading of JSON data files."""
        world_data.load_from_json(data_dir)
        
        # Verify data was loaded
        assert len(world_data.rooms) > 0
        assert len(world_data.objects) > 0
        assert len(world_data.initial_flags) > 0
        assert world_data._loaded is True
    
    def test_rooms_have_required_fields(self, world_data, data_dir):
        """Test that loaded rooms have all required fields."""
        world_data.load_from_json(data_dir)
        
        # Check a known room
        room = world_data.get_room('west_of_house')
        assert room.id == 'west_of_house'
        assert room.name is not None
        assert room.description_spooky is not None
        assert isinstance(room.exits, dict)
        assert isinstance(room.items, list)
    
    def test_objects_have_required_fields(self, world_data, data_dir):
        """Test that loaded objects have all required fields."""
        world_data.load_from_json(data_dir)
        
        # Check a known object
        obj = world_data.get_object('mailbox')
        assert obj.id == 'mailbox'
        assert obj.name is not None
        assert obj.type is not None
        assert isinstance(obj.state, dict)
        assert isinstance(obj.interactions, list)
    
    def test_objects_have_spooky_responses(self, world_data, data_dir):
        """Test that object interactions have spooky responses."""
        world_data.load_from_json(data_dir)
        
        obj = world_data.get_object('mailbox')
        assert len(obj.interactions) > 0
        
        # Check that interactions have response_spooky
        for interaction in obj.interactions:
            assert interaction.response_spooky is not None
            assert len(interaction.response_spooky) > 0
    
    def test_initial_flags_loaded(self, world_data, data_dir):
        """Test that initial flags are loaded correctly."""
        world_data.load_from_json(data_dir)
        
        # Check for expected flags
        assert 'sanity' in world_data.initial_flags
        assert 'cursed' in world_data.initial_flags
        assert 'blood_moon_active' in world_data.initial_flags
        assert 'score' in world_data.initial_flags
        assert 'moves' in world_data.initial_flags


class TestWorldDataErrorHandling:
    """Test error handling for invalid data."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def world_data(self):
        """Fixture providing a fresh WorldData instance."""
        WorldData.clear_cache()
        return WorldData()
    
    def test_missing_rooms_file(self, world_data, temp_dir):
        """Test error handling when rooms file is missing."""
        # Create only objects and flags files
        with open(os.path.join(temp_dir, 'objects_haunted.json'), 'w') as f:
            json.dump({}, f)
        with open(os.path.join(temp_dir, 'flags_haunted.json'), 'w') as f:
            json.dump({}, f)
        
        with pytest.raises(FileNotFoundError) as exc_info:
            world_data.load_from_json(temp_dir)
        assert 'rooms_haunted.json' in str(exc_info.value)
    
    def test_missing_objects_file(self, world_data, temp_dir):
        """Test error handling when objects file is missing."""
        # Create only rooms and flags files
        with open(os.path.join(temp_dir, 'rooms_haunted.json'), 'w') as f:
            json.dump({}, f)
        with open(os.path.join(temp_dir, 'flags_haunted.json'), 'w') as f:
            json.dump({}, f)
        
        with pytest.raises(FileNotFoundError) as exc_info:
            world_data.load_from_json(temp_dir)
        assert 'objects_haunted.json' in str(exc_info.value)
    
    def test_missing_flags_file(self, world_data, temp_dir):
        """Test error handling when flags file is missing."""
        # Create only rooms and objects files
        with open(os.path.join(temp_dir, 'rooms_haunted.json'), 'w') as f:
            json.dump({}, f)
        with open(os.path.join(temp_dir, 'objects_haunted.json'), 'w') as f:
            json.dump({}, f)
        
        with pytest.raises(FileNotFoundError) as exc_info:
            world_data.load_from_json(temp_dir)
        assert 'flags_haunted.json' in str(exc_info.value)
    
    def test_malformed_json(self, world_data, temp_dir):
        """Test error handling for malformed JSON."""
        # Create files with invalid JSON
        with open(os.path.join(temp_dir, 'rooms_haunted.json'), 'w') as f:
            f.write('{ invalid json }')
        with open(os.path.join(temp_dir, 'objects_haunted.json'), 'w') as f:
            json.dump({}, f)
        with open(os.path.join(temp_dir, 'flags_haunted.json'), 'w') as f:
            json.dump({}, f)
        
        with pytest.raises(json.JSONDecodeError):
            world_data.load_from_json(temp_dir)
    
    def test_missing_required_room_field(self, world_data, temp_dir):
        """Test error handling when room is missing required field."""
        # Create room without description_spooky
        rooms_data = {
            'test_room': {
                'name': 'Test Room',
                'exits': {},
                'items': []
                # Missing description_spooky
            }
        }
        
        with open(os.path.join(temp_dir, 'rooms_haunted.json'), 'w') as f:
            json.dump(rooms_data, f)
        with open(os.path.join(temp_dir, 'objects_haunted.json'), 'w') as f:
            json.dump({}, f)
        with open(os.path.join(temp_dir, 'flags_haunted.json'), 'w') as f:
            json.dump({}, f)
        
        with pytest.raises(ValueError) as exc_info:
            world_data.load_from_json(temp_dir)
        assert 'test_room' in str(exc_info.value)
        assert 'description_spooky' in str(exc_info.value)
    
    def test_missing_required_object_field(self, world_data, temp_dir):
        """Test error handling when object is missing required field."""
        # Create object without interactions
        objects_data = {
            'test_object': {
                'name': 'Test Object',
                'type': 'item',
                'state': {}
                # Missing interactions
            }
        }
        
        with open(os.path.join(temp_dir, 'rooms_haunted.json'), 'w') as f:
            json.dump({}, f)
        with open(os.path.join(temp_dir, 'objects_haunted.json'), 'w') as f:
            json.dump(objects_data, f)
        with open(os.path.join(temp_dir, 'flags_haunted.json'), 'w') as f:
            json.dump({}, f)
        
        with pytest.raises(ValueError) as exc_info:
            world_data.load_from_json(temp_dir)
        assert 'test_object' in str(exc_info.value)
        assert 'interactions' in str(exc_info.value)


class TestWorldDataAccess:
    """Test data access methods."""
    
    @pytest.fixture
    def data_dir(self):
        """Fixture providing path to actual game data."""
        return os.path.join(
            os.path.dirname(__file__),
            '../../amplify/functions/game-handler/data'
        )
    
    @pytest.fixture
    def loaded_world_data(self, data_dir):
        """Fixture providing a loaded WorldData instance."""
        WorldData.clear_cache()
        world_data = WorldData()
        world_data.load_from_json(data_dir)
        return world_data
    
    def test_get_room_success(self, loaded_world_data):
        """Test successful room retrieval."""
        room = loaded_world_data.get_room('west_of_house')
        assert room.id == 'west_of_house'
        assert isinstance(room, Room)
    
    def test_get_room_not_found(self, loaded_world_data):
        """Test error when room doesn't exist."""
        with pytest.raises(ValueError) as exc_info:
            loaded_world_data.get_room('nonexistent_room')
        assert 'not found' in str(exc_info.value).lower()
    
    def test_get_room_before_loading(self):
        """Test error when accessing room before loading data."""
        WorldData.clear_cache()
        world_data = WorldData()
        
        with pytest.raises(ValueError) as exc_info:
            world_data.get_room('west_of_house')
        assert 'not loaded' in str(exc_info.value).lower()
    
    def test_get_object_success(self, loaded_world_data):
        """Test successful object retrieval."""
        obj = loaded_world_data.get_object('mailbox')
        assert obj.id == 'mailbox'
        assert isinstance(obj, GameObject)
    
    def test_get_object_not_found(self, loaded_world_data):
        """Test error when object doesn't exist."""
        with pytest.raises(ValueError) as exc_info:
            loaded_world_data.get_object('nonexistent_object')
        assert 'not found' in str(exc_info.value).lower()
    
    def test_get_object_before_loading(self):
        """Test error when accessing object before loading data."""
        WorldData.clear_cache()
        world_data = WorldData()
        
        with pytest.raises(ValueError) as exc_info:
            world_data.get_object('mailbox')
        assert 'not loaded' in str(exc_info.value).lower()
    
    def test_get_room_description_returns_spooky(self, loaded_world_data):
        """Test that room description always returns spooky variant."""
        room_id = 'west_of_house'
        description = loaded_world_data.get_room_description(room_id, sanity_level=100)
        
        # Should return spooky description
        room = loaded_world_data.get_room(room_id)
        assert description == room.description_spooky
        assert description != room.description_original
    
    def test_get_room_description_ignores_sanity(self, loaded_world_data):
        """Test that room description is same regardless of sanity level."""
        room_id = 'west_of_house'
        
        desc_high_sanity = loaded_world_data.get_room_description(room_id, sanity_level=100)
        desc_low_sanity = loaded_world_data.get_room_description(room_id, sanity_level=0)
        
        # Should be the same (always spooky)
        assert desc_high_sanity == desc_low_sanity


class TestWorldDataCaching:
    """Test caching behavior for Lambda warm starts."""
    
    @pytest.fixture
    def data_dir(self):
        """Fixture providing path to actual game data."""
        return os.path.join(
            os.path.dirname(__file__),
            '../../amplify/functions/game-handler/data'
        )
    
    def test_cache_is_populated_after_first_load(self, data_dir):
        """Test that cache is populated after first load."""
        WorldData.clear_cache()
        
        # First load should populate cache
        world_data1 = WorldData()
        world_data1.load_from_json(data_dir)
        
        assert WorldData._cache is not None
        assert 'rooms' in WorldData._cache
        assert 'objects' in WorldData._cache
        assert 'initial_flags' in WorldData._cache
    
    def test_second_load_uses_cache(self, data_dir):
        """Test that second load uses cached data."""
        WorldData.clear_cache()
        
        # First load
        world_data1 = WorldData()
        world_data1.load_from_json(data_dir)
        rooms_count1 = len(world_data1.rooms)
        
        # Second load should use cache
        world_data2 = WorldData()
        world_data2.load_from_json(data_dir)
        rooms_count2 = len(world_data2.rooms)
        
        # Should have same data
        assert rooms_count1 == rooms_count2
        assert world_data2._loaded is True
    
    def test_cache_contains_same_data(self, data_dir):
        """Test that cached data is identical to original."""
        WorldData.clear_cache()
        
        # First load
        world_data1 = WorldData()
        world_data1.load_from_json(data_dir)
        room1 = world_data1.get_room('west_of_house')
        
        # Second load from cache
        world_data2 = WorldData()
        world_data2.load_from_json(data_dir)
        room2 = world_data2.get_room('west_of_house')
        
        # Should be the same room object (from cache)
        assert room1 is room2
    
    def test_clear_cache(self, data_dir):
        """Test that clear_cache removes cached data."""
        # Load data to populate cache
        world_data = WorldData()
        world_data.load_from_json(data_dir)
        assert WorldData._cache is not None
        
        # Clear cache
        WorldData.clear_cache()
        assert WorldData._cache is None
