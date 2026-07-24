# -*- coding: utf-8 -*-
"""
REFparts price: назва товару в колонці C (індекс 2), ціни опту в
колонках з заголовками 'Великий опт'/'Середній опт'/'Дрібний опт'
(за спостереженою структурою — M/N/O/P, але шукаємо за текстом,
щоб не зламатись при зсуві колонок).
"""
from parsers import freetext

SUPPLIER = "refparts"
NAME_COL = 2  # колонка C — спостережено фіксованою для всіх секцій файлу


def _find_price_columns(df):
    for i, row in df.iterrows():
        cells = [str(c).strip() for c in row.tolist()]
        if "Великий опт" in cells and "Дрібний опт" in cells:
            cols = []
            for label in ("Великий опт", "Середній опт", "Дрібний опт"):
                if label in cells:
                    cols.append((cells.index(label), label))
            return cols
    raise ValueError("Не знайшов колонки опту (Великий/Середній/Дрібний опт) у REFparts")


def parse(df, currency="USD"):
    price_cols = _find_price_columns(df)
    return freetext.parse(df, name_col=NAME_COL, price_cols=price_cols,
                           currency=currency, supplier=SUPPLIER, min_row=0)
