from datetime import date, timedelta
from typing import List, Tuple

from domain.interfaces.unit_of_work import UnitOfWork
from domain.entities.daily_stats import DailyStats


async def get_weekly_stats(
    user_id: int, reference_date: date, uow: UnitOfWork
) -> Tuple[date, date, List[DailyStats]]:
    """Получить статистику за неделю (понедельник–воскресенье), содержащую указанную дату.

    Возвращает кортеж (week_start, week_end, daily_stats_list), где daily_stats_list
    отсортирован по дате и содержит только существующие записи за неделю.
    """
    # Неделя начинается с понедельника (ISO)
    week_start = reference_date - timedelta(days=reference_date.weekday())
    week_end = week_start + timedelta(days=6)

    # Не загружаем данные будущих недель (ограничиваем сегодняшним днём)
    today = date.today()
    if week_start > today:
        # Если неделя полностью в будущем, возвращаем пустой список
        return week_start, week_end, []

    # Если неделя частично в будущем, ограничиваем конечную дату сегодняшним днём
    if week_end > today:
        week_end = today

    daily_stats = await uow.daily_stats.get_for_user_in_range(
        user_id, week_start, week_end
    )
    # Убедимся, что список отсортирован по дате
    daily_stats.sort(key=lambda s: s.date)
    return week_start, week_end, daily_stats