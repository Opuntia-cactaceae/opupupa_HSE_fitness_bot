from datetime import date

from domain.interfaces.unit_of_work import UnitOfWork
from application.use_cases.set_profile.finalize_profile import finalize_profile


async def ensure_daily_stats(user_id: int, uow: UnitOfWork) -> None:
    """Обеспечить наличие DailyStats на текущую дату (создание при необходимости)."""
    await finalize_profile(user_id, uow)