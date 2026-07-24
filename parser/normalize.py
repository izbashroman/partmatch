# -*- coding: utf-8 -*-
"""
Нормалізація "брудних" назв моделей і типів деталей у постачальників
до єдиного вигляду, що збігається з полем "Коротка назва бази пристрою"
та "Клас" у внутрішньому каталозі (Geckon).

Це серце матчингу: постачальники пишуть "15ProMax", "15 Pro Max",
"iPhone 15 Pro Max" по-різному — все зводимо до одного канонічного рядка.
"""
import re

# Канонічний список моделей iPhone (порядок важливий — довші назви раніше,
# щоб "15 Pro Max" не матчився як "15 Pro").
IPHONE_MODELS = [
    "17 Pro Max", "17 Pro", "17 Air", "17",
    "16 Pro Max", "16 Pro", "16 Plus", "16",
    "15 Pro Max", "15 Pro", "15 Plus", "15",
    "14 Pro Max", "14 Pro", "14 Plus", "14",
    "13 Pro Max", "13 Pro", "13 Mini", "13",
    "12 Pro Max", "12 Pro", "12 Mini", "12",
    "11 Pro Max", "11 Pro", "11",
    "SE 3 (2022)", "SE 2 (2020)", "SE",
    "XS Max", "XS", "XR", "X",
    "8 Plus", "8",
    "7 Plus", "7",
    "6S Plus", "6 Plus", "6S", "6",
    "5S", "5SE",
]

# Аліаси / скорочення, що трапляються у постачальників -> канонічна форма
MODEL_ALIASES = {
    "PROMAX": "PRO MAX",
    "PRO MAX": "PRO MAX",
    "PLUS": "PLUS",
    "MINI": "MINI",
}


def _squash(s: str) -> str:
    """Прибирає зайві пробіли, приводить до верхнього регістру, унормовує PROMAX->PRO MAX."""
    s = s.upper().strip()
    s = re.sub(r"\s+", " ", s)
    # "13PROMAX" / "13 PROMAX" -> "13 PRO MAX"
    s = re.sub(r"(\d)\s*PRO\s*MAX", r"\1 PRO MAX", s)
    s = re.sub(r"(\d)\s*PROMAX", r"\1 PRO MAX", s)
    s = re.sub(r"(\d)\s*PRO(?!\s*MAX)", r"\1 PRO", s)
    s = re.sub(r"(\d)\s*PLUS", r"\1 PLUS", s)
    s = re.sub(r"(\d)\s*MINI", r"\1 MINI", s)
    return s.strip()


def _find_model_token(s: str, cand: str):
    """
    Шукає cand (напр. "12", "12 PRO") в s як окремий токен, а не будь-де
    в середині числа/слова. Захищає від хибних збігів типу:
    - "PRO 12,9" (iPad) не повинно матчитись як iPhone "12"
    - "AIR 11'" (MacBook) не повинно матчитись як iPhone "11"
    - "IS900" не повинно матчитись як Galaxy "S9"
    - "12мм" (розмір) не повинно матчитись як iPhone "12"
    """
    pattern = r"(?<![\w.,])" + re.escape(cand) + r"(?![\w.,'’])"
    return re.search(pattern, s) is not None


def extract_iphone_model(raw: str):
    """
    Витягує канонічну модель iPhone з довільного рядка постачальника.
    Повертає рядок виду "IPHONE 15 PRO MAX" (без слова Apple), або None.
    """
    if not raw:
        return None
    s = _squash(raw)
    s = s.replace("APPLE", "").replace("IPHONE", "").strip()
    for model in sorted(IPHONE_MODELS, key=len, reverse=True):
        cand = _squash(model)
        if _find_model_token(s, cand):
            return f"IPHONE {cand}"
    return None


def catalog_device_key(raw: str):
    """
    Нормалізує поле каталогу "Коротка назва бази пристрою"
    (напр. 'Apple IPhone 13 Pro') до того самого канонічного вигляду.
    """
    return extract_device_model(raw)


