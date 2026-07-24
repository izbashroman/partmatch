# -*- coding: utf-8 -*-
"""
Зводить нормалізовані записи постачальників з каталогом за ключем
(device_model, klas). Курс UAH->USD береться з config.UAH_TO_USD_RATE.
"""
from config import UAH_TO_USD_RATE


def to_usd(price, currency):
    if price is None:
        return None
    if currency == "USD":
        return round(price, 2)
    if currency == "UAH":
        return round(price / UAH_TO_USD_RATE, 2)
    return None


def build_offer_index(supplier_records):
    """(device_model, klas) -> list of offers.

    ВАЖЛИВО: пропозиції з device_model=None (модель не впізнана) НЕ
    індексуються. Інакше вони "матчились" би з будь-якою позицією
    каталогу, чий device_key теж None (напр. каталог містить
    нерозпізнаний пристрій типу "Google Pixel 10") — None не означає
    "будь-який пристрій", він означає "невідомо який", тож дві
    невідомості не повинні вважатись збігом.
    """
    idx = {}
    for rec in supplier_records:
        device_model = rec.get("device_model")
        klas = rec.get("klas")
        if device_model is None or klas is None:
            continue
        idx.setdefault((device_model, klas), []).append(rec)
    return idx


def match(catalog_records, supplier_records):
    """
    Повертає список рядків звіту: один на кожну (позицію каталогу),
    з переліком пропозицій постачальників, відсортованих за ціною USD.
    Позиції каталогу без жодної пропозиції теж включаються (offers=[]).
    Позиції каталогу з нерозпізнаним пристроєм (device_key=None) —
    завжди без пропозицій, і це коректно: ми не вміємо їх шукати.
    """
    offer_idx = build_offer_index(supplier_records)
    report = []
    for item in catalog_records:
        if item["device_key"] is None or item["klas"] is None:
            offers = []
        else:
            key = (item["device_key"], item["klas"])
            offers = offer_idx.get(key, [])
        enriched = []
        for o in offers:
            usd = to_usd(o["price"], o["currency"])
            enriched.append({**o, "price_usd": usd})
        enriched.sort(key=lambda o: (o["price_usd"] is None, o["price_usd"]))
        report.append({
            "artikul": item["artikul"],
            "device": item.get("device_raw"),
            "klas": item.get("klas"),
            "unified_name": item.get("Уніфікована назва", ""),
            "offers": enriched,
            "best_price_usd": enriched[0]["price_usd"] if enriched else None,
            "best_supplier": enriched[0]["supplier"] if enriched else None,
        })
    return report


def format_offer(o):
    """Один рядок опису пропозиції для звіту — обов'язково включає raw_name
    (справжню назву товару з прайсу постачальника), якщо вона є, бо
    variant_label сам по собі часто лише підпис колонки ("Опт"/"Роздріб")
    і не дає зрозуміти, що це за товар."""
    label = o.get("variant_label", "") or ""
    name = o.get("raw_name", "") or ""
    detail = " — ".join(x for x in (label, name) if x)
    return f"{o['price_usd']}$ {o['supplier']} ({detail})" if detail else f"{o['price_usd']}$ {o['supplier']}"


def unmatched_supplier_records(catalog_records, supplier_records):
    """Пропозиції постачальників, для яких у каталозі немає жодної позиції
    з таким самим (device_model, klas) — кандидати на розширення мапи класів
    або на нові позиції каталогу. Записи з нерозпізнаною моделлю
    (device_model=None) сюди теж потрапляють — це найкорисніший сигнал:
    показує, які товари постачальника взагалі не вдалось прив'язати
    до жодного пристрою."""
    catalog_keys = {(c["device_key"], c["klas"]) for c in catalog_records
                     if c["device_key"] is not None and c["klas"] is not None}
    out = []
    for rec in supplier_records:
        key = (rec.get("device_model"), rec.get("klas"))
        if key not in catalog_keys:
            out.append(rec)
    return out
