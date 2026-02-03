from datetime import datetime

from domain.interfaces.unit_of_work import UnitOfWork
from .finalize_profile import finalize_profile


async def set_city(user_id: int, city: str, uow: UnitOfWork) -> None:
    """Установить город пользователя."""
    user = await uow.users.get(user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")
    user.city = city
    user.updated_at = datetime.utcnow()
    await uow.users.update(user)

    # Пересчитать цели в DailyStats (для температурной коррекции воды)
    await finalize_profile(user_id, uow)