from datetime import date, timedelta
from typing import List

from domain.interfaces.unit_of_work import UnitOfWork
from domain.entities.daily_stats import DailyStats


async def get_progress_chart_data(
    user_id: int, period_days: int, uow: UnitOfWork
) -> List[DailyStats]:
    """
    Возвращает данные суточной статистики пользователя за указанный период
    для построения графиков прогресса.

    Входные параметры:
        user_id (int): Идентификатор пользователя.
        period_days (int): Количество дней, за которые требуется получить данные.
        uow (UnitOfWork): Единица работы, предоставляющая доступ
        к репозиторию суточной статистики.

    Логика работы:
        - Проверяет, что период задан положительным числом.
        - Определяет диапазон дат от начальной до текущей даты.
        - Ограничивает диапазон дат максимальной глубиной в 10 лет.
        - Загружает суточную статистику пользователя за указанный период.
        - Сортирует записи по дате в порядке возрастания.

    Возвращаемое значение:
        List[DailyStats]:
            Список объектов суточной статистики пользователя
            за указанный период, отсортированный по дате.
            Может быть пустым, если данные отсутствуют.

    Исключения:
        ValueError: Если period_days меньше либо равен нулю.
    """
    if period_days <= 0:
        raise ValueError("period_days должно быть положительным числом")

    today = date.today()
    date_from = today - timedelta(days=period_days - 1)
    date_to = today


    if date_from < today - timedelta(days=365 * 10):
        date_from = today

    daily_stats = await uow.daily_stats.get_for_user_in_range(
        user_id, date_from, date_to
    )
                                               
    daily_stats.sort(key=lambda s: s.date)
    return daily_stats