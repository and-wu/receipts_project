from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties

from config_data.config import BOT_TOKEN

dp = Dispatcher()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))

