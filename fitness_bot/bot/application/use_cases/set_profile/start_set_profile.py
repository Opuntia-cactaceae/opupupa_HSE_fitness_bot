from datetime import datetime

from domain.entities.user import User
from domain.interfaces.unit_of_work import UnitOfWork


async def start_set_profile(user_id: int, uow: UnitOfWork) -> None:
    """
    Инициализирует профиль пользователя при начале его настройки.

    Входные параметры:
        user_id (int): Идентификатор пользователя.
        uow (UnitOfWork): Единица работы, предоставляющая доступ
        к репозиторию пользователей.

    Логика работы:
        - Загружает пользователя по идентификатору.
        - Если пользователь не существует, создаёт новую сущность пользователя
          с начальными значениями профиля.
        - Устанавливает дату и время создания и последнего обновления.
        - Сохраняет нового пользователя в хранилище.

    Возвращаемое значение:
        None.
    """
    user = await uow.users.get(user_id)
    if user is None:
        user = User(
            id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            weight_kg=0.0,
            height_cm=0.0,
            age_years=0,
            activity_minutes_per_day=0,
            city="",
            timezone="Europe/Amsterdam",
            calorie_goal_mode="auto",
            calorie_goal_kcal_manual=None,
        )
        await uow.users.add(user)