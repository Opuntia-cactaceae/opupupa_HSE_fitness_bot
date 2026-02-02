from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
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

router = Router()


@router.callback_query(F.data.startswith("workout_add"))
async def callback_workout_add(callback: CallbackQuery, state: FSMContext):
    """Начало логирования тренировки."""
    # Parse parent context from callback data (format: "workout_add" or "workout_add:parent")
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 else "main_menu"

    # Store parent context in FSM state
    await state.update_data(parent_context=parent_context)
    await state.set_state(WorkoutLogStates.select_workout_type)
    await callback.message.edit_text(
        "Выберите тип тренировки:",
        reply_markup=workout_type_keyboard(parent_context=parent_context),
    )


@router.callback_query(StateFilter(WorkoutLogStates.select_workout_type), F.data.startswith("workout_"))
async def callback_workout_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа тренировки."""
    # Parse callback data (format: "workout_running" or "workout_running:parent")
    parts = callback.data.split(":")
    workout_key = parts[0]
    parent_context = parts[1] if len(parts) > 1 else "main_menu"

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

    # Сохраняем тип тренировки и родительский контекст в состоянии
    await state.update_data(workout_type=workout_type, parent_context=parent_context)

    # Переходим к вводу минут
    await state.set_state(WorkoutLogStates.enter_minutes)
    await callback.message.edit_text(
        f"Выбрана тренировка: {workout_type}\n\n"
        "Введите длительность тренировки в минутах:",
    )


@router.message(StateFilter(WorkoutLogStates.enter_minutes), F.text)
async def process_workout_minutes_input(message: Message, state: FSMContext):
    """Обработка ввода длительности тренировки."""
    # Валидация ввода
    try:
        minutes = validate_workout_minutes(message.text)
    except ValidationError as e:
        await message.answer(f"❌ {e.message}")
        return

    # Получаем сохранённый тип тренировки из состояния
    data = await state.get_data()
    workout_type = data.get("workout_type", "бег")  # значение по умолчанию
    parent_context = data.get("parent_context", "main_menu")

    async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        # Получаем пользователя для расчёта калорий
        user = await uow.users.get(message.from_user.id)
        if user is None:
            # Determine which keyboard to show based on parent context
            if parent_context == "main_menu":
                keyboard = main_menu_keyboard()
            elif parent_context == "profile_setup":
                keyboard = profile_setup_keyboard(parent_context="main_menu")
            else:
                keyboard = main_menu_keyboard()  # Fallback

            await message.answer(
                "❌ Сначала настройте профиль.",
                reply_markup=keyboard,
            )
            await state.clear()
            return

        weight_kg = user.weight_kg
        try:
            kcal_burned, water_bonus_ml = calculate_workout_calories_and_water(
                weight_kg, workout_type, minutes
            )
        except ValidationError as e:
            await message.answer(f"❌ {e.message}")
            return

        await finalize_workout_log(
            user_id=message.from_user.id,
            workout_type=workout_type,
            minutes=minutes,
            kcal_burned=kcal_burned,
            water_bonus_ml=water_bonus_ml,
            uow=uow,
        )

    # Завершаем FSM и показываем результат
    await state.clear()

    # Determine which keyboard to show based on parent context
    if parent_context == "main_menu":
        keyboard = main_menu_keyboard()
    elif parent_context == "profile_setup":
        keyboard = profile_setup_keyboard(parent_context="main_menu")
    else:
        keyboard = main_menu_keyboard()  # Fallback

    await message.answer(
        f"🏃‍♂️ Тренировка записана\n\n"
        f"Тип: {workout_type}\n"
        f"Длительность: {minutes} мин\n"
        f"Сожжено калорий: {kcal_burned:.1f}\n"
        f"Дополнительная вода: {water_bonus_ml} мл",
        reply_markup=keyboard,
    )


