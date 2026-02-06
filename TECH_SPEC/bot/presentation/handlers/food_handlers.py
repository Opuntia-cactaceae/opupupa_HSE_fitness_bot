from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from presentation.fsm.states import FoodLogStates
from presentation.keyboards.inline import main_menu_keyboard, food_type_keyboard, profile_setup_keyboard, food_product_confirmation_keyboard
from presentation.validators.food import validate_product_name, validate_grams
from domain.exceptions import ValidationError, EntityNotFoundError
from presentation.services.menu_manager import replace_menu_message, show_menu, send_menu_new, clear_markup
from presentation.services.keyboard_mapper import get_callback_data_for_parent_context, get_keyboard_for_parent_context
from infrastructure.config.database import AsyncSessionFactory
from infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from application.use_cases.food.resolve_food_item import resolve_food_item
from application.use_cases.food.set_food_grams import set_food_grams
from application.use_cases.food.finalize_food_log import finalize_food_log
from application.use_cases.food.delete_food_log import delete_food_log

router = Router()


@router.callback_query(F.data.startswith("food_add"))
async def callback_food_add(callback: CallbackQuery, state: FSMContext):
    
                                                                                       
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

                                       
    await state.update_data(parent_context=parent_context)
    await state.set_state(FoodLogStates.enter_product_name)
    await replace_menu_message(
        message_or_callback=callback,
        text="Введите название продукта на английском языке (например: banana, chicken). Русские названия пока не поддерживаются.",
        state=state,
        return_menu=parent_context,
        keyboard=None,
    )

@router.callback_query(F.data.startswith("food_reject"))
async def callback_food_reject(callback: CallbackQuery, state: FSMContext):
    
                                                                            
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

                                   
    await state.update_data(
        product_query=None,
        product_name=None,
        kcal_per_100g=None,
        source=None,
    )

                                        
    await state.set_state(FoodLogStates.enter_product_name)

                                                          
    await replace_menu_message(
        message_or_callback=callback,
        text="Введите название продукта на английском языке (например: banana, chicken). Русские названия пока не поддерживаются.",
        state=state,
        return_menu=parent_context,
        keyboard=None,
    )

@router.callback_query(F.data.startswith("food_cancel"))
async def callback_food_cancel(callback: CallbackQuery, state: FSMContext):
    
                                                                            
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

                                   
    await state.update_data(
        product_query=None,
        product_name=None,
        kcal_per_100g=None,
        source=None,
    )

                     
    await state.set_state(None)

                      
    keyboard = get_keyboard_for_parent_context(parent_context, profile_setup_parent="main_menu")
    await replace_menu_message(
        message_or_callback=callback,
        text="Главное меню:" if parent_context == "main_menu" else "Настройка профиля:",
        state=state,
        return_menu=parent_context,
        keyboard=keyboard,
    )


@router.message(StateFilter(FoodLogStates.enter_product_name), F.text)
async def process_food_input(message: Message, state: FSMContext):
    
    product_query = message.text.strip()

                     
    try:
        product_query = validate_product_name(message.text)
    except ValidationError as e:
        await message.answer(f"❌ {e.message}")
        return

                                                              
    result = await resolve_food_item(product_query)

    if result is None:
                                                       
        data = await state.get_data()
        parent_context = data.get("parent_context", "main_menu")

                                                                  
        keyboard = get_keyboard_for_parent_context(parent_context, profile_setup_parent="main_menu")

        await show_menu(
            bot=message.bot,
            chat_id=message.chat.id,
            text="❌ Продукт не найден. Попробуйте другой.",
            state=state,
            return_menu=parent_context,
            keyboard=keyboard,
        )
        await state.set_state(None)
                                                          
        await state.update_data(parent_context=None)
        return

    product_name, kcal_per_100g = result

                                  
    await state.update_data(
        product_query=product_query,
        product_name=product_name,
        kcal_per_100g=kcal_per_100g,
        source="fatsecret"                           
    )

                        
    data = await state.get_data()
    parent_context = data.get("parent_context", "main_menu")

                                  
    keyboard = food_product_confirmation_keyboard(parent_context)

                                                         
    await show_menu(
        bot=message.bot,
        chat_id=message.chat.id,
        text=f"🍎 Найден продукт: {product_name}\n"
             f"Калорийность: {kcal_per_100g} ккал/100г\n"
             "Введите количество в граммах:",
        state=state,
        return_menu=parent_context,
        keyboard=keyboard,
    )

                                     
    await state.set_state(FoodLogStates.enter_grams)


@router.message(StateFilter(FoodLogStates.enter_grams), F.text)
async def process_grams_input(message: Message, state: FSMContext):
    
                     
    try:
        grams = validate_grams(message.text)
    except ValidationError as e:
                                                           
        data = await state.get_data()
        parent_context = data.get("parent_context", "main_menu")
        keyboard = food_product_confirmation_keyboard(parent_context)
        await show_menu(
            bot=message.bot,
            chat_id=message.chat.id,
            text=f"❌ {e.message}\n\nВведите количество в граммах:",
            state=state,
            return_menu=parent_context,
            keyboard=keyboard,
        )
        return

                                              
    data = await state.get_data()
    product_query = data.get("product_query")
    product_name = data.get("product_name")
    kcal_per_100g = data.get("kcal_per_100g")
    source = data.get("source", "manual")
    parent_context = data.get("parent_context", "main_menu")

    try:
                           
        grams, kcal_total = set_food_grams(kcal_per_100g, grams)

                        
        async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
            log_id = await finalize_food_log(
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
                                       
        keyboard = food_product_confirmation_keyboard(parent_context)
        await show_menu(
            bot=message.bot,
            chat_id=message.chat.id,
            text=f"❌ {e.message}\n\nВведите количество в граммах:",
            state=state,
            return_menu=parent_context,
            keyboard=keyboard,
        )
        return

                                          
    await state.set_state(None)
                                                      
    await state.update_data(parent_context=None)

                                                              
    keyboard = get_keyboard_for_parent_context(parent_context, profile_setup_parent="main_menu")
                              
    rows = keyboard.inline_keyboard.copy()
    rows.append([InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_food:{log_id}:{parent_context}")])
    keyboard_with_delete = InlineKeyboardMarkup(inline_keyboard=rows)

    await send_menu_new(
        bot=message.bot,
        chat_id=message.chat.id,
        text=f"🍽 Еда добавлена: {kcal_total:.1f} ккал\n"
             f"({product_name}, {grams}г)",
        keyboard=keyboard_with_delete,
        state=state,
        return_menu=parent_context,
    )


@router.callback_query(F.data.startswith("delete_food"))
async def callback_delete_food(callback: CallbackQuery, state: FSMContext):
    
                                                                           
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("Неверный формат")
        return
    log_id = int(parts[1])
    parent_context = parts[2] if parts[2] != "" else "main_menu"

    try:
        async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
            await delete_food_log(log_id, callback.from_user.id, uow)
    except EntityNotFoundError:
        await callback.answer("Запись не найдена")
        return

                                                             
    data = await state.get_data()
    profile_setup_parent = data.get("profile_setup_parent") or "main_menu"

                                                              
    keyboard = get_keyboard_for_parent_context(parent_context, profile_setup_parent)

    await replace_menu_message(
        message_or_callback=callback,
        text="🍽 Запись удалена",
        keyboard=keyboard,
        state=state,
        return_menu=parent_context,
    )


