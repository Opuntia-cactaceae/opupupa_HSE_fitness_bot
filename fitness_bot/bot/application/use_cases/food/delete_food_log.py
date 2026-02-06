from datetime import date, datetime
from domain.entities.food_log import FoodLog
from domain.interfaces.unit_of_work import UnitOfWork
from domain.exceptions import EntityNotFoundError


async def delete_food_log(log_id: int, user_id: int, uow: UnitOfWork) -> None:
    """
    Удаляет запись о приёме пищи и корректирует суточную статистику пользователя.

    Входные параметры:
        log_id (int): Идентификатор записи о приёме пищи.
        user_id (int): Идентификатор пользователя, которому принадлежит запись.
        uow (UnitOfWork): Единица работы, предоставляющая доступ к репозиториям и транзакции.

    Логика работы:
        - Загружает запись о приёме пищи по идентификатору.
        - Проверяет, что запись существует и принадлежит указанному пользователю.
        - Удаляет запись о приёме пищи.
        - Гарантирует существование суточной статистики за дату записи.
        - Уменьшает значение потреблённых калорий в суточной статистике
          на калорийность удалённой записи.
        - Обновляет время последнего изменения суточной статистики.

    Возвращаемое значение:
        None.

    Исключения:
        EntityNotFoundError: Если запись о приёме пищи не найдена
        или не принадлежит указанному пользователю.
    """
    food_log = await uow.food_logs.get_by_id(log_id)
    if food_log is None or food_log.user_id != user_id:
        raise EntityNotFoundError("Запись о еде не найдена")

                                                
    kcal_total = food_log.kcal_total
    log_date = food_log.date
    log_user_id = food_log.user_id

                    
    await uow.food_logs.delete(log_id)

                         
    daily_stats = await uow.daily_stats.get_or_create(log_user_id, log_date)
    daily_stats.calories_consumed_kcal -= int(kcal_total)
    daily_stats.updated_at = datetime.utcnow()
    await uow.daily_stats.update(daily_stats)