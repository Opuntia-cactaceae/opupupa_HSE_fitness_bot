from datetime import date, datetime

from domain.entities.food_log import FoodLog
from domain.interfaces.unit_of_work import UnitOfWork



async def finalize_food_log(
    user_id: int,
    product_query: str,
    product_name: str,
    source: str,
    kcal_per_100g: float,
    grams: float,
    kcal_total: float,
    uow: UnitOfWork,
) -> int:
    """
        Создаёт и сохраняет запись о приёме пищи, а также обновляет суточную статистику пользователя.

        Входные параметры:
            user_id (int): Идентификатор пользователя.
            product_query (str): Исходный текст запроса, по которому был найден продукт.
            product_name (str): Нормализованное название продукта.
            source (str): Источник данных о продукте.
            kcal_per_100g (float): Калорийность продукта на 100 грамм.
            grams (float): Масса потреблённого продукта в граммах.
            kcal_total (float): Общая калорийность потреблённой порции.
            uow (UnitOfWork): Единица работы, предоставляющая доступ к репозиториям и транзакции.

        Логика работы:
            - Формирует доменную сущность записи о приёме пищи с текущей датой и временем.
            - Сохраняет запись в хранилище.
            - Гарантирует существование суточной статистики пользователя за текущую дату.
            - Увеличивает значение потреблённых калорий в суточной статистике
              на калорийность добавленной записи.
            - Обновляет время последнего изменения суточной статистики.

        Возвращаемое значение:
            int: Идентификатор созданной записи о приёме пищи.
        """
    food_log = FoodLog(
        id=0,
        user_id=user_id,
        date=date.today(),
        logged_at=datetime.utcnow(),
        product_query=product_query,
        product_name=product_name,
        source=source,
        product_external_id=None,
        kcal_per_100g=kcal_per_100g,
        grams=grams,
        kcal_total=kcal_total,
    )
    await uow.food_logs.add(food_log)

                         
    today = date.today()
    daily_stats = await uow.daily_stats.get_or_create(user_id, today)
    daily_stats.calories_consumed_kcal += int(kcal_total)
    daily_stats.updated_at = datetime.utcnow()
    await uow.daily_stats.update(daily_stats)
    return food_log.id