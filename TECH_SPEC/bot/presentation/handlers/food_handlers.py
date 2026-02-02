from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from presentation.fsm.states import FoodLogStates
from presentation.keyboards.inline import main_menu_keyboard, food_type_keyboard, profile_setup_keyboard
from presentation.validators.food import validate_product_name, validate_grams
from domain.exceptions import ValidationError
from infrastructure.config.database import AsyncSessionFactory
from infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from application.use_cases.food.resolve_food_item import resolve_food_item
from application.use_cases.food.set_food_grams import set_food_grams
from application.use_cases.food.finalize_food_log import finalize_food_log

router = Router()


@router.callback_query(F.data.startswith("food_add"))
async def callback_food_add(callback: CallbackQuery, state: FSMContext):
    """Начало логирования еды."""
    # Parse parent context from callback data (format: "food_add" or "food_add:parent")
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 else "main_menu"

    # Store parent context in FSM state
    await state.update_data(parent_context=parent_context)
    await state.set_state(FoodLogStates.enter_product_name)
    await callback.message.edit_text(
        "Введите название продукта (например: 'банан', 'курица'):",
    )


@router.message(StateFilter(FoodLogStates.enter_product_name), F.text)
async def process_food_input(message: Message, state: FSMContext):
    """Обработка ввода продукта."""
    product_query = message.text.strip()

    # Валидация ввода
    try:
        product_query = validate_product_name(message.text)
    except ValidationError as e:
        await message.answer(f"❌ {e.message}")
        return

    # Используем инфраструктурный слой для разрешения продукта
    result = await resolve_food_item(product_query)

    if result is None:
        # Get parent context from state before clearing
        data = await state.get_data()
        parent_context = data.get("parent_context", "main_menu")

        # Determine which keyboard to show based on parent context
        if parent_context == "main_menu":
            keyboard = main_menu_keyboard()
        elif parent_context == "profile_setup":
            keyboard = profile_setup_keyboard(parent_context="main_menu")
        else:
            keyboard = main_menu_keyboard()  # Fallback

        await message.answer(
            "❌ Продукт не найден. Попробуйте другой.",
            reply_markup=keyboard,
        )
        await state.clear()
        return

    product_name, kcal_per_100g, attribution = result

    # Сохраняем данные в состоянии
    await state.update_data(
        product_query=product_query,
        product_name=product_name,
        kcal_per_100g=kcal_per_100g,
        source="fatsecret"  # данные от FatSecret API
    )

    # Переходим к вводу граммов
    await state.set_state(FoodLogStates.enter_grams)
    await message.answer(
        f"🍎 Найден продукт: {product_name}\n"
        f"Калорийность: {kcal_per_100g} ккал/100г\n"
        f"{attribution}\n\n"
        "Введите количество в граммах:",
    )


@router.message(StateFilter(FoodLogStates.enter_grams), F.text)
async def process_grams_input(message: Message, state: FSMContext):
    """Обработка ввода граммов."""
    # Валидация ввода
    try:
        grams = validate_grams(message.text)
    except ValidationError as e:
        await message.answer(f"❌ {e.message}")
        return

    # Получаем сохранённые данные из состояния
    data = await state.get_data()
    product_query = data.get("product_query")
    product_name = data.get("product_name")
    kcal_per_100g = data.get("kcal_per_100g")
    source = data.get("source", "manual")
    parent_context = data.get("parent_context", "main_menu")

    try:
        # Вычисляем калории
        grams, kcal_total = set_food_grams(kcal_per_100g, grams)

        # Сохраняем в БД
        async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
            await finalize_food_log(
                user_id=message.from_user.id,
                product_query=product_query,
                product_name=product_name,
                source=source,
                kcal_per_100g=kcal_per_100g,
                grams=grams,
                kcal_total=kcal_total,
                uow=uow,
            )
    except ValidationError as e:
        await message.answer(f"❌ {e.message}")
        return

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
        f"🍽 Еда добавлена: {kcal_total:.1f} ккал\n"
        f"({product_name}, {grams}г)",
        reply_markup=keyboard,
    )




