from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: int  # Telegram user_id
    created_at: datetime
    updated_at: datetime
    weight_kg: float
    height_cm: float
    age_years: int
    sex: Optional[str] = None
    activity_minutes_per_day: int = 0
    city: str = ""
    timezone: str = "Europe/Amsterdam"
    calorie_goal_mode: str = "auto"  # "auto" | "manual"
    calorie_goal_kcal_manual: Optional[int] = None
    water_goal_mode: str = "auto"  # "auto" | "manual"
    water_goal_ml_manual: Optional[int] = None

    def calculate_base_water_goal_ml(self) -> int:
        """Базовая норма воды: вес (кг) × 30 мл"""
        return int(self.weight_kg * 30)

    def calculate_base_calorie_goal_kcal(self) -> int:
        """Базовая норма калорий: 10 × вес (кг) + 6.25 × рост (см) − 5 × возраст"""
        return int(10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age_years)