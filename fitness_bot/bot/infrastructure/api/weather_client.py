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
        """
        Инициализирует клиент погоды.

        Входные параметры:
            api_key (Optional[str]): API-ключ внешнего погодного сервиса.

        Логика работы:
            - Сохраняет API-ключ.
            - Инициализирует HTTP-сессию в неинициализированном состоянии.
            - Инициализирует кэш результатов геокодирования города.

        Возвращаемое значение:
            None.
        """
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None
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
        Получает погодные данные для указанного города.

        Входные параметры:
            city (str): Название города.

        Логика работы:
            - Проверяет наличие API-ключа.
            - Нормализует входное название города.
            - Получает координаты города через геокодирование.
            - Запрашивает погодные данные по координатам.
            - Извлекает температуру и описание погоды из ответа.
            - Формирует объект WeatherInfo.

        Возвращаемое значение:
            Optional[WeatherInfo]:
                Данные о погоде, если они успешно получены и корректны.
                None, если данные недоступны или входные параметры некорректны.
        """
        if not self.api_key:
            logger.debug("No API key provided")
            return None

        city = city.strip()
        if not city:
            return None

        coords = await self._geocode_city(city)
        if coords is None:
            return None

        lat, lon = coords
        weather_data = await self._fetch_weather(lat, lon)
        if weather_data is None:
            return None

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
        Получает температуру воздуха для указанного города.

        Входные параметры:
            city (str): Название города.

        Логика работы:
            - Запрашивает погодные данные методом get_weather.
            - Возвращает температуру из результата при наличии данных.

        Возвращаемое значение:
            Optional[float]:
                Температура в градусах Цельсия, если данные доступны.
                None, если данные недоступны.
        """
        weather = await self.get_weather(city)
        if weather is None:
            return None
        return weather.temperature_c

    async def _geocode_city(self, city: str) -> Optional[tuple[float, float]]:
        """
        Возвращает координаты города, используя кэш и при необходимости геокодирование.

        Входные параметры:
            city (str): Название города.

        Логика работы:
            - Проверяет наличие координат в локальном кэше.
            - Выполняет запрос геокодирования по исходному названию.
            - При неудаче и наличии кириллицы выполняет повторную попытку
              с транслитерированным названием.
            - Сохраняет успешный результат в кэш для исходного и транслитерированного названия.

        Возвращаемое значение:
            Optional[tuple[float, float]]:
                Координаты (lat, lon), если город успешно геокодирован.
                None, если координаты получить не удалось.
        """
        if city in self._geocache:
            return self._geocache[city]

        coords = await self._geocode(city)
        transliterated = None
        if coords is None and _contains_cyrillic(city):
            transliterated = _transliterate_cyrillic(city)
            if transliterated != city:
                logger.debug(f"Retrying geocoding with transliterated name: {transliterated}")
                coords = await self._geocode(transliterated)

        if coords is not None:
            self._geocache[city] = coords
            if transliterated is not None and transliterated != city:
                self._geocache[transliterated] = coords
        return coords

    async def _geocode(self, city: str) -> Optional[tuple[float, float]]:
        """
       Выполняет геокодирование города через OpenWeatherMap Geocoding API.

       Входные параметры:
           city (str): Название города.

       Логика работы:
           - Отправляет запрос к endpoint геокодирования с ограничением на один результат.
           - Проверяет статус ответа.
           - Извлекает широту и долготу из первого результата.
           - Обрабатывает сетевые ошибки, таймауты и ошибки парсинга.

       Возвращаемое значение:
           Optional[tuple[float, float]]:
               Координаты (lat, lon) при успешном получении данных.
               None при ошибке запроса или отсутствии данных.
       """
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
        """
        Запрашивает погодные данные по координатам через OpenWeatherMap Weather API.

        Входные параметры:
            lat (float): Широта точки запроса.
            lon (float): Долгота точки запроса.

        Логика работы:
            - Отправляет запрос к endpoint текущей погоды с метрическими единицами
              и русским языком описаний.
            - Проверяет статус ответа.
            - Возвращает JSON-ответ.
            - Обрабатывает сетевые ошибки, таймауты и ошибки парсинга.

        Возвращаемое значение:
            Optional[dict]:
                Сырой JSON-ответ погодного сервиса при успешном запросе.
                None при ошибке запроса или некорректном ответе.
        """
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
    return any('\u0400' <= char <= '\u04FF' for char in text)


@lru_cache(maxsize=128)
def _transliterate_cyrillic(text: str) -> str:
    """
    Выполняет транслитерацию кириллического текста в латиницу по заданной таблице.

    Входные параметры:
        text (str): Исходная строка, возможно содержащая кириллицу.

    Логика работы:
        - Преобразует каждый символ по таблице соответствий.
        - Неизвестные символы оставляет без изменений.
        - Кэширует результат для повторных вызовов.

    Возвращаемое значение:
        str: Транслитерированная строка.
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
            result.append(char)
    return ''.join(result)