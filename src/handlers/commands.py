from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from ..logic.paddleOCR_logic import save_photo, process_receipt

router = Router()


# Обработчик команды /start
@router.message(CommandStart())
async def send_welcome(message: Message):
    await message.answer(f"Привет, я бот который умеет считывать информацию с чеков!\nОтправь мне фотографию чека и я пришлю тебе всю информацию с него")


@router.message(Command("help"))
async def send_help(message: Message):
    await message.answer(f"я бот который считывает инфу с чета, просто пришли мне его фото")


@router.message(F.photo)
async def process_photo(message: Message):
    await message.answer(f'Обрабатываю полученное фото')

    # Берём фото в максимальном качестве
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)

    # Скачиваем в память
    photo_bytes = await message.bot.download_file(file.file_path, destination=None)

    # Сохраняем на диск
    file_path = save_photo(photo_bytes, message.message_id)

    # Обрабатываем чек (OCR)
    text_lines = process_receipt(file_path)

    # Отправляем результат
    if text_lines:
        response = "🧾 Распознанный чек:\n\n" + "\n".join(text_lines)
    else:
        response = "Не удалось распознать чек 😔"

    await message.answer(response)

