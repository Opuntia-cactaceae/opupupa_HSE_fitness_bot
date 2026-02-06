from typing import Optional, Tuple

from infrastructure.ai.food_client import FoodClient
from config.settings import settings


async def resolve_food_item(query: str) -> Optional[Tuple[str, float]]:
    """
    Возвращает (name, kcal_per_100g, attribution)
    или None, если kcal определить нельзя.
    """
    food_client = FoodClient(
        consumer_key=settings.FATSECRET_CONSUMER_KEY or "",
        consumer_secret=settings.FATSECRET_CONSUMER_SECRET or "",
    )

    try:
        items = await food_client.foods_search(query, max_results=1)
        print(items)
        if not items:
            return None

        food_id = items[0].food_id
        name = items[0].name

        kcal_per_100g = await food_client.get_food_kcal_per_100g(food_id)
        print(kcal_per_100g)
        if not kcal_per_100g or kcal_per_100g <= 0:
            return None
        print(name, kcal_per_100g)
        return name, kcal_per_100g

    finally:
        await food_client.close()