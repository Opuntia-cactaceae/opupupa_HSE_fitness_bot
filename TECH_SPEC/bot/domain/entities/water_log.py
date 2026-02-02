from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class WaterLog:
    id: int
    user_id: int
    date: date
    logged_at: datetime
    ml: int