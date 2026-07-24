# -*- coding: utf-8 -*-
"""
Парсер внутрішнього каталогу "01. Catalogs (Geckon)".

Не прив'язується до жорстких літер колонок (B, C, D...) — шукає рядок
заголовків за назвами полів і будує мапу назва->індекс. Так парсер
не ламається, якщо в каталозі додадуть/приберуть колонку.
"""
from normalize import catalog_device_key

REQUIRED_HEADERS = ["Артикул", "Клас", "Коротка назва бази пристрою"]
OPTIONAL_HEADERS = ["Уніфікована назва", "Колір", "Якісний залишок",
                     "Бракований залишок", "Загальний залишок"]


def _find_header_row(df):
    for i, row in df.iterrows():
        cells = [str(c).strip() for c in row.tolist()]
        if all(any(h == c for c in cells) for h in REQUIRED_HEADERS):
            return i, cells
    raise ValueError("Не знайшов рядок заголовків каталогу (Артикул/Клас/Коротка назва бази пристрою)")


def parse(df):
    header_idx, headers = _find_header_row(df)
    col = {}
    for name in REQUIRED_HEADERS + OPTIONAL_HEADERS:
        if name in headers:
            col[name] = headers.index(name)

    records = []
    for i in range(header_idx + 1, len(df)):
        row = df.iloc[i]
        cells = [str(c) if c is not None and str(c) != "nan" else "" for c in row.tolist()]
        artikul = cells[col["Артикул"]].strip() if col.get("Артикул") is not None and col["Артикул"] < len(cells) else ""
        if not artikul or not artikul.startswith("U."):
            continue
        klas = cells[col["Клас"]].strip() if col["Клас"] < len(cells) else ""
        device_raw = cells[col["Коротка назва бази пристрою"]].strip() if col["Коротка назва бази пристрою"] < len(cells) else ""
        device_key = catalog_device_key(device_raw)
        record = {
            "artikul": artikul,
            "klas": klas,
            "device_raw": device_raw,
            "device_key": device_key,
        }
        for opt in OPTIONAL_HEADERS:
            if opt in col and col[opt] < len(cells):
                record[opt] = cells[col[opt]].strip()
        records.append(record)
    return records
