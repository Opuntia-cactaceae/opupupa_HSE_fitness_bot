import pytest
from datetime import date
from unittest.mock import AsyncMock, patch

from application.use_cases.set_profile.finalize_profile import finalize_profile


class TestFinalizeProfile:
    """Тестирование finalize_profile use case."""

    @pytest.mark.asyncio
    async def test_finalize_profile_auto_mode_calculates_goals(self, mock_uow, sample_user, sample_daily_stats):
        """Завершение профиля в auto режиме рассчитывает цели."""
        # Arrange
        user_id = 12345
        sample_user.calorie_goal_mode = "auto"
        sample_user.calorie_goal_kcal_manual = None
        sample_user.activity_minutes_per_day = 60  # 2 intervals of 30 minutes

        mock_uow.users.get.return_value = sample_user
        mock_uow.daily_stats.get_or_create.return_value = sample_daily_stats

        # Mock WeatherClient and settings
        with patch('application.use_cases.set_profile.finalize_profile.WeatherClient') as MockWeatherClient, \
             patch('application.use_cases.set_profile.finalize_profile.settings') as mock_settings:

            mock_weather = AsyncMock()
            mock_weather.get_temperature.return_value = 15.0  # below 25°C
            MockWeatherClient.return_value = mock_weather

            mock_settings.WEATHER_API_KEY = "test-api-key"

            # Act
            await finalize_profile(user_id, mock_uow)

        # Assert
        mock_uow.users.get.assert_called_once_with(user_id)
        mock_uow.daily_stats.get_or_create.assert_called_once_with(user_id, date.today())

        # Check calculations
        # Base water: 70kg * 30ml = 2100ml
        # Activity bonus: 60min // 30 * 500ml = 1000ml
        # Temperature bonus: 0ml (temp <= 25)
        # Total water goal: 3100ml
        assert sample_daily_stats.water_goal_ml == 3100

        # Base calories: 10*70 + 6.25*175 - 5*30 = 700 + 1093.75 - 150 = 1643.75 ≈ 1643
        # Activity bonus: 60min // 30 * 300kcal = 600kcal
        # Total calorie goal: ~2243kcal
        assert sample_daily_stats.calorie_goal_kcal == 2243

    @pytest.mark.asyncio
    async def test_finalize_profile_manual_mode_uses_manual_goal(self, mock_uow, sample_user, sample_daily_stats):
        """Завершение профиля в manual режиме использует ручную цель."""
        # Arrange
        user_id = 12345
        sample_user.calorie_goal_mode = "manual"
        sample_user.calorie_goal_kcal_manual = 2500
        sample_user.activity_minutes_per_day = 60

        mock_uow.users.get.return_value = sample_user
        mock_uow.daily_stats.get_or_create.return_value = sample_daily_stats

        with patch('application.use_cases.set_profile.finalize_profile.WeatherClient') as MockWeatherClient, \
             patch('application.use_cases.set_profile.finalize_profile.settings') as mock_settings:

            mock_weather = AsyncMock()
            mock_weather.get_temperature.return_value = 15.0
            MockWeatherClient.return_value = mock_weather

            mock_settings.WEATHER_API_KEY = "test-api-key"

            # Act
            await finalize_profile(user_id, mock_uow)

        # Assert
        mock_uow.users.get.assert_called_once_with(user_id)
        mock_uow.daily_stats.get_or_create.assert_called_once_with(user_id, date.today())

        # Water goal should still be calculated
        # Base water: 2100ml + activity 1000ml = 3100ml
        assert sample_daily_stats.water_goal_ml == 3100

        # Calorie goal should be manual value
        assert sample_daily_stats.calorie_goal_kcal == 2500

    @pytest.mark.asyncio
    async def test_finalize_profile_with_temperature_bonus(self, mock_uow, sample_user, sample_daily_stats):
        """Завершение профиля добавляет бонус воды при температуре выше 25°C."""
        # Arrange
        user_id = 12345
        sample_user.calorie_goal_mode = "auto"
        sample_user.activity_minutes_per_day = 60

        mock_uow.users.get.return_value = sample_user
        mock_uow.daily_stats.get_or_create.return_value = sample_daily_stats

        with patch('application.use_cases.set_profile.finalize_profile.WeatherClient') as MockWeatherClient, \
             patch('application.use_cases.set_profile.finalize_profile.settings') as mock_settings:

            mock_weather = AsyncMock()
            mock_weather.get_temperature.return_value = 30.0  # above 25°C
            MockWeatherClient.return_value = mock_weather

            mock_settings.WEATHER_API_KEY = "test-api-key"

            # Act
            await finalize_profile(user_id, mock_uow)

        # Assert
        # Base water: 2100ml
        # Activity bonus: 1000ml
        # Temperature bonus: 750ml
        # Total: 3850ml
        assert sample_daily_stats.water_goal_ml == 3850

    @pytest.mark.asyncio
    async def test_finalize_profile_raises_error_when_user_not_found(self, mock_uow):
        """Выбрасывается ошибка, если пользователь не найден."""
        # Arrange
        user_id = 99999
        mock_uow.users.get.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match=f"User {user_id} not found"):
            await finalize_profile(user_id, mock_uow)