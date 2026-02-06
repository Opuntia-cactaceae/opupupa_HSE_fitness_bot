from datetime import datetime

from domain.interfaces.unit_of_work import UnitOfWork


async def set_activity_minutes(user_id: int, activity_minutes_per_day: int, uow: UnitOfWork) -> None:
    """
    Устанавливает количество минут физической активности пользователя в день
    и обновляет метку последнего изменения.

    Входные параметры:
        user_id (int): Идентификатор пользователя.
        activity_minutes_per_day (int): Количество минут физической активности
        пользователя в день.
        uow (UnitOfWork): Единица работы, предоставляющая доступ
        к репозиторию пользователей.

    Логика работы:
        - Загружает пользователя по идентификатору.
        - Проверяет существование пользователя.
        - Устанавливает значение ежедневной физической активности.
        - Обновляет время последнего изменения пользователя.
        - Сохраняет изменения в хранилище.

    Возвращаемое значение:
        None.

    Исключения:
        ValueError: Если пользователь с указанным идентификатором не найден.
    """
    user = await uow.users.get(user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")
    user.activity_minutes_per_day = activity_minutes_per_day
    user.updated_at = datetime.utcnow()
    await uow.users.update(user)