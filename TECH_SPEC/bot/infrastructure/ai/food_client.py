import base64, hashlib, hmac, secrets, time, urllib.parse, logging, aiohttp
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class FoodSearchItem:
    food_id: str
    name: str
    brand: Optional[str] = None

#решил использовать фетсикрет, думал изи катка, но помучался с их oauth
#видел либу на питоне но не смотрел тк думал на изичах реализую один-то метод, а потом уже было поздно
class FatSecretOAuth1:
    def __init__(self, consumer_key: str, consumer_secret: str):
        """
        Инициализирует объект OAuth 1.0 с ключом и секретом приложения.

        Входные параметры:
            consumer_key (str): OAuth consumer key приложения.
            consumer_secret (str): OAuth consumer secret приложения.

        Логика работы:
            - Нормализует входные значения (обрезает пробелы).
            - Сохраняет ключ и секрет для последующей подписи запросов.

        Возвращаемое значение:
            None.
        """
        self.consumer_key = (consumer_key or "").strip()
        self.consumer_secret = (consumer_secret or "").strip()

    @staticmethod
    def _enc(x: str) -> str:
        """
        Кодирует значение согласно правилам percent-encoding,
        применяемым в OAuth 1.0.

        Входные параметры:
            x (str): Значение для кодирования.

        Логика работы:
            - Приводит значение к строке.
            - Выполняет URL-кодирование с безопасным набором символов -._~.

        Возвращаемое значение:
            str: Закодированная строка.
        """
        return urllib.parse.quote(str(x), safe="-._~")

    def _oauth_params(self) -> Dict[str, str]:
        return {
            "oauth_consumer_key": self.consumer_key,
            "oauth_nonce": secrets.token_hex(8),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_version": "1.0",
        }

    def _normalized_params(self, params: Dict[str, str]) -> str:
        pairs = [(self._enc(k), self._enc(v)) for k, v in params.items()]
        pairs.sort(key=lambda kv: (kv[0], kv[1]))
        return "&".join(f"{k}={v}" for k, v in pairs)

    def sign_query(self, http_method: str, url: str, params: Dict[str, Any]) -> Dict[str, str]:
        """
        Подписывает параметры запроса согласно OAuth 1.0 и возвращает
        объединённый набор параметров запроса и OAuth-параметров.

        Входные параметры:
            http_method (str): HTTP-метод запроса (например, "GET").
            url (str): Базовый URL конечной точки без query string.
            params (Dict[str, Any]): Параметры запроса, которые должны быть подписаны.

        Логика работы:
            - Проверяет наличие consumer_key и consumer_secret.
            - Приводит параметры запроса к строковым значениям.
            - Генерирует OAuth-параметры (nonce, timestamp и т.д.).
            - Объединяет параметры запроса и OAuth-параметры.
            - Строит base string OAuth 1.0.
            - Вычисляет HMAC-SHA1 подпись и кодирует её в base64.
            - Возвращает параметры запроса, дополненные OAuth-параметрами и подписью.

        Возвращаемое значение:
            Dict[str, str]: Параметры запроса, содержащие исходные параметры,
            OAuth-параметры и oauth_signature. Может быть пустым словарём,
            если ключ или секрет не заданы.
        """
        if not self.consumer_key or not self.consumer_secret:
            return {}

                                         
        req_params: Dict[str, str] = {str(k): str(v) for k, v in params.items()}
        oauth = self._oauth_params()

        merged = {**req_params, **oauth}                          
        normalized = self._normalized_params(merged)

        base_string = "&".join([
            self._enc(http_method.upper()),
            self._enc(url),
            self._enc(normalized),
        ])

        signing_key = f"{self._enc(self.consumer_secret)}&"                      
        digest = hmac.new(signing_key.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha1).digest()
        sig_b64 = base64.b64encode(digest).decode("utf-8")

                                                                                     
        oauth["oauth_signature"] = sig_b64

        return {**req_params, **oauth}


