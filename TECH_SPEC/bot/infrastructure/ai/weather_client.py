from typing import Optional, NamedTuple
import aiohttp
import asyncio
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class WeatherInfo(NamedTuple):
    temperature_c: float
    description: Optional[str] = None
    main: Optional[str] = None
    condition_id: Optional[int] = None


class WeatherClient:
    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None
        # Simple in-memory cache for city -> (lat, lon)
        self._geocache: dict[str, tuple[float, float]] = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def get_weather(self, city: str) -> Optional[WeatherInfo]:
        """
        Получить информацию о погоде для города.
        Возвращает WeatherInfo или None в случае ошибки.
        """
        if not self.api_key:
            logger.debug("No API key provided")
            return None

        city = city.strip()
        if not city:
            return None

        # Try geocoding (with Cyrillic fallback if needed)
        coords = await self._geocode_city(city)
        if coords is None:
            return None

        lat, lon = coords
        weather_data = await self._fetch_weather(lat, lon)
        if weather_data is None:
            return None

        # Extract relevant fields
        temp = weather_data.get("main", {}).get("temp")
        if temp is None:
            return None

        weather = weather_data.get("weather", [{}])[0]
        description = weather.get("description")
        main = weather.get("main")
        condition_id = weather.get("id")

        return WeatherInfo(
            temperature_c=float(temp),
            description=description,
            main=main,
            condition_id=condition_id
        )

    async def get_temperature(self, city: str) -> Optional[float]:
        """
        Получить температуру в градусах Цельсия для города.
        Для обратной совместимости.
        """
        weather = await self.get_weather(city)
        if weather is None:
            return None
        return weather.temperature_c

    async def _geocode_city(self, city: str) -> Optional[tuple[float, float]]:
        """Получить координаты города через OpenWeather Geocoding API."""
        # Check cache first
        if city in self._geocache:
            return self._geocache[city]

        # Try geocoding with original city name
        coords = await self._geocode(city)
        transliterated = None
        if coords is None and _contains_cyrillic(city):
            # Transliterate and retry
            transliterated = _transliterate_cyrillic(city)
            if transliterated != city:
                logger.debug(f"Retrying geocoding with transliterated name: {transliterated}")
                coords = await self._geocode(transliterated)

        if coords is not None:
            self._geocache[city] = coords
            # Also cache transliterated name if different
            if transliterated is not None and transliterated != city:
                self._geocache[transliterated] = coords
        return coords

    async def _geocode(self, city: str) -> Optional[tuple[float, float]]:
        """Вызов API геокодирования."""
        url = "https://api.openweathermap.org/geo/1.0/direct"
        params = {
            "q": city,
            "limit": 1,
            "appid": self.api_key
        }

        try:
            session = await self._get_session()
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"Geocoding failed with status {resp.status}")
                    return None
                data = await resp.json()
                if not data or not isinstance(data, list):
                    return None
                item = data[0]
                lat = item.get("lat")
                lon = item.get("lon")
                if lat is None or lon is None:
                    return None
                return (float(lat), float(lon))
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.debug(f"Geocoding error: {e}")
            return None
        except (KeyError, IndexError, ValueError, TypeError) as e:
            logger.debug(f"Geocoding parsing error: {e}")
            return None

    async def _fetch_weather(self, lat: float, lon: float) -> Optional[dict]:
        """Получить текущую погоду по координатам."""
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric",
            "lang": "ru"
        }

        try:
            session = await self._get_session()
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"Weather API failed with status {resp.status}")
                    return None
                return await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.debug(f"Weather API error: {e}")
            return None
        except (ValueError, TypeError) as e:
            logger.debug(f"Weather API parsing error: {e}")
            return None


def _contains_cyrillic(text: str) -> bool:
    """Проверить, содержит ли текст кириллические символы."""
    return any('\u0400' <= char <= '\u04FF' for char in text)


@lru_cache(maxsize=128)
def _transliterate_cyrillic(text: str) -> str:
    """
    Простая транслитерация кириллицы в латиницу.
    Обрабатывает основные русские буквы, пробелы и дефисы.
    """
    mapping = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e',
        'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k',
        'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
        'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
        'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '',
        'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E',
        'Ё': 'Yo', 'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K',
        'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R',
        'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts',
        'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch', 'Ъ': '', 'Ы': 'Y', 'Ь': '',
        'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
        ' ': ' ', '-': '-'
    }

    result = []
    for char in text:
        if char in mapping:
            result.append(mapping[char])
        else:
            # Keep non-Cyrillic characters as is (Latin letters, digits, punctuation)
            result.append(char)
    return ''.join(result)