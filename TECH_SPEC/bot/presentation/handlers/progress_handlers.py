from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from presentation.keyboards.inline import main_menu_keyboard, profile_setup_keyboard, weekly_stats_keyboard, progress_keyboard
from infrastructure.config.database import AsyncSessionFactory
from infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from application.use_cases.progress.check_progress import check_progress
from application.use_cases.progress.get_weekly_stats import get_weekly_stats
from presentation.services.menu_manager import replace_menu_message

router = Router()


@router.callback_query(F.data.startswith("progress_show"))
async def callback_progress_show(callback: CallbackQuery, state: FSMContext):
    """Показать прогресс по всем параметрам."""
    # Parse parent context from callback data (format: "progress_show" or "progress_show:parent")
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        progress = await check_progress(callback.from_user.id, uow)

        water_logged = progress["water_logged_ml"]
        water_goal = progress["water_goal_ml"]
        water_remaining = progress["water_remaining_ml"]
        calories_consumed = progress["calories_consumed_kcal"]
        calories_burned = progress["calories_burned_kcal"]
        calorie_balance = progress["calorie_balance_kcal"]

        water_percentage = (water_logged / water_goal * 100) if water_goal > 0 else 0
        calorie_percentage = (calories_consumed / (water_goal or 1) * 100) if water_goal > 0 else 0

        message = (
            "📊 **Ваш прогресс на сегодня:**\n\n"
            f"💧 **Вода:**\n"
            f"   Выпито: {water_logged} мл\n"
            f"   Цель: {water_goal} мл\n"
            f"   Осталось: {water_remaining} мл\n"
            f"   Прогресс: {water_percentage:.1f}%\n\n"
            f"🍎 **Калории:**\n"
            f"   Потреблено: {calories_consumed} ккал\n"
            f"   Сожжено: {calories_burned} ккал\n"
            f"   Баланс: {calorie_balance} ккал\n\n"
        )

        if calorie_balance > 0:
            message += "📈 Вы в профиците калорий."
        elif calorie_balance < 0:
            message += "📉 Вы в дефиците калорий."
        else:
            message += "⚖️ Баланс калорий нейтральный."

        # Determine which keyboard to show based on parent context
        if parent_context == "main_menu":
            keyboard = progress_keyboard(parent_context)
        elif parent_context == "profile_setup":
            keyboard = profile_setup_keyboard(parent_context="main_menu")
        else:
            keyboard = main_menu_keyboard()  # Fallback

        await replace_menu_message(
            message_or_callback=callback,
            text=message,
            keyboard=keyboard,
            state=state,
            return_menu=parent_context,
        )


@router.callback_query(F.data.startswith("progress_weekly_show"))
async def callback_progress_weekly_show(callback: CallbackQuery, state: FSMContext):
    """Показать недельную статистику."""
    from datetime import date, timedelta

    # Parse reference date from callback data (format: "progress_weekly_show:YYYY-MM-DD")
    parts = callback.data.split(":")
    if len(parts) > 1:
        try:
            reference_date = date.fromisoformat(parts[1])
        except ValueError:
            reference_date = date.today()
    else:
        reference_date = date.today()

    async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        week_start, week_end, daily_stats_list = await get_weekly_stats(
            callback.from_user.id, reference_date, uow
        )

        # Build message
        message = f"📅 **Неделя:** {week_start.strftime('%d.%m')} – {week_end.strftime('%d.%m')}\n\n"

        # Prepare dict of existing stats by date for quick lookup
        stats_by_date = {stats.date: stats for stats in daily_stats_list}

        # Iterate through each day of the week (Monday to Sunday)
        for day_offset in range(7):
            day_date = week_start + timedelta(days=day_offset)
            stats = stats_by_date.get(day_date)

            # Day header
            day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
            message += f"{day_names[day_offset]} {day_date.strftime('%d.%m')}\n"

            if stats is None:
                message += "💧 0 / 0 мл\n🔥 0 / 0 ккал (−0)\n🏃 Сожжено: 0 ккал, 0 мл\n\n"
            else:
                water_logged = stats.water_logged_ml
                water_goal = stats.water_goal_ml
                calories_consumed = stats.calories_consumed_kcal
                calorie_goal = stats.calorie_goal_kcal
                calories_burned = stats.calories_burned_kcal
                calorie_balance = stats.calorie_balance_kcal
                water_burned = 0  # TODO: calculate water burned from workouts

                message += (
                    f"💧 {water_logged} / {water_goal} мл\n"
                    f"🔥 {calories_consumed} / {calorie_goal} ккал ({calorie_balance:+})\n"
                    f"🏃 Сожжено: {calories_burned} ккал, {water_burned} мл\n\n"
                )

        keyboard = weekly_stats_keyboard(reference_date)
        await replace_menu_message(
            message_or_callback=callback,
            text=message,
            keyboard=keyboard,
            state=state,
            return_menu="main_menu",
        )