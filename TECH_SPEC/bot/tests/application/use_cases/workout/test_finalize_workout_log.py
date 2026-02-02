import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock

from domain.entities.workout_log import WorkoutLog
from application.use_cases.workout.finalize_workout_log import finalize_workout_log


class TestFinalizeWorkoutLog:
    """Тестирование finalize_workout_log use case."""

    @pytest.mark.asyncio
    async def test_finalize_workout_log_creates_log_and_updates_stats(self, mock_uow, sample_daily_stats):
        """finalize_workout_log создает запись и обновляет статистику."""
        # Arrange
        user_id = 12345
        workout_type = "бег"
        minutes = 60
        kcal_burned = 560.0
        water_bonus_ml = 400

        today = date.today()
        mock_uow.daily_stats.get_or_create.return_value = sample_daily_stats
        initial_calories_burned = sample_daily_stats.calories_burned_kcal
        initial_water_goal = sample_daily_stats.water_goal_ml

        # Act
        await finalize_workout_log(
            user_id, workout_type, minutes, kcal_burned, water_bonus_ml, mock_uow
        )

        # Assert
        # Check WorkoutLog creation
        mock_uow.workout_logs.add.assert_called_once()
        workout_log = mock_uow.workout_logs.add.call_args[0][0]
        assert isinstance(workout_log, WorkoutLog)
        assert workout_log.user_id == user_id
        assert workout_log.date == today
        assert workout_log.workout_type == workout_type
        assert workout_log.minutes == minutes
        assert workout_log.kcal_burned == kcal_burned
        assert workout_log.water_bonus_ml == water_bonus_ml

        # Check DailyStats update
        mock_uow.daily_stats.get_or_create.assert_called_once_with(user_id, today)
        assert sample_daily_stats.calories_burned_kcal == initial_calories_burned + int(kcal_burned)
        assert sample_daily_stats.water_goal_ml == initial_water_goal + water_bonus_ml
        assert sample_daily_stats.updated_at > datetime(2024, 1, 1, 12, 0, 0)
        mock_uow.daily_stats.update.assert_called_once_with(sample_daily_stats)

    @pytest.mark.asyncio
    async def test_finalize_workout_log_with_fractional_kcal(self, mock_uow, sample_daily_stats):
        """finalize_workout_log округляет калории при добавлении в статистику."""
        # Arrange
        user_id = 12345
        workout_type = "ходьба"
        minutes = 45
        kcal_burned = 210.75  # дробное значение
        water_bonus_ml = 200

        today = date.today()
        mock_uow.daily_stats.get_or_create.return_value = sample_daily_stats
        initial_calories_burned = sample_daily_stats.calories_burned_kcal

        # Act
        await finalize_workout_log(
            user_id, workout_type, minutes, kcal_burned, water_bonus_ml, mock_uow
        )

        # Assert
        # Калории должны быть округлены до int
        assert sample_daily_stats.calories_burned_kcal == initial_calories_burned + int(kcal_burned)
        assert sample_daily_stats.calories_burned_kcal == initial_calories_burned + 210

    @pytest.mark.asyncio
    async def test_finalize_workout_log_creates_new_daily_stats(self, mock_uow):
        """finalize_workout_log создает новую DailyStats, если её нет."""
        # Arrange
        user_id = 12345
        workout_type = "велосипед"
        minutes = 90
        kcal_burned = 731.25
        water_bonus_ml = 600

        today = date.today()

        # Create new DailyStats mock
        new_daily_stats = AsyncMock()
        new_daily_stats.calories_burned_kcal = 0
        new_daily_stats.water_goal_ml = 2500
        new_daily_stats.updated_at = datetime.utcnow()

        mock_uow.daily_stats.get_or_create.return_value = new_daily_stats

        # Act
        await finalize_workout_log(
            user_id, workout_type, minutes, kcal_burned, water_bonus_ml, mock_uow
        )

        # Assert
        mock_uow.daily_stats.get_or_create.assert_called_once_with(user_id, today)
        assert new_daily_stats.calories_burned_kcal == int(kcal_burned)
        assert new_daily_stats.water_goal_ml == 2500 + water_bonus_ml
        mock_uow.daily_stats.update.assert_called_once_with(new_daily_stats)

    @pytest.mark.asyncio
    async def test_finalize_workout_log_with_zero_water_bonus(self, mock_uow, sample_daily_stats):
        """finalize_workout_log работает с нулевым бонусом воды."""
        # Arrange
        user_id = 12345
        workout_type = "силовая"
        minutes = 25  # меньше 30 минут
        kcal_burned = 150.0
        water_bonus_ml = 0

        today = date.today()
        mock_uow.daily_stats.get_or_create.return_value = sample_daily_stats
        initial_water_goal = sample_daily_stats.water_goal_ml

        # Act
        await finalize_workout_log(
            user_id, workout_type, minutes, kcal_burned, water_bonus_ml, mock_uow
        )

        # Assert
        # Water goal should not change
        assert sample_daily_stats.water_goal_ml == initial_water_goal

    @pytest.mark.asyncio
    async def test_finalize_workout_log_with_negative_values(self, mock_uow, sample_daily_stats):
        """finalize_workout_log работает с отрицательными значениями (не должно быть, но проверим)."""
        # Arrange
        user_id = 12345
        workout_type = "бег"
        minutes = 60
        kcal_burned = -100.0  # отрицательные калории
        water_bonus_ml = -200  # отрицательный бонус воды

        today = date.today()
        mock_uow.daily_stats.get_or_create.return_value = sample_daily_stats
        initial_calories_burned = sample_daily_stats.calories_burned_kcal
        initial_water_goal = sample_daily_stats.water_goal_ml

        # Act
        await finalize_workout_log(
            user_id, workout_type, minutes, kcal_burned, water_bonus_ml, mock_uow
        )

        # Assert
        # Values should be updated even if negative
        assert sample_daily_stats.calories_burned_kcal == initial_calories_burned + int(kcal_burned)
        assert sample_daily_stats.water_goal_ml == initial_water_goal + water_bonus_ml