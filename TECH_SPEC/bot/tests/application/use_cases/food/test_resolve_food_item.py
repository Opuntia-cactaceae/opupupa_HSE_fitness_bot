import pytest
from unittest.mock import AsyncMock, patch

from application.use_cases.food.resolve_food_item import resolve_food_item


class TestResolveFoodItem:
    """Тестирование resolve_food_item use case."""

    @pytest.mark.asyncio
    async def test_resolve_food_item_calls_food_client(self):
        """resolve_food_item вызывает FoodClient."""
        # Arrange
        query = "яблоко"
        expected_result = ("Яблоко", 52.0)

        with patch('application.use_cases.food.resolve_food_item.FoodClient') as MockFoodClient, \
             patch('application.use_cases.food.resolve_food_item.settings') as mock_settings:

            mock_client = AsyncMock()
            mock_client.search_product.return_value = expected_result
            MockFoodClient.return_value = mock_client

            # Act
            result = await resolve_food_item(query)

            # Assert
            MockFoodClient.assert_called_once()
            mock_client.search_product.assert_called_once_with(query)
            assert result == expected_result

    @pytest.mark.asyncio
    async def test_resolve_food_item_returns_none_when_no_match(self):
        """resolve_food_item возвращает None, если продукт не найден."""
        # Arrange
        query = "несуществующий продукт"

        with patch('application.use_cases.food.resolve_food_item.FoodClient') as MockFoodClient, \
             patch('application.use_cases.food.resolve_food_item.settings') as mock_settings:

            mock_client = AsyncMock()
            mock_client.search_product.return_value = None
            MockFoodClient.return_value = mock_client

            # Act
            result = await resolve_food_item(query)

            # Assert
            mock_client.search_product.assert_called_once_with(query)
            assert result is None