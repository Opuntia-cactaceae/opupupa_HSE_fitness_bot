from datetime import date, datetime

from domain.interfaces.unit_of_work import UnitOfWork
from infrastructure.ai.weather_client import WeatherClient
from config.settings import settings


async def finalize_profile(user_id: int, uow: UnitOfWork) -> None:
    """Завершить настройку профиля: рассчитать цели и создать DailyStats."""
    user = await uow.users.get(user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")

    import math

    # Получить температуру для коррекции воды (сохраняем для DailyStats)
    weather_client = WeatherClient(settings.WEATHER_API_KEY)
    temperature = await weather_client.get_temperature(user.city)

    # Рассчитать цель по воде
    if user.water_goal_mode == "manual" and user.water_goal_ml_manual is not None:
        water_goal_ml = user.water_goal_ml_manual
    else:
        water_goal_ml = user.calculate_base_water_goal_ml()  # weight_kg * 30
        # Добавить за активность: floor(activity_minutes / 30) * 500, clamp до 3000 мл
        activity_bonus_ml = (user.activity_minutes_per_day // 30) * 500
        activity_bonus_ml = min(activity_bonus_ml, 3000)
        water_goal_ml += activity_bonus_ml
        # Добавить за температуру, если > 25°C
        if temperature is not None and temperature > 25:
            water_goal_ml += 500  # фиксированная добавка 500 мл при температуре > 25°C

    # Рассчитать цель калорий
    if user.calorie_goal_mode == "auto":
        calorie_goal_kcal = user.calculate_base_calorie_goal_kcal()  # BMR
        # Добавить за активность: 200 (<30 мин), 300 (30-60), 400 (>60)
        activity_min = user.activity_minutes_per_day
        if activity_min < 30:
            activity_kcal_bonus = 200
        elif activity_min <= 60:
            activity_kcal_bonus = 300
        else:
            activity_kcal_bonus = 400
        calorie_goal_kcal += activity_kcal_bonus
    else:
        calorie_goal_kcal = user.calorie_goal_kcal_manual or 0

    # Создать или обновить DailyStats на сегодня
    today = date.today()
    daily_stats = await uow.daily_stats.get_or_create(user_id, today)
    daily_stats.temperature_c = temperature
    daily_stats.water_goal_ml = water_goal_ml
    daily_stats.calorie_goal_kcal = calorie_goal_kcal
    daily_stats.updated_at = datetime.utcnow()

    await uow.daily_stats.update(daily_stats)