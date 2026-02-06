from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, List

from domain.entities.daily_stats import DailyStats


class DailyStatsRepository(ABC):
    @abstractmethod
    async def add(self, daily_stats: DailyStats) -> None:
        pass

    @abstractmethod
    async def get(self, user_id: int, date: date) -> Optional[DailyStats]:
        pass

    @abstractmethod
    async def update(self, daily_stats: DailyStats) -> None:
        pass

    @abstractmethod
    async def delete(self, daily_stats_id: int) -> None:
        pass

    @abstractmethod
    async def get_or_create(self, user_id: int, date: date) -> DailyStats:
        pass

    @abstractmethod
    async def get_for_user_in_range(self, user_id: int, date_from: date, date_to: date) -> List[DailyStats]:
        pass