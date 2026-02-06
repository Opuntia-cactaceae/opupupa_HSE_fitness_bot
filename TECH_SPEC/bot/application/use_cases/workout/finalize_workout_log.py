from datetime import date, datetime

from domain.entities.workout_log import WorkoutLog
from domain.interfaces.unit_of_work import UnitOfWork
from application.use_cases.maintenance.ensure_daily_stats import ensure_daily_stats


async def finalize_workout_log(
    user_id: int,
    workout_type: str,
    minutes: int,
    kcal_burned: float,
    water_bonus_ml: int,
    uow: UnitOfWork,
) -> None:
    """Записать WorkoutLog и обновить дневную статистику."""
    # Создать WorkoutLog
    workout_log = WorkoutLog(
        id=0,
        user_id=user_id,
        date=date.today(),
        logged_at=datetime.utcnow(),
        workout_type=workout_type,
        minutes=minutes,
        kcal_burned=kcal_burned,
        water_bonus_ml=water_bonus_ml,
    )
    await uow.workout_logs.add(workout_log)

    # Обновить DailyStats
    today = date.today()
    await ensure_daily_stats(user_id, uow)
    daily_stats = await uow.daily_stats.get(user_id, today)
    daily_stats.calories_burned_kcal += int(kcal_burned)
    daily_stats.water_goal_ml += water_bonus_ml
    daily_stats.updated_at = datetime.utcnow()
    await uow.daily_stats.update(daily_stats)