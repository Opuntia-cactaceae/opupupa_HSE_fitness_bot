from datetime import date
from typing import Dict

from domain.interfaces.unit_of_work import UnitOfWork


async def check_progress(user_id: int, uow: UnitOfWork) -> Dict[str, int]:
    """Сформировать сводку прогресса: вода, калории потреблено, сожжено, баланс."""
    today = date.today()
    daily_stats = await uow.daily_stats.get(user_id, today)

    if daily_stats is None:
        return {
            "water_logged_ml": 0,
            "water_goal_ml": 0,
            "water_remaining_ml": 0,
            "calories_consumed_kcal": 0,
            "calories_burned_kcal": 0,
            "calorie_balance_kcal": 0,
        }

    return {
        "water_logged_ml": daily_stats.water_logged_ml,
        "water_goal_ml": daily_stats.water_goal_ml,
        "water_remaining_ml": daily_stats.water_remaining_ml,
        "calories_consumed_kcal": daily_stats.calories_consumed_kcal,
        "calories_burned_kcal": daily_stats.calories_burned_kcal,
        "calorie_balance_kcal": daily_stats.calorie_balance_kcal,
    }