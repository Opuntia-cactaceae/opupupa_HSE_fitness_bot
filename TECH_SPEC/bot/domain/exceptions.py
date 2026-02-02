"""Исключения предметной области."""

class DomainError(Exception):
    """Базовое исключение предметной области."""
    pass

class ValidationError(DomainError):
    """Ошибка валидации входных данных."""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)

class EntityNotFoundError(DomainError):
    """Сущность не найдена."""
    pass

class BusinessRuleViolationError(DomainError):
    """Нарушение бизнес-правила."""
    pass