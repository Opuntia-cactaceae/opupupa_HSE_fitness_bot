import pytest
from datetime import date
from unittest.mock import AsyncMock

from domain.entities.daily_stats import DailyStats
from application.use_cases.water.get_water_progress import get_water_progress


class TestGetWaterProgress:
    """Тестирование get_water_progress use case."""

    @pytest.mark.asyncio
    async def test_get_water_progress_returns_correct_values(self, mock_uow, sample_daily_stats):
        """Получение прогресса возвращает правильные значения."""
        # Arrange
        user_id = 12345
        today = date.today()

        # Setup sample stats
        sample_daily_stats.water_goal_ml = 2500
        sample_daily_stats.water_logged_ml = 1500
        # water_remaining_ml should be 1000 (2500 - 1500)

        mock_uow.daily_stats.get.return_value = sample_daily_stats

        # Act
        result = await get_water_progress(user_id, mock_uow)

        # Assert
        mock_uow.daily_stats.get.assert_called_once_with(user_id, today)
        assert result == (1500, 2500, 1000)  # (logged, goal, remaining)

    @pytest.mark.asyncio
    async def test_get_water_progress_returns_zeros_when_no_stats(self, mock_uow):
        """Получение прогресса возвращает нули, если статистики нет."""
        # Arrange
        user_id = 12345
        mock_uow.daily_stats.get.return_value = None

        # Act
        result = await get_water_progress(user_id, mock_uow)

        # Assert
        mock_uow.daily_stats.get.assert_called_once_with(user_id, date.today())
        assert result == (0, 0, 0)

    @pytest.mark.asyncio
    async def test_get_water_progress_handles_negative_remaining(self, mock_uow, sample_daily_stats):
        """Получение прогресса корректно обрабатывает отрицательный остаток."""
        # Arrange
        user_id = 12345
        today = date.today()

        # User drank more than goal
        sample_daily_stats.water_goal_ml = 2000
        sample_daily_stats.water_logged_ml = 2500
        # water_remaining_ml should be 0 (max(0, 2000 - 2500))

        mock_uow.daily_stats.get.return_value = sample_daily_stats

        # Act
        result = await get_water_progress(user_id, mock_uow)

        # Assert
        mock_uow.daily_stats.get.assert_called_once_with(user_id, today)
        assert result == (2500, 2000, 0)  # remaining should be 0, not -500

    @pytest.mark.asyncio
    async def test_get_water_progress_calculates_remaining_correctly(self, mock_uow, sample_daily_stats):
        """Проверка правильности расчета оставшейся воды."""
        # Arrange
        user_id = 12345
        today = date.today()

        # Test case 1: normal case
        sample_daily_stats.water_goal_ml = 3000
        sample_daily_stats.water_logged_ml = 1200
        # remaining should be 1800

        mock_uow.daily_stats.get.return_value = sample_daily_stats

        # Act
        result = await get_water_progress(user_id, mock_uow)

        # Assert
        assert result == (1200, 3000, 1800)

        # Test case 2: exact goal reached
        sample_daily_stats.water_logged_ml = 3000
        mock_uow.daily_stats.get.return_value = sample_daily_stats

        result = await get_water_progress(user_id, mock_uow)
        assert result == (3000, 3000, 0)

        # Test case 3: zero goal
        sample_daily_stats.water_goal_ml = 0
        sample_daily_stats.water_logged_ml = 500
        mock_uow.daily_stats.get.return_value = sample_daily_stats

        result = await get_water_progress(user_id, mock_uow)
        assert result == (500, 0, 0)