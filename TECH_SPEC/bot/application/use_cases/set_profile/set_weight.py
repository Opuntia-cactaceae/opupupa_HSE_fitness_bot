from datetime import datetime

from domain.interfaces.unit_of_work import UnitOfWork


async def set_weight(user_id: int, weight_kg: float, uow: UnitOfWork) -> None:
    """Установить вес пользователя."""
    user = await uow.users.get(user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")
    user.weight_kg = weight_kg
    user.updated_at = datetime.utcnow()
    await uow.users.update(user)