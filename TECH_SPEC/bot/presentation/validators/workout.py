"""Валидаторы для сценариев трекинга тренировок."""

from .base import create_numeric_validator


validate_workout_minutes = create_numeric_validator(
    field_name="Длительность",
    min_val=1,
    max_val=300,
    allow_zero=False,
    field='workout_minutes'
)