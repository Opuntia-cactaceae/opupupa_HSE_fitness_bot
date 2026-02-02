import pytest
from datetime import date
from unittest.mock import AsyncMock

from application.use_cases.maintenance.ensure_daily_stats import ensure_daily_stats


class TestEnsureDailyStats:
    """Тестирование ensure_daily_stats use case."""

    @pytest.mark.asyncio
    async def test_ensure_daily_stats_calls_get_or_create(self, mock_uow):
        """ensure_daily_stats вызывает get_or_create для текущей даты."""
        # Arrange
        user_id = 12345
        today = date.today()

        # Act
        await ensure_daily_stats(user_id, mock_uow)

        # Assert
        mock_uow.daily_stats.get_or_create.assert_called_once_with(user_id, today)

    @pytest.mark.asyncio
    async def test_ensure_daily_stats_with_different_user_ids(self, mock_uow):
        """ensure_daily_stats работает с разными ID пользователей."""
        # Arrange
        user_ids = [12345, 67890, 11111]
        today = date.today()

        for user_id in user_ids:
            # Reset mock for each test
            mock_uow.daily_stats.get_or_create.reset_mock()

            # Act
            await ensure_daily_stats(user_id, mock_uow)

            # Assert
            mock_uow.daily_stats.get_or_create.assert_called_once_with(user_id, today)

    @pytest.mark.asyncio
    async def test_ensure_daily_stats_does_not_call_other_repositories(self, mock_uow):
        """ensure_daily_stats не вызывает другие репозитории."""
        # Arrange
        user_id = 12345

        # Act
        await ensure_daily_stats(user_id, mock_uow)

        # Assert
        # Only daily_stats.get_or_create should be called
        mock_uow.daily_stats.get_or_create.assert_called_once()

        # Other repositories should not be called
        mock_uow.users.get.assert_not_called()
        mock_uow.users.add.assert_not_called()
        mock_uow.users.update.assert_not_called()
        mock_uow.food_logs.add.assert_not_called()
        mock_uow.workout_logs.add.assert_not_called()
        mock_uow.water_logs.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_daily_stats_with_edge_case_user_ids(self, mock_uow):
        """ensure_daily_stats работает с граничными значениями ID пользователей."""
        # Arrange
        test_cases = [
            (1, "минимальный ID"),
            (999999999, "большой ID"),
            (0, "нулевой ID"),  # хотя 0 не должен быть Telegram ID
            (-1, "отрицательный ID"),  # хотя отрицательные не должны быть Telegram ID
        ]

        today = date.today()

        for user_id, description in test_cases:
            # Reset mock for each test
            mock_uow.daily_stats.get_or_create.reset_mock()

            # Act
            await ensure_daily_stats(user_id, mock_uow)

            # Assert
            mock_uow.daily_stats.get_or_create.assert_called_once_with(user_id, today)

    @pytest.mark.asyncio
    async def test_ensure_daily_stats_returns_nothing(self, mock_uow):
        """ensure_daily_stats не возвращает значение."""
        # Arrange
        user_id = 12345

        # Act
        result = await ensure_daily_stats(user_id, mock_uow)

        # Assert
        assert result is None  # Функция возвращает None