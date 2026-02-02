from datetime import date
from typing import Tuple

from domain.interfaces.unit_of_work import UnitOfWork


async def get_water_progress(user_id: int, uow: UnitOfWork) -> Tuple[int, int, int]:
    """Вернуть прогресс по воде: выпито, цель, остаток."""
    today = date.today()
    daily_stats = await uow.daily_stats.get(user_id, today)
    if daily_stats is None:
        return (0, 0, 0)
    return (
        daily_stats.water_logged_ml,
        daily_stats.water_goal_ml,
        daily_stats.water_remaining_ml,
    )