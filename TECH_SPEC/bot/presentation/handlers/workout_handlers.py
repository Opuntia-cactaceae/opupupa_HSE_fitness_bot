from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from presentation.fsm.states import WorkoutLogStates
from presentation.keyboards.inline import main_menu_keyboard, workout_type_keyboard, profile_setup_keyboard
from presentation.validators.workout import validate_workout_minutes
from domain.exceptions import ValidationError
from infrastructure.config.database import AsyncSessionFactory
from infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from application.use_cases.workout.set_workout_type import get_workout_met
from application.use_cases.workout.set_workout_minutes import calculate_workout_calories_and_water
from application.use_cases.workout.finalize_workout_log import finalize_workout_log
from presentation.services.menu_manager import show_menu, replace_menu_message, send_menu_new
from presentation.services.keyboard_mapper import get_keyboard_for_parent_context, get_callback_data_for_parent_context

router = Router()


@router.callback_query(F.data.startswith("workout_add"))
async def callback_workout_add(callback: CallbackQuery, state: FSMContext):
    """Начало логирования тренировки."""
    # Parse parent context from callback data (format: "workout_add" or "workout_add:parent")
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    # Store parent context in FSM state
    await state.update_data(parent_context=parent_context)
    await state.set_state(WorkoutLogStates.select_workout_type)
    await replace_menu_message(
        message_or_callback=callback,
        text="Выберите тип тренировки:",
        keyboard=workout_type_keyboard(parent_context=parent_context),
        state=state,
        return_menu=parent_context,
    )


@router.callback_query(StateFilter(WorkoutLogStates.select_workout_type), F.data.startswith("workout_"))
async def callback_workout_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа тренировки."""
    # Parse callback data (format: "workout_running" or "workout_running:parent")
    parts = callback.data.split(":")
    workout_key = parts[0]
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    type_map = {
        "workout_running": "бег",
        "workout_walking": "ходьба",
        "workout_strength": "силовая",
        "workout_swimming": "плавание",
    }
    workout_type = type_map.get(workout_key)
    if workout_type is None:
        await callback.answer("Неизвестный тип тренировки")
        return

    # Retrieve profile_setup_parent from state (if available)
    data = await state.get_data()
    profile_setup_parent = data.get("profile_setup_parent") or "main_menu"

    # Сохраняем тип тренировки и родительский контекст в состоянии
    await state.update_data(workout_type=workout_type, parent_context=parent_context, profile_setup_parent=profile_setup_parent)

    # Переходим к вводу минут
    await state.set_state(WorkoutLogStates.enter_minutes)

    # Create cancel button with appropriate callback data
    cancel_callback_data = get_callback_data_for_parent_context(parent_context, profile_setup_parent)
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data=cancel_callback_data)]
    ])

    await replace_menu_message(
        message_or_callback=callback,
        text=(
            f"Выбрана тренировка: {workout_type}\n\n"
            "Введите длительность тренировки в минутах:"
        ),
        keyboard=cancel_keyboard,
        state=state,
        return_menu=parent_context,
    )


@router.message(StateFilter(WorkoutLogStates.enter_minutes), F.text)
async def process_workout_minutes_input(message: Message, state: FSMContext):
    """Обработка ввода длительности тренировки."""
    # Валидация ввода
    try:
        minutes = validate_workout_minutes(message.text)
    except ValidationError as e:
        # Edit the existing menu message to show error
        data = await state.get_data()
        workout_type = data.get("workout_type", "бег")
        parent_context = data.get("parent_context") or "main_menu"
        profile_setup_parent = data.get("profile_setup_parent") or "main_menu"
        cancel_callback_data = get_callback_data_for_parent_context(parent_context, profile_setup_parent)
        cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Отмена", callback_data=cancel_callback_data)]
        ])
        await show_menu(
            bot=message.bot,
            chat_id=message.chat.id,
            text=f"❌ {e.message}\n\nВыбрана тренировка: {workout_type}\n\nВведите длительность тренировки в минутах:",
            keyboard=cancel_keyboard,
            state=state,
            return_menu=parent_context,
        )
        return

    # Получаем сохранённый тип тренировки из состояния
    data = await state.get_data()
    workout_type = data.get("workout_type", "бег")  # значение по умолчанию
    parent_context = data.get("parent_context") or "main_menu"
    profile_setup_parent = data.get("profile_setup_parent") or "main_menu"

    async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        # Получаем пользователя для расчёта калорий
        user = await uow.users.get(message.from_user.id)
        if user is None:
            # Determine which keyboard to show based on parent context
            keyboard = get_keyboard_for_parent_context(parent_context, profile_setup_parent)

            await show_menu(
                bot=message.bot,
                chat_id=message.chat.id,
                text="❌ Сначала настройте профиль.",
                keyboard=keyboard,
                state=state,
                return_menu=parent_context,
            )
            await state.set_state(None)
            # Remove temporary keys but keep menu_manager keys
            await state.update_data(parent_context=None, profile_setup_parent=None, workout_type=None)
            return

        weight_kg = user.weight_kg
        try:
            kcal_burned, water_bonus_ml = calculate_workout_calories_and_water(
                weight_kg, workout_type, minutes
            )
        except ValidationError as e:
            # Determine which keyboard to show based on parent context
            keyboard = get_keyboard_for_parent_context(parent_context, profile_setup_parent)
            await show_menu(
                bot=message.bot,
                chat_id=message.chat.id,
                text=f"❌ {e.message}",
                keyboard=keyboard,
                state=state,
                return_menu=parent_context,
            )
            return

        await finalize_workout_log(
            user_id=message.from_user.id,
            workout_type=workout_type,
            minutes=minutes,
            kcal_burned=kcal_burned,
            water_bonus_ml=water_bonus_ml,
            uow=uow,
        )

    # Determine which keyboard to show based on parent context
    if parent_context == "main_menu":
        keyboard = main_menu_keyboard()
    elif parent_context == "profile_setup":
        keyboard = profile_setup_keyboard(parent_context="main_menu")
    else:
        keyboard = main_menu_keyboard()  # Fallback

    await send_menu_new(
        bot=message.bot,
        chat_id=message.chat.id,
        text=(
            f"🏃‍♂️ Тренировка записана\n\n"
            f"Тип: {workout_type}\n"
            f"Длительность: {minutes} мин\n"
            f"Сожжено калорий: {kcal_burned:.1f}\n"
            f"Дополнительная вода: {water_bonus_ml} мл"
        ),
        keyboard=keyboard,
        state=state,
        return_menu=parent_context,
    )
    await state.clear()


