import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from application.use_cases.set_profile.set_age import set_age


class TestSetAge:
    """Тестирование set_age use case."""

    @pytest.mark.asyncio
    async def test_set_age_updates_existing_user(self, mock_uow, sample_user):
        """Возраст обновляется для существующего пользователя."""
        # Arrange
        user_id = 12345
        new_age = 35
        mock_uow.users.get.return_value = sample_user

        # Act
        await set_age(user_id, new_age, mock_uow)

        # Assert
        mock_uow.users.get.assert_called_once_with(user_id)
        assert sample_user.age_years == new_age
        assert sample_user.updated_at > datetime(2024, 1, 1, 12, 0, 0)
        mock_uow.users.update.assert_called_once_with(sample_user)