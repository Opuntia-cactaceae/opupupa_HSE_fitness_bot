from datetime import date, timedelta
from typing import List, Tuple

from domain.interfaces.unit_of_work import UnitOfWork
from domain.entities.daily_stats import DailyStats


async def get_weekly_stats(
    user_id: int, reference_date: date, uow: UnitOfWork
) -> Tuple[date, date, List[DailyStats]]:
    """
    Возвращает суточную статистику пользователя за календарную неделю,
    в которую входит указанная дата.

    Входные параметры:
        user_id (int): Идентификатор пользователя.
        reference_date (date): Дата, определяющая неделю,
        для которой требуется получить статистику.
        uow (UnitOfWork): Единица работы, предоставляющая доступ
        к репозиторию суточной статистики.

    Логика работы:
        - Определяет начало недели (понедельник) на основе reference_date.
        - Определяет конец недели (воскресенье).
        - Проверяет, что начало недели не лежит в будущем.
        - Ограничивает конец недели текущей датой, если неделя ещё не завершена.
        - Загружает суточную статистику пользователя за вычисленный диапазон дат.
        - Сортирует записи по дате в порядке возрастания.

    Возвращаемое значение:
        Tuple[date, date, List[DailyStats]]:
            Дата начала недели, дата окончания недели
            и список объектов суточной статистики пользователя
            за соответствующий период.
            Список может быть пустым, если данные отсутствуют
            или неделя находится в будущем.
    """
    week_start = reference_date - timedelta(days=reference_date.weekday())
    week_end = week_start + timedelta(days=6)

                                                                        
    today = date.today()
    if week_start > today:
                                                                   
        return week_start, week_end, []

                                                                                 
    if week_end > today:
        week_end = today

    daily_stats = await uow.daily_stats.get_for_user_in_range(
        user_id, week_start, week_end
    )
                                               
    daily_stats.sort(key=lambda s: s.date)
    return week_start, week_end, daily_stats