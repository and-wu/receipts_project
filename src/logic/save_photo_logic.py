import os
from aiogram.types import Message

# Папка для чеков
SAVE_DIR = "checks"
os.makedirs(SAVE_DIR, exist_ok=True)

async def save_photo(message: Message) -> str:

    # Берём фото в максимальном качестве
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)

    # Скачиваем в память
    photo_bytes = await message.bot.download_file(file.file_path, destination=None)


    """Сохраняем фото чека на диск и возвращаем путь """
    file_name = os.path.join(SAVE_DIR, f"check_{message.message_id}.jpg")
    with open(file_name, "wb") as f:
        f.write(photo_bytes.getvalue())  # Получаем все байты из BytesIO

    return file_name


