from typing import Tuple

from domain.exceptions import ValidationError
from .set_workout_type import get_workout_met, get_workout_sweat_rate


def calculate_workout_calories_and_water(
    weight_kg: float, workout_type: str, minutes: int
) -> Tuple[float, int]:
    
    if weight_kg <= 0:
        raise ValidationError("Вес должен быть положительным")

    met = get_workout_met(workout_type)
    sweat_rate = get_workout_sweat_rate(workout_type)
    hours = minutes / 60.0
    kcal_burned = met * weight_kg * hours
    water_burned_ml = sweat_rate * minutes

                                       
    if kcal_burned > 1500:
        kcal_burned = 1500
    if water_burned_ml > 2000:
        water_burned_ml = 2000

    return round(kcal_burned, 1), int(water_burned_ml)