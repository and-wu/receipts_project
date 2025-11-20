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

        print("вот текст перед парсингом", texts)

        # Парсим основную информацию
        receipt_info = self._extract_receipt_info(texts)
        print("спарсили основную информацию", receipt_info)

        # Парсим товары
        items = self._extract_items(texts)
        print("спарсили товары", items)

        # Парсим итоговую сумму
        totals = self._extract_totals(texts)
        print("спарсили итоговую сумму", totals)

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
        # Возможные стоп-слова
        stop_words = ["унп", "код", "номер", "чек", "касса", "итого", "сумма", "пратекный"]

        # Ключевые слова, характерные для магазинов
        store_keywords = ["ооо", "зао", "ип", "магазин", "супермаркет", "универсам", "market"]

        candidate = ""
        for text in texts[:10]:  # смотрим только первые 10 строк
            clean = text.strip()
            lower = clean.lower()

            if len(clean) < 3:  # слишком короткие строки пропускаем
                continue
            if sum(c.isdigit() for c in clean) > len(clean) / 2:  # если больше половины цифр
                continue
            if any(word in lower for word in stop_words):
                continue

            # если есть ключевое слово - почти наверняка магазин
            if any(word in lower for word in store_keywords):
                info["store"] = clean
                return info

            # сохраняем как кандидата, если строка длиннее
            if len(clean) > len(candidate):
                candidate = clean

        info["store"] = candidate


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
                    info["cashier"] = " ".join(parts[1:3])
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
        """Извлекает итоговые суммы с учётом скидок"""
        totals = {
            "subtotal": 0.0,  # до скидки (если есть)
            "total_to_pay": 0.0,  # окончательная сумма к оплате
            "payment_method": ""
        }

        all_amounts = []  # все найденные суммы
        subtotal_candidates = []  # промежуточные (ИТОГО, ВСЕГО)
        final_candidates = []  # финальные (К ОПЛАТЕ, TOTAL, ИТОГО К ОПЛАТЕ)

        for text in texts:
            # Ищем суммы
            total_match = re.findall(r'(\d+[.,]\d{1,2})', text)
            if total_match:
                for raw in total_match:
                    try:
                        amount = float(raw.replace(',', '.'))
                    except ValueError:
                        continue

                    all_amounts.append(amount)

                    text_lower = text.lower()
                    # Если это явная финальная сумма
                    if any(kw in text_lower for kw in ["к оплате", "total", "итого к оплате"]):
                        final_candidates.append(amount)
                    # Если это просто "ИТОГО" или "ВСЕГО"
                    elif any(kw in text_lower for kw in ["итого", "всего", "subtotal"]):
                        subtotal_candidates.append(amount)

            # Определяем способ оплаты
            if 'банк' in text.lower() and ('карт' in text.lower() or 'пл' in text.lower()):
                totals["payment_method"] = "банковская карта"
            elif 'наличн' in text.lower():
                totals["payment_method"] = "наличные"

        # Выбираем сумму
        if final_candidates:
            totals["total_to_pay"] = min(final_candidates)  # к оплате обычно меньше
        elif subtotal_candidates:
            totals["total_to_pay"] = max(subtotal_candidates)  # если нет "к оплате", берём максимум
        elif all_amounts:
            totals["total_to_pay"] = max(all_amounts)

        # Определяем subtotal (до скидок) — берём максимум
        if subtotal_candidates:
            totals["subtotal"] = max(subtotal_candidates)
        else:
            totals["subtotal"] = totals["total_to_pay"]

        return totals


    def save_to_json(self, parsed_data: Dict[str, Any], filename: str) -> None:
        """Сохраняет данные в JSON файл"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)


    def parse_and_save(self, ocr_data: Dict[str, Any], output_file: str) -> Dict[str, Any]:
        """Парсит OCR данные и сохраняет в файл"""
        parsed_data = self.parse_ocr_result(ocr_data)
        self.save_to_json(parsed_data, output_file)
        return parsed_data
