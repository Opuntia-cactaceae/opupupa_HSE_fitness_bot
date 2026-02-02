import pytest
from unittest.mock import AsyncMock

from application.use_cases.workout.start_log_workout import start_log_workout


class TestStartLogWorkout:
    """Тестирование start_log_workout use case."""

    @pytest.mark.asyncio
    async def test_start_log_workout_does_nothing(self, mock_uow):
        """start_log_workout ничего не делает (заглушка)."""
        # Arrange
        user_id = 12345

        # Act
        await start_log_workout(user_id, mock_uow)

        # Assert
        # Ничего не должно вызываться, это заглушка
        pass