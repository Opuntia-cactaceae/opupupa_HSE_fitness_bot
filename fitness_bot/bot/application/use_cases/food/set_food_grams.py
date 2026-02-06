from typing import Tuple

from domain.exceptions import ValidationError


def set_food_grams(kcal_per_100g: float, grams: float) -> Tuple[float, float]:
    """
        Рассчитывает суммарную калорийность продукта на основе массы
        и калорийности на 100 грамм.

        Входные параметры:
            kcal_per_100g (float): Калорийность продукта на 100 грамм.
            grams (float): Масса продукта в граммах.

        Логика работы:
            - Проверяет, что калорийность на 100 грамм является положительным числом.
            - Вычисляет суммарную калорийность пропорционально массе продукта.

        Возвращаемое значение:
            Tuple[float, float]:
                Масса продукта в граммах и суммарная калорийность.
                Первый элемент — grams,
                второй элемент — kcal_total.

        Исключения:
            ValidationError: Если калорийность на 100 грамм меньше либо равна нулю.
        """
    if kcal_per_100g <= 0:
        raise ValidationError("Калорийность продукта должна быть положительной")

    kcal_total = (kcal_per_100g / 100.0) * grams
    return grams, kcal_total