from aiogram.fsm.state import State, StatesGroup


class SetProfileStates(StatesGroup):
    
    set_weight = State()
    set_height = State()
    set_age = State()
    set_activity_minutes = State()
    set_city = State()
    set_calorie_goal_manual = State()
    set_water_goal_manual = State()


class FoodLogStates(StatesGroup):
    
    enter_product_name = State()
    enter_grams = State()


class WorkoutLogStates(StatesGroup):
    
    select_workout_type = State()
    enter_minutes = State()


class WaterLogStates(StatesGroup):
    
    enter_ml = State()