from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from ..logic.db_logic import Database
from ..logic.save_photo_logic import save_photo
from ..logic.save_sheets_logic import USER_SHEETS
from ..utils.text_parser import parse_message_text
from ..logic.google_sheets_logic import save_to_sheet
from aiogram.fsm.state import State, StatesGroup

router = Router()

db = Database()


class UserSheetState(StatesGroup):
    waiting_for_sheet_link = State()


# Обработчик команды /start
@router.message(CommandStart())
async def send_welcome(message: Message, state: FSMContext):
    username = str(message.from_user.id)

    # Проверяем, есть ли пользователь в JSON
    if username in USER_SHEETS:
        await message.answer(
            "Привет! 😊\n"
            "Я бот, который ведет учет твоих расходом!\n"
            "Отправь мне информацию о твоей покупки, и я сохраню все в гугл-таблицу.\n"
            "жду инфу в таком формате - товар магазин сумма\n"
            "например - 'продукты дикси 780' или 'топливо 900 заправка'\n"
            "также можешь приложить фото чека и я сохраню его"
        )
        return

    # Если пользователя нет → просим отправить ссылку
    await message.answer(
        "👋 Привет! Похоже, ты тут впервые.\n\n"
        "Чтобы я мог сохранять данные в твою Google-таблицу, пришли мне, пожалуйста, ссылку на неё.\n\n"
        "📌 Формат: ссылка на Google Sheets с правами *редактирования*."
    )

    # Устанавливаем состояние
    await state.set_state(UserSheetState.waiting_for_sheet_link)


@router.message(Command("help"))
async def send_help(message: Message):
    await message.answer(f"я бот который ведет учет твоих расходом")


@router.message(F.photo)
async def process_photo(message: Message):
    await message.answer(f'Обрабатываю полученное фото')

    # Сохраняем фото на диск
    file_path = await save_photo(message)

    print(f'фото сохранилось сюда {file_path}')

    await message.answer(f"✅ Фото чека сохранено!")





    caption = (message.caption or "").strip() # текст, если есть

    print(f'текст из сообщения - {caption}')

    try:
        parsed = parse_message_text(caption)  # например, {'amount': 305.0, 'product': 'Конфеты', 'store': 'Дикси'}
        await message.answer(f"Ок! Ты купил {parsed['product']} за {parsed['amount']} в {parsed['store']}")

        db.add_purchase({
            "user_id": message.from_user.id,
            "username": message.from_user.username,
            "first_name": message.from_user.first_name,
            "last_name": message.from_user.last_name,
            **parsed
        })
    except ValueError as e:
        print(str(e))


    if caption:
        await message.answer(f"📸 Получено фото с подписью: {caption}\n"
                             f"✅ Покупка сохранена!\n💰 {parsed['amount']} ₽ - {parsed['product']} - ({parsed['store']})"
                             f"✅ Фото чека сохранено!")

    else:
        await message.answer("📸 Фото без подписи.")


    await save_to_sheet(message.from_user.username, parsed, photo_path=file_path)


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

    username = str(message.from_user.id)
    user_id = str(message.from_user.id)
    await save_to_sheet(username, user_id, parsed)

    if text:
        await message.answer(f"✅ Покупка сохранена!\n💰 {parsed['amount']} ₽ - {parsed['product']} - ({parsed['store']})")

    else:
        await message.answer("нет текста")

