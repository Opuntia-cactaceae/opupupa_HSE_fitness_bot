import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, patch

from domain.entities.water_log import WaterLog
from domain.entities.daily_stats import DailyStats
from application.use_cases.water.log_water import log_water


class TestLogWater:
    """Тестирование log_water use case."""

    @pytest.mark.asyncio
    @patch('application.use_cases.set_profile.finalize_profile.WeatherClient')
    async def test_log_water_creates_water_log_and_updates_stats(self, MockWeatherClient, mock_uow, sample_daily_stats, sample_user):
        """Добавление воды создает запись и обновляет статистику."""
        # Arrange
        user_id = 12345
        water_ml = 500
        today = date.today()

        mock_uow.users.get.return_value = sample_user
        mock_uow.daily_stats.get_or_create.return_value = sample_daily_stats
        mock_uow.daily_stats.get.return_value = sample_daily_stats
        initial_water_logged = sample_daily_stats.water_logged_ml

        # Mock weather client
        mock_weather_client = AsyncMock()
        mock_weather_client.get_temperature.return_value = None
        MockWeatherClient.return_value = mock_weather_client

        # Act
        await log_water(user_id, water_ml, mock_uow)

        # Assert
        # Check WaterLog creation
        mock_uow.water_logs.add.assert_called_once()
        water_log = mock_uow.water_logs.add.call_args[0][0]
        assert isinstance(water_log, WaterLog)
        assert water_log.user_id == user_id
        assert water_log.date == today
        assert water_log.ml == water_ml

        # Check DailyStats update
        mock_uow.daily_stats.get_or_create.assert_called_once_with(user_id, today)
        assert sample_daily_stats.water_logged_ml == initial_water_logged + water_ml
        assert sample_daily_stats.updated_at > datetime(2024, 1, 1, 12, 0, 0)
        assert mock_uow.daily_stats.update.call_count == 2

    @pytest.mark.asyncio
    @patch('application.use_cases.set_profile.finalize_profile.WeatherClient')
    async def test_log_water_creates_new_daily_stats_if_not_exists(self, MockWeatherClient, mock_uow, sample_user):
        """Добавление воды создает новую DailyStats, если её нет."""
        # Arrange
        user_id = 12345
        water_ml = 500
        today = date.today()

        mock_uow.users.get.return_value = sample_user
        # Create new DailyStats
        new_daily_stats = DailyStats(
            id=1,
            user_id=user_id,
            date=today,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            water_logged_ml=0,
            water_goal_ml=2500,
        )
        mock_uow.daily_stats.get_or_create.return_value = new_daily_stats
        mock_uow.daily_stats.get.return_value = new_daily_stats

        # Mock weather client
        mock_weather_client = AsyncMock()
        mock_weather_client.get_temperature.return_value = None
        MockWeatherClient.return_value = mock_weather_client

        # Act
        await log_water(user_id, water_ml, mock_uow)

        # Assert
        mock_uow.daily_stats.get_or_create.assert_called_once_with(user_id, today)
        assert new_daily_stats.water_logged_ml == water_ml
        assert mock_uow.daily_stats.update.call_count == 2