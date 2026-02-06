import io
from datetime import date
from typing import List, Optional

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure

from domain.entities.daily_stats import DailyStats


def build_progress_charts_png(daily_stats: List[DailyStats]) -> Optional[bytes]:
    """
    Строит PNG-изображение с графиками прогресса по воде и калориям
    на основе списка суточной статистики.

    Входные параметры:
        daily_stats (List[DailyStats]): Список объектов суточной статистики,
        содержащих значения потребления воды и калорий по датам.

    Логика работы:
        - При отсутствии данных возвращает None.
        - Извлекает временной ряд дат и ключевых показателей из списка статистики.
        - Строит два графика:
            - прогресс по воде (выпито и цель),
            - прогресс по калориям (потреблено, сожжено и цель).
        - Форматирует ось дат.
        - Сохраняет результат в буфер памяти в формате PNG и возвращает байты.

    Возвращаемое значение:
        Optional[bytes]:
            Байтовое содержимое PNG-файла с графиками прогресса
            или None при отсутствии данных.
    """
    if not daily_stats:
        return None

    dates = [s.date for s in daily_stats]
    water_logged = [s.water_logged_ml for s in daily_stats]
    water_goal = [s.water_goal_ml for s in daily_stats]
    calories_consumed = [s.calories_consumed_kcal for s in daily_stats]
    calories_burned = [s.calories_burned_kcal for s in daily_stats]
    calorie_goal = [s.calorie_goal_kcal for s in daily_stats]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    fig.suptitle("Прогресс по воде и калориям", fontsize=14)

                 
    ax1.plot(dates, water_logged, marker='o', label='Выпито, мл', color='#1f77b4')
    ax1.plot(dates, water_goal, marker='s', linestyle='--', label='Цель, мл', color='#ff7f0e')
    ax1.set_ylabel('Вода (мл)')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)

                    
    ax2.plot(dates, calories_consumed, marker='o', label='Потреблено, ккал', color='#2ca02c')
    ax2.plot(dates, calories_burned, marker='^', label='Сожжено, ккал', color='#d62728')
    ax2.plot(dates, calorie_goal, marker='s', linestyle='--', label='Цель, ккал', color='#9467bd')
    ax2.set_xlabel('Дата')
    ax2.set_ylabel('Калории (ккал)')
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)

                            
    date_fmt = mdates.DateFormatter('%d.%m')
    ax2.xaxis.set_major_formatter(date_fmt)
    fig.autofmt_xdate(rotation=30)

                        
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf.read()


