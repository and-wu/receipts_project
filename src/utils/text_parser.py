import re

def parse_message_text(text: str) -> dict:
    """
    Разбирает сообщение с суммой, товаром и магазином в любом порядке.
    Примеры допустимых форматов:
      - "305 конфеты дикси"
      - "дикси шоколадка 305"
      - "305р конфеты в дикси"
      - "конфеты в дикси 305.50 руб"

    Возвращает:
      {
          "amount": float,
          "product": str,
          "store": str
      }
    """
    text = text.strip().lower()

    # 🔹 1. Находим сумму (число с точкой или запятой, возможно с "р", "руб", "byn")
    amount_match = re.search(r'(\d+[.,]?\d*)\s*(р|руб|byn|бел|бел\.р)?', text)
    if not amount_match:
        raise ValueError("❗ Не удалось определить сумму в сообщении.")

    amount_str = amount_match.group(1).replace(',', '.')
    amount = float(amount_str)

    # Убираем сумму из текста, чтобы не мешала остальным частям
    cleaned_text = text.replace(amount_match.group(0), '').strip()

    print(f'сумма - {amount}, строка без суммы - {cleaned_text}')

    # 🔹 2. Ищем возможное название магазина
    store_keywords = [
        "дикси", "евроопт", "соседи", "виталюр", "магнит", "пятерочка", "белмаркет",
        "светофор", "алми", "green", "prostore", "супермаркет", "market", "перекресток",
        "вкусвилл", "топливо", "заправка"
    ]

    store = ""
    for keyword in store_keywords:
        if keyword in cleaned_text:
            store = keyword.capitalize()
            cleaned_text = cleaned_text.replace(keyword, '').strip()
            break

    print(f'магазин - {store}, строка без суммы и магазина - {cleaned_text}')

    # 🔹 3. Остальное — это товар
    product = cleaned_text.strip()
    if not product:
        raise ValueError("❗ Не удалось определить название товара.")

    print(f'товар - {product}')


    return {
        "amount": amount,
        "product": product.capitalize(),
        "store": store or "Неизвестно"
    }
