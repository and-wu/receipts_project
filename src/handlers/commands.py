from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from ..logic.paddleOCR_logic import save_photo, process_receipt
from ..logic.db_logic import Database
from ..utils.text_parser import parse_message_text
from ..logic.google_sheets_logic import save_to_sheet


router = Router()

db = Database()

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
    #text_lines = process_receipt(file_path)

    #print("вот итог", text_lines)

    #user = message.from_user

    # Отправляем результат

    # Форматируем красиво
    #text = (
    #    f" *Информация о пользователе:*\n\n"
    #    f" ID: {user.id}\n"
    #    f" Имя: {user.first_name}\n"
    #    f" Фамилия: {user.last_name}\n"
    #    f" Юзернейм: {user.username}\n"
    #    f" Бот: {user.is_bot}\n\n"
    #    f"🧾 *Информация о чеке:*\n\n"
    #    f"📅 Дата: {text_lines['date']}\n"
    #    f"🕒 Время: {text_lines['time']}\n"
    #    f"💰 Сумма к оплате: {text_lines['total_sum']} руб."
    #)

    #await message.answer(text, parse_mode=None)
    await message.answer(f"✅ Фото чека сохранено!")


    caption = (message.caption or "").strip() # текст, если есть

    print(f'текст из сообщения - {caption}')

    parsed = parse_message_text(caption)  # например, {'amount': 305.0, 'product': 'Конфеты', 'store': 'Дикси'}

    db.add_purchase({
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name,
        **parsed
    })

    if caption:
        await message.answer(f"📸 Получено фото с подписью: {caption}\n"
                             f"✅ Покупка сохранена!\n💰 {parsed['amount']} ₽ - {parsed['product']} - ({parsed['store']})"
                             f"✅ Фото чека сохранено!")

    else:
        await message.answer("📸 Фото без подписи.")


    await save_to_sheet(message.from_user.username, parsed, photo_path=file_path)


    #if text_lines:
    #    response = "🧾 Распознанный чек:\n\n" + "\n".join(text_lines)
    #else:
    #    response = "Не удалось распознать чек 😔"

    #await message.answer(response)


@router.message(F.text)
async def process_text(message: Message):
    await message.answer(f'Обрабатываю полученное сообщение')

    text = (message.text or "").strip()  # текст, если есть

    print(f'текст из сообщения - {text}')

    parsed = parse_message_text(text)  # например, {'amount': 305.0, 'product': 'Конфеты', 'store': 'Дикси'}

    db.add_purchase({
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name,
        **parsed
    })

    await save_to_sheet(message.from_user.username, parsed)

    if text:
        await message.answer(f"✅ Покупка сохранена!\n💰 {parsed['amount']} ₽ - {parsed['product']} - ({parsed['store']})")

    else:
        await message.answer("нет текста")

