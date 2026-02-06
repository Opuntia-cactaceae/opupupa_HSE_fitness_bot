from aiogram import Router

from presentation.handlers import profile_handlers, water_handlers, food_handlers, workout_handlers, progress_handlers


def setup_routers() -> Router:
    router = Router()

    router.include_router(profile_handlers.router)
    router.include_router(water_handlers.router)
    router.include_router(food_handlers.router)
    router.include_router(workout_handlers.router)
    router.include_router(progress_handlers.router)

    return router
