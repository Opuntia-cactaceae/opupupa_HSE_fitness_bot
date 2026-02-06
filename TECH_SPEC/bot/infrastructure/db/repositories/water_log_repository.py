from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from domain.entities.water_log import WaterLog
from domain.interfaces.water_log_repository import WaterLogRepository
from infrastructure.db.models import WaterLogModel


def to_domain(model: WaterLogModel) -> WaterLog:
    return WaterLog(
        id=model.id,
        user_id=model.user_id,
        date=model.date,
        logged_at=model.logged_at,
        ml=model.ml,
    )


def to_model(water_log: WaterLog) -> WaterLogModel:
    kwargs = {
        "user_id": water_log.user_id,
        "date": water_log.date,
        "logged_at": water_log.logged_at,
        "ml": water_log.ml,
    }
    if water_log.id != 0:
        kwargs["id"] = water_log.id
    return WaterLogModel(**kwargs)


class WaterLogRepositoryImpl(WaterLogRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, water_log: WaterLog) -> None:
        model = to_model(water_log)
        self._session.add(model)

    async def get_by_user_and_date(self, user_id: int, date: date) -> list[WaterLog]:
        stmt = select(WaterLogModel).where(
            WaterLogModel.user_id == user_id, WaterLogModel.date == date
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [to_domain(model) for model in models]

    async def delete(self, water_log_id: int) -> None:
        stmt = select(WaterLogModel).where(WaterLogModel.id == water_log_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)