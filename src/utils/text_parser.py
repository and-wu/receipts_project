import re

def parse_message_text(text: str) -> dict:
    """
    Разбор текста вида:
      "305 конфеты дикси"
      "дикси шоколадка 305"
      "конфеты в дикси 305.40 руб"

    Возвращает словарь с:
      amount, product, store
    """

    original = text
    text = text.strip().lower()

    # =====================================
    # 1) Ищем сумму
    # =====================================
    money_pattern = r'(\d+[.,]?\d*)\s*(?:р|руб|byn|bel|бел|бел\.р|р\.|руб\.)?'
    amount_match = re.search(money_pattern, text)

    if not amount_match:
        raise ValueError("❗ Не удалось определить сумму в сообщении.")

    amount_str = amount_match.group(1).replace(",", ".")
    amount = float(amount_str)

    # Удаляем сумму из текста
    cleaned = text.replace(amount_match.group(0), "").strip()

    # =====================================
    # 2) Поиск магазина по слову целиком
    # =====================================
    store_keywords = [
        "дикси", "евроопт", "соседи", "виталюр", "магнит", "пятерочка", "белмаркет",
        "светофор", "алми", "green", "prostore", "супермаркет", "market",
        "перекресток", "вкусвилл", "заправка", "топливо"
    ]

    store = ""

    # Ищем магазин как отдельное слово
    words = cleaned.split()

    for w in words:
        if w in store_keywords:
            store = w.capitalize()
            words.remove(w)        # удаляем магазин из запроса
            break

    # =====================================
    # 3) Очищаем мусор ("в", "на", "из")
    # =====================================
    prepositions = {"в", "во", "на", "из", "по", "за"}
    words = [w for w in words if w not in prepositions]

    # =====================================
    # 4) Остаток — это товар
    # =====================================
    if not words:
        raise ValueError(f"❗ Не удалось определить товар (исходный текст: {original})")

    product = " ".join(words).strip().capitalize()

    # =====================================
    # 5) Формируем результат
    # =====================================
    return {
        "amount": amount,
        "product": product,
        "store": store or "Неизвестно"
    }
