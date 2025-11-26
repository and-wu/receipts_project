import re
from src.utils.stores_and_currency import CURRENCY_MAP, STORE_KEYWORDS, PREPOSITIONS

# Компилируем регулярку один раз для производительности
CURRENCY_PATTERN = re.compile(
    r"""
    (?P<amount>\d+(?:[.,]\d+)?)    # число (целое или с дробной частью)
    \s*                             # опциональные пробелы
    (?P<currency>
        \$|usd|dollar|дол(?:л(?:ары?)?)?|  # доллары
        ₽|руб(?:л[ья])?\.?|rub|р\b|р\.|    # рубли
        br|byn|б[рп]\.?|бел\.?р            # белорусские рубли
    )?                              # валюта опциональна
    """,
    re.VERBOSE | re.IGNORECASE
)


def normalize_currency(currency_raw: str | None) -> str:
    """Нормализует валюту к стандартному виду."""
    if not currency_raw:
        return "Br"

    cur = currency_raw.lower().strip()

    for standard, variants in CURRENCY_MAP.items():
        if cur in variants:
            return standard

    return "Br"  # fallback


def extract_store(words: list[str]) -> tuple[str, list[str]]:
    """
    Извлекает название магазина из списка слов.
    Возвращает (название_магазина, оставшиеся_слова).
    """
    for i, word in enumerate(words):
        if word in STORE_KEYWORDS:
            store = word.capitalize()
            remaining_words = words[:i] + words[i + 1:]
            return store, remaining_words

    return "", words


def parse_message_text(text: str) -> dict:
    """
    Парсинг текста вида:
        "305 конфеты дикси"
        "дикси шоколадка 305"
        "конфеты в дикси 305.40 руб"
        "305.40$ дикси"
        "кока-кола 5.2 Br"
        "сыр 500 р дикси"

    Возвращает dict: amount, currency, product, store
    """
    if not text or not text.strip():
        raise ValueError("❗ Пустое сообщение")

    original = text
    text_lower = text.strip().lower()

    # 1) Ищем сумму + валюту
    amount_match = CURRENCY_PATTERN.search(text_lower)

    if not amount_match:
        raise ValueError("❗ Не удалось определить сумму в сообщении.")

    amount_str = amount_match.group("amount").replace(",", ".")

    try:
        amount = float(amount_str)
    except ValueError:
        raise ValueError(f"❗ Некорректная сумма: {amount_str}")

    currency_raw = amount_match.group("currency")
    currency = normalize_currency(currency_raw)

    # 2) Удаляем найденный блок из текста
    cleaned = text_lower[:amount_match.start()] + text_lower[amount_match.end():]
    cleaned = cleaned.strip()

    # 3) Разбиваем на слова и убираем предлоги
    words = [w for w in cleaned.split() if w and w not in PREPOSITIONS]

    if not words:
        raise ValueError(f"❗ Не удалось определить товар (исходный текст: {original})")

    # 4) Определяем магазин
    store, words = extract_store(words)

    # 5) Остаток → товар
    if not words:
        raise ValueError(f"❗ Не удалось определить товар (исходный текст: {original})")

    product = " ".join(words).strip().capitalize()

    result = {
        "amount": amount,
        "currency": currency,
        "product": product,
        "store": store or "Неизвестно"
    }

    return result
