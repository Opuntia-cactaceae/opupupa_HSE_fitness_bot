from datetime import date
from typing import Tuple

from domain.interfaces.unit_of_work import UnitOfWork


async def get_water_progress(user_id: int, uow: UnitOfWork) -> Tuple[int, int, int]:
    """
    Возвращает текущий прогресс пользователя по потреблению воды за сегодня.

    Входные параметры:
        user_id (int): Идентификатор пользователя.
        uow (UnitOfWork): Единица работы, предоставляющая доступ
        к репозиторию суточной статистики.

    Логика работы:
        - Определяет текущую дату.
        - Загружает суточную статистику пользователя за текущую дату.
        - Если статистика отсутствует, возвращает нулевые значения.
        - Извлекает показатели потреблённой воды, целевого значения
          и оставшегося объёма воды.

    Возвращаемое значение:
        Tuple[int, int, int]:
            Кортеж из трёх значений:
            - объём потреблённой воды за день (мл),
            - суточная цель по воде (мл),
            - оставшийся до цели объём воды (мл).
    """
    today = date.today()
    daily_stats = await uow.daily_stats.get(user_id, today)
    if daily_stats is None:
        return (0, 0, 0)
    return (
        daily_stats.water_logged_ml,
        daily_stats.water_goal_ml,
        daily_stats.water_remaining_ml,
    )