from datetime import date, datetime
import math
from domain.interfaces.unit_of_work import UnitOfWork
from infrastructure.api.weather_client import WeatherClient
from config.settings import settings


async def finalize_profile(user_id: int, uow: UnitOfWork) -> None:
    """
    Завершает настройку профиля пользователя и рассчитывает суточные цели
    по воде и калориям с учётом параметров профиля и погодных условий.

    Входные параметры:
        user_id (int): Идентификатор пользователя.
        uow (UnitOfWork): Единица работы, предоставляющая доступ
        к репозиториям пользователей и суточной статистики.

    Логика работы:
        - Загружает пользователя по идентификатору и проверяет его существование.
        - Получает текущую температуру воздуха для города пользователя
          через клиент погодного сервиса.
        - Определяет суточную цель по воде:
            - Использует ручное значение, если выбран ручной режим.
            - В противном случае рассчитывает базовую норму,
              добавляет надбавку за физическую активность
              и корректирует значение при высокой температуре воздуха.
        - Определяет суточную цель по калориям:
            - Рассчитывает значение автоматически с учётом уровня активности
              либо использует ручное значение при отключённом автоматическом режиме.
        - Загружает или создаёт суточную статистику за текущую дату.
        - Сохраняет рассчитанные цели и температуру в суточной статистике
          и обновляет время последнего изменения.

    Возвращаемое значение:
        None.

    Исключения:
        ValueError: Если пользователь с указанным идентификатором не найден.
    """
    user = await uow.users.get(user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")

    weather_client = WeatherClient(settings.WEATHER_API_KEY)
    temperature = await weather_client.get_temperature(user.city)

    water_goal_ml = user.calculate_water_goal_ml(temperature)
    calorie_goal_kcal = user.calculate_calorie_goal_kcal()

                                                
    today = date.today()
    daily_stats = await uow.daily_stats.get_or_create(user_id, today)
    daily_stats.temperature_c = temperature
    daily_stats.water_goal_ml = water_goal_ml
    daily_stats.calorie_goal_kcal = calorie_goal_kcal
    daily_stats.updated_at = datetime.utcnow()

    await uow.daily_stats.update(daily_stats)