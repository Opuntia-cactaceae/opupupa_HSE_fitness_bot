from datetime import date, datetime

from domain.entities.water_log import WaterLog
from domain.interfaces.unit_of_work import UnitOfWork
from application.use_cases.maintenance.ensure_daily_stats import ensure_daily_stats


async def log_water(user_id: int, ml: int, uow: UnitOfWork) -> None:
    """Добавить воду и обновить дневную статистику."""
    # Создать запись воды
    water_log = WaterLog(
        id=0,  # будет сгенерировано БД
        user_id=user_id,
        date=date.today(),
        logged_at=datetime.utcnow(),
        ml=ml,
    )
    await uow.water_logs.add(water_log)

    # Обновить DailyStats
    today = date.today()
    await ensure_daily_stats(user_id, uow)
    daily_stats = await uow.daily_stats.get(user_id, today)
    daily_stats.water_logged_ml += ml
    daily_stats.updated_at = datetime.utcnow()
    await uow.daily_stats.update(daily_stats)