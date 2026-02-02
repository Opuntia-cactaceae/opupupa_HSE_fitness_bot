import pytest
from unittest.mock import AsyncMock

from application.use_cases.set_profile.set_calorie_goal_mode import set_calorie_goal_mode


class TestSetCalorieGoalMode:
    """Тестирование set_calorie_goal_mode use case."""

    @pytest.mark.asyncio
    async def test_set_calorie_goal_mode_auto_updates_existing_user(self, mock_uow, sample_user):
        """Режим цели калорий обновляется на 'auto'."""
        # Arrange
        user_id = 12345
        new_mode = "auto"
        mock_uow.users.get.return_value = sample_user

        # Act
        await set_calorie_goal_mode(user_id, new_mode, mock_uow)

        # Assert
        mock_uow.users.get.assert_called_once_with(user_id)
        assert sample_user.calorie_goal_mode == new_mode
        mock_uow.users.update.assert_called_once_with(sample_user)

    @pytest.mark.asyncio
    async def test_set_calorie_goal_mode_manual_updates_existing_user(self, mock_uow, sample_user):
        """Режим цели калорий обновляется на 'manual'."""
        # Arrange
        user_id = 12345
        new_mode = "manual"
        mock_uow.users.get.return_value = sample_user

        # Act
        await set_calorie_goal_mode(user_id, new_mode, mock_uow)

        # Assert
        mock_uow.users.get.assert_called_once_with(user_id)
        assert sample_user.calorie_goal_mode == new_mode
        mock_uow.users.update.assert_called_once_with(sample_user)

    @pytest.mark.asyncio
    async def test_set_calorie_goal_mode_invalid_mode_raises_error(self, mock_uow, sample_user):
        """Некорректный режим вызывает ошибку."""
        # Arrange
        user_id = 12345
        invalid_mode = "invalid"
        mock_uow.users.get.return_value = sample_user

        # Act & Assert
        with pytest.raises(ValueError, match="Mode must be 'auto' or 'manual'"):
            await set_calorie_goal_mode(user_id, invalid_mode, mock_uow)

        mock_uow.users.get.assert_not_called()
        mock_uow.users.update.assert_not_called()