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