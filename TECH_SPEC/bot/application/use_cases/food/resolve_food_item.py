from typing import Optional, Tuple

from infrastructure.ai.food_client import FoodClient
from config.settings import settings


async def resolve_food_item(query: str) -> Optional[Tuple[str, float]]:
    """Найти продукт через Food API и вернуть (название, ккал на 100г)."""
    food_client = FoodClient()  # Заглушка, не требует API ключа
    result = await food_client.search_product(query)
    if result is None:
        return None
    name, kcal_per_100g = result
    if kcal_per_100g <= 0:
        return None
    return name, kcal_per_100g