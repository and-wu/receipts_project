from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

router = Router()


# Обработчик команды /start
@router.message(CommandStart())
async def send_welcome(message: Message):
    await message.answer(f"Привет, я бот который умеет считывать информацию с чеков!\nОтправь мне фотографию чека и я пришлю тебе всю информацию с него")


@router.message(Command("help"))
async def send_help(message: Message):
    await message.answer(f"я бот который считывает инфу с чета, просто пришли мне его фото")


