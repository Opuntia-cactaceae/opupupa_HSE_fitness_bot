from datetime import datetime

from domain.interfaces.unit_of_work import UnitOfWork
from .finalize_profile import finalize_profile


async def set_water_goal_manual(user_id: int, water_goal_ml: int, uow: UnitOfWork) -> None:
    """Установить ручную цель по воде."""
    user = await uow.users.get(user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")
    user.water_goal_ml_manual = water_goal_ml
    user.updated_at = datetime.utcnow()
    await uow.users.update(user)

    # Пересчитать цели в DailyStats
    await finalize_profile(user_id, uow)