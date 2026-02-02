import asyncio
import logging

from config.settings import settings
from infrastructure.db.unit_of_work import UnitOfWork
from presentation.routers import setup_routers

from aiogram import Bot, Dispatcher


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(setup_routers())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())