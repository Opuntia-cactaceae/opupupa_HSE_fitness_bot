from datetime import datetime

from domain.interfaces.unit_of_work import UnitOfWork


async def set_calorie_goal_manual(user_id: int, calorie_goal_kcal: int, uow: UnitOfWork) -> None:
    """Установить ручную цель калорий."""
    user = await uow.users.get(user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")
    user.calorie_goal_kcal_manual = calorie_goal_kcal
    user.updated_at = datetime.utcnow()
    await uow.users.update(user)