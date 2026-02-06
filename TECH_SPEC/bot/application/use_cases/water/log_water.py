from datetime import date, datetime

from domain.entities.water_log import WaterLog
from domain.interfaces.unit_of_work import UnitOfWork


async def log_water(user_id: int, ml: int, uow: UnitOfWork) -> int:
    """
    Создаёт запись о потреблении воды и обновляет суточную статистику пользователя.

    Входные параметры:
        user_id (int): Идентификатор пользователя.
        ml (int): Объём потреблённой воды в миллилитрах.
        uow (UnitOfWork): Единица работы, предоставляющая доступ
        к репозиториям записей воды и суточной статистики.

    Логика работы:
        - Формирует сущность записи о потреблении воды с текущей датой
          и временем фиксации.
        - Сохраняет запись о воде в хранилище.
        - Загружает суточную статистику пользователя за текущую дату.
        - Увеличивает показатель потреблённой воды
          на объём добавленной записи.
        - Обновляет время последнего изменения суточной статистики.
        - Сохраняет изменения в хранилище.

    Возвращаемое значение:
        int: Идентификатор созданной записи о потреблении воды.
    """
                         
    water_log = WaterLog(
        id=0,                          
        user_id=user_id,
        date=date.today(),
        logged_at=datetime.utcnow(),
        ml=ml,
    )
    await uow.water_logs.add(water_log)

                         
    today = date.today()
    daily_stats = await uow.daily_stats.get(user_id, today)
    daily_stats.water_logged_ml += ml
    daily_stats.updated_at = datetime.utcnow()
    await uow.daily_stats.update(daily_stats)
    return water_log.id