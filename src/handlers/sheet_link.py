from aiogram import Router
from aiogram.dispatcher import router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.handlers.commands import UserSheetState
from src.logic.save_sheets_logic import USER_SHEETS, save_user_sheets


router = Router()

@router.message(UserSheetState.waiting_for_sheet_link)
async def process_sheet_link(message: Message, state: FSMContext):
    username = str(message.from_user.id)
    link = message.text.strip()

    # Минимальная проверка
    if not link.startswith("http"):
        await message.answer("❌ Это не похоже на ссылку. Попробуй ещё раз.")
        return

    # Сохраняем в JSON
    USER_SHEETS[username] = link
    save_user_sheets(USER_SHEETS)

    await message.answer(
        "✅ Отлично! Я сохранил твою таблицу.\n"
        "теперь отправь мне информацию о твоей покупки, и я сохраню все в гугл-таблицу.\n"
        "жду инфу в таком формате - товар магазин сумма\n"
        "например - 'продукты дикси 780' или 'топливо 900 заправка'\n"
        "также можешь приложить фото чека и я сохраню его"
    )

    await state.clear()
