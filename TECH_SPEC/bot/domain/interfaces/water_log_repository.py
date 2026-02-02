from abc import ABC, abstractmethod
from datetime import date
from typing import List

from domain.entities.water_log import WaterLog


class WaterLogRepository(ABC):
    @abstractmethod
    async def add(self, water_log: WaterLog) -> None:
        pass

    @abstractmethod
    async def get_by_user_and_date(self, user_id: int, date: date) -> List[WaterLog]:
        pass

    @abstractmethod
    async def delete(self, water_log_id: int) -> None:
        pass