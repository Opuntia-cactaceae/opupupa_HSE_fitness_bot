import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock

from domain.entities.daily_stats import DailyStats
from application.use_cases.progress.check_progress import check_progress


class TestCheckProgress:
    """Тестирование check_progress use case."""

    @pytest.mark.asyncio
    async def test_check_progress_returns_correct_values(self, mock_uow, sample_daily_stats):
        """check_progress возвращает правильные значения прогресса."""
        # Arrange
        user_id = 12345
        today = date.today()

        # Setup sample stats
        sample_daily_stats.water_goal_ml = 2500
        sample_daily_stats.water_logged_ml = 1500
        # water_remaining_ml should be 1000 (2500 - 1500)

        sample_daily_stats.calories_consumed_kcal = 1800
        sample_daily_stats.calories_burned_kcal = 400
        # calorie_balance_kcal should be 1400 (1800 - 400)

        mock_uow.daily_stats.get.return_value = sample_daily_stats

        # Act
        result = await check_progress(user_id, mock_uow)

        # Assert
        mock_uow.daily_stats.get.assert_called_once_with(user_id, today)
        assert result == {
            "water_logged_ml": 1500,
            "water_goal_ml": 2500,
            "water_remaining_ml": 1000,
            "calories_consumed_kcal": 1800,
            "calories_burned_kcal": 400,
            "calorie_balance_kcal": 1400,
        }

    @pytest.mark.asyncio
    async def test_check_progress_returns_zeros_when_no_stats(self, mock_uow):
        """check_progress возвращает нули, если статистики нет."""
        # Arrange
        user_id = 12345
        mock_uow.daily_stats.get.return_value = None

        # Act
        result = await check_progress(user_id, mock_uow)

        # Assert
        mock_uow.daily_stats.get.assert_called_once_with(user_id, date.today())
        assert result == {
            "water_logged_ml": 0,
            "water_goal_ml": 0,
            "water_remaining_ml": 0,
            "calories_consumed_kcal": 0,
            "calories_burned_kcal": 0,
            "calorie_balance_kcal": 0,
        }

    @pytest.mark.asyncio
    async def test_check_progress_handles_negative_water_remaining(self, mock_uow, sample_daily_stats):
        """check_progress корректно обрабатывает отрицательный остаток воды."""
        # Arrange
        user_id = 12345
        today = date.today()

        # User drank more than goal
        sample_daily_stats.water_goal_ml = 2000
        sample_daily_stats.water_logged_ml = 2500
        # water_remaining_ml should be 0 (max(0, 2000 - 2500))

        sample_daily_stats.calories_consumed_kcal = 1500
        sample_daily_stats.calories_burned_kcal = 300
        # calorie_balance_kcal should be 1200

        mock_uow.daily_stats.get.return_value = sample_daily_stats

        # Act
        result = await check_progress(user_id, mock_uow)

        # Assert
        assert result["water_remaining_ml"] == 0  # not -500
        assert result["calorie_balance_kcal"] == 1200

    @pytest.mark.asyncio
    async def test_check_progress_handles_negative_calorie_balance(self, mock_uow, sample_daily_stats):
        """check_progress корректно обрабатывает отрицательный баланс калорий."""
        # Arrange
        user_id = 12345
        today = date.today()

        # User burned more calories than consumed
        sample_daily_stats.water_goal_ml = 2500
        sample_daily_stats.water_logged_ml = 1200

        sample_daily_stats.calories_consumed_kcal = 1200
        sample_daily_stats.calories_burned_kcal = 1800
        # calorie_balance_kcal should be -600 (1200 - 1800)

        mock_uow.daily_stats.get.return_value = sample_daily_stats

        # Act
        result = await check_progress(user_id, mock_uow)

        # Assert
        assert result["calorie_balance_kcal"] == -600  # negative balance is allowed

    @pytest.mark.asyncio
    async def test_check_progress_with_zero_values(self, mock_uow, sample_daily_stats):
        """check_progress работает с нулевыми значениями."""
        # Arrange
        user_id = 12345
        today = date.today()

        # All zeros
        sample_daily_stats.water_goal_ml = 0
        sample_daily_stats.water_logged_ml = 0
        sample_daily_stats.calories_consumed_kcal = 0
        sample_daily_stats.calories_burned_kcal = 0

        mock_uow.daily_stats.get.return_value = sample_daily_stats

        # Act
        result = await check_progress(user_id, mock_uow)

        # Assert
        assert result["water_remaining_ml"] == 0
        assert result["calorie_balance_kcal"] == 0

    @pytest.mark.asyncio
    async def test_check_progress_with_high_values(self, mock_uow, sample_daily_stats):
        """check_progress работает с большими значениями."""
        # Arrange
        user_id = 12345
        today = date.today()

        # High values
        sample_daily_stats.water_goal_ml = 5000
        sample_daily_stats.water_logged_ml = 3200
        # water_remaining_ml should be 1800

        sample_daily_stats.calories_consumed_kcal = 3500
        sample_daily_stats.calories_burned_kcal = 800
        # calorie_balance_kcal should be 2700

        mock_uow.daily_stats.get.return_value = sample_daily_stats

        # Act
        result = await check_progress(user_id, mock_uow)

        # Assert
        assert result["water_remaining_ml"] == 1800
        assert result["calorie_balance_kcal"] == 2700

    @pytest.mark.asyncio
    async def test_check_progress_calculates_water_remaining_correctly(self, mock_uow):
        """Проверка правильности расчета оставшейся воды."""
        # Arrange
        user_id = 12345
        today = date.today()

        # Create DailyStats with different values
        daily_stats = DailyStats(
            id=1,
            user_id=user_id,
            date=today,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            water_goal_ml=3000,
            water_logged_ml=1200,
            calories_consumed_kcal=2000,
            calories_burned_kcal=500,
        )

        mock_uow.daily_stats.get.return_value = daily_stats

        # Act
        result = await check_progress(user_id, mock_uow)

        # Assert
        # water_remaining_ml should be calculated by DailyStats property
        expected_remaining = daily_stats.water_remaining_ml
        assert result["water_remaining_ml"] == expected_remaining
        assert result["water_remaining_ml"] == 1800  # 3000 - 1200

    @pytest.mark.asyncio
    async def test_check_progress_calculates_calorie_balance_correctly(self, mock_uow):
        """Проверка правильности расчета баланса калорий."""
        # Arrange
        user_id = 12345
        today = date.today()

        # Create DailyStats with different values
        daily_stats = DailyStats(
            id=1,
            user_id=user_id,
            date=today,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            water_goal_ml=2500,
            water_logged_ml=1000,
            calories_consumed_kcal=1800,
            calories_burned_kcal=600,
        )

        mock_uow.daily_stats.get.return_value = daily_stats

        # Act
        result = await check_progress(user_id, mock_uow)

        # Assert
        # calorie_balance_kcal should be calculated by DailyStats property
        expected_balance = daily_stats.calorie_balance_kcal
        assert result["calorie_balance_kcal"] == expected_balance
        assert result["calorie_balance_kcal"] == 1200  # 1800 - 600