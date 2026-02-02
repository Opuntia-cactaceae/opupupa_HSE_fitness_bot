"""Тесты для валидаторов ввода с использованием Pydantic моделей."""

import pytest
from pydantic import ValidationError as PydanticValidationError

from presentation.validators.base import NumericInput
from presentation.validators.profile import validate_city


class TestNumericInput:
    """Тестирование базовой модели NumericInput."""

    def test_valid_number_within_range(self):
        """Валидное число в диапазоне."""
        model = NumericInput(
            text="50",
            field_name="Поле",
            min_val=0,
            max_val=100,
            allow_zero=True
        )
        assert model.text == 50.0

    def test_valid_boundary_min(self):
        """Валидное число на нижней границе."""
        model = NumericInput(
            text="0",
            field_name="Поле",
            min_val=0,
            max_val=100,
            allow_zero=True
        )
        assert model.text == 0.0

    def test_valid_boundary_max(self):
        """Валидное число на верхней границе."""
        model = NumericInput(
            text="100",
            field_name="Поле",
            min_val=0,
            max_val=100,
            allow_zero=True
        )
        assert model.text == 100.0

    def test_below_min(self):
        """Число ниже минимального."""
        with pytest.raises(PydanticValidationError) as exc:
            NumericInput(
                text="-5",
                field_name="Поле",
                min_val=0,
                max_val=100,
                allow_zero=True
            )
        assert "не менее 0" in str(exc.value)

    def test_above_max(self):
        """Число выше максимального."""
        with pytest.raises(PydanticValidationError) as exc:
            NumericInput(
                text="150",
                field_name="Поле",
                min_val=0,
                max_val=100,
                allow_zero=True
            )
        assert "не может превышать 100" in str(exc.value)

    def test_not_a_number(self):
        """Ввод не является числом."""
        with pytest.raises(PydanticValidationError) as exc:
            NumericInput(
                text="abc",
                field_name="Поле",
                min_val=0,
                max_val=100,
                allow_zero=True
            )
        assert "должно быть числом" in str(exc.value)

    def test_zero_not_allowed(self):
        """Нулевое значение, когда allow_zero=False."""
        with pytest.raises(PydanticValidationError) as exc:
            NumericInput(
                text="0",
                field_name="Поле",
                min_val=0,
                max_val=100,
                allow_zero=False
            )
        assert "должен быть больше 0" in str(exc.value)

    def test_zero_allowed_with_min_greater_than_zero(self):
        """Минимальное значение больше 0, но ввод 0."""
        with pytest.raises(PydanticValidationError) as exc:
            NumericInput(
                text="0",
                field_name="Поле",
                min_val=10,
                max_val=100,
                allow_zero=True  # Игнорируется, т.к. min_val > 0
            )
        assert "не менее 10" in str(exc.value)

    def test_fractional_number(self):
        """Дробное число."""
        model = NumericInput(
            text="75.5",
            field_name="Поле",
            min_val=0,
            max_val=100,
            allow_zero=True
        )
        assert model.text == 75.5

    def test_negative_min_value(self):
        """Отрицательное минимальное значение."""
        model = NumericInput(
            text="-10",
            field_name="Температура",
            min_val=-20,
            max_val=0,
            allow_zero=True
        )
        assert model.text == -10.0


class TestValidateCity:
    """Тестирование validate_city."""

    def test_valid_city(self):
        """Валидный город."""
        result = validate_city("Москва")
        assert result == "Москва"

    def test_valid_city_with_spaces(self):
        """Город с пробелами."""
        result = validate_city("Нью Йорк")
        assert result == "Нью Йорк"

    def test_valid_city_with_hyphen(self):
        """Город с дефисом."""
        result = validate_city("Ростов-на-Дону")
        assert result == "Ростов-на-Дону"

    def test_valid_city_with_dot(self):
        """Город с точкой."""
        result = validate_city("Санкт-Петербург")
        assert result == "Санкт-Петербург"

    def test_valid_city_with_apostrophe(self):
        """Город с апострофом."""
        result = validate_city("О'Фаллон")
        assert result == "О'Фаллон"

    def test_empty_city(self):
        """Пустой город."""
        with pytest.raises(Exception) as exc:
            validate_city("")
        assert "не может быть пустым" in str(exc.value)

    def test_city_too_short(self):
        """Слишком короткое название."""
        with pytest.raises(Exception) as exc:
            validate_city("А")
        assert "от 2 до 64 символов" in str(exc.value)

    def test_city_too_long(self):
        """Слишком длинное название."""
        long_city = "А" * 65
        with pytest.raises(Exception) as exc:
            validate_city(long_city)
        assert "от 2 до 64 символов" in str(exc.value)

    def test_city_with_numbers(self):
        """Город с цифрами."""
        with pytest.raises(Exception) as exc:
            validate_city("Москва123")
        assert "только буквы" in str(exc.value)

    def test_city_with_special_chars(self):
        """Город со специальными символами."""
        with pytest.raises(Exception) as exc:
            validate_city("Москва@")
        assert "только буквы" in str(exc.value)

    def test_city_with_mixed_case(self):
        """Город с разным регистром."""
        result = validate_city("мОсКвА")
        assert result == "мОсКвА"

    def test_city_trim_spaces(self):
        """Город с пробелами в начале и конце."""
        result = validate_city("  Москва  ")
        assert result == "Москва"  # validator strips