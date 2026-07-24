# -*- coding: utf-8 -*-
"""
Спільний парсер для прайсів, де кожен рядок — це вільний текстовий опис
товару + одна чи кілька колонок з ціною (OCAPRO, REFparts, UParts).
Категорія/розділ (типу "AirPods", "01. iPhone 17 Pro Max") — окремий
рядок-заголовок з одним заповненим стовпцем, використовується як
додатковий контекст для розпізнавання моделі, якщо в самій назві
товару моделі немає.
"""
from normalize import extract_device_model_strict, guess_part_class, parse_price_to_float


def _row_cells(df, i):
    row = df.iloc[i]
    return [str(c) if c is not None and str(c) != "nan" else "" for c in row.tolist()]


def parse(df, name_col: int, price_cols: list, currency: str,
          supplier: str, section_col: int = None, min_row: int = 0):
    """
    name_col — індекс колонки з повною назвою товару
    price_cols — список (idx, label) цінових колонок
    section_col — індекс колонки, де інколи трапляються рядки-заголовки розділу
                  (використовується як fallback контекст для моделі)
    """
    records = []
    current_section = None
    for i in range(min_row, len(df)):
        cells = _row_cells(df, i)
        if len(cells) <= name_col:
            continue
        name = cells[name_col].strip()
        # рядок-заголовок розділу: заповнена лише назва, або тільки name_col=0/section_col, ціни порожні
        prices_here = [parse_price_to_float(cells[c]) if c < len(cells) else None for c, _ in price_cols]
        if name and all(p is None for p in prices_here):
            current_section = name
            continue
        if not name:
            continue

        context = f"{current_section or ''} {name}"
        device_model = extract_device_model_strict(context)
        klas = guess_part_class(context)

        for (c, label), price in zip(price_cols, prices_here):
            if price is None:
                continue
            records.append({
                "supplier": supplier,
                "raw_name": name,
                "section": current_section,
                "device_model": device_model,
                "klas": klas,
                "variant_label": label,
                "price": price,
                "currency": currency,
            })
    return records
