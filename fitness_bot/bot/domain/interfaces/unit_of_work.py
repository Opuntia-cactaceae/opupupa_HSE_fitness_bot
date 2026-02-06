from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class UnitOfWork(ABC):
    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork":
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    @property
    @abstractmethod
    def users(self):
        pass

    @property
    @abstractmethod
    def daily_stats(self):
        pass

    @property
    @abstractmethod
    def food_logs(self):
        pass

    @property
    @abstractmethod
    def workout_logs(self):
        pass

    @property
    @abstractmethod
    def water_logs(self):
        pass