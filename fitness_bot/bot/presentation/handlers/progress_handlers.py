import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)

from presentation.keyboards.inline import main_menu_keyboard, profile_setup_keyboard, weekly_stats_keyboard, progress_keyboard, charts_keyboard
from infrastructure.config.database import AsyncSessionFactory
from infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from application.use_cases.progress.check_progress import check_progress
from application.use_cases.progress.get_weekly_stats import get_weekly_stats
from application.use_cases.progress.get_progress_chart_data import get_progress_chart_data
from presentation.services.charts import build_progress_chart
from presentation.services.menu_manager import replace_menu_message

router = Router()


@router.callback_query(F.data.startswith("progress_show"))
async def callback_progress_show(callback: CallbackQuery, state: FSMContext):
    
                                                                                                 
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        progress = await check_progress(callback.from_user.id, uow)

        water_logged = progress["water_logged_ml"]
        water_goal = progress["water_goal_ml"]
        water_remaining = progress["water_remaining_ml"]
        calories_consumed = progress["calories_consumed_kcal"]
        calories_burned = progress["calories_burned_kcal"]
        calorie_balance = progress["calorie_balance_kcal"]

        water_percentage = (water_logged / water_goal * 100) if water_goal > 0 else 0
        calorie_percentage = (calories_consumed / (water_goal or 1) * 100) if water_goal > 0 else 0

        message = (
            "📊 **Ваш прогресс на сегодня:**\n\n"
            f"💧 **Вода:**\n"
            f"   Выпито: {water_logged} мл\n"
            f"   Цель: {water_goal} мл\n"
            f"   Осталось: {water_remaining} мл\n"
            f"   Прогресс: {water_percentage:.1f}%\n\n"
            f"🍎 **Калории:**\n"
            f"   Потреблено: {calories_consumed} ккал\n"
            f"   Сожжено: {calories_burned} ккал\n"
            f"   Баланс: {calorie_balance} ккал\n\n"
        )

        if calorie_balance > 0:
            message += "📈 Вы в профиците калорий."
        elif calorie_balance < 0:
            message += "📉 Вы в дефиците калорий."
        else:
            message += "⚖️ Баланс калорий нейтральный."

                                                                  
        if parent_context == "main_menu":
            keyboard = progress_keyboard(parent_context)
        elif parent_context == "profile_setup":
            keyboard = profile_setup_keyboard(parent_context="main_menu")
        else:
            keyboard = main_menu_keyboard()            

        await replace_menu_message(
            message_or_callback=callback,
            text=message,
            keyboard=keyboard,
            state=state,
            return_menu=parent_context,
        )


@router.callback_query(F.data.startswith("progress_weekly_show"))
async def callback_progress_weekly_show(callback: CallbackQuery, state: FSMContext):
    
    from datetime import date, timedelta

                                                                                         
    parts = callback.data.split(":")
    if len(parts) > 1:
        try:
            reference_date = date.fromisoformat(parts[1])
        except ValueError:
            reference_date = date.today()
    else:
        reference_date = date.today()

    async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        week_start, week_end, daily_stats_list = await get_weekly_stats(
            callback.from_user.id, reference_date, uow
        )

                       
        message = f"📅 **Неделя:** {week_start.strftime('%d.%m')} – {week_end.strftime('%d.%m')}\n\n"

                                                                 
        stats_by_date = {stats.date: stats for stats in daily_stats_list}

                                                                 
        for day_offset in range(7):
            day_date = week_start + timedelta(days=day_offset)
            stats = stats_by_date.get(day_date)

                        
            day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
            message += f"{day_names[day_offset]} {day_date.strftime('%d.%m')}\n"

            if stats is None:
                message += "💧 0 / 0 мл\n🔥 0 / 0 ккал (−0)\n🏃 Сожжено: 0 ккал, 0 мл\n\n"
            else:
                water_logged = stats.water_logged_ml
                water_goal = stats.water_goal_ml
                calories_consumed = stats.calories_consumed_kcal
                calorie_goal = stats.calorie_goal_kcal
                calories_burned = stats.calories_burned_kcal
                calorie_balance = stats.calorie_balance_kcal
                water_burned = 0                                              

                message += (
                    f"💧 {water_logged} / {water_goal} мл\n"
                    f"🔥 {calories_consumed} / {calorie_goal} ккал ({calorie_balance:+})\n"
                    f"🏃 Сожжено: {calories_burned} ккал, {water_burned} мл\n\n"
                )

        keyboard = weekly_stats_keyboard(reference_date)
        await replace_menu_message(
            message_or_callback=callback,
            text=message,
            keyboard=keyboard,
            state=state,
            return_menu="main_menu",
        )


@router.callback_query(F.data.startswith("charts_show"))
async def callback_charts_show(callback: CallbackQuery, state: FSMContext):
    
    parts = callback.data.split(":")
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    keyboard = charts_keyboard(parent_context)
    await replace_menu_message(
        message_or_callback=callback,
        text="Выберите период для графиков:",
        keyboard=keyboard,
        state=state,
        return_menu=parent_context,
    )


@router.callback_query(F.data.startswith("charts_period_"))
async def callback_charts_period(callback: CallbackQuery, state: FSMContext):
    
    parts = callback.data.split(":")
    period_str = parts[0].split("_")[-1]                            
    parent_context = parts[1] if len(parts) > 1 and parts[1] != "" else "main_menu"

    try:
        period_days = int(period_str)
    except ValueError:
        period_days = 7

    async with SqlAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        daily_stats = await get_progress_chart_data(callback.from_user.id, period_days, uow)

        try:
            png_bytes = build_progress_chart(daily_stats)
        except Exception as e:
            logger.exception("Ошибка при генерации графиков")
            await callback.message.answer("❌ Ошибка при построении графиков. Попробуйте позже.")
            message_text = "Произошла ошибка при построении графиков. Выберите другой период:"
        else:
            if png_bytes is None:
                await callback.message.answer("📊 Нет данных за выбранный период.")
                message_text = "Нет данных за выбранный период. Выберите другой период:"
            else:
                input_file = BufferedInputFile(png_bytes, filename="progress_chart.png")
                await callback.message.answer_photo(
                    photo=input_file,
                    caption=f"Графики прогресса за {period_days} дней",
                )
                message_text = f"Графики за {period_days} дней отправлены. Выберите другой период:"

        keyboard = charts_keyboard(parent_context)
        await replace_menu_message(
            message_or_callback=callback,
            text=message_text,
            keyboard=keyboard,
            state=state,
            return_menu=parent_context,
        )