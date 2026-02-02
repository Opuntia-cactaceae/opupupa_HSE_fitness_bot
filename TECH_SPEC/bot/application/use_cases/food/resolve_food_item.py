from typing import Optional, Tuple

from infrastructure.ai.food_client import FoodClient
from config.settings import settings


async def resolve_food_item(query: str) -> Optional[Tuple[str, float, str]]:
    """Найти продукт через Food API и вернуть (название, ккал на 100г, атрибуция)."""
    food_client = FoodClient(
        consumer_key=settings.FATSECRET_CONSUMER_KEY or "",
        consumer_secret=settings.FATSECRET_CONSUMER_SECRET or "",
    )
    result = await food_client.search_product(query)
    if result is None:
        return None
    name, kcal_per_100g, attribution = result
    if kcal_per_100g <= 0:
        return None
    return name, kcal_per_100g, attribution