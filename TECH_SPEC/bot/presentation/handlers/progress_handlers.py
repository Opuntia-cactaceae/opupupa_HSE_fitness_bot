from aiogram import Router, F
from aiogram.types import CallbackQuery

from presentation.keyboards.inline import main_menu_keyboard, profile_setup_keyboard
from infrastructure.config.database import AsyncSessionFactory
from infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from application.use_cases.progress.check_progress import check_progress

router = Router()


@router.callback_query(F.data.startswith("progress_show"))
async def callback_progress_show(callback: CallbackQuery):
    """Показать прогресс по всем параметрам."""
    # Parse parent context from callback data (format: "progress_show" or "progress_show:parent")
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 else "main_menu"

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
            keyboard = main_menu_keyboard()
        elif parent_context == "profile_setup":
            keyboard = profile_setup_keyboard(parent_context="main_menu")
        else:
            keyboard = main_menu_keyboard()  # Fallback

        await callback.message.edit_text(
            message,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )