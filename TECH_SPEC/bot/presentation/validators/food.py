"""Валидаторы для сценариев трекинга еды."""

from .base import create_numeric_validator
from domain.exceptions import ValidationError


validate_grams = create_numeric_validator(
    field_name="Количество",
    min_val=1,
    max_val=3000,
    allow_zero=False,
    field='grams'
)


def validate_product_name(text: str) -> str:
    """Валидация названия продукта."""
    product_name = text.strip()

    if not product_name:
        raise ValidationError("Название продукта не может быть пустым", field='product_name')

    if len(product_name) < 1 or len(product_name) > 100:
        raise ValidationError("Название продукта должно быть от 1 до 100 символов", field='product_name')

    # Разрешаем буквы, цифры, пробелы, дефисы, точки, апострофы, скобки, запятые
    allowed_chars = set(
        "abcdefghijklmnopqrstuvwxyzабвгдеёжзийклмнопрстуфхцчшщъыьэюя"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ0123456789 -.'(),"
    )
    if not all(c in allowed_chars for c in product_name):
        raise ValidationError(
            "Название продукта должно содержать только буквы, цифры, пробелы, дефисы, "
            "точки, апострофы, скобки и запятые",
            field='product_name'
        )

    return product_name