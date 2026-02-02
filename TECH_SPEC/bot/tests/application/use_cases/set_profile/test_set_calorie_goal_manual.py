import pytest
from unittest.mock import AsyncMock

from application.use_cases.set_profile.set_calorie_goal_manual import set_calorie_goal_manual


class TestSetCalorieGoalManual:
    """Тестирование set_calorie_goal_manual use case."""

    @pytest.mark.asyncio
    async def test_set_calorie_goal_manual_updates_existing_user(self, mock_uow, sample_user):
        """Ручная цель калорий обновляется для существующего пользователя."""
        # Arrange
        user_id = 12345
        new_calorie_goal = 2200
        mock_uow.users.get.return_value = sample_user

        # Act
        await set_calorie_goal_manual(user_id, new_calorie_goal, mock_uow)

        # Assert
        mock_uow.users.get.assert_called_once_with(user_id)
        assert sample_user.calorie_goal_kcal_manual == new_calorie_goal
        mock_uow.users.update.assert_called_once_with(sample_user)