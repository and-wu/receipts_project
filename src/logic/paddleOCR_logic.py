import json
import os

import numpy as np
from paddleocr import PaddleOCR
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
from src.logic.OCRReceiptParser import OCRReceiptParser

# Папка для чеков
SAVE_DIR = "checks"
os.makedirs(SAVE_DIR, exist_ok=True)

# OCR-модель (инициализируем один раз при импорте модуля)
ocr = PaddleOCR(lang="ru")


def preprocess_image(img: Image.Image) -> Image.Image:
    """Предобработка изображения для улучшения OCR"""
    img = img.convert("L")                                      # Преобразует изображение в оттенки серого (grayscale).
    img = ImageEnhance.Contrast(img).enhance(1.5)               # Создаётся объект ImageEnhance.Contrast для регулировки контраста
    # img = img.point(lambda x: 0 if x < 160 else 255, "1") # Применяется бинаризация изображения: превращаем серые пиксели в чисто черные или белые
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
    try:
        img = Image.open(file_path)

        # Сначала попробуем без предобработки
        img_array = np.array(img)
        results = ocr.ocr(img_array)


        if not results or not results[0]:
            print("Попробуем с предобработкой...")
            # Если не получилось, применяем предобработку
            img = preprocess_image(img)
            processed_name = file_path.replace(".jpg", "_processed.jpg")
            img.save(processed_name)

            img_array = np.array(img)
            results = ocr.ocr(img_array)

        print("OCR Results:", results)


        parser = OCRReceiptParser()

        info_for_answer = {}

        try:
            # Парсим данные
            result = parser.parse_ocr_result(results)

            info_for_answer["date"] = result["receipt_info"]["date"]
            info_for_answer["time"] = result["receipt_info"]["time"]
            info_for_answer["total_sum"] = result["totals"]["total_to_pay"]

            # Выводим результат
            print("Результат парсинга:")
            print(json.dumps(result, ensure_ascii=False, indent=2))

            # Сохраняем в файл
            parser.save_to_json(result, f"{file_path}_receipt.json")
            print(f"\nДанные сохранены в файл {file_path}_receipt.json")

        except Exception as e:
            print(f"Ошибка при парсинге: {e}")

        return info_for_answer

        texts = []


        if results and "rec_texts" in results[0]:
            rec_texts = results[0]["rec_texts"]
            rec_scores = results[0]["rec_scores"]

            for text, confidence in zip(rec_texts, rec_scores):
                print("text:", text, "| confidence:", confidence)
                texts.append(text)

        if not texts:
            print("Текст не найден на изображении")
        else:
            print("Распознанные строки:", texts)
            return texts

    except Exception as e:
        print(f"Ошибка обработки файла {file_path}: {e}")
        return []
