import pytest

from application.use_cases.food.set_food_grams import set_food_grams


class TestSetFoodGrams:
    """Тестирование set_food_grams use case."""

    def test_set_food_grams_calculates_correctly(self):
        """set_food_grams правильно рассчитывает калории."""
        # Test case 1: normal values
        kcal_per_100g = 100.0
        grams = 200.0
        expected_grams, expected_kcal = grams, 200.0  # (100/100)*200 = 200

        result_grams, result_kcal = set_food_grams(kcal_per_100g, grams)

        assert result_grams == expected_grams
        assert result_kcal == expected_kcal

    def test_set_food_grams_with_fractional_values(self):
        """set_food_rams работает с дробными значениями."""
        # Test case 2: fractional values
        kcal_per_100g = 89.5
        grams = 150.0
        expected_kcal = (89.5 / 100.0) * 150.0  # 134.25

        _, result_kcal = set_food_grams(kcal_per_100g, grams)

        assert result_kcal == pytest.approx(expected_kcal)

    def test_set_food_grams_with_zero_grams(self):
        """set_food_grams работает с нулевым весом."""
        kcal_per_100g = 100.0
        grams = 0.0
        expected_kcal = 0.0

        _, result_kcal = set_food_grams(kcal_per_100g, grams)

        assert result_kcal == expected_kcal

    def test_set_food_grams_with_small_amount(self):
        """set_food_grams работает с маленьким количеством."""
        kcal_per_100g = 350.0  # high-calorie food
        grams = 10.0  # just 10 grams
        expected_kcal = 35.0  # (350/100)*10 = 35

        _, result_kcal = set_food_grams(kcal_per_100g, grams)

        assert result_kcal == expected_kcal