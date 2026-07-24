# -*- coding: utf-8 -*-
"""
Парсер вкладки iCracked "АКБ iPhone" (весь лист, включно з блоком
"АКБ / БАНКИ" нижче — це та сама вкладка, дві різні таблиці одна під одною).

Підхід: шукаємо рядки-заголовки за наявністю "Серія"/"Модель" в сусідніх
колонках, зчитуємо назви цінових колонок з цього ж рядка (і, за потреби,
з рядка над ним — у iCracked заголовок цінового блоку двухрівневий),
далі йдемо по рядках до наступного заголовка/розділу.
"""
import re

from normalize import extract_iphone_model, parse_price_to_float

SUPPLIER = "icracked"

COLUMN_KLAS_KEYWORDS = [
    (r"genuine|оригінальн", "АКБ з калібруванням"),
    (r"з\s*контролер|калібру", "АКБ з калібруванням"),
    (r"банка|без\s*контрол", "АКБ без калібрування"),
    (r"tag-?on|шлейф", "Шлейф акумулятора"),
    (r"посилен|стандарт|АКБ", "АКБ без калібрування"),
]


def _guess_column_klas(header_text: str):
    """Повертає канонічний Клас лише якщо впізнали ключове слово в заголовку
    колонки — БЕЗ широкого дефолту. Раніше будь-яка нерозпізнана колонка
    (навіть "Рік"/"Номер моделі" з таблиці iPad) отримувала клас "АКБ без
    калібрування" за замовчуванням, що засмічувало матчинг."""
    if not header_text:
        return None
    text = header_text.lower()
    for pattern, canon in COLUMN_KLAS_KEYWORDS:
        if re.search(pattern, text):
            return canon
    return None


def _row_cells(df, i):
    row = df.iloc[i]
    return [str(c) if c is not None and str(c) != "nan" else "" for c in row.tolist()]


def _find_table_starts(df):
    """Знаходить рядки-заголовки "Серія|Модель" ТА перевіряє, що це справді
    таблиця iPhone (значення в колонці "Серія" містять слово "Серія" —
    напр. "15 Серія"), а не таблиця iPad/MacBook з такою самою назвою
    заголовків, але іншим змістом (напр. "Pro 12,9")."""
    starts = []
    for i in range(len(df)):
        cells = _row_cells(df, i)
        for j in range(len(cells) - 1):
            if cells[j].strip() == "Серія" and "Модель" in cells[j + 1]:
                # перевіряємо кілька наступних рядків на слово "Серія" в значеннях
                looks_like_iphone_table = False
                for r in range(i + 1, min(i + 6, len(df))):
                    peek = _row_cells(df, r)
                    if j < len(peek) and "Серія" in peek[j]:
                        looks_like_iphone_table = True
                        break
                if looks_like_iphone_table:
                    starts.append((i, j))
                break
    return starts


def parse(df, currency="USD"):
    records = []
    starts = _find_table_starts(df)
    for idx, (header_row, series_col) in enumerate(starts):
        model_col = series_col + 1
        header_cells = _row_cells(df, header_row)
        upper_cells = _row_cells(df, header_row - 1) if header_row > 0 else []

        price_cols = []
        for c in range(model_col + 1, len(header_cells)):
            label = header_cells[c].strip()
            if label in ("Модель", "Серія"):
                continue
            combined_label = (upper_cells[c].strip() if c < len(upper_cells) else "") + " " + label
            combined_label = re.sub(r"\s+", " ", combined_label).strip()
            klas = _guess_column_klas(combined_label)
            if klas is None:
                continue  # нерозпізнана колонка — пропускаємо, не вигадуємо клас
            price_cols.append((c, klas, combined_label))

        next_header_row = starts[idx + 1][0] if idx + 1 < len(starts) else len(df)
        series = None
        for r in range(header_row + 1, next_header_row):
            cells = _row_cells(df, r)
            if len(cells) <= model_col:
                continue
            if cells[series_col].strip():
                series = cells[series_col].strip()
            model_raw = cells[model_col].strip()
            if not model_raw:
                continue
            canon_model = extract_iphone_model(model_raw)
            if not canon_model:
                continue
            for c, klas, label in price_cols:
                if c >= len(cells):
                    continue
                price = parse_price_to_float(cells[c])
                if price is None:
                    continue
                records.append({
                    "supplier": SUPPLIER,
                    "device_model": canon_model,
                    "series_raw": series,
                    "klas": klas,
                    "variant_label": label,
                    "price": price,
                    "currency": currency,
                })
    return records
