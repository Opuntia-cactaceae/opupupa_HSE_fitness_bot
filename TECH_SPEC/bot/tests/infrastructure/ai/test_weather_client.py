import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp
import asyncio
from typing import Optional, Dict, Any

from infrastructure.ai.weather_client import (
    WeatherClient,
    WeatherInfo,
    _contains_cyrillic,
    _transliterate_cyrillic,
)


class TestWeatherClient:
    """Тесты для WeatherClient с OpenWeather API."""

    @pytest.fixture
    def api_key(self):
        return "test-api-key"

    @pytest.fixture
    def client(self, api_key):
        return WeatherClient(api_key)

    @pytest.mark.asyncio
    async def test_get_weather_success(self, client):
        """Успешное получение погоды."""
        with patch.object(client, '_geocode', new_callable=AsyncMock) as mock_geocode, \
             patch.object(client, '_fetch_weather', new_callable=AsyncMock) as mock_fetch:

            mock_geocode.return_value = (55.7558, 37.6173)
            mock_fetch.return_value = {
                "main": {"temp": 23.5},
                "weather": [
                    {"description": "ясно", "main": "Clear", "id": 800}
                ]
            }

            result = await client.get_weather("Moscow")

            assert isinstance(result, WeatherInfo)
            assert result.temperature_c == 23.5
            assert result.description == "ясно"
            assert result.main == "Clear"
            assert result.condition_id == 800

            mock_geocode.assert_called_once_with("Moscow")
            mock_fetch.assert_called_once_with(55.7558, 37.6173)

    @pytest.mark.asyncio
    async def test_get_temperature_calls_get_weather(self, client):
        """get_temperature вызывает get_weather и возвращает температуру."""
        with patch.object(client, 'get_weather', new_callable=AsyncMock) as mock_get_weather:
            mock_get_weather.return_value = WeatherInfo(temperature_c=15.0)
            result = await client.get_temperature("Moscow")
            mock_get_weather.assert_called_once_with("Moscow")
            assert result == 15.0

    @pytest.mark.asyncio
    async def test_get_temperature_returns_none_if_weather_none(self, client):
        """get_temperature возвращает None, если get_weather вернул None."""
        with patch.object(client, 'get_weather', new_callable=AsyncMock) as mock_get_weather:
            mock_get_weather.return_value = None
            result = await client.get_temperature("Moscow")
            assert result is None

    @pytest.mark.asyncio
    async def test_no_api_key_returns_none(self):
        """Если API ключ отсутствует, возвращается None."""
        client = WeatherClient(None)
        result = await client.get_weather("Moscow")
        assert result is None

        client = WeatherClient("")
        result = await client.get_weather("Moscow")
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_city_returns_none(self, client):
        """Пустой город возвращает None."""
        result = await client.get_weather("")
        assert result is None
        result = await client.get_weather("   ")
        assert result is None

    @pytest.mark.asyncio
    async def test_geocoding_fails_returns_none(self, client):
        """Если геокодирование не нашло город, возвращается None."""
        with patch.object(client, '_geocode', new_callable=AsyncMock) as mock_geocode:
            mock_geocode.return_value = None
            result = await client.get_weather("UnknownCity")
            assert result is None

    @pytest.mark.asyncio
    async def test_weather_api_fails_returns_none(self, client):
        """Если API погоды вернуло ошибку, возвращается None."""
        with patch.object(client, '_geocode', new_callable=AsyncMock) as mock_geocode, \
             patch.object(client, '_fetch_weather', new_callable=AsyncMock) as mock_fetch:

            mock_geocode.return_value = (55.7558, 37.6173)
            mock_fetch.return_value = None

            result = await client.get_weather("Moscow")
            assert result is None

    @pytest.mark.asyncio
    async def test_missing_temperature_in_response_returns_none(self, client):
        """Если в ответе нет температуры, возвращается None."""
        with patch.object(client, '_geocode', new_callable=AsyncMock) as mock_geocode, \
             patch.object(client, '_fetch_weather', new_callable=AsyncMock) as mock_fetch:

            mock_geocode.return_value = (55.7558, 37.6173)
            mock_fetch.return_value = {"main": {}, "weather": []}

            result = await client.get_weather("Moscow")
            assert result is None

    @pytest.mark.asyncio
    async def test_geocoding_cache(self, client):
        """Координаты кэшируются после первого успешного геокодирования."""
        with patch.object(client, '_geocode', new_callable=AsyncMock) as mock_geocode, \
             patch.object(client, '_fetch_weather', new_callable=AsyncMock) as mock_fetch:

            mock_geocode.return_value = (55.7558, 37.6173)
            mock_fetch.return_value = {"main": {"temp": 23.5}, "weather": [{"description": "clear", "main": "Clear", "id": 800}]}

            # Первый вызов
            result1 = await client.get_weather("Moscow")
            assert result1 is not None
            # Второй вызов для того же города
            result2 = await client.get_weather("Moscow")
            assert result2 is not None

            # Должен быть только один вызов геокодирования
            assert mock_geocode.call_count == 1
            assert mock_fetch.call_count == 2

    @pytest.mark.asyncio
    async def test_cyrillic_city_fallback_success(self, client):
        """Город на кириллице транслитерируется при неудаче геокодирования."""
        with patch.object(client, '_geocode', new_callable=AsyncMock) as mock_geocode, \
             patch.object(client, '_fetch_weather', new_callable=AsyncMock) as mock_fetch:

            # Первый вызов геокодирования (кириллица) возвращает None
            # Второй вызов (транслитерированный) успешен
            def geocode_side_effect(city):
                if city == "Москва":
                    return None
                elif city == "Moskva":
                    return (55.7558, 37.6173)
                return None

            mock_geocode.side_effect = geocode_side_effect
            mock_fetch.return_value = {"main": {"temp": 23.5}, "weather": [{"description": "clear", "main": "Clear", "id": 800}]}

            result = await client.get_weather("Москва")
            assert result is not None

            # Проверяем, что было два вызова геокодирования
            assert mock_geocode.call_count == 2
            calls = mock_geocode.call_args_list
            assert calls[0][0][0] == "Москва"
            assert calls[1][0][0] == "Moskva"

    @pytest.mark.asyncio
    async def test_cyrillic_city_no_fallback_if_not_cyrillic(self, client):
        """Транслитерация не применяется, если город не содержит кириллицу."""
        with patch.object(client, '_geocode', new_callable=AsyncMock) as mock_geocode:
            mock_geocode.return_value = None
            result = await client.get_weather("Berlin")
            assert result is None
            # Только один вызов геокодирования
            mock_geocode.assert_called_once_with("Berlin")

    @pytest.mark.asyncio
    async def test_cyrillic_city_fallback_already_transliterated(self, client):
        """Если город уже транслитерирован, повторная транслитерация не меняет его."""
        with patch.object(client, '_geocode', new_callable=AsyncMock) as mock_geocode:
            mock_geocode.return_value = None
            result = await client.get_weather("Moskva")
            assert result is None
            # Только один вызов геокодирования, без дополнительных вызовов
            mock_geocode.assert_called_once_with("Moskva")

    @pytest.mark.asyncio
    async def test_geocode_method_handles_api_key_none(self):
        """_geocode возвращает None, если API ключ отсутствует."""
        client = WeatherClient(None)
        result = await client._geocode("Moscow")
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_weather_method_handles_api_key_none(self):
        """_fetch_weather возвращает None, если API ключ отсутствует."""
        client = WeatherClient(None)
        result = await client._fetch_weather(55.7558, 37.6173)
        assert result is None


