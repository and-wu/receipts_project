from asyncio.log import logger
import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Подключение к Google Sheets
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("receipts-sheet-d1198145dbde.json", scope)
client = gspread.authorize(creds)

# Открываем таблицу
sheet = client.open("receipts_sheets").sheet1  # можно по ID, если нужно


async def save_to_sheet(user_name: str, data: dict, photo_path: str | None = None) -> bool:
    """
    Сохраняет запись о покупке в Google Таблицу

    Args:
        user_name: имя пользователя
        data: словарь с ключами amount, product, store
        photo_path: путь к файлу чека (на диске)

    Returns:
        bool
    """
    try:
        # Валидация
        required_fields = ["product", "amount", "store"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            return False, f"❌ Отсутствуют поля: {', '.join(missing)}"

        # Подготовка данных
        now = datetime.now()
        row = [
            now.strftime("%d.%m.%Y"),
            now.strftime("%H:%M"),
            user_name,
            str(data["product"]),
            data["amount"],  # оставляем как число
            str(data["store"]),
            photo_path if photo_path else "нет фото"  # путь к фото чека
        ]

        # Запись в таблицу
        await asyncio.to_thread(sheet.append_row, row)

        print("Запись добавлена ✅")
        return True

    except Exception as e:
        logger.error(f"Error saving to sheet: {e}", exc_info=True)
        print(f"❌ Ошибка записи: {str(e)}")