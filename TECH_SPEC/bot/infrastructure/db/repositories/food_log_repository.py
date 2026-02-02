from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from domain.entities.food_log import FoodLog
from domain.interfaces.food_log_repository import FoodLogRepository
from infrastructure.db.models import FoodLogModel


def to_domain(model: FoodLogModel) -> FoodLog:
    return FoodLog(
        id=model.id,
        user_id=model.user_id,
        date=model.date,
        logged_at=model.logged_at,
        product_query=model.product_query,
        product_name=model.product_name,
        source=model.source,
        product_external_id=model.product_external_id,
        kcal_per_100g=model.kcal_per_100g,
        grams=model.grams,
        kcal_total=model.kcal_total,
    )


def to_model(food_log: FoodLog) -> FoodLogModel:
    return FoodLogModel(
        id=food_log.id,
        user_id=food_log.user_id,
        date=food_log.date,
        logged_at=food_log.logged_at,
        product_query=food_log.product_query,
        product_name=food_log.product_name,
        source=food_log.source,
        product_external_id=food_log.product_external_id,
        kcal_per_100g=food_log.kcal_per_100g,
        grams=food_log.grams,
        kcal_total=food_log.kcal_total,
    )


class FoodLogRepositoryImpl(FoodLogRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, food_log: FoodLog) -> None:
        model = to_model(food_log)
        self._session.add(model)

    async def get_by_user_and_date(self, user_id: int, date: date) -> list[FoodLog]:
        stmt = select(FoodLogModel).where(
            FoodLogModel.user_id == user_id, FoodLogModel.date == date
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [to_domain(model) for model in models]

    async def delete(self, food_log_id: int) -> None:
        stmt = select(FoodLogModel).where(FoodLogModel.id == food_log_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)