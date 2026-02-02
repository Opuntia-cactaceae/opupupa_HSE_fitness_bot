import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock

from domain.entities.daily_stats import DailyStats
from application.use_cases.progress.get_weekly_stats import get_weekly_stats


class TestGetWeeklyStats:
    """Тестирование get_weekly_stats use case."""

    @pytest.mark.asyncio
    async def test_get_weekly_stats_returns_correct_week_boundaries(self, mock_uow):
        """get_weekly_stats возвращает правильные границы недели."""
        user_id = 12345
        reference_date = date(2024, 2, 7)  # Wednesday
        expected_start = date(2024, 2, 5)  # Monday
        expected_end = date(2024, 2, 11)   # Sunday

        # Mock empty list (no stats)
        mock_uow.daily_stats.get_for_user_in_range.return_value = []

        week_start, week_end, stats_list = await get_weekly_stats(
            user_id, reference_date, mock_uow
        )

        assert week_start == expected_start
        assert week_end == expected_end
        assert stats_list == []
        mock_uow.daily_stats.get_for_user_in_range.assert_called_once_with(
            user_id, expected_start, expected_end
        )

    @pytest.mark.asyncio
    async def test_get_weekly_stats_handles_monday_as_reference(self, mock_uow):
        """get_weekly_stats работает, когда reference_date - понедельник."""
        user_id = 12345
        reference_date = date(2024, 2, 5)  # Monday
        expected_start = reference_date
        expected_end = date(2024, 2, 11)

        mock_uow.daily_stats.get_for_user_in_range.return_value = []

        week_start, week_end, stats_list = await get_weekly_stats(
            user_id, reference_date, mock_uow
        )

        assert week_start == expected_start
        assert week_end == expected_end

    @pytest.mark.asyncio
    async def test_get_weekly_stats_handles_sunday_as_reference(self, mock_uow):
        """get_weekly_stats работает, когда reference_date - воскресенье."""
        user_id = 12345
        reference_date = date(2024, 2, 11)  # Sunday
        expected_start = date(2024, 2, 5)
        expected_end = reference_date

        mock_uow.daily_stats.get_for_user_in_range.return_value = []

        week_start, week_end, stats_list = await get_weekly_stats(
            user_id, reference_date, mock_uow
        )

        assert week_start == expected_start
        assert week_end == expected_end

    @pytest.mark.asyncio
    async def test_get_weekly_stats_returns_stats_sorted_by_date(self, mock_uow):
        """get_weekly_stats возвращает статистику, отсортированную по дате."""
        user_id = 12345
        reference_date = date(2024, 2, 7)
        week_start = date(2024, 2, 5)
        week_end = date(2024, 2, 11)

        # Create stats for Monday and Wednesday
        stat_monday = DailyStats(
            id=1,
            user_id=user_id,
            date=week_start,
            created_at=date(2024, 2, 5),
            updated_at=date(2024, 2, 5),
            water_goal_ml=2500,
            water_logged_ml=500,
            calories_consumed_kcal=1500,
            calories_burned_kcal=300,
            calorie_goal_kcal=2000,
        )
        stat_wednesday = DailyStats(
            id=2,
            user_id=user_id,
            date=date(2024, 2, 7),
            created_at=date(2024, 2, 7),
            updated_at=date(2024, 2, 7),
            water_goal_ml=2500,
            water_logged_ml=800,
            calories_consumed_kcal=1800,
            calories_burned_kcal=400,
            calorie_goal_kcal=2000,
        )
        # Repository returns unsorted (Wednesday before Monday)
        mock_uow.daily_stats.get_for_user_in_range.return_value = [
            stat_wednesday,
            stat_monday,
        ]

        week_start_res, week_end_res, stats_list = await get_weekly_stats(
            user_id, reference_date, mock_uow
        )

        # Should be sorted by date (Monday before Wednesday)
        assert len(stats_list) == 2
        assert stats_list[0].date == stat_monday.date
        assert stats_list[1].date == stat_wednesday.date
        assert stat_monday in stats_list
        assert stat_wednesday in stats_list

    @pytest.mark.asyncio
    async def test_get_weekly_stats_clamps_future_weeks(self, mock_uow):
        """get_weekly_stats ограничивает будущие недели сегодняшним днём."""
        user_id = 12345
        today = date.today()
        # Reference date far in future
        reference_date = today + timedelta(days=30)
        # Week start should be Monday of that future week, but end clamped to today
        week_start = reference_date - timedelta(days=reference_date.weekday())
        # Since week_start > today, we expect empty list
        # According to implementation, if week_start > today, returns empty list
        # Let's test that behavior
        mock_uow.daily_stats.get_for_user_in_range.return_value = []

        week_start_res, week_end_res, stats_list = await get_weekly_stats(
            user_id, reference_date, mock_uow
        )

        # week_start_res should be Monday of that future week
        assert week_start_res == week_start
        # week_end_res should be Sunday of that week (still future)
        assert week_end_res == week_start_res + timedelta(days=6)
        # stats_list empty
        assert stats_list == []
        # Repository should not be called because week_start > today
        mock_uow.daily_stats.get_for_user_in_range.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_weekly_stats_clamps_partial_future_week(self, mock_uow):
        """get_weekly_stats ограничивает неделю, частично находящуюся в будущем."""
        user_id = 12345
        today = date.today()
        # Choose reference date such that week_start <= today < week_end
        # Let's pick a date where week_end is tomorrow (future)
        # Ensure today is not Sunday (weekday < 6)
        if today.weekday() == 6:  # Sunday, adjust
            today = today - timedelta(days=1)
        # Set reference_date to today (so week_start is Monday of this week)
        reference_date = today
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        # week_end is future (since today < Sunday)
        # Implementation should clamp week_end to today
        expected_end = today

        mock_uow.daily_stats.get_for_user_in_range.return_value = []

        week_start_res, week_end_res, stats_list = await get_weekly_stats(
            user_id, reference_date, mock_uow
        )

        assert week_start_res == week_start
        assert week_end_res == expected_end
        # Repository called with clamped range
        mock_uow.daily_stats.get_for_user_in_range.assert_called_once_with(
            user_id, week_start, expected_end
        )

    @pytest.mark.asyncio
    async def test_get_weekly_stats_handles_empty_stats_for_week(self, mock_uow):
        """get_weekly_stats возвращает пустой список, если статистики нет."""
        user_id = 12345
        reference_date = date(2024, 2, 7)

        mock_uow.daily_stats.get_for_user_in_range.return_value = []

        week_start, week_end, stats_list = await get_weekly_stats(
            user_id, reference_date, mock_uow
        )

        assert stats_list == []

    @pytest.mark.asyncio
    async def test_get_weekly_stats_passes_correct_user_id(self, mock_uow):
        """get_weekly_stats передаёт правильный user_id в репозиторий."""
        user_id = 99999
        reference_date = date(2024, 2, 7)
        week_start = date(2024, 2, 5)
        week_end = date(2024, 2, 11)

        mock_uow.daily_stats.get_for_user_in_range.return_value = []

        await get_weekly_stats(user_id, reference_date, mock_uow)

        mock_uow.daily_stats.get_for_user_in_range.assert_called_once_with(
            user_id, week_start, week_end
        )