from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from presentation.fsm.states import SetProfileStates

from presentation.keyboards.inline import (
    main_menu_keyboard,
    profile_setup_keyboard,
    calorie_goal_mode_keyboard,
    water_goal_mode_keyboard,
)
from presentation.services.menu_manager import show_menu, replace_menu_message, send_menu_new
from presentation.services.keyboard_mapper import get_keyboard_for_parent_context, get_callback_data_for_parent_context
from presentation.validators.profile import (
    validate_weight,
    validate_height,
    validate_age,
    validate_activity_minutes,
    validate_city,
    validate_calorie_goal,
    validate_water_goal,
)
from domain.exceptions import ValidationError
from infrastructure.config.database import AsyncSessionFactory
from infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from application.use_cases.set_profile.start_set_profile import start_set_profile
from application.use_cases.set_profile.set_weight import set_weight
from application.use_cases.set_profile.set_height import set_height
from application.use_cases.set_profile.set_age import set_age
from application.use_cases.set_profile.set_activity_minutes import set_activity_minutes
from application.use_cases.set_profile.set_city import set_city
from application.use_cases.set_profile.set_calorie_goal_mode import set_calorie_goal_mode
from application.use_cases.set_profile.set_calorie_goal_manual import set_calorie_goal_manual
from application.use_cases.set_profile.set_water_goal_mode import set_water_goal_mode
from application.use_cases.set_profile.set_water_goal_manual import set_water_goal_manual
from application.use_cases.set_profile.finalize_profile import finalize_profile

router = Router()


