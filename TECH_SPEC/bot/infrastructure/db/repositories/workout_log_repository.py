from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from domain.entities.workout_log import WorkoutLog
from domain.interfaces.workout_log_repository import WorkoutLogRepository
from infrastructure.db.models import WorkoutLogModel


def to_domain(model: WorkoutLogModel) -> WorkoutLog:
    return WorkoutLog(
        id=model.id,
        user_id=model.user_id,
        date=model.date,
        logged_at=model.logged_at,
        workout_type=model.workout_type,
        minutes=model.minutes,
        kcal_burned=model.kcal_burned,
        water_bonus_ml=model.water_bonus_ml,
    )


def to_model(workout_log: WorkoutLog) -> WorkoutLogModel:
    return WorkoutLogModel(
        id=workout_log.id,
        user_id=workout_log.user_id,
        date=workout_log.date,
        logged_at=workout_log.logged_at,
        workout_type=workout_log.workout_type,
        minutes=workout_log.minutes,
        kcal_burned=workout_log.kcal_burned,
        water_bonus_ml=workout_log.water_bonus_ml,
    )


class WorkoutLogRepositoryImpl(WorkoutLogRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, workout_log: WorkoutLog) -> None:
        model = to_model(workout_log)
        self._session.add(model)

    async def get_by_user_and_date(self, user_id: int, date: date) -> list[WorkoutLog]:
        stmt = select(WorkoutLogModel).where(
            WorkoutLogModel.user_id == user_id, WorkoutLogModel.date == date
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [to_domain(model) for model in models]

    async def delete(self, workout_log_id: int) -> None:
        stmt = select(WorkoutLogModel).where(WorkoutLogModel.id == workout_log_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)