import sys
import os

# Add the bot directory to Python path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock pydantic_settings before it gets imported
from unittest.mock import MagicMock

# Create mock for pydantic_settings
class MockBaseSettings:
    pass

class MockSettingsConfigDict:
    pass

mock_pydantic_settings = MagicMock()
mock_pydantic_settings.BaseSettings = MockBaseSettings
mock_pydantic_settings.SettingsConfigDict = MockSettingsConfigDict

# Create mock for config.settings module
mock_config_settings = MagicMock()
mock_config_settings.settings = MagicMock()
mock_config_settings.settings.WEATHER_API_KEY = "test-api-key"
mock_config_settings.settings.FOOD_API_KEY = "test-food-api-key"

# Create mock for config module
mock_config = MagicMock()
mock_config.settings = mock_config_settings

# Patch sys.modules before any imports
sys.modules['pydantic_settings'] = mock_pydantic_settings
sys.modules['config'] = mock_config
sys.modules['config.settings'] = mock_config_settings

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, MagicMock
from typing import Dict, Any, Optional

from domain.interfaces.unit_of_work import UnitOfWork
from domain.interfaces.user_repository import UserRepository
from domain.interfaces.daily_stats_repository import DailyStatsRepository
from domain.interfaces.food_log_repository import FoodLogRepository
from domain.interfaces.workout_log_repository import WorkoutLogRepository
from domain.interfaces.water_log_repository import WaterLogRepository


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_user_repository():
    """Mock UserRepository."""
    mock = AsyncMock(spec=UserRepository)
    mock.get = AsyncMock()
    mock.add = AsyncMock()
    mock.update = AsyncMock()
    return mock


@pytest.fixture
def mock_daily_stats_repository():
    """Mock DailyStatsRepository."""
    mock = AsyncMock(spec=DailyStatsRepository)
    mock.get = AsyncMock()
    mock.get_or_create = AsyncMock()
    mock.update = AsyncMock()
    mock.get_for_user_in_range = AsyncMock()
    return mock


@pytest.fixture
def mock_food_log_repository():
    """Mock FoodLogRepository."""
    mock = AsyncMock(spec=FoodLogRepository)
    mock.add = AsyncMock()
    return mock


@pytest.fixture
def mock_workout_log_repository():
    """Mock WorkoutLogRepository."""
    mock = AsyncMock(spec=WorkoutLogRepository)
    mock.add = AsyncMock()
    return mock


@pytest.fixture
def mock_water_log_repository():
    """Mock WaterLogRepository."""
    mock = AsyncMock(spec=WaterLogRepository)
    mock.add = AsyncMock()
    return mock


@pytest.fixture
def mock_uow(
    mock_user_repository,
    mock_daily_stats_repository,
    mock_food_log_repository,
    mock_workout_log_repository,
    mock_water_log_repository,
):
    """Mock UnitOfWork with all repositories."""
    mock = AsyncMock(spec=UnitOfWork)

    # Setup repository properties
    type(mock).users = mock_user_repository
    type(mock).daily_stats = mock_daily_stats_repository
    type(mock).food_logs = mock_food_log_repository
    type(mock).workout_logs = mock_workout_log_repository
    type(mock).water_logs = mock_water_log_repository

    # Setup async context manager
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=None)

    return mock


@pytest.fixture
def sample_user():
    """Create a sample user entity for testing."""
    from datetime import datetime
    from domain.entities.user import User

    return User(
        id=12345,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
        weight_kg=70.0,
        height_cm=175.0,
        age_years=30,
        sex="male",
        activity_minutes_per_day=60,
        city="Moscow",
        timezone="Europe/Moscow",
        calorie_goal_mode="auto",
        calorie_goal_kcal_manual=None,
    )


@pytest.fixture
def sample_daily_stats():
    """Create sample daily stats for testing."""
    from datetime import date, datetime
    from domain.entities.daily_stats import DailyStats

    return DailyStats(
        id=1,
        user_id=12345,
        date=date(2024, 1, 1),
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
        temperature_c=20.0,
        water_goal_ml=2500,
        water_logged_ml=500,
        calories_consumed_kcal=1500,
        calories_burned_kcal=300,
        calorie_goal_kcal=2000,
    )