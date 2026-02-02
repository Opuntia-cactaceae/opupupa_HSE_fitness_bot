import asyncio
import base64
import hashlib
import hmac
import logging
import secrets
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

logger = logging.getLogger(__name__)

# Attribution constant
FATSECRET_ATTRIBUTION = "Powered by FatSecret"


@dataclass
class FoodSearchItem:
    food_id: str
    name: str
    brand: Optional[str] = None


@dataclass
class FoodNutrition:
    kcal_per_100g: float
    protein_g: Optional[float] = None
    fat_g: Optional[float] = None
    carbs_g: Optional[float] = None


class FoodClient:
    """Client for FatSecret REST API using OAuth 1.0 authentication."""

    BASE_URL = "https://platform.fatsecret.com/rest/server.api"

    def __init__(self, consumer_key: str, consumer_secret: str):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self._session: Optional[aiohttp.ClientSession] = None

    @staticmethod
    def _percent_encode(s: str) -> str:
        """
        Percent-encode a string according to RFC 3986 (OAuth 1.0 requirement).

        Encodes everything except unreserved characters:
        A-Z a-z 0-9 hyphen (-), period (.), underscore (_), tilde (~).
        """
        # urllib.parse.quote encodes all characters except alphanumerics and _ . -
        # We need to also keep tilde (~) unencoded, so add it to safe characters.
        # Decode any existing percent-encoding to ensure idempotency.
        return urllib.parse.quote(urllib.parse.unquote(s), safe="-._~")

    def _build_encoded_query(self, params: Dict[str, str]) -> str:
        """
        Build percent-encoded query string from parameters according to RFC 3986.

        Returns string in format "key1=value1&key2=value2" with keys and values
        percent-encoded and sorted lexicographically.
        """
        encoded = {}
        for k, v in params.items():
            encoded[self._percent_encode(k)] = self._percent_encode(v)
        # Sort by encoded key, then value
        sorted_items = sorted(encoded.items(), key=lambda x: (x[0], x[1]))
        return "&".join(f"{k}={v}" for k, v in sorted_items)

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

    def _generate_nonce(self) -> str:
        """Generate a random string for OAuth nonce."""
        return secrets.token_hex(8)

    def _generate_timestamp(self) -> str:
        """Generate current Unix timestamp for OAuth."""
        return str(int(time.time()))

    def _sign_request(
        self, method: str, url: str, params: Dict[str, str]
    ) -> str:
        """
        Generate OAuth 1.0 HMAC-SHA1 signature.

        Returns the value for the Authorization header.
        """

        # OAuth parameters
        oauth_params = {
            "oauth_consumer_key": self.consumer_key,
            "oauth_nonce": self._generate_nonce(),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": self._generate_timestamp(),
            "oauth_version": "1.0",
        }

        # Merge all parameters (excluding oauth_signature)
        all_params = {**oauth_params, **params}
        # Percent-encode keys and values according to RFC 3986
        encoded_params = {}
        for k, v in all_params.items():
            encoded_params[
                self._percent_encode(k)
            ] = self._percent_encode(v)

        # Sort by encoded key, then by value
        sorted_items = sorted(
            encoded_params.items(), key=lambda x: (x[0], x[1])
        )
        # Create parameter string
        param_string = "&".join(f"{k}={v}" for k, v in sorted_items)

        # Create signature base string
        encoded_url = self._percent_encode(url)
        encoded_method = self._percent_encode(method.upper())
        encoded_param_string = urllib.parse.quote(param_string, safe='%')
        base_string = f"{encoded_method}&{encoded_url}&{encoded_param_string}"

        # Create signing key (consumer_secret & token_secret, token_secret is empty)
        signing_key = f"{self._percent_encode(self.consumer_secret)}&"

        # Generate HMAC-SHA1 signature
        signature = hmac.new(
            signing_key.encode("utf-8"),
            base_string.encode("utf-8"),
            hashlib.sha1,
        ).digest()
        signature_b64 = base64.b64encode(signature).decode("utf-8")
        # Build Authorization header
        oauth_params["oauth_signature"] = signature_b64
        auth_header = "OAuth " + ", ".join(
            f'{self._percent_encode(k)}="{self._percent_encode(v)}"'
            for k, v in oauth_params.items()
        )
        return auth_header

    async def _make_request(
        self, method: str, params: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """
        Make authenticated request to FatSecret API.

        Returns parsed JSON response or None on error.
        """
        if not self.consumer_key or not self.consumer_secret:
            logger.debug("FatSecret credentials not configured")
            return None

        # Ensure format=json for JSON responses
        params = {**params, "format": "json"}

        try:
            session = await self._get_session()
            headers = {
                "Authorization": self._sign_request(
                    method, self.BASE_URL, params
                )
            }
            encoded_query = self._build_encoded_query(params)
            async with session.request(
                method, self.BASE_URL, params=encoded_query, headers=headers
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        f"FatSecret API request failed with status {resp.status}"
                    )
                    return None
                data = await resp.json()
                # FatSecret wraps response in a top-level key
                # e.g., {"foods": {"food": [...]}} or {"food": {...}}
                return data
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.debug(f"FatSecret API network error: {e}")
            return None
        except (ValueError, TypeError, KeyError) as e:
            logger.debug(f"FatSecret API parsing error: {e}")
            return None

    async def search_products(self, query: str) -> List[FoodSearchItem]:
        """
        Search for food products by query.

        Returns a list of FoodSearchItem objects, or empty list on error/no results.
        """
        params = {
            "method": "foods.search",
            "search_expression": query,
            "max_results": "10",
        }
        data = await self._make_request("GET", params)
        if not data:
            return []

        try:
            # Response structure: {"foods": {"food": [{...}, ...]}}
            foods = data.get("foods", {}).get("food", [])
            # If only one result, API returns a dict, not list
            if isinstance(foods, dict):
                foods = [foods]

            results = []
            for food in foods:
                food_id = food.get("food_id")
                name = food.get("food_name")
                brand = food.get("brand_name")
                if food_id and name:
                    results.append(
                        FoodSearchItem(
                            food_id=str(food_id),
                            name=name,
                            brand=brand,
                        )
                    )
            return results
        except (AttributeError, KeyError, TypeError) as e:
            logger.debug(f"Error parsing search results: {e}")
            return []

    async def get_food(self, food_id: str) -> Optional[FoodNutrition]:
        """
        Get detailed nutrition information for a specific food.

        Returns FoodNutrition object normalized to per 100g, or None on error.
        """
        params = {
            "method": "food.get",
            "food_id": food_id,
        }
        data = await self._make_request("GET", params)
        if not data:
            return None

        try:
            # Response structure: {"food": {...}}
            food = data.get("food", {})
            # Nutrition information is in "servings" -> "serving"
            servings = food.get("servings", {}).get("serving")
            if not servings:
                return None

            # If multiple serving sizes, use the first one
            if isinstance(servings, list):
                serving = servings[0]
            else:
                serving = servings

            # Extract values
            kcal = serving.get("calories")
            protein = serving.get("protein")
            fat = serving.get("fat")
            carbs = serving.get("carbohydrate")
            serving_size = serving.get("metric_serving_amount")
            serving_unit = serving.get("metric_serving_unit")

            # Normalize to per 100g
            kcal_per_100g = 0.0
            protein_per_100g = None
            fat_per_100g = None
            carbs_per_100g = None

            if kcal and serving_size and serving_unit == "g":
                try:
                    factor = 100.0 / float(serving_size)
                    kcal_per_100g = float(kcal) * factor
                    if protein:
                        protein_per_100g = float(protein) * factor
                    if fat:
                        fat_per_100g = float(fat) * factor
                    if carbs:
                        carbs_per_100g = float(carbs) * factor
                except (ValueError, ZeroDivisionError):
                    pass

            return FoodNutrition(
                kcal_per_100g=kcal_per_100g,
                protein_g=protein_per_100g,
                fat_g=fat_per_100g,
                carbs_g=carbs_per_100g,
            )
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            logger.debug(f"Error parsing food nutrition: {e}")
            return None

    async def search_product(self, query: str) -> Optional[Tuple[str, float, str]]:
        """
        Legacy method for backward compatibility.

        Returns (product_name, kcal_per_100g, attribution) tuple or None.
        Uses the first search result from FatSecret.
        If no search results, returns (query, 0.0, "").
        """
        products = await self.search_products(query)
        if not products:
            return (query, 0.0, "")

        # Get nutrition for the first product
        nutrition = await self.get_food(products[0].food_id)
        if not nutrition or nutrition.kcal_per_100g <= 0:
            return None

        return (products[0].name, nutrition.kcal_per_100g, FATSECRET_ATTRIBUTION)