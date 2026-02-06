from datetime import datetime

from domain.interfaces.unit_of_work import UnitOfWork


async def set_calorie_goal_manual(user_id: int, calorie_goal_kcal: int, uow: UnitOfWork) -> None:
    """
    Устанавливает ручную суточную цель по калориям для пользователя
    и обновляет метку последнего изменения.

    Входные параметры:
        user_id (int): Идентификатор пользователя.
        calorie_goal_kcal (int): Суточная цель по калориям в килокалориях,
        заданная пользователем вручную.
        uow (UnitOfWork): Единица работы, предоставляющая доступ
        к репозиторию пользователей.

    Логика работы:
        - Загружает пользователя по идентификатору.
        - Проверяет существование пользователя.
        - Устанавливает ручное значение суточной цели по калориям.
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
    user.calorie_goal_kcal_manual = calorie_goal_kcal
    user.updated_at = datetime.utcnow()
    await uow.users.update(user)