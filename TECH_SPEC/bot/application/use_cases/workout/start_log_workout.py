from domain.interfaces.unit_of_work import UnitOfWork


async def start_log_workout(user_id: int, uow: UnitOfWork) -> None:
    """Начать сценарий логирования тренировки."""
    # В реальной реализации здесь может быть инициализация состояния FSM
    # Пока просто заглушка
    pass