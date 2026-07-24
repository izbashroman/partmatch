# -*- coding: utf-8 -*-
"""
UParts b2b: розхідники/інструменти, НЕ прив'язані до конкретної моделі
пристрою (device_model завжди буде None) — матчаться до каталогу лише
за Класом ("Витратні матеріали для монтажу", "Інструменти" тощо).
Колонка B (індекс 1) — назва товару, колонка C (індекс 2) — ціна $.
"""
from parsers import freetext

SUPPLIER = "uparts"
NAME_COL = 1
PRICE_COL = 2


def parse(df, currency="USD"):
    return freetext.parse(df, name_col=NAME_COL, price_cols=[(PRICE_COL, "Ціна")],
                           currency=currency, supplier=SUPPLIER, min_row=0)
