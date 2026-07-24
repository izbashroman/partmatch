# -*- coding: utf-8 -*-
"""
Офлайн-прогін усього пайплайну на sample_data/ (без мережі) — для перевірки,
що парсери й матчер працюють коректно, і для отримання зразкового звіту.
Запуск: python3 test_run.py
"""
import csv
import sys

import pandas as pd

from parsers import catalog as catalog_parser
from parsers import icracked as icracked_parser
from parsers import ocapro as ocapro_parser
from parsers import refparts as refparts_parser
from parsers import uparts as uparts_parser
from parsers import levelparts as levelparts_parser
import match


def load_csv(path):
    return pd.read_csv(path, header=None, dtype=str)


def main():
    cat_df = load_csv("sample_data/catalog_sample.csv")
    catalog_records = catalog_parser.parse(cat_df)
    print(f"Каталог: {len(catalog_records)} позицій", file=sys.stderr)

    supplier_records = []

    icr_df = load_csv("sample_data/icracked_sample.csv")
    icr_recs = icracked_parser.parse(icr_df, currency="USD")
    print(f"iCracked: {len(icr_recs)} цінових записів", file=sys.stderr)
    supplier_records += icr_recs

    oca_df = load_csv("sample_data/ocapro_sample.csv")
    oca_recs = ocapro_parser.parse(oca_df, currency="UAH")
    print(f"OCAPRO: {len(oca_recs)} цінових записів", file=sys.stderr)
    supplier_records += oca_recs

    ref_df = load_csv("sample_data/refparts_sample.csv")
    ref_recs = refparts_parser.parse(ref_df, currency="USD")
    print(f"REFparts: {len(ref_recs)} цінових записів", file=sys.stderr)
    supplier_records += ref_recs

    up_df = load_csv("sample_data/uparts_sample.csv")
    up_recs = uparts_parser.parse(up_df, currency="USD")
    print(f"UParts: {len(up_recs)} цінових записів", file=sys.stderr)
    supplier_records += up_recs

    lvl_df = load_csv("sample_data/levelparts_sample.csv")
    lvl_recs = levelparts_parser.parse(lvl_df, currency="USD")
    print(f"Levelparts: {len(lvl_recs)} цінових записів", file=sys.stderr)
    supplier_records += lvl_recs

    report = match.match(catalog_records, supplier_records)

    out_path = "output/report_sample.csv"
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Артикул", "Пристрій", "Клас", "К-ть пропозицій",
                    "Найкраща ціна $", "Постачальник", "Всі пропозиції ($, постачальник, варіант)"])
        for row in report:
            offers_str = " | ".join(match.format_offer(o) for o in row["offers"])
            w.writerow([
                row["artikul"], row["device"], row["klas"], len(row["offers"]),
                row["best_price_usd"], row["best_supplier"], offers_str,
            ])
    print(f"\nЗвіт записано: {out_path}", file=sys.stderr)

    matched = sum(1 for r in report if r["offers"])
    print(f"Зіставлено з пропозиціями: {matched}/{len(report)} позицій каталогу", file=sys.stderr)

    unmatched = match.unmatched_supplier_records(catalog_records, supplier_records)
    print(f"\nПропозиції постачальників без відповідника в каталозі: {len(unmatched)}", file=sys.stderr)
    for u in unmatched[:15]:
        print(f"  - [{u['supplier']}] model={u.get('device_model')} klas={u.get('klas')} "
              f"price={u['price']}{u['currency']} :: {u.get('raw_name', u.get('variant_label',''))}",
              file=sys.stderr)


if __name__ == "__main__":
    main()
