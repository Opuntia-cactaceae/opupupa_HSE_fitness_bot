from datetime import datetime

from domain.interfaces.unit_of_work import UnitOfWork


async def set_calorie_goal_mode(user_id: int, mode: str, uow: UnitOfWork) -> None:
    """
    Устанавливает режим расчёта суточной цели по калориям для пользователя
    и обновляет метку последнего изменения.

    Входные параметры:
        user_id (int): Идентификатор пользователя.
        mode (str): Режим расчёта суточной цели по калориям.
        Допустимые значения: "auto", "manual".
        uow (UnitOfWork): Единица работы, предоставляющая доступ
        к репозиторию пользователей.

    Логика работы:
        - Проверяет корректность значения режима расчёта.
        - Загружает пользователя по идентификатору.
        - Проверяет существование пользователя.
        - Устанавливает режим расчёта суточной цели по калориям.
        - Обновляет время последнего изменения пользователя.
        - Сохраняет изменения в хранилище.

    Возвращаемое значение:
        None.

    Исключения:
        ValueError: Если режим расчёта задан некорректно
        или пользователь с указанным идентификатором не найден.
    """
    if mode not in ("auto", "manual"):
        raise ValueError("Mode must be 'auto' or 'manual'")

    user = await uow.users.get(user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")
    user.calorie_goal_mode = mode
    user.updated_at = datetime.utcnow()
    await uow.users.update(user)