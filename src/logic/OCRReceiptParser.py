import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime


class OCRReceiptParser:
    """
    Класс для парсинга OCR результатов чеков и преобразования их в JSON
    """

    def __init__(self):
        # Паттерны для поиска различных элементов чека
        self.price_pattern = r'(\d+[.,]\d{1,2})'
        self.quantity_pattern = r'\*(\d+[.,]\d{1,3})'
        self.date_pattern = r'(\d{1,2}\.\d{1,2}\.\d{4})'
        self.time_pattern = r'(\d{1,2}:\d{1,2}:\d{1,2})'
        self.total_pattern = r'(?:ИТОГО|итого|К ОПЛАТЕ|к оплате|ВСЕГО|всего).*?(\d+[.,]\d{1,2})'

    def parse_ocr_result(self, ocr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Основной метод для парсинга OCR данных

        Args:
            ocr_data: Словарь с результатами OCR (как в вашем примере)

        Returns:
            Структурированный словарь с данными чека
        """
        # Извлекаем тексты из OCR результата
        if isinstance(ocr_data, list) and len(ocr_data) > 0:
            texts = ocr_data[0].get('rec_texts', [])
        else:
            texts = ocr_data.get('rec_texts', [])

        if not texts:
            raise ValueError("Не найдены распознанные тексты в OCR данных")

        # Парсим основную информацию
        receipt_info = self._extract_receipt_info(texts)

        # Парсим товары
        items = self._extract_items(texts)

        # Парсим итоговую сумму
        totals = self._extract_totals(texts)

        return {
            "receipt_info": receipt_info,
            "items": items,
            "totals": totals
        }

    def _extract_receipt_info(self, texts: List[str]) -> Dict[str, str]:
        """Извлекает информацию о чеке (магазин, дата, время, кассир)"""
        info = {
            "store": "",
            "date": "",
            "time": "",
            "cashier": "",
            "receipt_number": ""
        }

        # Ищем название магазина (обычно в начале)
        for i, text in enumerate(texts[:10]):
            if len(text) > 5 and any(char.isalpha() for char in text):
                if not any(keyword in text.lower() for keyword in ['унп', 'код', 'номер', '№']):
                    info["store"] = text.strip()
                    break

        # Ищем дату и время
        for text in texts:
            date_match = re.search(self.date_pattern, text)
            if date_match:
                info["date"] = date_match.group(1)

            time_match = re.search(self.time_pattern, text)
            if time_match:
                info["time"] = time_match.group(1)

        # Ищем кассира
        for text in texts:
            if 'кассир' in text.lower() or 'касир' in text.lower():
                # Извлекаем имя после слова "кассир"
                parts = text.split()
                if len(parts) > 1:
                    info["cashier"] = " ".join(parts[1:]).split()[0:2]
                    info["cashier"] = " ".join(info["cashier"])

        # Ищем номер чека
        for text in texts:
            if 'чек' in text.lower() and ':' in text:
                parts = text.split(':')
                if len(parts) > 1:
                    info["receipt_number"] = parts[-1].strip()

        return info

    def _extract_items(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Извлекает список товаров с ценами"""
        items = []

        i = 0
        while i < len(texts):
            text = texts[i].strip()

            # Пропускаем служебные строки
            if self._is_service_line(text):
                i += 1
                continue

            # Ищем строки с ценами
            if self._has_price_pattern(text):
                item = self._parse_item_line(text)
                if item:
                    # Ищем название товара в предыдущих строках
                    item_name = self._find_item_name(texts, i)
                    if item_name:
                        item["name"] = item_name
                        items.append(item)

            i += 1

        return items

    def _is_service_line(self, text: str) -> bool:
        """Проверяет, является ли строка служебной информацией"""
        service_keywords = [
            'итого', 'всего', 'к оплате', 'банк', 'карт', 'касс',
            'чек', 'унп', 'адрес', 'телефон', 'спасибо', 'приход'
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in service_keywords)

    def _has_price_pattern(self, text: str) -> bool:
        """Проверяет, содержит ли строка паттерн цены"""
        # Ищем паттерн: цена *количество итого
        pattern = r'\d+[.,]\d{1,2}\s*\*\d+[.,]\d{1,3}\s*\d+[.,]\d{1,2}'
        return bool(re.search(pattern, text))

    def _parse_item_line(self, text: str) -> Optional[Dict[str, Any]]:
        """Парсит строку с информацией о товаре"""
        # Паттерн: price *quantity total
        pattern = r'(\d+[.,]\d{1,2})\s*\*(\d+[.,]\d{1,3})\s*(\d+[.,]\d{1,2})'
        match = re.search(pattern, text)

        if match:
            price_str = match.group(1).replace(',', '.')
            quantity_str = match.group(2).replace(',', '.')
            total_str = match.group(3).replace(',', '.')

            try:
                return {
                    "name": "",  # Будет заполнено позже
                    "price": float(price_str),
                    "quantity": float(quantity_str),
                    "total": float(total_str)
                }
            except ValueError:
                return None

        return None

    def _find_item_name(self, texts: List[str], current_index: int) -> str:
        """Находит название товара, просматривая предыдущие строки"""
        # Ищем название товара в предыдущих 1-3 строках
        for j in range(max(0, current_index - 3), current_index):
            candidate = texts[j].strip()

            # Пропускаем строки с кодами товаров
            if self._is_product_code(candidate):
                continue

            # Пропускаем служебные строки
            if self._is_service_line(candidate):
                continue

            # Пропускаем строки только с числами
            if candidate.isdigit():
                continue

            # Если строка содержит буквы и выглядит как название товара
            if len(candidate) > 2 and any(char.isalpha() for char in candidate):
                return candidate

        return "Товар без названия"

    def _is_product_code(self, text: str) -> bool:
        """Проверяет, является ли строка кодом товара"""
        # Коды товаров обычно начинаются с [M] или содержат много цифр
        if text.startswith('[M]') or text.startswith('M]'):
            return True

        # Или содержат преимущественно цифры
        digit_count = sum(1 for char in text if char.isdigit())
        return digit_count > len(text) * 0.7

    def _extract_totals(self, texts: List[str]) -> Dict[str, Any]:
        """Извлекает итоговые суммы"""
        totals = {
            "subtotal": 0.0,
            "total_to_pay": 0.0,
            "payment_method": ""
        }

        # Ищем общую сумму
        for text in texts:
            # Ищем строку с итоговой суммой
            total_match = re.search(self.total_pattern, text, re.IGNORECASE)
            if total_match:
                total_str = total_match.group(1).replace(',', '.')
                try:
                    total_amount = float(total_str)
                    totals["subtotal"] = total_amount
                    totals["total_to_pay"] = total_amount
                except ValueError:
                    continue

            # Ищем способ оплаты
            if 'банк' in text.lower() and ('карт' in text.lower() or 'пл' in text.lower()):
                totals["payment_method"] = "банковская карта"
            elif 'наличн' in text.lower():
                totals["payment_method"] = "наличные"

        return totals



    def parse_and_save(self, ocr_data: Dict[str, Any], output_file: str) -> Dict[str, Any]:
        """Парсит OCR данные и сохраняет в файл"""
        parsed_data = self.parse_ocr_result(ocr_data)
        self.save_to_json(parsed_data, output_file)
        return parsed_data
