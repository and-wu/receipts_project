import asyncio
import logging

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties

from config_data.config import BOT_TOKEN
from src.handlers.commands import router as commands_router


# Настройка логирования
logging.basicConfig(level=logging.INFO)


dp = Dispatcher()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))


async def start():
    dp.include_router(commands_router)


    await bot.delete_webhook(drop_pending_updates=True)
    print(await bot.me())
    print(f"Бот запущен")
    await dp.start_polling(bot)


asyncio.run(start())
