from datetime import datetime

from domain.interfaces.unit_of_work import UnitOfWork


async def set_age(user_id: int, age_years: int, uow: UnitOfWork) -> None:
    """
    Устанавливает возраст пользователя и обновляет метку последнего изменения.

    Входные параметры:
        user_id (int): Идентификатор пользователя.
        age_years (int): Возраст пользователя в полных годах.
        uow (UnitOfWork): Единица работы, предоставляющая доступ
        к репозиторию пользователей.

    Логика работы:
        - Загружает пользователя по идентификатору.
        - Проверяет существование пользователя.
        - Устанавливает значение возраста пользователя.
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
    user.age_years = age_years
    user.updated_at = datetime.utcnow()
    await uow.users.update(user)