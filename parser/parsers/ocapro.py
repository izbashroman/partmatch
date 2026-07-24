# -*- coding: utf-8 -*-
"""
OCAPRO.xls: заголовок '№ п/п | Код | Повна назва товару | Ціна(грн.) | Опт.(грн.) | Гарантія | | На складі'
Назва товару — вільний текст з моделлю в середині ("OCA Galaxy A50 Mitsubishi").
"""
from parsers import freetext

SUPPLIER = "ocapro"


def _find_header_row(df):
    for i, row in df.iterrows():
        cells = [str(c).strip() for c in row.tolist()]
        if "Повна назва товару" in cells:
            return i, cells
    raise ValueError("Не знайшов заголовок 'Повна назва товару' у OCAPRO")


def parse(df, currency="UAH"):
    header_row, cells = _find_header_row(df)
    name_col = cells.index("Повна назва товару")
    price_cols = []
    if "Ціна(грн.)" in cells:
        price_cols.append((cells.index("Ціна(грн.)"), "Роздріб"))
    if "Опт.(грн.)" in cells:
        price_cols.append((cells.index("Опт.(грн.)"), "Опт"))
    return freetext.parse(df, name_col=name_col, price_cols=price_cols,
                           currency=currency, supplier=SUPPLIER, min_row=header_row + 1)
