"""Валидаторы для сценариев трекинга тренировок."""

from .base import create_numeric_validator
from domain.exceptions import ValidationError


def validate_workout_minutes(text: str) -> int:
    """
    Валидация длительности тренировки (1-300 минут, целое число).
    Возвращает целое число минут.
    """
    # Используем базовый числовой валидатор для проверки диапазона
    numeric_validator = create_numeric_validator(
        field_name="Длительность",
        min_val=1,
        max_val=300,
        allow_zero=False,
        field='workout_minutes'
    )

    # Проверяем диапазон и получаем значение как float
    value = numeric_validator(text)

    # Проверяем, что значение целое (без дробной части)
    if value != int(value):
        raise ValidationError(
            "Длительность должна быть целым числом",
            field='workout_minutes'
        )

    # Возвращаем целое число
    return int(value)