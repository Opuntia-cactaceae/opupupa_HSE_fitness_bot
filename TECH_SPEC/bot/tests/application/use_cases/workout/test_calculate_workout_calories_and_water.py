import pytest

from application.use_cases.workout.set_workout_minutes import calculate_workout_calories_and_water


class TestCalculateWorkoutCaloriesAndWater:
    """Тестирование calculate_workout_calories_and_water use case."""

    def test_calculate_workout_calories_and_water_running(self):
        """Расчет калорий и воды для бега."""
        weight_kg = 70.0
        workout_type = "бег"  # MET = 8.0
        minutes = 60

        kcal_burned, water_bonus_ml = calculate_workout_calories_and_water(
            weight_kg, workout_type, minutes
        )

        # Calories: 8.0 * 70 * 1.0 = 560 kcal
        # Water: 60 // 30 * 200 = 400 ml
        assert kcal_burned == pytest.approx(560.0)
        assert water_bonus_ml == 400

    def test_calculate_workout_calories_and_water_walking(self):
        """Расчет калорий и воды для ходьбы."""
        weight_kg = 80.0
        workout_type = "ходьба"  # MET = 3.5
        minutes = 45

        kcal_burned, water_bonus_ml = calculate_workout_calories_and_water(
            weight_kg, workout_type, minutes
        )

        # Calories: 3.5 * 80 * 0.75 = 210 kcal
        # Water: 45 // 30 * 200 = 200 ml (only one 30-minute interval)
        assert kcal_burned == pytest.approx(210.0)
        assert water_bonus_ml == 200

    def test_calculate_workout_calories_and_water_unknown_type(self):
        """Расчет калорий и воды для неизвестного типа тренировки."""
        weight_kg = 65.0
        workout_type = "йога"  # Default MET = 5.0
        minutes = 90

        kcal_burned, water_bonus_ml = calculate_workout_calories_and_water(
            weight_kg, workout_type, minutes
        )

        # Calories: 5.0 * 65 * 1.5 = 487.5 kcal
        # Water: 90 // 30 * 200 = 600 ml
        assert kcal_burned == pytest.approx(487.5)
        assert water_bonus_ml == 600

    def test_calculate_workout_calories_and_water_short_workout(self):
        """Расчет для короткой тренировки (меньше 30 минут)."""
        weight_kg = 60.0
        workout_type = "силовая"  # MET = 6.0
        minutes = 25

        kcal_burned, water_bonus_ml = calculate_workout_calories_and_water(
            weight_kg, workout_type, minutes
        )

        # Calories: 6.0 * 60 * (25/60) = 150 kcal
        # Water: 25 // 30 * 200 = 0 ml (no complete 30-minute interval)
        assert kcal_burned == pytest.approx(150.0)
        assert water_bonus_ml == 0

    def test_calculate_workout_calories_and_water_zero_minutes(self):
        """Расчет для нулевой продолжительности."""
        weight_kg = 70.0
        workout_type = "бег"
        minutes = 0

        kcal_burned, water_bonus_ml = calculate_workout_calories_and_water(
            weight_kg, workout_type, minutes
        )

        assert kcal_burned == 0.0
        assert water_bonus_ml == 0

    def test_calculate_workout_calories_and_water_fractional_hours(self):
        """Расчет для нецелого количества часов."""
        weight_kg = 75.0
        workout_type = "плавание"  # MET = 7.0
        minutes = 90  # 1.5 hours

        kcal_burned, water_bonus_ml = calculate_workout_calories_and_water(
            weight_kg, workout_type, minutes
        )

        # Calories: 7.0 * 75 * 1.5 = 787.5 kcal
        # Water: 90 // 30 * 200 = 600 ml
        assert kcal_burned == pytest.approx(787.5)
        assert water_bonus_ml == 600