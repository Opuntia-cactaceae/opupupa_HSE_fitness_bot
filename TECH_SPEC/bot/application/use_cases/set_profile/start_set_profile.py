from datetime import datetime

from domain.entities.user import User
from domain.interfaces.unit_of_work import UnitOfWork


async def start_set_profile(user_id: int, uow: UnitOfWork) -> None:
    """
    Инициализация сценария настройки профиля.
    Создаёт запись пользователя если её нет.
    """
    user = await uow.users.get(user_id)
    if user is None:
        user = User(
            id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            weight_kg=0.0,
            height_cm=0.0,
            age_years=0,
            activity_minutes_per_day=0,
            city="",
            timezone="Europe/Amsterdam",
            calorie_goal_mode="auto",
            calorie_goal_kcal_manual=None,
        )
        await uow.users.add(user)