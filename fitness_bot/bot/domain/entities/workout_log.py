from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class WorkoutLog:
    id: int
    user_id: int
    date: date
    logged_at: datetime
    workout_type: str
    minutes: int
    kcal_burned: float = 0.0
    water_bonus_ml: int = 0