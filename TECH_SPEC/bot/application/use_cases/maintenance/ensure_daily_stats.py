from datetime import date

from domain.interfaces.unit_of_work import UnitOfWork


async def ensure_daily_stats(user_id: int, uow: UnitOfWork) -> None:
    """Обеспечить наличие DailyStats на текущую дату (создание при необходимости)."""
    today = date.today()
    await uow.daily_stats.get_or_create(user_id, today)