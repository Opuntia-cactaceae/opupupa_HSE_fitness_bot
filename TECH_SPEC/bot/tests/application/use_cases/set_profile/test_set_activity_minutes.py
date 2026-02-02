import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from application.use_cases.set_profile.set_activity_minutes import set_activity_minutes


class TestSetActivityMinutes:
    """Тестирование set_activity_minutes use case."""

    @pytest.mark.asyncio
    async def test_set_activity_minutes_updates_existing_user(self, mock_uow, sample_user):
        """Активность обновляется для существующего пользователя."""
        # Arrange
        user_id = 12345
        new_activity = 90
        mock_uow.users.get.return_value = sample_user

        # Act
        await set_activity_minutes(user_id, new_activity, mock_uow)

        # Assert
        mock_uow.users.get.assert_called_once_with(user_id)
        assert sample_user.activity_minutes_per_day == new_activity
        assert sample_user.updated_at > datetime(2024, 1, 1, 12, 0, 0)
        mock_uow.users.update.assert_called_once_with(sample_user)