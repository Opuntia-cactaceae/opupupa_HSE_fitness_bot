from typing import Tuple

from domain.exceptions import ValidationError


def set_food_grams(kcal_per_100g: float, grams: float) -> Tuple[float, float]:
    """Рассчитать общие калории для указанного количества грамм."""
    if kcal_per_100g <= 0:
        raise ValidationError("Калорийность продукта должна быть положительной")

    kcal_total = (kcal_per_100g / 100.0) * grams
    return grams, kcal_total