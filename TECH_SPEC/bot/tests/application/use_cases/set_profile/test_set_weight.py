import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from application.use_cases.set_profile.set_weight import set_weight


class TestSetWeight:
    """Тестирование set_weight use case."""

    @pytest.mark.asyncio
    async def test_set_weight_updates_existing_user(self, mock_uow, sample_user):
        """Вес обновляется для существующего пользователя."""
        # Arrange
        user_id = 12345
        new_weight = 75.5
        mock_uow.users.get.return_value = sample_user

        # Act
        await set_weight(user_id, new_weight, mock_uow)

        # Assert
        mock_uow.users.get.assert_called_once_with(user_id)
        assert sample_user.weight_kg == new_weight
        assert sample_user.updated_at > datetime(2024, 1, 1, 12, 0, 0)
        mock_uow.users.update.assert_called_once_with(sample_user)

    @pytest.mark.asyncio
    async def test_set_weight_raises_error_when_user_not_found(self, mock_uow):
        """Выбрасывается ошибка, если пользователь не найден."""
        # Arrange
        user_id = 99999
        new_weight = 75.5
        mock_uow.users.get.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match=f"User {user_id} not found"):
            await set_weight(user_id, new_weight, mock_uow)

        mock_uow.users.get.assert_called_once_with(user_id)
        mock_uow.users.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_weight_does_not_create_daily_stats(self, mock_uow, sample_user):
        """set_weight не создаёт daily_stats."""
        # Arrange
        user_id = 12345
        new_weight = 75.5
        mock_uow.users.get.return_value = sample_user
        # Mock daily_stats.get_or_create to track calls
        mock_uow.daily_stats.get_or_create = AsyncMock()

        # Act
        await set_weight(user_id, new_weight, mock_uow)

        # Assert
        mock_uow.daily_stats.get_or_create.assert_not_called()