# Мінімальний список моделей Samsung Galaxy / AirPods / MacBook для
# розпізнавання у вільному тексті постачальників (OCAPRO, REFparts тощо).
# Список неповний навмисно — легко розширювати додаванням рядків.
GALAXY_MODELS = [
    "NOTE 20 ULTRA", "NOTE 20U", "NOTE 20", "NOTE 10 PLUS", "NOTE 10", "NOTE 9", "NOTE 8",
    "S23 ULTRA", "S22 ULTRA", "S21 ULTRA", "S20 ULTRA",
    "S23 PLUS", "S22 PLUS", "S21 PLUS", "S20 PLUS",
    "S23", "S22", "S21", "S20", "S10 PLUS", "S10", "S9 PLUS", "S9", "S8 PLUS", "S8",
    "A50", "A80", "A90",
]

AIRPODS_MODELS = [
    "AIRPODS PRO 2", "AIRPODS PRO", "AIRPODS 3", "AIRPODS 1", "AIRPODS 2", "AIRPODS",
]

MACBOOK_MODELS = [
    "AIR 11", "AIR 13", "AIR 15", "PRO 13", "PRO 14", "PRO 15", "PRO 16",
]


def extract_device_model(raw: str):
    """Розширений екстрактор: спершу пробує iPhone, потім Galaxy/AirPods/MacBook.

    ВАЖЛИВО: це "вільний" режим без вимоги бренд-ключового слова —
    підходить лише коли модель береться зі СПЕЦІАЛЬНО відведеної колонки
    "Модель" (матричні парсери icracked/levelparts, де в колонці завідомо
    лежить тільки модель пристрою). Для вільного тексту (назва товару, що
    може містити будь-які числа — розміри, кількість, номери каталогу)
    використовуй extract_device_model_strict нижче — інакше "11 шт" чи
    "12мм" будуть хибно розпізнані як iPhone 11/12.
    """
    if not raw:
        return None
    iphone = extract_iphone_model(raw)
    if iphone:
        return iphone
    s = _squash(raw)
    for model in sorted(GALAXY_MODELS, key=len, reverse=True):
        if _find_model_token(s, model):
            return f"GALAXY {model}"
    for model in sorted(AIRPODS_MODELS, key=len, reverse=True):
        if _find_model_token(s, model):
            return model
    for model in sorted(MACBOOK_MODELS, key=len, reverse=True):
        if _find_model_token(s, model):
            return f"MACBOOK {model}"
    return None


# Ключові слова бренду, наявність яких у тексті потрібна для visнання
# моделі у ВІЛЬНОМУ тексті (назви товарів постачальників). Без цієї
# перевірки будь-яке число в описі (розмір, кількість, номер SKU)
# ризикує хибно зматчитись з моделлю пристрою.
_BRAND_KEYWORDS = {
    "iphone": re.compile(r"\bIPHONE\b", re.IGNORECASE),
    "galaxy": re.compile(r"\bGALAXY\b", re.IGNORECASE),
    "airpods": re.compile(r"\bAIRPODS\b", re.IGNORECASE),
    "macbook": re.compile(r"\bMACBOOK\b", re.IGNORECASE),
}


def extract_device_model_strict(raw: str):
    """Те саме, що extract_device_model, але повертає результат лише якщо
    у вихідному тексті справді присутнє відповідне бренд-слово ("iPhone",
    "Galaxy", "AirPods", "MacBook") — а не просто випадковий збіг числа.
    Використовуй це для вільнотекстових прайсів (OCAPRO/REFparts/UParts),
    де числа в назві товару часто означають розмір/кількість, а не модель.
    """
    if not raw:
        return None
    model = extract_device_model(raw)
    if not model:
        return None
    if model.startswith("IPHONE") and not _BRAND_KEYWORDS["iphone"].search(raw):
        return None
    if model.startswith("GALAXY") and not _BRAND_KEYWORDS["galaxy"].search(raw):
        return None
    if model.startswith("AIRPODS") and not _BRAND_KEYWORDS["airpods"].search(raw):
        return None
    if model.startswith("MACBOOK") and not _BRAND_KEYWORDS["macbook"].search(raw):
        return None
    return model


