import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

from domain.entities.food_log import FoodLog
from application.use_cases.food.finalize_food_log import finalize_food_log


class TestFinalizeFoodLog:
    """Тестирование finalize_food_log use case."""

    @pytest.mark.asyncio
    async def test_finalize_food_log_creates_log_and_updates_stats(self, mock_uow, sample_daily_stats):
        """finalize_food_log создает запись и обновляет статистику."""
        # Arrange
        user_id = 12345
        product_query = "яблоко"
        product_name = "Яблоко"
        source = "api"
        kcal_per_100g = 52.0
        grams = 200.0
        kcal_total = 104.0  # (52/100)*200

        today = date.today()
        mock_uow.daily_stats.get_or_create.return_value = sample_daily_stats
        initial_calories_consumed = sample_daily_stats.calories_consumed_kcal

        # Act
        await finalize_food_log(
            user_id, product_query, product_name, source,
            kcal_per_100g, grams, kcal_total, mock_uow
        )

        # Assert
        # Check FoodLog creation
        mock_uow.food_logs.add.assert_called_once()
        food_log = mock_uow.food_logs.add.call_args[0][0]
        assert isinstance(food_log, FoodLog)
        assert food_log.user_id == user_id
        assert food_log.date == today
        assert food_log.product_query == product_query
        assert food_log.product_name == product_name
        assert food_log.source == source
        assert food_log.kcal_per_100g == kcal_per_100g
        assert food_log.grams == grams
        assert food_log.kcal_total == kcal_total
        assert food_log.product_external_id is None

        # Check DailyStats update
        mock_uow.daily_stats.get_or_create.assert_called_once_with(user_id, today)
        assert sample_daily_stats.calories_consumed_kcal == initial_calories_consumed + int(kcal_total)
        assert sample_daily_stats.updated_at > datetime(2024, 1, 1, 12, 0, 0)
        mock_uow.daily_stats.update.assert_called_once_with(sample_daily_stats)

    @pytest.mark.asyncio
    async def test_finalize_food_log_with_negative_kcal_total(self, mock_uow, sample_daily_stats):
        """finalize_food_log работает с отрицательными калориями (не должно быть, но проверим)."""
        # Arrange
        user_id = 12345
        product_query = "продукт"
        product_name = "Продукт"
        source = "manual"
        kcal_per_100g = -50.0  # Негативные калории не должны быть в реальности
        grams = 100.0
        kcal_total = -50.0

        today = date.today()
        mock_uow.daily_stats.get_or_create.return_value = sample_daily_stats
        initial_calories_consumed = sample_daily_stats.calories_consumed_kcal

        # Act
        await finalize_food_log(
            user_id, product_query, product_name, source,
            kcal_per_100g, grams, kcal_total, mock_uow
        )

        # Assert
        # Калории должны обновиться (даже если отрицательные)
        assert sample_daily_stats.calories_consumed_kcal == initial_calories_consumed + int(kcal_total)

    @pytest.mark.asyncio
    async def test_finalize_food_log_creates_new_daily_stats(self, mock_uow):
        """finalize_food_log создает новую DailyStats, если её нет."""
        # Arrange
        user_id = 12345
        product_query = "банан"
        product_name = "Банан"
        source = "api"
        kcal_per_100g = 89.0
        grams = 150.0
        kcal_total = 133.5

        today = date.today()

        # Create new DailyStats
        new_daily_stats = MagicMock()
        new_daily_stats.calories_consumed_kcal = 0
        new_daily_stats.updated_at = datetime.utcnow()

        mock_uow.daily_stats.get_or_create.return_value = new_daily_stats

        # Act
        await finalize_food_log(
            user_id, product_query, product_name, source,
            kcal_per_100g, grams, kcal_total, mock_uow
        )

        # Assert
        mock_uow.daily_stats.get_or_create.assert_called_once_with(user_id, today)
        assert new_daily_stats.calories_consumed_kcal == int(kcal_total)
        mock_uow.daily_stats.update.assert_called_once_with(new_daily_stats)

    @pytest.mark.asyncio
    async def test_finalize_food_log_with_fractional_kcal_total(self, mock_uow, sample_daily_stats):
        """finalize_food_log округляет калории при добавлении в статистику."""
        # Arrange
        user_id = 12345
        product_query = "овсянка"
        product_name = "Овсянка"
        source = "api"
        kcal_per_100g = 389.0
        grams = 45.0  # 45 grams
        kcal_total = 175.05  # (389/100)*45 = 175.05

        today = date.today()
        mock_uow.daily_stats.get_or_create.return_value = sample_daily_stats
        initial_calories_consumed = sample_daily_stats.calories_consumed_kcal

        # Act
        await finalize_food_log(
            user_id, product_query, product_name, source,
            kcal_per_100g, grams, kcal_total, mock_uow
        )

        # Assert
        # Калории должны быть округлены до int
        assert sample_daily_stats.calories_consumed_kcal == initial_calories_consumed + int(kcal_total)
        assert sample_daily_stats.calories_consumed_kcal == initial_calories_consumed + 175