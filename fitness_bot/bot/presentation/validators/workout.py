

from .base import create_numeric_validator
from domain.exceptions import ValidationError


def validate_workout_minutes(text: str) -> int:
    
                                                                  
    numeric_validator = create_numeric_validator(
        field_name="Длительность",
        min_val=1,
        max_val=300,
        allow_zero=False,
        field='workout_minutes'
    )

                                                      
    value = numeric_validator(text)

                                                       
    if value != int(value):
        raise ValidationError(
            "Длительность должна быть целым числом",
            field='workout_minutes'
        )

                            
    return int(value)