import os
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers.auth import (
    user_profile,
    authentication,
    registration,
)
from handlers.vocabulary import vocabulary, words, collections
from handlers import core
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv('AIOGRAM_LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

BOT_TOKEN = os.getenv('BOT_TOKEN')


async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.include_routers(
        user_profile.router,
        registration.router,
        authentication.router,
        vocabulary.router,
        words.router,
        collections.router,
        core.router,
    )

    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
