
from aiogram.types import InlineKeyboardMarkup
from presentation.keyboards.inline import main_menu_keyboard, profile_setup_keyboard


def _normalize_context(context: str, default: str = "main_menu") -> str:
    
    return default if context == "" else context


def get_keyboard_for_parent_context(parent_context: str, profile_setup_parent: str = "main_menu") -> InlineKeyboardMarkup:
    
                                                                                     
    parent_context = _normalize_context(parent_context)
    profile_setup_parent = _normalize_context(profile_setup_parent)

    if parent_context == "profile_setup":
                                                                                                        
        return profile_setup_keyboard(parent_context=profile_setup_parent)
    elif parent_context == "main_menu":
        return main_menu_keyboard()
    else:
                                       
        return main_menu_keyboard()


def get_callback_data_for_parent_context(parent_context: str, profile_setup_parent: str = "main_menu") -> str:
    
                                                                                     
    parent_context = _normalize_context(parent_context)
    profile_setup_parent = _normalize_context(profile_setup_parent)

    if parent_context == "profile_setup":
        return f"profile_setup:{profile_setup_parent}"
    else:
        return parent_context