from aiogram import Router, F
from aiogram.types import CallbackQuery

from presentation.keyboards.inline import main_menu_keyboard, water_volume_keyboard, profile_setup_keyboard
from infrastructure.config.database import AsyncSessionFactory
from infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from application.use_cases.water.log_water import log_water
from application.use_cases.water.get_water_progress import get_water_progress

router = Router()


@router.callback_query(F.data.startswith("water_add"))
async def callback_water_add(callback: CallbackQuery):
    """Добавление воды."""
    # Parse parent context from callback data (format: "water_add" or "water_add:parent")
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 else "main_menu"

    await callback.message.edit_text(
        "Выберите объём воды:",
        reply_markup=water_volume_keyboard(parent_context=parent_context),
    )


@router.callback_query(F.data.startswith("water_"))
async def callback_water_volume(callback: CallbackQuery):
    """Обработка выбора объёма воды."""
    # Parse callback data (format: "water_250" or "water_250:parent")
    parts = callback.data.split(":")
    volume_key = parts[0]
    parent_context = parts[1] if len(parts) > 1 else "main_menu"

    volume_map = {
        "water_250": 250,
        "water_500": 500,
        "water_750": 750,
        "water_1000": 1000,
    }
    volume = volume_map.get(volume_key)
    if volume is None:
        await callback.answer("Неизвестный объём")
        return

    async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        await log_water(callback.from_user.id, volume, uow)

        # Показать обновлённый прогресс
        progress = await get_water_progress(callback.from_user.id, uow)
        logged, goal, remaining = progress

        # Determine which keyboard to show based on parent context
        if parent_context == "main_menu":
            keyboard = main_menu_keyboard()
        elif parent_context == "profile_setup":
            keyboard = profile_setup_keyboard(parent_context="main_menu")
        else:
            # Fallback to main menu for unknown parent context
            keyboard = main_menu_keyboard()

        await callback.message.edit_text(
            f"💧 Вода добавлена: {volume} мл\n\n"
            f"📊 Прогресс:\n"
            f"Выпито: {logged} мл\n"
            f"Цель: {goal} мл\n"
            f"Осталось: {remaining} мл",
            reply_markup=keyboard,
        )


@router.callback_query(F.data.startswith("water_progress"))
async def callback_water_progress(callback: CallbackQuery):
    """Показать прогресс по воде."""
    # Parse parent context from callback data (format: "water_progress" or "water_progress:parent")
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 else "main_menu"

    async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        logged, goal, remaining = await get_water_progress(callback.from_user.id, uow)

        # Determine which keyboard to show based on parent context
        if parent_context == "main_menu":
            keyboard = main_menu_keyboard()
        elif parent_context == "profile_setup":
            keyboard = profile_setup_keyboard(parent_context="main_menu")
        else:
            # Fallback to main menu for unknown parent context
            keyboard = main_menu_keyboard()

        await callback.message.edit_text(
            f"📊 Прогресс по воде:\n"
            f"Выпито: {logged} мл\n"
            f"Цель: {goal} мл\n"
            f"Осталось: {remaining} мл",
            reply_markup=keyboard,
        )