from datetime import datetime

from domain.interfaces.unit_of_work import UnitOfWork
from .finalize_profile import finalize_profile


async def set_water_goal_mode(user_id: int, mode: str, uow: UnitOfWork) -> None:
    """Установить режим цели по воде: 'auto' или 'manual'."""
    if mode not in ("auto", "manual"):
        raise ValueError("Mode must be 'auto' or 'manual'")

    user = await uow.users.get(user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")
    user.water_goal_mode = mode
    user.updated_at = datetime.utcnow()
    await uow.users.update(user)

    # Пересчитать цели в DailyStats
    await finalize_profile(user_id, uow)