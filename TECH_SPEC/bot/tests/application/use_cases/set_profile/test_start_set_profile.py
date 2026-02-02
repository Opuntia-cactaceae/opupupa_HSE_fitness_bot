import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from application.use_cases.set_profile.start_set_profile import start_set_profile


class TestStartSetProfile:
    """Тестирование start_set_profile use case."""

    @pytest.mark.asyncio
    async def test_start_set_profile_creates_user_when_not_exists(self, mock_uow, sample_user):
        """Пользователь создается, если его нет в базе."""
        # Arrange
        user_id = 12345
        mock_uow.users.get.return_value = None

        # Act
        await start_set_profile(user_id, mock_uow)

        # Assert
        mock_uow.users.get.assert_called_once_with(user_id)
        mock_uow.users.add.assert_called_once()
        added_user = mock_uow.users.add.call_args[0][0]
        assert added_user.id == user_id
        assert added_user.weight_kg == 0.0
        assert added_user.height_cm == 0.0
        assert added_user.age_years == 0
        assert added_user.activity_minutes_per_day == 0
        assert added_user.city == ""
        assert added_user.calorie_goal_mode == "auto"
        assert added_user.calorie_goal_kcal_manual is None

    @pytest.mark.asyncio
    async def test_start_set_profile_does_nothing_when_user_exists(self, mock_uow, sample_user):
        """Ничего не происходит, если пользователь уже существует."""
        # Arrange
        user_id = 12345
        mock_uow.users.get.return_value = sample_user

        # Act
        await start_set_profile(user_id, mock_uow)

        # Assert
        mock_uow.users.get.assert_called_once_with(user_id)
        mock_uow.users.add.assert_not_called()