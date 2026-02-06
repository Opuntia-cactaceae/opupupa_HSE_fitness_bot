from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from domain.entities.user import User
from domain.interfaces.user_repository import UserRepository
from infrastructure.db.models import UserModel


def to_domain(user_model: UserModel) -> User:
    return User(
        id=user_model.id,
        created_at=user_model.created_at,
        updated_at=user_model.updated_at,
        weight_kg=user_model.weight_kg,
        height_cm=user_model.height_cm,
        age_years=user_model.age_years,
        sex=user_model.sex,
        activity_minutes_per_day=user_model.activity_minutes_per_day,
        city=user_model.city,
        timezone=user_model.timezone,
        calorie_goal_mode=user_model.calorie_goal_mode,
        calorie_goal_kcal_manual=user_model.calorie_goal_kcal_manual,
        water_goal_mode=user_model.water_goal_mode,
        water_goal_ml_manual=user_model.water_goal_ml_manual,
    )


def to_model(user: User) -> UserModel:
    return UserModel(
        id=user.id,
        created_at=user.created_at,
        updated_at=user.updated_at,
        weight_kg=user.weight_kg,
        height_cm=user.height_cm,
        age_years=user.age_years,
        sex=user.sex,
        activity_minutes_per_day=user.activity_minutes_per_day,
        city=user.city,
        timezone=user.timezone,
        calorie_goal_mode=user.calorie_goal_mode,
        calorie_goal_kcal_manual=user.calorie_goal_kcal_manual,
        water_goal_mode=user.water_goal_mode,
        water_goal_ml_manual=user.water_goal_ml_manual,
    )


class UserRepositoryImpl(UserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, user: User) -> None:
        model = to_model(user)
        self._session.add(model)

    async def get(self, user_id: int) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def update(self, user: User) -> None:
        stmt = select(UserModel).where(UserModel.id == user.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.weight_kg = user.weight_kg
        model.height_cm = user.height_cm
        model.age_years = user.age_years
        model.sex = user.sex
        model.activity_minutes_per_day = user.activity_minutes_per_day
        model.city = user.city
        model.timezone = user.timezone
        model.calorie_goal_mode = user.calorie_goal_mode
        model.calorie_goal_kcal_manual = user.calorie_goal_kcal_manual
        model.water_goal_mode = user.water_goal_mode
        model.water_goal_ml_manual = user.water_goal_ml_manual
        model.updated_at = user.updated_at

    async def delete(self, user_id: int) -> None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)