from datetime import date, datetime

from domain.entities.food_log import FoodLog
from domain.interfaces.unit_of_work import UnitOfWork


async def finalize_food_log(
    user_id: int,
    product_query: str,
    product_name: str,
    source: str,
    kcal_per_100g: float,
    grams: float,
    kcal_total: float,
    uow: UnitOfWork,
) -> None:
    """Записать FoodLog и обновить дневную статистику."""
    # Создать FoodLog
    food_log = FoodLog(
        id=0,
        user_id=user_id,
        date=date.today(),
        logged_at=datetime.utcnow(),
        product_query=product_query,
        product_name=product_name,
        source=source,
        product_external_id=None,
        kcal_per_100g=kcal_per_100g,
        grams=grams,
        kcal_total=kcal_total,
    )
    await uow.food_logs.add(food_log)

    # Обновить DailyStats
    today = date.today()
    daily_stats = await uow.daily_stats.get_or_create(user_id, today)
    daily_stats.calories_consumed_kcal += int(kcal_total)
    daily_stats.updated_at = datetime.utcnow()
    await uow.daily_stats.update(daily_stats)