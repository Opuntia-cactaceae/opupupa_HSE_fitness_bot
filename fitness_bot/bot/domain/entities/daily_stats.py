from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class DailyStats:
    id: int
    user_id: int
    date: date
    created_at: datetime
    updated_at: datetime

    temperature_c: Optional[float] = None
    water_goal_ml: int = 0
    calorie_goal_kcal: int = 0
    water_logged_ml: int = 0
    calories_consumed_kcal: int = 0
    calories_burned_kcal: int = 0

    @property
    def water_remaining_ml(self) -> int:
        return max(0, self.water_goal_ml - self.water_logged_ml)

    @property
    def calorie_balance_kcal(self) -> int:
        return self.calories_consumed_kcal - self.calories_burned_kcal