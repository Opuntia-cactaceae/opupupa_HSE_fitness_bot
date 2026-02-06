from abc import ABC, abstractmethod
from datetime import date
from typing import List

from domain.entities.workout_log import WorkoutLog


class WorkoutLogRepository(ABC):
    @abstractmethod
    async def add(self, workout_log: WorkoutLog) -> int:
        pass

    @abstractmethod
    async def get_by_user_and_date(self, user_id: int, date: date) -> List[WorkoutLog]:
        pass

    @abstractmethod
    async def get_by_id(self, workout_log_id: int) -> WorkoutLog | None:
        pass

    @abstractmethod
    async def delete(self, workout_log_id: int) -> None:
        pass