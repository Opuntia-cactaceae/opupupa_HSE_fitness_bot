from datetime import datetime

from domain.interfaces.unit_of_work import UnitOfWork


async def set_age(user_id: int, age_years: int, uow: UnitOfWork) -> None:
    """Установить возраст пользователя."""
    user = await uow.users.get(user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")
    user.age_years = age_years
    user.updated_at = datetime.utcnow()
    await uow.users.update(user)