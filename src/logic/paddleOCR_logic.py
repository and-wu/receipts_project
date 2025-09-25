import os

from paddleocr import PaddleOCR
from PIL import Image, ImageEnhance, ImageOps, ImageFilter

# Папка для чеков
SAVE_DIR = "checks"
os.makedirs(SAVE_DIR, exist_ok=True)

# OCR-модель (инициализируем один раз при импорте модуля)
ocr = PaddleOCR(lang="ru")


def preprocess_image(img: Image.Image) -> Image.Image:
    """Предобработка изображения для улучшения OCR"""
    img = img.convert("L")                                      # Преобразует изображение в оттенки серого (grayscale).
    img = ImageEnhance.Contrast(img).enhance(2.0)               # Создаётся объект ImageEnhance.Contrast для регулировки контраста
    img = img.point(lambda x: 0 if x < 160 else 255, "1") # Применяется бинаризация изображения: превращаем серые пиксели в чисто черные или белые
    img = img.filter(ImageFilter.MedianFilter(size=3))          # Убирает шумы и мелкие пятна, сглаживая картинку
    return img


def save_photo(photo_file, message_id: int) -> str:
    """Сохраняем фото чека на диск и возвращаем путь"""
    file_name = os.path.join(SAVE_DIR, f"check_{message_id}.jpg")
    with open(file_name, "wb") as f:
        f.write(photo_file.getvalue())  # Получаем все байты из BytesIO
    return file_name


def process_receipt(file_path: str) -> list[str]:
    """Распознаём чек и возвращаем список строк"""
    img = Image.open(file_path)
    img = preprocess_image(img)

    processed_name = file_path.replace(".jpg", "_processed.jpg")
    img.save(processed_name)  # сохраняем улучшенный вариант

    results = ocr.ocr(img)
    print(results)
    texts = []

    if results:
        for line in results[0]:  # иногда results[0] тоже может быть пустым
            try:
                box, (text, confidence) = line
                texts.append(text)
            except Exception:
                continue

    if not texts:
        print("Текст не найден на изображении")
    else:
        print(texts)
        return [line[1][0] for line in results[0]]
