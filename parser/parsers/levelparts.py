# -*- coding: utf-8 -*-
"""
"Price" (@levelpart_s): одна таблиця Серія|Модель|Корпус(оригінал)|Скло корпусу|Корпус(HQ).
"""
import re

from normalize import extract_iphone_model, parse_price_to_float

SUPPLIER = "levelparts"

COLUMN_KLAS_KEYWORDS = [
    (r"скло\s*корпусу", "Скло задньої кришки"),
    (r"корпус", "Кришка корпусу задня без обвісу"),
]


def _guess_klas(label):
    text = (label or "").lower()
    for pattern, canon in COLUMN_KLAS_KEYWORDS:
        if re.search(pattern, text):
            return canon
    return None


def _row_cells(df, i):
    row = df.iloc[i]
    return [str(c) if c is not None and str(c) != "nan" else "" for c in row.tolist()]


def parse(df, currency="USD"):
    records = []
    header_row = None
    series_col = None
    for i in range(len(df)):
        cells = _row_cells(df, i)
        for j in range(len(cells) - 1):
            if cells[j].strip() == "Серія" and "Модель" in cells[j + 1]:
                header_row, series_col = i, j
                break
        if header_row is not None:
            break
    if header_row is None:
        return records

    model_col = series_col + 1
    header_cells = _row_cells(df, header_row)
    price_cols = []
    for c in range(model_col + 1, len(header_cells)):
        label = header_cells[c].strip()
        if not label:
            continue
        klas = _guess_klas(label)
        price_cols.append((c, klas, label))

    series = None
    for r in range(header_row + 1, len(df)):
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
