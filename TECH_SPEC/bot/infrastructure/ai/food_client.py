from typing import Optional, Tuple


class FoodClient:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    async def search_product(self, query: str) -> Optional[Tuple[str, float]]:
        """
        Заглушка для Food API (например, OpenFoodFacts).
        Возвращает (название продукта, ккал на 100г).
        """
        # Имитация поиска
        products = {
            "банан": ("Банан", 89.0),
            "яблоко": ("Яблоко", 52.0),
            "курица": ("Курица грудка", 165.0),
            "рис": ("Рис белый", 130.0),
            "хлеб": ("Хлеб пшеничный", 265.0),
        }
        query_lower = query.lower()
        for key, value in products.items():
            if key in query_lower:
                return value
        return ("Неизвестный продукт", 0.0)