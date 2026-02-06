from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: int
    created_at: datetime
    updated_at: datetime
    weight_kg: float
    height_cm: float
    age_years: int
    sex: Optional[str] = None
    activity_minutes_per_day: int = 0
    city: str = ""
    timezone: str = "Europe/Moscow"
    calorie_goal_mode: str = "auto"
    calorie_goal_kcal_manual: Optional[int] = None
    water_goal_mode: str = "auto"
    water_goal_ml_manual: Optional[int] = None

    def calculate_base_water_goal_ml(self) -> int:
        return int(self.weight_kg * 30)

    def calculate_base_calorie_goal_kcal(self) -> int:
        return int(10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age_years)

    def calculate_water_goal_ml(self, temperature_c: Optional[float] = None) -> int:
        if self.water_goal_mode == "manual" and self.water_goal_ml_manual is not None:
            return self.water_goal_ml_manual

        water_goal_ml = self.calculate_base_water_goal_ml()

        activity_bonus_ml = (self.activity_minutes_per_day // 30) * 500
        activity_bonus_ml = min(activity_bonus_ml, 3000)
        water_goal_ml += activity_bonus_ml

        if temperature_c is not None and temperature_c > 25:
            water_goal_ml += 500

        return water_goal_ml

    def calculate_calorie_goal_kcal(self) -> int:
        if self.calorie_goal_mode != "auto":
            return self.calorie_goal_kcal_manual or 0

        calorie_goal_kcal = self.calculate_base_calorie_goal_kcal()

        activity_min = self.activity_minutes_per_day
        if activity_min < 30:
            activity_kcal_bonus = 200
        elif activity_min <= 60:
            activity_kcal_bonus = 300
        else:
            activity_kcal_bonus = 400
        calorie_goal_kcal += activity_kcal_bonus

        return calorie_goal_kcal