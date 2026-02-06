from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class FoodLog:
    id: int
    user_id: int
    date: date
    logged_at: datetime
    product_query: str
    product_name: str
    source: str
    product_external_id: Optional[str] = None
    kcal_per_100g: float = 0.0
    grams: float = 0.0
    kcal_total: float = 0.0