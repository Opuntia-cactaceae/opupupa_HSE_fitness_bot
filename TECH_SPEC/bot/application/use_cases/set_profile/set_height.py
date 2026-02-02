from datetime import datetime

from domain.interfaces.unit_of_work import UnitOfWork


async def set_height(user_id: int, height_cm: float, uow: UnitOfWork) -> None:
    """Установить рост пользователя."""
    user = await uow.users.get(user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")
    user.height_cm = height_cm
    user.updated_at = datetime.utcnow()
    await uow.users.update(user)