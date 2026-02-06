"""Тесты для валидаторов ввода с использованием Pydantic моделей."""

import pytest
from pydantic import ValidationError as PydanticValidationError

from presentation.validators.base import NumericInput, create_numeric_validator
from presentation.validators.profile import validate_city, validate_weight
from presentation.validators.workout import validate_workout_minutes
from domain.exceptions import ValidationError


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

class TestWeightValidator:
    """Тестирование валидатора веса."""

    def test_valid_weight(self):
        """Валидный вес."""
        result = validate_weight("90")
        assert result == 90.0

    def test_zero_weight_raises_error(self):
        """Вес 0 вызывает ValidationError."""
        with pytest.raises(ValidationError) as exc:
            validate_weight("0")
        assert "не менее 30" in str(exc.value)

    def test_out_of_range_weight_raises_error(self):
        """Вес вне диапазона вызывает ValidationError."""
        with pytest.raises(ValidationError) as exc:
            validate_weight("10")
        assert "не менее 30" in str(exc.value)


class TestCreateNumericValidator:
    """Тестирование create_numeric_validator."""

    def test_none_min_val_raises_runtime_error(self):
        """min_val=None вызывает RuntimeError."""
        with pytest.raises(RuntimeError) as exc:
            create_numeric_validator(
                field_name="Тест",
                min_val=None,
                max_val=100,
                allow_zero=True
            )
        assert "не могут быть None" in str(exc.value)

    def test_none_max_val_raises_runtime_error(self):
        """max_val=None вызывает RuntimeError."""
        with pytest.raises(RuntimeError) as exc:
            create_numeric_validator(
                field_name="Тест",
                min_val=0,
                max_val=None,
                allow_zero=True
            )
        assert "не могут быть None" in str(exc.value)

    def test_min_greater_than_max_raises_runtime_error(self):
        """min_val > max_val вызывает RuntimeError."""
        with pytest.raises(RuntimeError) as exc:
            create_numeric_validator(
                field_name="Тест",
                min_val=100,
                max_val=50,
                allow_zero=True
            )
        assert "не может быть больше" in str(exc.value)


class TestWorkoutValidator:
    """Тестирование валидатора длительности тренировки."""

    def test_valid_minutes(self):
        """Валидное количество минут."""
        result = validate_workout_minutes("60")
        assert result == 60
        assert isinstance(result, int)

    def test_min_boundary(self):
        """Нижняя граница (1 минута)."""
        result = validate_workout_minutes("1")
        assert result == 1

    def test_max_boundary(self):
        """Верхняя граница (300 минут)."""
        result = validate_workout_minutes("300")
        assert result == 300

    def test_below_min(self):
        """Ниже минимального (0 минут)."""
        with pytest.raises(ValidationError) as exc:
            validate_workout_minutes("0")
        assert "не менее 1" in str(exc.value) or "больше 0" in str(exc.value)

    def test_above_max(self):
        """Выше максимального (301 минута)."""
        with pytest.raises(ValidationError) as exc:
            validate_workout_minutes("301")
        assert "не может превышать 300" in str(exc.value)

    def test_not_a_number(self):
        """Ввод не является числом."""
        with pytest.raises(ValidationError) as exc:
            validate_workout_minutes("abc")
        assert "должно быть числом" in str(exc.value)

    def test_fractional_minutes(self):
        """Дробное количество минут."""
        with pytest.raises(ValidationError) as exc:
            validate_workout_minutes("45.5")
        assert "целым числом" in str(exc.value)

    def test_negative_minutes(self):
        """Отрицательное количество минут."""
        with pytest.raises(ValidationError) as exc:
            validate_workout_minutes("-10")
        assert "не менее 1" in str(exc.value)