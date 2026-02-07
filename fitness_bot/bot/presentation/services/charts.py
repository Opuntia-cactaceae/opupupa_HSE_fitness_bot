from typing import List, Optional
from domain.entities.daily_stats import DailyStats
from infrastructure.charts.progress_charts import build_progress_charts_png


def build_progress_chart(daily_stats: List[DailyStats]) -> Optional[bytes]:
    """
    Генерирует PNG-график прогресса по воде и калориям.

    Входные параметры:
        daily_stats (List[DailyStats]): Список суточной статистики.

    Возвращаемое значение:
        Optional[bytes]: Байты PNG-изображения или None, если данных нет.
    """
    return build_progress_charts_png(daily_stats)
