from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import date


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню бота."""
    buttons = [
        [
            InlineKeyboardButton(text="⚙️ Настройка профиля", callback_data="profile_setup:main_menu"),
            InlineKeyboardButton(text="💧 Добавить воду", callback_data="water_add:main_menu"),
        ],
        [
            InlineKeyboardButton(text="🍎 Добавить еду", callback_data="food_add:main_menu"),
            InlineKeyboardButton(text="🏃 Добавить тренировку", callback_data="workout_add:main_menu"),
        ],
        [
            InlineKeyboardButton(text="📊 Показать прогресс", callback_data="progress_show:main_menu"),
        ],
        [
            InlineKeyboardButton(text="📅 Недельная статистика", callback_data=f"progress_weekly_show:{date.today().isoformat()}"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def profile_setup_keyboard(parent_context: str = "main_menu") -> InlineKeyboardMarkup:
    """Клавиатура настройки профиля."""
    buttons = [
        [
            InlineKeyboardButton(text="Вес", callback_data=f"profile_set_weight:profile_setup"),
            InlineKeyboardButton(text="Рост", callback_data=f"profile_set_height:profile_setup"),
        ],
        [
            InlineKeyboardButton(text="Возраст", callback_data=f"profile_set_age:profile_setup"),
            InlineKeyboardButton(text="Активность", callback_data=f"profile_set_activity:profile_setup"),
        ],
        [
            InlineKeyboardButton(text="Город", callback_data=f"profile_set_city:profile_setup"),
            InlineKeyboardButton(text="Цель калорий", callback_data=f"profile_set_calorie_goal:profile_setup"),
        ],
        [
            InlineKeyboardButton(text="✅ Завершить настройку", callback_data=f"profile_finalize:{parent_context}"),
            InlineKeyboardButton(text="◀️ Назад", callback_data=parent_context),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def water_volume_keyboard(parent_context: str = "main_menu") -> InlineKeyboardMarkup:
    """Клавиатура выбора объёма воды."""
    buttons = [
        [
            InlineKeyboardButton(text="250 мл", callback_data=f"water_250:{parent_context}"),
            InlineKeyboardButton(text="500 мл", callback_data=f"water_500:{parent_context}"),
        ],
        [
            InlineKeyboardButton(text="750 мл", callback_data=f"water_750:{parent_context}"),
            InlineKeyboardButton(text="1000 мл", callback_data=f"water_1000:{parent_context}"),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data=parent_context),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def food_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа еды (пример)."""
    buttons = [
        [
            InlineKeyboardButton(text="Завтрак", callback_data="food_breakfast"),
            InlineKeyboardButton(text="Обед", callback_data="food_lunch"),
        ],
        [
            InlineKeyboardButton(text="Ужин", callback_data="food_dinner"),
            InlineKeyboardButton(text="Перекус", callback_data="food_snack"),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def workout_type_keyboard(parent_context: str = "main_menu") -> InlineKeyboardMarkup:
    """Клавиатура выбора типа тренировки."""
    buttons = [
        [
            InlineKeyboardButton(text="🏃 Бег", callback_data=f"workout_running:{parent_context}"),
            InlineKeyboardButton(text="🚶 Ходьба", callback_data=f"workout_walking:{parent_context}"),
        ],
        [
            InlineKeyboardButton(text="💪 Силовая", callback_data=f"workout_strength:{parent_context}"),
            InlineKeyboardButton(text="🏊 Плавание", callback_data=f"workout_swimming:{parent_context}"),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data=parent_context),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def calorie_goal_mode_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора режима цели калорий."""
    buttons = [
        [
            InlineKeyboardButton(text="Авто расчет", callback_data="calorie_goal_auto"),
            InlineKeyboardButton(text="Ручной ввод", callback_data="calorie_goal_manual"),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="profile_setup"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def weekly_stats_keyboard(reference_date: date) -> InlineKeyboardMarkup:
    """Клавиатура навигации по недельной статистике."""
    from datetime import timedelta
    prev_week = reference_date - timedelta(days=7)
    next_week = reference_date + timedelta(days=7)
    buttons = [
        [
            InlineKeyboardButton(text="◀️ Предыдущая неделя",
                                 callback_data=f"progress_weekly_show:{prev_week.isoformat()}"),
            InlineKeyboardButton(text="▶️ Следующая неделя",
                                 callback_data=f"progress_weekly_show:{next_week.isoformat()}"),
        ],
        [
            InlineKeyboardButton(text="🔙 В главное меню",
                                 callback_data="main_menu"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)