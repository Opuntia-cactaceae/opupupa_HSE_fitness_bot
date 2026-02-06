from abc import ABC, abstractmethod
from datetime import date
from typing import List

from domain.entities.food_log import FoodLog


class FoodLogRepository(ABC):
    @abstractmethod
    async def add(self, food_log: FoodLog) -> int:
        pass

    @abstractmethod
    async def get_by_user_and_date(self, user_id: int, date: date) -> List[FoodLog]:
        pass

    @abstractmethod
    async def get_by_id(self, food_log_id: int) -> FoodLog | None:
        pass

    @abstractmethod
    async def delete(self, food_log_id: int) -> None:
        pass