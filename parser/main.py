# -*- coding: utf-8 -*-
"""
Головний скрипт: тягне каталог + прайси постачальників з Google Sheets,
зіставляє і зберігає звіт у <out_dir>/report.csv (за замовчуванням output/).

Запуск (потрібен доступ до docs.google.com і `pip install pandas requests`):
    python3 main.py
    python3 main.py --out-dir ../docs   # напр. для GitHub Actions, щоб писати прямо в docs/

Офлайн-демо на тестових даних (без мережі):
    python3 test_run.py
"""
import argparse
import csv
import os
import sys

from config import CATALOG, SUPPLIERS
from fetch import fetch_sheet_csv
import match
from parsers import catalog as catalog_parser
from parsers import icracked, ocapro, refparts, uparts, levelparts

PARSER_MAP = {
    "icracked": icracked,
    "ocapro": ocapro,
    "refparts": refparts,
    "uparts": uparts,
    "levelparts": levelparts,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="output", help="куди писати report.csv / unmatched_supplier_offers.csv")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    print("Завантажую каталог...", file=sys.stderr)
    cat_df = fetch_sheet_csv(CATALOG["sheet_id"], CATALOG["gid"])
    catalog_records = catalog_parser.parse(cat_df)
    print(f"  каталог: {len(catalog_records)} позицій", file=sys.stderr)

    all_supplier_records = []
    for src in SUPPLIERS:
        parser_mod = PARSER_MAP.get(src["parser"])
        if parser_mod is None:
            print(f"  [{src['name']}] немає парсера, пропущено", file=sys.stderr)
            continue
        try:
            df = fetch_sheet_csv(src["sheet_id"], src["gid"])
            recs = parser_mod.parse(df, currency=src["currency"])
            print(f"  [{src['name']}] {len(recs)} цінових записів", file=sys.stderr)
            all_supplier_records.extend(recs)
        except Exception as e:
            print(f"  [{src['name']}] ПОМИЛКА: {e}", file=sys.stderr)

    report = match.match(catalog_records, all_supplier_records)

    report_path = os.path.join(args.out_dir, "report.csv")
    with open(report_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Артикул", "Пристрій", "Клас", "К-ть пропозицій",
                    "Найкраща ціна $", "Постачальник", "Всі пропозиції"])
        for row in report:
            offers_str = " | ".join(match.format_offer(o) for o in row["offers"])
            w.writerow([row["artikul"], row["device"], row["klas"], len(row["offers"]),
                        row["best_price_usd"], row["best_supplier"], offers_str])

    matched = sum(1 for r in report if r["offers"])
    print(f"\nГотово: {report_path} ({matched}/{len(report)} позицій каталогу мають пропозиції)",
          file=sys.stderr)

    unmatched = match.unmatched_supplier_records(catalog_records, all_supplier_records)
    unmatched_path = os.path.join(args.out_dir, "unmatched_supplier_offers.csv")
    with open(unmatched_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Постачальник", "Модель (розпізнано)", "Клас (розпізнано)", "Ціна", "Валюта", "Опис/варіант"])
        for u in unmatched:
            w.writerow([u["supplier"], u.get("device_model"), u.get("klas"), u["price"], u["currency"],
                        u.get("raw_name", u.get("variant_label", ""))])
    print(f"Пропозиції без відповідника в каталозі: {len(unmatched)} -> {unmatched_path}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