class TestTransliterationHelpers:
    """Тесты вспомогательных функций транслитерации."""

    def test_contains_cyrillic(self):
        """Проверка обнаружения кириллических символов."""
        assert _contains_cyrillic("Москва") is True
        assert _contains_cyrillic("Санкт-Петербург") is True
        assert _contains_cyrillic("Moscow") is False
        assert _contains_cyrillic("Berlin") is False
        assert _contains_cyrillic("123") is False
        assert _contains_cyrillic("") is False
        # Смешанный текст
        assert _contains_cyrillic("Moscow Москва") is True

    def test_transliterate_cyrillic(self):
        """Проверка транслитерации."""
        # Основные случаи
        assert _transliterate_cyrillic("Москва") == "Moskva"
        assert _transliterate_cyrillic("Санкт-Петербург") == "Sankt-Peterburg"
        assert _transliterate_cyrillic("Новосибирск") == "Novosibirsk"
        assert _transliterate_cyrillic("Екатеринбург") == "Ekaterinburg"
        assert _transliterate_cyrillic("ёжик") == "yozhik"
        assert _transliterate_cyrillic("Щука") == "Shchuka"

        # Регистр сохраняется
        assert _transliterate_cyrillic("Москва-Сити") == "Moskva-Siti"
        assert _transliterate_cyrillic("пятьдесят пять") == "pyatdesyat pyat"

        # Не-кириллические символы остаются как есть
        assert _transliterate_cyrillic("Moscow 123!") == "Moscow 123!"
        assert _transliterate_cyrillic("") == ""

        # Кэширование работает (вызов дважды)
        result1 = _transliterate_cyrillic("Москва")
        result2 = _transliterate_cyrillic("Москва")
        assert result1 == result2 == "Moskva"

    def test_transliterate_edge_cases(self):
        """Крайние случаи транслитерации."""
        # Мягкий и твёрдый знаки удаляются
        assert _transliterate_cyrillic("объект") == "obekt"
        assert _transliterate_cyrillic("подъезд") == "podezd"
        # Буква "ы"
        assert _transliterate_cyrillic("ты") == "ty"
        # Буква "э"
        assert _transliterate_cyrillic("это") == "eto"


if __name__ == "__main__":
    pytest.main([__file__])