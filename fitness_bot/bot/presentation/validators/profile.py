

from .base import create_numeric_validator
from domain.exceptions import ValidationError


validate_weight = create_numeric_validator(
    field_name="Вес",
    min_val=30,
    max_val=300,
    allow_zero=False,
    field='weight'
)

validate_height = create_numeric_validator(
    field_name="Рост",
    min_val=100,
    max_val=230,
    allow_zero=False,
    field='height'
)

validate_age = create_numeric_validator(
    field_name="Возраст",
    min_val=10,
    max_val=120,
    allow_zero=False,
    field='age'
)

validate_activity_minutes = create_numeric_validator(
    field_name="Активность",
    min_val=0,
    max_val=600,
    allow_zero=True,
    field='activity_minutes'
)

validate_calorie_goal = create_numeric_validator(
    field_name="Цель по калориям",
    min_val=1200,
    max_val=5000,
    allow_zero=False,
    field='calorie_goal'
)

validate_water_goal = create_numeric_validator(
    field_name="Цель по воде",
    min_val=500,
    max_val=6000,
    allow_zero=False,
    field='water_goal'
)


def validate_city(text: str) -> str:
    
    city = text.strip()

    if not city:
        raise ValidationError("Город не может быть пустым", field='city')

    if len(city) < 2 or len(city) > 64:
        raise ValidationError("Название города должно быть от 2 до 64 символов", field='city')

                                                                 
    allowed_chars = set(
        "abcdefghijklmnopqrstuvwxyzабвгдеёжзийклмнопрстуфхцчшщъыьэюя"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ -.'"
    )
    if not all(c in allowed_chars for c in city):
        raise ValidationError(
            "Город должен содержать только буквы, пробелы, дефисы, точки и апострофы",
            field='city'
        )

    return city