import asyncio
import logging

from aiogram import Bot, Dispatcher

import handlers.auth_handlers
import handlers.common_handlers
import handlers.registration_handlers
from constants import API_TOKEN

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)


async def main():
    bot = Bot(token=API_TOKEN, parse_mode='HTML')
    dp = Dispatcher()
    dp.include_routers(
        # порядок расположения важен, т.к. может приводить
        # к нежелательным перехватам
        handlers.common_handlers.router,
        handlers.registration_handlers.router,
        handlers.auth_handlers.router,
    )
    await bot.delete_webhook(
        drop_pending_updates=True
    )  # удаление вебхука, ответственного за получение сообщений
    # вне периода активности бота
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
