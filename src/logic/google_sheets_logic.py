import json
import os
from asyncio.log import logger
import asyncio
import gspread
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

from config_data.config import GOOGLE_SERVICE_ACCOUNT_JSON
from src.logic.save_sheets_logic import USER_SHEETS

# Загружаем переменные из .env
load_dotenv()


# Подключение к Google Sheets
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]


# Читаем JSON из переменной окружения
key_data = GOOGLE_SERVICE_ACCOUNT_JSON
if not key_data:
    raise ValueError("Не найдена переменная окружения GOOGLE_SERVICE_ACCOUNT_JSON")


# Создаём credentials из словаря
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(key_data), scope)
#creds = ServiceAccountCredentials.from_json_keyfile_name("receipts-sheet-d1198145dbde.json", scope)
client = gspread.authorize(creds)

# Открываем таблицу
sheet = client.open("receipts_sheets").sheet1  # можно по ID, если нужно


async def save_to_sheet(username: str, user_id: str, data: dict, photo_path: str | None = None) -> bool:
    """
    Сохраняет запись в Google Sheets для конкретного пользователя.
    Таблица выбирается из user_sheets.json по user_id
    """
    print(f'username - {username}, user_id - {user_id}')
    try:
        # 🔍 Проверяем, есть ли таблица для этого пользователя
        if user_id not in USER_SHEETS:
            return False, "❌ Для этого пользователя нет связанной Google-таблицы."

        sheet_link = USER_SHEETS[user_id]

        try:
            # 🔗 Открываем таблицу по ссылке
            spreadsheet = client.open_by_url(sheet_link)
            sheet = spreadsheet.sheet1
        except Exception as e:
            return False, f"❌ Не удалось открыть таблицу: {e}"

        # Валидация данных
        required_fields = ["product", "amount", "store", "currency"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            return False, f"❌ Отсутствуют поля: {', '.join(missing)}"

        # Формируем строку
        now = datetime.now()
        row = [
            now.strftime("%d.%m.%Y"),   # Дата
            now.strftime("%H:%M"),      # Время
            username,                   # Пользователь
            str(data["product"]),       # Товар
            data["amount"],             # Сумма
            data["currency"],           # Валюта
            str(data["store"]),         # Магазин
            photo_path if photo_path else "нет фото"
        ]

        # Запись в Google Sheets
        await asyncio.to_thread(sheet.append_row, row)

        print("Запись добавлена ✅")
        return True

    except Exception as e:
        logger.error(f"Error saving to sheet: {e}", exc_info=True)
        return False, f"❌ Ошибка записи: {str(e)}"