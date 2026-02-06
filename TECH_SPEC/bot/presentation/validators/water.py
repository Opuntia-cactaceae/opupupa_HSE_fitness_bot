

from .base import create_numeric_validator
from domain.exceptions import ValidationError


validate_water_ml = create_numeric_validator(
    field_name="Объём воды",
    min_val=50,
    max_val=3000,
    allow_zero=False,
    field='water_ml'
)