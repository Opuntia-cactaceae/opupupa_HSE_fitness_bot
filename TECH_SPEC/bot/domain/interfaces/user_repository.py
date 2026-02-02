from abc import ABC, abstractmethod
from typing import Optional

from domain.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    async def add(self, user: User) -> None:
        pass

    @abstractmethod
    async def get(self, user_id: int) -> Optional[User]:
        pass

    @abstractmethod
    async def update(self, user: User) -> None:
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> None:
        pass