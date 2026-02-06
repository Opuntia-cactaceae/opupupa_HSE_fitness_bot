"""Базовые модели валидации с использованием Pydantic."""

from decimal import Decimal
from typing import Union

from pydantic import BaseModel, field_validator, ValidationError as PydanticValidationError

from domain.exceptions import ValidationError


class NumericInput(BaseModel):
    """Базовая модель для валидации числового ввода из строки."""
    min_val: float
    max_val: float
    allow_zero: bool = True
    field_name: str
    text: str

    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str, info) -> float:
        """Преобразует текст в число и проверяет диапазон."""
        field_name = info.data.get('field_name', 'значение')
        min_val = info.data.get('min_val')
        max_val = info.data.get('max_val')
        allow_zero = info.data.get('allow_zero', True)

        # Защита от некорректной конфигурации валидатора
        if min_val is None:
            raise RuntimeError(f"min_val не может быть None для поля '{field_name}'")
        if max_val is None:
            raise RuntimeError(f"max_val не может быть None для поля '{field_name}'")

        # Преобразуем текст в число
        try:
            value = float(v)
        except ValueError:
            raise ValueError(f"{field_name} должно быть числом")

        # Проверка диапазона
        if min_val == 0 and not allow_zero and value == 0:
            raise ValueError(f"{field_name} должен быть больше 0")

        if value < min_val:
            raise ValueError(f"{field_name} должен быть не менее {min_val}")

        if value > max_val:
            raise ValueError(f"{field_name} не может превышать {max_val}")

        return value


def create_numeric_validator(
    field_name: str,
    min_val: float,
    max_val: float,
    allow_zero: bool = True,
    field: str = None
):
    """Создаёт функцию-валидатор для числового ввода."""
    if min_val is None or max_val is None:
        raise RuntimeError(f"min_val и max_val не могут быть None для валидатора '{field_name}'")
    if min_val > max_val:
        raise RuntimeError(f"min_val ({min_val}) не может быть больше max_val ({max_val}) для валидатора '{field_name}'")
    def validator(text: str) -> float:
        try:
            model = NumericInput(
                text=text,
                field_name=field_name,
                min_val=min_val,
                max_val=max_val,
                allow_zero=allow_zero
            )
            return model.text  # после валидации это float
        except PydanticValidationError as e:
            raise ValidationError(str(e.errors()[0]['msg']), field=field)
    return validator