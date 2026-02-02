import pytest

from application.use_cases.workout.set_workout_type import get_workout_met


class TestGetWorkoutMet:
    """Тестирование get_workout_met use case."""

    def test_get_workout_met_returns_correct_values(self):
        """get_workout_met возвращает правильные MET значения."""
        # Test known workout types
        assert get_workout_met("ходьба") == 3.5
        assert get_workout_met("бег") == 8.0
        assert get_workout_met("силовая") == 6.0
        assert get_workout_met("плавание") == 7.0
        assert get_workout_met("велосипед") == 6.5

    def test_get_workout_met_case_insensitive(self):
        """get_workout_met не зависит от регистра."""
        assert get_workout_met("ХОДЬБА") == 3.5
        assert get_workout_met("Бег") == 8.0
        assert get_workout_met("СИЛОВАЯ") == 6.0

    def test_get_workout_met_returns_default_for_unknown(self):
        """get_workout_met возвращает значение по умолчанию для неизвестных типов."""
        assert get_workout_met("йога") == 5.0
        assert get_workout_met("пилатес") == 5.0
        assert get_workout_met("неизвестная тренировка") == 5.0

    def test_get_workout_met_works_with_empty_string(self):
        """get_workout_met работает с пустой строкой."""
        assert get_workout_met("") == 5.0