from typing import Dict


# MET (Metabolic Equivalent of Task) values для разных типов тренировок
# согласно спецификации
WORKOUT_MET: Dict[str, float] = {
    "ходьба": 3.5,
    "бег": 9.5,  # среднее между 8-11
    "силовая": 5.0,  # среднее между 4-6
    "плавание": 7.0,  # среднее между 6-8
    "йога": 2.5,
    "стретчинг": 2.5,
    "hiit": 10.0,  # интенсивная тренировка
}

# Скорость потоотделения (мл/мин) для разных типов тренировок
WORKOUT_SWEAT_RATE_ML_PER_MIN: Dict[str, int] = {
    "ходьба": 5,
    "бег": 12,
    "силовая": 8,
    "плавание": 7,
    "йога": 4,
    "стретчинг": 4,
    "hiit": 15,
}


def get_workout_met(workout_type: str) -> float:
    """Получить MET значение для типа тренировки."""
    return WORKOUT_MET.get(workout_type.lower(), 5.0)


def get_workout_sweat_rate(workout_type: str) -> int:
    """Получить скорость потоотделения (мл/мин) для типа тренировки."""
    return WORKOUT_SWEAT_RATE_ML_PER_MIN.get(workout_type.lower(), 5)