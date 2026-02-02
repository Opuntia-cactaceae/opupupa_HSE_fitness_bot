from sqlalchemy.ext.asyncio import AsyncSession

from domain.interfaces.unit_of_work import UnitOfWork
from infrastructure.db.repositories.user_repository import UserRepositoryImpl
from infrastructure.db.repositories.daily_stats_repository import DailyStatsRepositoryImpl
from infrastructure.db.repositories.food_log_repository import FoodLogRepositoryImpl
from infrastructure.db.repositories.workout_log_repository import WorkoutLogRepositoryImpl
from infrastructure.db.repositories.water_log_repository import WaterLogRepositoryImpl


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._session: AsyncSession | None = None
        self._users: UserRepositoryImpl | None = None
        self._daily_stats: DailyStatsRepositoryImpl | None = None
        self._food_logs: FoodLogRepositoryImpl | None = None
        self._workout_logs: WorkoutLogRepositoryImpl | None = None
        self._water_logs: WaterLogRepositoryImpl | None = None
        self._entered: bool = False

    @property
    def users(self) -> "UserRepositoryImpl":
        if self._users is None:
            raise RuntimeError("UnitOfWork not entered. Use async with.")
        return self._users

    @property
    def daily_stats(self) -> "DailyStatsRepositoryImpl":
        if self._daily_stats is None:
            raise RuntimeError("UnitOfWork not entered. Use async with.")
        return self._daily_stats

    @property
    def food_logs(self) -> "FoodLogRepositoryImpl":
        if self._food_logs is None:
            raise RuntimeError("UnitOfWork not entered. Use async with.")
        return self._food_logs

    @property
    def workout_logs(self) -> "WorkoutLogRepositoryImpl":
        if self._workout_logs is None:
            raise RuntimeError("UnitOfWork not entered. Use async with.")
        return self._workout_logs

    @property
    def water_logs(self) -> "WaterLogRepositoryImpl":
        if self._water_logs is None:
            raise RuntimeError("UnitOfWork not entered. Use async with.")
        return self._water_logs

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        if self._entered:
            raise RuntimeError("UnitOfWork already entered. Do not nest async with.")
        self._session = self.session_factory()
        self._users = UserRepositoryImpl(self._session)
        self._daily_stats = DailyStatsRepositoryImpl(self._session)
        self._food_logs = FoodLogRepositoryImpl(self._session)
        self._workout_logs = WorkoutLogRepositoryImpl(self._session)
        self._water_logs = WaterLogRepositoryImpl(self._session)
        self._entered = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
        await self._session.close()
        self._entered = False

    async def commit(self) -> None:
        if self._session:
            await self._session.commit()

    async def rollback(self) -> None:
        if self._session:
            await self._session.rollback()