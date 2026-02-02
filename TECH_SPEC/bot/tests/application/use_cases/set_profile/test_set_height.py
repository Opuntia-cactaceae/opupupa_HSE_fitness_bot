import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from application.use_cases.set_profile.set_height import set_height


class TestSetHeight:
    """Тестирование set_height use case."""

    @pytest.mark.asyncio
    async def test_set_height_updates_existing_user(self, mock_uow, sample_user):
        """Рост обновляется для существующего пользователя."""
        # Arrange
        user_id = 12345
        new_height = 180.0
        mock_uow.users.get.return_value = sample_user

        # Act
        await set_height(user_id, new_height, mock_uow)

        # Assert
        mock_uow.users.get.assert_called_once_with(user_id)
        assert sample_user.height_cm == new_height
        assert sample_user.updated_at > datetime(2024, 1, 1, 12, 0, 0)
        mock_uow.users.update.assert_called_once_with(sample_user)

    @pytest.mark.asyncio
    async def test_set_height_raises_error_when_user_not_found(self, mock_uow):
        """Выбрасывается ошибка, если пользователь не найден."""
        # Arrange
        user_id = 99999
        new_height = 180.0
        mock_uow.users.get.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match=f"User {user_id} not found"):
            await set_height(user_id, new_height, mock_uow)