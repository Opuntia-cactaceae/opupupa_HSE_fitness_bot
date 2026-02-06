from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from presentation.fsm.states import WaterLogStates
from presentation.validators.water import validate_water_ml
from domain.exceptions import ValidationError
from presentation.keyboards.inline import main_menu_keyboard, water_volume_keyboard, profile_setup_keyboard
from infrastructure.config.database import AsyncSessionFactory
from infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from application.use_cases.water.log_water import log_water
from application.use_cases.water.get_water_progress import get_water_progress
from presentation.services.menu_manager import show_menu, replace_menu_message, send_menu_new
from presentation.services.keyboard_mapper import get_keyboard_for_parent_context, get_callback_data_for_parent_context

router = Router()


@router.callback_query(F.data.startswith("water_add"))
async def callback_water_add(callback: CallbackQuery, state: FSMContext):
    """Добавление воды."""
    # Parse parent context from callback data (format: "water_add" or "water_add:parent")
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    await replace_menu_message(
        message_or_callback=callback,
        text="Выберите объём воды:",
        keyboard=water_volume_keyboard(parent_context=parent_context),
        state=state,
        return_menu=parent_context,
    )


@router.callback_query(F.data.startswith("water_custom"))
async def callback_water_custom(callback: CallbackQuery, state: FSMContext):
    """Запрос ввода произвольного объёма воды."""
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    # Retrieve profile_setup_parent from state (if available)
    data = await state.get_data()
    profile_setup_parent = data.get("profile_setup_parent") or "main_menu"

    # Store parent context and profile_setup_parent in FSM state
    await state.update_data(parent_context=parent_context, profile_setup_parent=profile_setup_parent)
    await state.set_state(WaterLogStates.enter_ml)

    # Create cancel button with appropriate callback data
    cancel_callback_data = get_callback_data_for_parent_context(parent_context, profile_setup_parent)
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data=cancel_callback_data)]
    ])

    await replace_menu_message(
        message_or_callback=callback,
        text="Введите объём воды в мл (от 50 до 3000):",
        keyboard=cancel_keyboard,
        state=state,
        return_menu=parent_context,
    )


@router.callback_query(F.data.startswith("water_"))
async def callback_water_volume(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора объёма воды."""
    # Parse callback data (format: "water_250" or "water_250:parent")
    parts = callback.data.split(":")
    volume_key = parts[0]
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

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

        # Retrieve profile_setup_parent from state (if available)
        data = await state.get_data()
        profile_setup_parent = data.get("profile_setup_parent") or "main_menu"

        # Determine which keyboard to show based on parent context
        keyboard = get_keyboard_for_parent_context(parent_context, profile_setup_parent)

        await replace_menu_message(
            message_or_callback=callback,
            text=(
                f"💧 Вода добавлена: {volume} мл\n\n"
                f"📊 Прогресс:\n"
                f"Выпито: {logged} мл\n"
                f"Цель: {goal} мл\n"
                f"Осталось: {remaining} мл"
            ),
            keyboard=keyboard,
            state=state,
            return_menu=parent_context,
        )


@router.callback_query(F.data.startswith("water_progress"))
async def callback_water_progress(callback: CallbackQuery, state: FSMContext):
    """Показать прогресс по воде."""
    # Parse parent context from callback data (format: "water_progress" or "water_progress:parent")
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        logged, goal, remaining = await get_water_progress(callback.from_user.id, uow)

        # Retrieve profile_setup_parent from state (if available)
        data = await state.get_data()
        profile_setup_parent = data.get("profile_setup_parent") or "main_menu"

        # Determine which keyboard to show based on parent context
        keyboard = get_keyboard_for_parent_context(parent_context, profile_setup_parent)

        await replace_menu_message(
            message_or_callback=callback,
            text=(
                f"📊 Прогресс по воде:\n"
                f"Выпито: {logged} мл\n"
                f"Цель: {goal} мл\n"
                f"Осталось: {remaining} мл"
            ),
            keyboard=keyboard,
            state=state,
            return_menu=parent_context,
        )


@router.message(StateFilter(WaterLogStates.enter_ml), F.text)
async def process_water_ml_input(message: Message, state: FSMContext):
    """Обработка ввода произвольного объёма воды."""
    # Валидация ввода
    try:
        volume = validate_water_ml(message.text)
    except ValidationError as e:
        # Edit the existing menu message to show error
        data = await state.get_data()
        parent_context = data.get("parent_context") or "main_menu"
        profile_setup_parent = data.get("profile_setup_parent") or "main_menu"
        cancel_callback_data = get_callback_data_for_parent_context(parent_context, profile_setup_parent)
        cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Отмена", callback_data=cancel_callback_data)]
        ])
        await show_menu(
            bot=message.bot,
            chat_id=message.chat.id,
            text=f"❌ {e.message}\n\nВведите объём воды в мл (от 50 до 3000):",
            keyboard=cancel_keyboard,
            state=state,
            return_menu=parent_context,
        )
        return

    async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        await log_water(message.from_user.id, volume, uow)

        # Получить обновлённый прогресс
        logged, goal, remaining = await get_water_progress(message.from_user.id, uow)

        # Получить parent_context и profile_setup_parent из состояния
        data = await state.get_data()
        parent_context = data.get("parent_context") or "main_menu"
        profile_setup_parent = data.get("profile_setup_parent") or "main_menu"

        # Определить клавиатуру в зависимости от контекста
        keyboard = get_keyboard_for_parent_context(parent_context, profile_setup_parent)

        await send_menu_new(
            bot=message.bot,
            chat_id=message.chat.id,
            text=(
                f"💧 Вода добавлена: {volume} мл\n\n"
                f"📊 Прогресс:\n"
                f"Выпито: {logged} мл\n"
                f"Цель: {goal} мл\n"
                f"Осталось: {remaining} мл"
            ),
            keyboard=keyboard,
            state=state,
            return_menu=parent_context,
        )
        await state.set_state(None)
        # Remove temporary keys but keep menu_manager keys
        await state.update_data(parent_context=None, profile_setup_parent=None)