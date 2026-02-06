from datetime import date, datetime

from domain.entities.water_log import WaterLog
from domain.interfaces.unit_of_work import UnitOfWork
from domain.exceptions import EntityNotFoundError


async def delete_water_log(log_id: int, user_id: int, uow: UnitOfWork) -> None:
    """
    Удаляет запись о потреблении воды и корректирует суточную статистику пользователя.

    Входные параметры:
        log_id (int): Идентификатор записи о потреблении воды.
        user_id (int): Идентификатор пользователя, которому принадлежит запись.
        uow (UnitOfWork): Единица работы, предоставляющая доступ
        к репозиториям записей воды и суточной статистики.

    Логика работы:
        - Загружает запись о потреблении воды по идентификатору.
        - Проверяет, что запись существует и принадлежит указанному пользователю.
        - Удаляет запись о потреблении воды.
        - Загружает суточную статистику за дату записи.
        - Уменьшает объём зафиксированной воды в суточной статистике
          на значение удалённой записи.
        - Обновляет время последнего изменения суточной статистики.

    Возвращаемое значение:
        None.

    Исключения:
        EntityNotFoundError: Если запись о потреблении воды не найдена
        или не принадлежит указанному пользователю.
    """
    water_log = await uow.water_logs.get_by_id(log_id)
    if water_log is None or water_log.user_id != user_id:
        raise EntityNotFoundError("Запись о воде не найдена")

                                                
    ml = water_log.ml
    log_date = water_log.date
    log_user_id = water_log.user_id

                    
    await uow.water_logs.delete(log_id)

    daily_stats = await uow.daily_stats.get(log_user_id, log_date)
    daily_stats.water_logged_ml -= ml
    daily_stats.updated_at = datetime.utcnow()
    await uow.daily_stats.update(daily_stats)