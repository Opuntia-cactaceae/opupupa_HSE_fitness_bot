from datetime import datetime

from domain.interfaces.unit_of_work import UnitOfWork


async def set_city(user_id: int, city: str, uow: UnitOfWork) -> None:
    """
    Устанавливает город проживания пользователя и обновляет метку
    последнего изменения.

    Входные параметры:
        user_id (int): Идентификатор пользователя.
        city (str): Название города пользователя.
        uow (UnitOfWork): Единица работы, предоставляющая доступ
        к репозиторию пользователей.

    Логика работы:
        - Загружает пользователя по идентификатору.
        - Проверяет существование пользователя.
        - Устанавливает значение города пользователя.
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
    user.city = city
    user.updated_at = datetime.utcnow()
    await uow.users.update(user)