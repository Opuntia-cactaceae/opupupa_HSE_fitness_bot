from typing import Optional


class WeatherClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_temperature(self, city: str) -> Optional[float]:
        """
        Заглушка для Weather API.
        В реальной реализации здесь будет вызов к OpenWeatherMap или аналогичному сервису.
        """
        # Имитация возврата температуры
        return 20.0  # градусов Цельсия