async def get_formatted_profile_text(user_id: int, uow: SqlAlchemyUnitOfWork) -> str:
    """Возвращает отформатированный текст текущего профиля."""
    user = await uow.users.get(user_id)

    if user is None:
        return "📋 Профиль не настроен.\n⬇️ Выберите параметр для изменения:"

    # Форматируем значения
    weight_text = f"{user.weight_kg} кг" if user.weight_kg > 0 else "не задано"
    height_text = f"{user.height_cm} см" if user.height_cm > 0 else "не задано"
    age_text = f"{user.age_years}" if user.age_years > 0 else "не задано"
    activity_text = f"{user.activity_minutes_per_day} мин/день" if user.activity_minutes_per_day > 0 else "не задано"
    city_text = user.city if user.city else "не задано"

    if user.calorie_goal_mode == "manual" and user.calorie_goal_kcal_manual:
        calorie_goal_text = f"ручная ({user.calorie_goal_kcal_manual} ккал)"
    else:
        calorie_goal_text = f"авто ({user.calculate_base_calorie_goal_kcal()} ккал)"

    if user.water_goal_mode == "manual" and user.water_goal_ml_manual:
        water_goal_text = f"ручная ({user.water_goal_ml_manual} мл)"
    else:
        water_goal_text = f"авто ({user.calculate_base_water_goal_ml()} мл)"

    return (
        "📋 **Текущий профиль:**\n"
        f"• Вес: {weight_text}\n"
        f"• Рост: {height_text}\n"
        f"• Возраст: {age_text}\n"
        f"• Активность: {activity_text}\n"
        f"• Город: {city_text}\n"
        f"• Цель калорий: {calorie_goal_text}\n"
        f"• Цель воды: {water_goal_text}\n\n"
        "⬇️ Выберите параметр для изменения:"
    )


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start."""
    await message.answer(
        "Добро пожаловать в бот для трекинга здоровья!",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("set_profile"))
async def cmd_set_profile(message: Message):
    """Обработчик команды /set_profile (входная точка)."""
    async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        await start_set_profile(message.from_user.id, uow)
        profile_text = await get_formatted_profile_text(message.from_user.id, uow)
        await message.answer(
            profile_text,
            reply_markup=profile_setup_keyboard(parent_context="main_menu"),
            parse_mode="Markdown",
        )


@router.callback_query(F.data.startswith("profile_setup"))
async def callback_profile_setup(callback: CallbackQuery, state: FSMContext):
    """Переход к настройке профиля."""
    # Parse parent context from callback data (format: "profile_setup" or "profile_setup:parent")
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"
    # Store parent context for profile setup menu (needed for nested navigation)
    await state.update_data(profile_setup_parent=parent_context)

    async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        await start_set_profile(callback.from_user.id, uow)
        profile_text = await get_formatted_profile_text(callback.from_user.id, uow)
        await replace_menu_message(
            message_or_callback=callback,
            text=profile_text,
            keyboard=profile_setup_keyboard(parent_context=parent_context),
            state=state,
            return_menu=parent_context,
        )


@router.callback_query(F.data.startswith("profile_set_weight"))
async def callback_set_weight(callback: CallbackQuery, state: FSMContext):
    """Запрос ввода веса."""
    # Parse parent context from callback data (format: "profile_set_weight" or "profile_set_weight:parent")
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    # Retrieve profile_setup_parent from state (if available)
    data = await state.get_data()
    profile_setup_parent = data.get("profile_setup_parent") or "main_menu"

    # Store parent context and profile_setup_parent in FSM state
    await state.update_data(parent_context=parent_context, profile_setup_parent=profile_setup_parent)
    await state.set_state(SetProfileStates.set_weight)

    # Create cancel button with appropriate callback data
    cancel_callback_data = get_callback_data_for_parent_context(parent_context, profile_setup_parent)
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data=cancel_callback_data)]
    ])

    await replace_menu_message(
        message_or_callback=callback,
        text="Введите ваш вес в кг (например: 70.5):",
        keyboard=cancel_keyboard,
        state=state,
        return_menu=parent_context,
    )


@router.message(StateFilter(SetProfileStates.set_weight), F.text)
async def process_weight_input(message: Message, state: FSMContext):
    """Обработка ввода веса."""
    # Валидация ввода
    try:
        weight = validate_weight(message.text)
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
            text=f"❌ {e.message}\n\nВведите ваш вес в кг (например: 70.5):",
            keyboard=cancel_keyboard,
            state=state,
            return_menu=parent_context,
        )
        return

    try:
        async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
            await set_weight(message.from_user.id, weight, uow)
            # Get parent context and profile_setup_parent from state before clearing
            data = await state.get_data()
            parent_context = data.get("parent_context") or "main_menu"
            profile_setup_parent = data.get("profile_setup_parent") or "main_menu"
            # Determine which keyboard to show based on parent context
            keyboard = get_keyboard_for_parent_context(parent_context, profile_setup_parent)

            await send_menu_new(
                bot=message.bot,
                chat_id=message.chat.id,
                text=f"✅ Вес сохранён: {weight} кг",
                keyboard=keyboard,
                state=state,
                return_menu=parent_context,
            )
            await state.set_state(None)
            # Remove temporary keys but keep menu_manager keys
            await state.update_data(parent_context=None, profile_setup_parent=None)
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
            text=f"❌ {e.message}\n\nВведите ваш вес в кг (например: 70.5):",
            keyboard=cancel_keyboard,
            state=state,
            return_menu=parent_context,
        )




@router.callback_query(F.data.startswith("profile_set_height"))
async def callback_set_height(callback: CallbackQuery, state: FSMContext):
    """Запрос ввода роста."""
    # Parse parent context from callback data (format: "profile_set_height" or "profile_set_height:parent")
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    # Retrieve profile_setup_parent from state (if available)
    data = await state.get_data()
    profile_setup_parent = data.get("profile_setup_parent") or "main_menu"

    # Store parent context and profile_setup_parent in FSM state
    await state.update_data(parent_context=parent_context, profile_setup_parent=profile_setup_parent)
    await state.set_state(SetProfileStates.set_height)

    # Create cancel button with appropriate callback data
    cancel_callback_data = get_callback_data_for_parent_context(parent_context, profile_setup_parent)
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data=cancel_callback_data)]
    ])

    await replace_menu_message(
        message_or_callback=callback,
        text="Введите ваш рост в см (например: 175):",
        keyboard=cancel_keyboard,
        state=state,
        return_menu=parent_context,
    )


@router.message(StateFilter(SetProfileStates.set_height), F.text)
async def process_height_input(message: Message, state: FSMContext):
    """Обработка ввода роста."""
    # Валидация ввода
    try:
        height = validate_height(message.text)
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
            text=f"❌ {e.message}\n\nВведите ваш рост в см (например: 175):",
            keyboard=cancel_keyboard,
            state=state,
            return_menu=parent_context,
        )
        return

    try:
        async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
            await set_height(message.from_user.id, height, uow)
            # Get parent context and profile_setup_parent from state before clearing
            data = await state.get_data()
            parent_context = data.get("parent_context") or "main_menu"
            profile_setup_parent = data.get("profile_setup_parent") or "main_menu"
            # Determine which keyboard to show based on parent context
            keyboard = get_keyboard_for_parent_context(parent_context, profile_setup_parent)

            await send_menu_new(
                bot=message.bot,
                chat_id=message.chat.id,
                text=f"✅ Рост сохранён: {height} см",
                keyboard=keyboard,
                state=state,
                return_menu=parent_context,
            )
            await state.set_state(None)
            # Remove temporary keys but keep menu_manager keys
            await state.update_data(parent_context=None, profile_setup_parent=None)
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
            text=f"❌ {e.message}\n\nВведите ваш рост в см (например: 175):",
            keyboard=cancel_keyboard,
            state=state,
            return_menu=parent_context,
        )


@router.callback_query(F.data.startswith("profile_set_age"))
async def callback_set_age(callback: CallbackQuery, state: FSMContext):
    """Запрос ввода возраста."""
    # Parse parent context from callback data (format: "profile_set_age" or "profile_set_age:parent")
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    # Retrieve profile_setup_parent from state (if available)
    data = await state.get_data()
    profile_setup_parent = data.get("profile_setup_parent") or "main_menu"

    # Store parent context and profile_setup_parent in FSM state
    await state.update_data(parent_context=parent_context, profile_setup_parent=profile_setup_parent)
    await state.set_state(SetProfileStates.set_age)

    # Create cancel button with appropriate callback data
    cancel_callback_data = get_callback_data_for_parent_context(parent_context, profile_setup_parent)
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data=cancel_callback_data)]
    ])

    await replace_menu_message(
        message_or_callback=callback,
        text="Введите ваш возраст в годах (например: 30):",
        keyboard=cancel_keyboard,
        state=state,
        return_menu=parent_context,
    )


@router.message(StateFilter(SetProfileStates.set_age), F.text)
async def process_age_input(message: Message, state: FSMContext):
    """Обработка ввода возраста."""
    # Валидация ввода
    try:
        age = validate_age(message.text)
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
            text=f"❌ {e.message}\n\nВведите ваш возраст в годах (например: 30):",
            keyboard=cancel_keyboard,
            state=state,
            return_menu=parent_context,
        )
        return

    try:
        async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
            await set_age(message.from_user.id, age, uow)
            # Get parent context and profile_setup_parent from state before clearing
            data = await state.get_data()
            parent_context = data.get("parent_context") or "main_menu"
            profile_setup_parent = data.get("profile_setup_parent") or "main_menu"
            # Determine which keyboard to show based on parent context
            keyboard = get_keyboard_for_parent_context(parent_context, profile_setup_parent)

            await send_menu_new(
                bot=message.bot,
                chat_id=message.chat.id,
                text=f"✅ Возраст сохранён: {age} лет",
                keyboard=keyboard,
                state=state,
                return_menu=parent_context,
            )
            await state.set_state(None)
            # Remove temporary keys but keep menu_manager keys
            await state.update_data(parent_context=None, profile_setup_parent=None)
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
            text=f"❌ {e.message}\n\nВведите ваш возраст в годах (например: 30):",
            keyboard=cancel_keyboard,
            state=state,
            return_menu=parent_context,
        )


@router.callback_query(F.data.startswith("profile_set_activity"))
async def callback_set_activity_minutes(callback: CallbackQuery, state: FSMContext):
    """Запрос ввода минут активности."""
    # Parse parent context from callback data (format: "profile_set_activity" or "profile_set_activity:parent")
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    # Retrieve profile_setup_parent from state (if available)
    data = await state.get_data()
    profile_setup_parent = data.get("profile_setup_parent") or "main_menu"

    # Store parent context and profile_setup_parent in FSM state
    await state.update_data(parent_context=parent_context, profile_setup_parent=profile_setup_parent)
    await state.set_state(SetProfileStates.set_activity_minutes)

    # Create cancel button with appropriate callback data
    cancel_callback_data = get_callback_data_for_parent_context(parent_context, profile_setup_parent)
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data=cancel_callback_data)]
    ])

    await replace_menu_message(
        message_or_callback=callback,
        text="Введите ежедневную активность в минутах (например: 60):",
        keyboard=cancel_keyboard,
        state=state,
        return_menu=parent_context,
    )


@router.message(StateFilter(SetProfileStates.set_activity_minutes), F.text)
async def process_activity_minutes_input(message: Message, state: FSMContext):
    """Обработка ввода минут активности."""
    # Валидация ввода
    try:
        minutes = validate_activity_minutes(message.text)
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
            text=f"❌ {e.message}\n\nВведите ежедневную активность в минутах (например: 60):",
            keyboard=cancel_keyboard,
            state=state,
            return_menu=parent_context,
        )
        return

    try:
        async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
            await set_activity_minutes(message.from_user.id, minutes, uow)
            # Get parent context and profile_setup_parent from state before clearing
            data = await state.get_data()
            parent_context = data.get("parent_context") or "main_menu"
            profile_setup_parent = data.get("profile_setup_parent") or "main_menu"
            # Determine which keyboard to show based on parent context
            keyboard = get_keyboard_for_parent_context(parent_context, profile_setup_parent)

            await send_menu_new(
                bot=message.bot,
                chat_id=message.chat.id,
                text=f"✅ Активность сохранена: {minutes} мин/день",
                keyboard=keyboard,
                state=state,
                return_menu=parent_context,
            )
            await state.set_state(None)
            # Remove temporary keys but keep menu_manager keys
            await state.update_data(parent_context=None, profile_setup_parent=None)
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
            text=f"❌ {e.message}\n\nВведите ежедневную активность в минутах (например: 60):",
            keyboard=cancel_keyboard,
            state=state,
            return_menu=parent_context,
        )


@router.callback_query(F.data.startswith("profile_set_city"))
async def callback_set_city(callback: CallbackQuery, state: FSMContext):
    """Запрос ввода города."""
    # Parse parent context from callback data (format: "profile_set_city" or "profile_set_city:parent")
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    # Retrieve profile_setup_parent from state (if available)
    data = await state.get_data()
    profile_setup_parent = data.get("profile_setup_parent") or "main_menu"

    # Store parent context and profile_setup_parent in FSM state
    await state.update_data(parent_context=parent_context, profile_setup_parent=profile_setup_parent)
    await state.set_state(SetProfileStates.set_city)

    # Create cancel button with appropriate callback data
    cancel_callback_data = get_callback_data_for_parent_context(parent_context, profile_setup_parent)
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data=cancel_callback_data)]
    ])

    await replace_menu_message(
        message_or_callback=callback,
        text="Введите ваш город (например: Москва):",
        keyboard=cancel_keyboard,
        state=state,
        return_menu=parent_context,
    )


@router.message(StateFilter(SetProfileStates.set_city), F.text)
async def process_city_input(message: Message, state: FSMContext):
    """Обработка ввода города."""
    # Validation
    try:
        city = validate_city(message.text)
    except ValidationError as e:
        await message.answer(f"❌ {e.message}")
        return

    async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        await set_city(message.from_user.id, city, uow)
        # Get parent context and profile_setup_parent from state before clearing
        data = await state.get_data()
        parent_context = data.get("parent_context") or "main_menu"
        profile_setup_parent = data.get("profile_setup_parent") or "main_menu"
        # Determine which keyboard to show based on parent context
        keyboard = get_keyboard_for_parent_context(parent_context, profile_setup_parent)

        await send_menu_new(
            bot=message.bot,
            chat_id=message.chat.id,
            text=f"✅ Город сохранён: {city}",
            keyboard=keyboard,
            state=state,
            return_menu=parent_context,
        )
        await state.clear()


@router.callback_query(F.data.startswith("profile_set_calorie_goal"))
async def callback_set_calorie_goal(callback: CallbackQuery, state: FSMContext):
    """Переход к выбору режима цели калорий."""
    # Parse parent context from callback data (format: "profile_set_calorie_goal" or "profile_set_calorie_goal:parent")
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    await replace_menu_message(
        message_or_callback=callback,
        text="Выберите режим цели по калориям:",
        keyboard=calorie_goal_mode_keyboard(parent_context=parent_context),
        state=state,
        return_menu=parent_context,
    )


@router.callback_query(F.data.startswith("calorie_goal_auto"))
async def callback_calorie_goal_auto(callback: CallbackQuery, state: FSMContext):
    """Установить автоматический режим цели калорий."""
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        await set_calorie_goal_mode(callback.from_user.id, "auto", uow)

        keyboard = profile_setup_keyboard(parent_context=parent_context)
        await replace_menu_message(
            message_or_callback=callback,
            text="✅ Режим цели калорий установлен: авто расчет.",
            keyboard=keyboard,
            state=state,
            return_menu=parent_context,
        )


@router.callback_query(F.data.startswith("calorie_goal_manual"))
async def callback_calorie_goal_manual(callback: CallbackQuery, state: FSMContext):
    """Установить ручной режим цели калорий и запросить ввод."""
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    # Retrieve profile_setup_parent from state (if available)
    data = await state.get_data()
    profile_setup_parent = data.get("profile_setup_parent") or "main_menu"

    # Store parent context and profile_setup_parent in FSM state
    await state.update_data(parent_context=parent_context, profile_setup_parent=profile_setup_parent)
    await state.set_state(SetProfileStates.set_calorie_goal_manual)

    async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        await set_calorie_goal_mode(callback.from_user.id, "manual", uow)

    # Create cancel button with appropriate callback data
    cancel_callback_data = get_callback_data_for_parent_context(parent_context, profile_setup_parent)
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data=cancel_callback_data)]
    ])

    await replace_menu_message(
        message_or_callback=callback,
        text="Введите цель по калориям в ккал (например: 2000):",
        keyboard=cancel_keyboard,
        state=state,
        return_menu=parent_context,
    )


@router.callback_query(F.data.startswith("profile_set_water_goal"))
async def callback_set_water_goal(callback: CallbackQuery, state: FSMContext):
    """Переход к выбору режима цели по воде."""
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    await replace_menu_message(
        message_or_callback=callback,
        text="Выберите режим цели по воде:",
        keyboard=water_goal_mode_keyboard(parent_context=parent_context),
        state=state,
        return_menu=parent_context,
    )


@router.callback_query(F.data.startswith("water_goal_auto"))
async def callback_water_goal_auto(callback: CallbackQuery, state: FSMContext):
    """Установить автоматический режим цели по воде."""
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        await set_water_goal_mode(callback.from_user.id, "auto", uow)

        keyboard = profile_setup_keyboard(parent_context=parent_context)
        await replace_menu_message(
            message_or_callback=callback,
            text="✅ Режим цели по воде установлен: авто расчет.",
            keyboard=keyboard,
            state=state,
            return_menu=parent_context,
        )


@router.callback_query(F.data.startswith("water_goal_manual"))
async def callback_water_goal_manual(callback: CallbackQuery, state: FSMContext):
    """Установить ручной режим цели по воде и запросить ввод."""
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    # Retrieve profile_setup_parent from state (if available)
    data = await state.get_data()
    profile_setup_parent = data.get("profile_setup_parent") or "main_menu"

    # Store parent context and profile_setup_parent in FSM state
    await state.update_data(parent_context=parent_context, profile_setup_parent=profile_setup_parent)
    await state.set_state(SetProfileStates.set_water_goal_manual)

    async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        await set_water_goal_mode(callback.from_user.id, "manual", uow)

    # Create cancel button with appropriate callback data
    cancel_callback_data = get_callback_data_for_parent_context(parent_context, profile_setup_parent)
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data=cancel_callback_data)]
    ])

    await replace_menu_message(
        message_or_callback=callback,
        text="Введите цель по воде в мл (например: 2000):",
        keyboard=cancel_keyboard,
        state=state,
        return_menu=parent_context,
    )


@router.message(StateFilter(SetProfileStates.set_calorie_goal_manual), F.text)
async def process_calorie_goal_manual_input(message: Message, state: FSMContext):
    """Обработка ввода цели по калориям."""
    # Валидация ввода
    try:
        calories = validate_calorie_goal(message.text)
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
            text=f"❌ {e.message}\n\nВведите цель по калориям в ккал (например: 2000):",
            keyboard=cancel_keyboard,
            state=state,
            return_menu=parent_context,
        )
        return

    try:
        async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
            await set_calorie_goal_manual(message.from_user.id, calories, uow)
            # Get parent context and profile_setup_parent from state before clearing
            data = await state.get_data()
            parent_context = data.get("parent_context") or "main_menu"
            profile_setup_parent = data.get("profile_setup_parent") or "main_menu"
            # Determine which keyboard to show based on parent context
            keyboard = get_keyboard_for_parent_context(parent_context, profile_setup_parent)

            await send_menu_new(
                bot=message.bot,
                chat_id=message.chat.id,
                text=f"✅ Цель по калориям сохранена: {calories} ккал",
                keyboard=keyboard,
                state=state,
                return_menu=parent_context,
            )
            await state.set_state(None)
            # Remove temporary keys but keep menu_manager keys
            await state.update_data(parent_context=None, profile_setup_parent=None)
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
            text=f"❌ {e.message}\n\nВведите цель по калориям в ккал (например: 2000):",
            keyboard=cancel_keyboard,
            state=state,
            return_menu=parent_context,
        )


@router.message(StateFilter(SetProfileStates.set_water_goal_manual), F.text)
async def process_water_goal_manual_input(message: Message, state: FSMContext):
    """Обработка ввода цели по воде."""
    # Валидация ввода
    try:
        water_ml = validate_water_goal(message.text)
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
            text=f"❌ {e.message}\n\nВведите цель по воде в мл (например: 2000):",
            keyboard=cancel_keyboard,
            state=state,
            return_menu=parent_context,
        )
        return

    try:
        async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
            await set_water_goal_manual(message.from_user.id, water_ml, uow)
            # Get parent context and profile_setup_parent from state before clearing
            data = await state.get_data()
            parent_context = data.get("parent_context") or "main_menu"
            profile_setup_parent = data.get("profile_setup_parent") or "main_menu"
            # Determine which keyboard to show based on parent context
            keyboard = get_keyboard_for_parent_context(parent_context, profile_setup_parent)

            await send_menu_new(
                bot=message.bot,
                chat_id=message.chat.id,
                text=f"✅ Цель по воде сохранена: {water_ml} мл",
                keyboard=keyboard,
                state=state,
                return_menu=parent_context,
            )
            await state.set_state(None)
            # Remove temporary keys but keep menu_manager keys
            await state.update_data(parent_context=None, profile_setup_parent=None)
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
            text=f"❌ {e.message}\n\nВведите цель по воде в мл (например: 2000):",
            keyboard=cancel_keyboard,
            state=state,
            return_menu=parent_context,
        )


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню."""
    await replace_menu_message(
        message_or_callback=callback,
        text="Главное меню:",
        keyboard=main_menu_keyboard(),
        state=state,
        return_menu="main_menu",
    )