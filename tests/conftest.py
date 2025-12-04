"""
Pytest configuration for West of Haunted House tests.

This module provides fixtures and configuration for all tests.
"""

import sys
import os
import pytest

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/lambda/game_handler'))

from world_loader import WorldData


@pytest.fixture(autouse=True)
def clear_world_cache():
    """Clear WorldData cache before each test to ensure fresh data."""
    WorldData.clear_cache()
    yield
    # Optionally clear after test as well
    WorldData.clear_cache()
