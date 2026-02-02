import pytest
from unittest.mock import AsyncMock

from application.use_cases.food.start_log_food import start_log_food


class TestStartLogFood:
    """Тестирование start_log_food use case."""

    @pytest.mark.asyncio
    async def test_start_log_food_does_nothing(self, mock_uow):
        """start_log_food ничего не делает (заглушка)."""
        # Arrange
        user_id = 12345

        # Act
        await start_log_food(user_id, mock_uow)

        # Assert
        # Ничего не должно вызываться, это заглушка
        pass