# ---- Класи деталей -------------------------------------------------------
# Мапа: (тип деталі за змістом опису постачальника) -> канонічний "Клас"
# зі стовпця каталогу. Ключі — regex-паттерни (case-insensitive) для
# пошуку в сирому описі позиції постачальника.
PART_CLASS_RULES = [
    # СПЕЦИФІЧНІ правила йдуть ПЕРШИМИ навмисно: широке правило
    # "battery|акб|акумулятор" нижче зловило б і "Проклейка акумулятора"
    # (клей, не батарея), і "Шлейф акумулятора" (шлейф, не сама батарея),
    # якби стояло раніше них.
    (r"шлейф\s*акумулятор|tag-?on", "Шлейф акумулятора"),
    (r"проклейк|adhesive(?!.*батар)|скотч|клей|герметик|праймер|лент[а-я]*\s*для\s*ізоляц|стрічк[а-я]*\s*ізоляц", "Витратні матеріали для монтажу"),
    (r"захисн\w*\s*скло|захисн\w*\s*плівк|захисна\s*плівка", "Плівка дисплею смартфону захисна"),
    (r"\bбанк[а-я]*\b", "АКБ без калібрування"),  # "банка" сама по собі = без контролера
    (r"акб.*без\s*контрол", "АКБ без калібрування"),
    (r"акб.*(з\s*контрол|з\s*калібр|калібру)", "АКБ з калібруванням"),
    (r"battery|акб|акумулятор", "АКБ з калібруванням"),  # дефолт для АКБ, якщо тип не вказано явно
    (r"дисплейн\w*\s*модул|LCD.*touch|дисплей", "Дисплейний модуль"),
    (r"скло\s*дисплея|скло\+оса|скло\s*\+\s*оса|стекло.*дисплея", "Скло дисплейного модулю"),
    (r"рамка\s*дисплея", "Рамка дисплейного модулю"),
    (r"корпус.*в\s*зборі|корпус.*sim", "Корпус смартфону в зборі"),
    (r"кришка\s*корпус|задня\s*кришка|housing", "Кришка корпусу задня без обвісу"),
    (r"скло\s*основної\s*камери|скло\s*камери", "Комплект скла основної камери"),
    (r"камера\s*основна", "Камера основна без лідару"),
    (r"камера\s*фронтальн", "Камера фронтальна без FaceID"),
    (r"леза|лопатк|відвертк|отвертк|пінцет|пинцет|викрутк|кусачк", "Інструменти"),
    (r"трафарет", "Трафарет"),
]


def guess_part_class(description: str):
    """Пробує вгадати канонічний Клас за текстовим описом позиції постачальника."""
    if not description:
        return None
    text = description.lower()
    for pattern, canon in PART_CLASS_RULES:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return canon
    return None


def parse_price_to_float(raw):
    """
    '19$' / '19,5$' / '4823,000' / '3,7' -> float, або None якщо не число.

    ВАЖЛИВО: бере лише ПЕРШЕ число в рядку, а не всі цифри підряд.
    Комірки на кшталт '🔄 18$ 💪🏼🍏 (+367 mAh 🔝8%)' містять кілька чисел
    (ціна, ємність акумулятора, відсоток) — старий код склеював їх в одне
    число ("18" + "367" + "8" -> 183678), новий бере тільки перше ("18").
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s in ("-", "—", ""):
        return None
    # перше число: послідовність цифр з опційною десятковою частиною через , або .
    m = re.search(r"-?\d+(?:[.,]\d+)?", s)
    if not m:
        return None
    num = m.group(0).replace(",", ".")
    try:
        return float(num)
    except ValueError:
        return None
