
from typing import Optional, Union
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.fsm.context import FSMContext


def _validate_inline_keyboard(keyboard: InlineKeyboardMarkup) -> None:
    
    for row_idx, row in enumerate(keyboard.inline_keyboard):
        for btn_idx, button in enumerate(row):
            if not button.callback_data and not button.url:
                raise ValueError(
                    f"Inline keyboard button at row {row_idx}, column {btn_idx} "
                    f"has text '{button.text}' but lacks both callback_data and url. "
                    f"Text buttons are not allowed in inline keyboards."
                )


async def show_menu(
    bot: Bot,
    chat_id: int,
    text: str,
    state: FSMContext,
    return_menu: str,
    keyboard: Optional[InlineKeyboardMarkup] = None,
    force_message_id: Optional[int] = None,
) -> None:
    
                               
    await state.update_data(return_menu=return_menu)

                                   
    if keyboard is not None:
        _validate_inline_keyboard(keyboard)

                                                   
    previous_message_id: Optional[int] = None
    if force_message_id is not None:
                                                       
        previous_message_id = force_message_id
        await state.update_data(menu_message_id=force_message_id)
    else:
        data = await state.get_data()
        previous_message_id = data.get("menu_message_id")

    try:
        if previous_message_id is not None:
                                              
            edit_kwargs = {
                "chat_id": chat_id,
                "message_id": previous_message_id,
                "text": text,
                "parse_mode": "Markdown",
            }
            if keyboard is not None:
                edit_kwargs["reply_markup"] = keyboard
            await bot.edit_message_text(**edit_kwargs)
                                                   
            return
    except Exception:
                                                                        
                                               
                                                                        
        if previous_message_id is not None:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=previous_message_id)
            except Exception:
                                                                   
                pass
                                                               
        await state.update_data(menu_message_id=None)

                           
    send_kwargs = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    if keyboard is not None:
        send_kwargs["reply_markup"] = keyboard
    message: Message = await bot.send_message(**send_kwargs)
    await state.update_data(menu_message_id=message.message_id)


async def replace_menu_message(
    message_or_callback: Union[Message, CallbackQuery],
    text: str,
    state: FSMContext,
    return_menu: str,
    keyboard: Optional[InlineKeyboardMarkup] = None,
) -> None:
    
    if isinstance(message_or_callback, CallbackQuery):
        bot = message_or_callback.bot
        chat_id = message_or_callback.message.chat.id
        message_id = message_or_callback.message.message_id
    else:
        bot = message_or_callback.bot
        chat_id = message_or_callback.chat.id
        message_id = message_or_callback.message_id

    await show_menu(
        bot=bot,
        chat_id=chat_id,
        text=text,
        keyboard=keyboard,
        state=state,
        return_menu=return_menu,
        force_message_id=message_id,
    )


async def clear_previous_menu(bot: Bot, chat_id: int, state: FSMContext) -> None:
    
    data = await state.get_data()
    previous_message_id: Optional[int] = data.get("menu_message_id")
    if previous_message_id is not None:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=previous_message_id)
        except Exception:
                                                               
            pass
                                  
        await state.update_data(menu_message_id=None)


async def clear_markup(bot: Bot, chat_id: int, message_id: int) -> None:
    
    try:
        await bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=None,
        )
    except Exception:
                                                                             
        pass


async def send_menu_new(
    bot: Bot,
    chat_id: int,
    text: str,
    keyboard: Optional[InlineKeyboardMarkup],
    state: FSMContext,
    return_menu: str,
) -> None:
    
                               
    await state.update_data(return_menu=return_menu)

                                   
    if keyboard is not None:
        _validate_inline_keyboard(keyboard)

                                          
    data = await state.get_data()
    previous_message_id: Optional[int] = data.get("menu_message_id")

                                                            
    if previous_message_id is not None:
        await clear_markup(bot, chat_id, previous_message_id)

                           
    send_kwargs = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    if keyboard is not None:
        send_kwargs["reply_markup"] = keyboard
    message: Message = await bot.send_message(**send_kwargs)

                               
    await state.update_data(menu_message_id=message.message_id)


async def get_return_menu(state: FSMContext) -> str:
    
    data = await state.get_data()
    return data.get("return_menu", "main_menu")