from datetime import datetime

from domain.interfaces.unit_of_work import UnitOfWork
from .finalize_profile import finalize_profile


async def set_activity_minutes(user_id: int, activity_minutes_per_day: int, uow: UnitOfWork) -> None:
    """Установить уровень активности пользователя (минуты в день)."""
    user = await uow.users.get(user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")
    user.activity_minutes_per_day = activity_minutes_per_day
    user.updated_at = datetime.utcnow()
    await uow.users.update(user)

    # Пересчитать цели в DailyStats
    await finalize_profile(user_id, uow)