class FoodClient:
    FOODS_SEARCH_URL = "https://platform.fatsecret.com/rest/foods/search/v1"
    FOOD_GET_URL = "https://platform.fatsecret.com/rest/food/v5"

    def __init__(self, consumer_key: str, consumer_secret: str):
        """
        Инициализирует клиента FatSecret и подготавливает OAuth-подпись запросов.

        Входные параметры:
            consumer_key (str): OAuth consumer key приложения.
            consumer_secret (str): OAuth consumer secret приложения.

        Логика работы:
            - Создаёт объект OAuth-подписи.
            - Инициализирует сессию HTTP-клиента в неинициализированном состоянии.

        Возвращаемое значение:
            None.
        """
        self.oauth = FatSecretOAuth1(consumer_key, consumer_secret)
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def foods_search(
        self,
        search_expression: str,
        max_results: int = 10,
        page_number: int = 0,
    ) -> List[FoodSearchItem]:
        """
        Выполняет поиск продуктов по строке запроса и возвращает список найденных позиций.

        Входные параметры:
            search_expression (str): Поисковая строка для запроса к API.
            max_results (int): Максимальное количество результатов на страницу.
            page_number (int): Номер страницы результатов.

        Логика работы:
            - Формирует параметры запроса поиска продуктов.
            - Подписывает запрос OAuth 1.0.
            - Выполняет GET-запрос к endpoint поиска продуктов.
            - Пытается распарсить JSON-ответ.
            - При ошибке парсинга или ошибке API возвращает пустой список.
            - Преобразует ответ API в список FoodSearchItem.

        Возвращаемое значение:
            List[FoodSearchItem]: Список найденных продуктов.
            Может быть пустым, если продуктов нет или произошла ошибка.
        """
        params = {
            "search_expression": search_expression,
            "max_results": str(max_results),
            "page_number": str(page_number),
            "format": "json",
        }
        signed = self.oauth.sign_query("GET", self.FOODS_SEARCH_URL, params)

        session = await self._get_session()
        async with session.get(self.FOODS_SEARCH_URL, params=signed) as resp:
            raw = await resp.text()
            print(raw)
            try:
                data = await resp.json(content_type=None)
            except Exception:
                logger.warning("FatSecret JSON parse error status=%s body=%s", resp.status, raw)
                return []

            if isinstance(data, dict) and "error" in data:
                logger.warning("FatSecret API error status=%s body=%s", resp.status, data)
                return []

            foods = data.get("foods", {}).get("food", [])
            if isinstance(foods, dict):
                foods = [foods]

            out: List[FoodSearchItem] = []
            for f in foods:
                fid = f.get("food_id")
                name = f.get("food_name")
                brand = f.get("brand_name")
                if fid and name:
                    out.append(FoodSearchItem(food_id=str(fid), name=str(name), brand=brand))
            return out

    async def get_food_kcal_per_100g(self, food_id: str) -> Optional[float]:
        """
        Получает калорийность продукта на 100 грамм по идентификатору продукта.

        Входные параметры:
            food_id (str): Идентификатор продукта во внешнем сервисе.

        Логика работы:
            - Формирует параметры запроса получения данных о продукте.
            - Подписывает запрос OAuth 1.0.
            - Выполняет GET-запрос к endpoint получения продукта.
            - Пытается распарсить JSON-ответ.
            - При ошибке парсинга или ошибке API возвращает None.
            - Извлекает данные о порции и проверяет, что единицы измерения в граммах.
            - Пересчитывает калорийность порции к значению на 100 грамм.

        Возвращаемое значение:
            Optional[float]:
                Калорийность на 100 грамм, если данные получены и корректны.
                None, если данные отсутствуют или не поддаются интерпретации.
        """
        params = {
            "food_id": food_id,
            "format": "json",
        }

        signed = self.oauth.sign_query("GET", self.FOOD_GET_URL, params)
        session = await self._get_session()

        async with session.get(self.FOOD_GET_URL, params=signed) as resp:
            raw = await resp.text()
            try:
                data = await resp.json(content_type=None)
            except Exception:
                logger.warning("FatSecret food.get parse error status=%s body=%s", resp.status, raw)
                return None

            if isinstance(data, dict) and "error" in data:
                logger.warning("FatSecret food.get error status=%s body=%s", resp.status, data)
                return None

            food = data.get("food")
            if not food:
                return None

            servings = food.get("servings", {}).get("serving")
            if not servings:
                return None

            serving = servings[0] if isinstance(servings, list) else servings

            kcal = serving.get("calories")
            amount = serving.get("metric_serving_amount")
            unit = serving.get("metric_serving_unit")

            if not kcal or not amount or unit != "g":
                return None

            try:
                return float(kcal) * (100.0 / float(amount))
            except (ValueError, ZeroDivisionError):
                return None