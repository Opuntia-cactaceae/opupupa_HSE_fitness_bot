from datetime import date, datetime

from domain.entities.workout_log import WorkoutLog
from domain.interfaces.unit_of_work import UnitOfWork
from domain.exceptions import EntityNotFoundError


async def delete_workout_log(log_id: int, user_id: int, uow: UnitOfWork) -> None:
    
                     
    workout_log = await uow.workout_logs.get_by_id(log_id)
    if workout_log is None or workout_log.user_id != user_id:
        raise EntityNotFoundError("Запись о тренировке не найдена")

                                                
    kcal_burned = workout_log.kcal_burned
    water_bonus_ml = workout_log.water_bonus_ml
    log_date = workout_log.date
    log_user_id = workout_log.user_id

                    
    await uow.workout_logs.delete(log_id)

                         
    await ensure_daily_stats(log_user_id, uow)
    daily_stats = await uow.daily_stats.get(log_user_id, log_date)
    daily_stats.calories_burned_kcal -= int(kcal_burned)
    daily_stats.water_goal_ml -= water_bonus_ml
    daily_stats.updated_at = datetime.utcnow()
    await uow.daily_stats.update(daily_stats)