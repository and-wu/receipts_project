import asyncio
import logging
import sys

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest


from config_data.config import BOT_TOKEN
from src.handlers.commands import router as commands_router
from src.handlers.sheet_link import router as sheet_link_router
from aiogram.client.default import DefaultBotProperties


# Настройка логирования
logging.basicConfig(level=logging.INFO)


dp = Dispatcher()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))

# новый коментарий

async def start():
    dp.include_router(sheet_link_router)
    dp.include_router(commands_router)


    try:
        # Удаляем возможный вебхук и сбрасываем накопившиеся апдейты
        await bot.delete_webhook(drop_pending_updates=True)
    except TelegramBadRequest as e:
        logging.warning(f"Ошибка при удалении вебхука: {e}")

    try:
        me = await bot.me()
        print(f"Бот запущен: @{me.username} (id: {me.id})")
        print("Polling запущен...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Не удалось запустить бота: {e}")
        await bot.session.close()
        sys.exit(1)



if __name__ == "__main__":
    try:
        asyncio.run(start())
    except KeyboardInterrupt:
        print("Бот остановлен вручную")
    finally:
        asyncio.run(bot.session.close())