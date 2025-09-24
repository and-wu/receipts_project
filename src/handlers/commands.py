from aiogram import Router, F
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


@router.message(F.photo)
async def process_photo(message: Message):
    await message.answer(f'Обрабатываю полученное фото')

    # берём фото в наилучшем качестве
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)

    # скачиваем фото
    file_path = file.file_path
    downloaded = await message.bot.download_file(file_path)

    # сохраняем временно
    image_path = "check.jpg"
    with open(image_path, "wb") as f:
        f.write(downloaded.read())

    # OCR (распознавание текста)
    text = pytesseract.image_to_string(Image.open(image_path), lang="rus+eng")

    # Отправляем результат
    if text.strip():
        await message.answer(f"📄 Я нашёл такой текст:\n\n<code>{text}</code>")
    else:
        await message.answer("⚠️ Не удалось распознать текст на чеке.")

