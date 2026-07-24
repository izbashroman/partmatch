# -*- coding: utf-8 -*-
"""
Завантаження вкладок Google Sheets як CSV.

Працює лише для файлів, відкритих "для всіх, у кого є посилання" (перегляд).
Якщо потрібної мережі немає (наприклад, у цьому пісочному середовищі) —
використовуй sample_data/ і test_run.py для перевірки логіки офлайн,
або запусти цей модуль на машині з доступом до docs.google.com.
"""
import io
import sys

import pandas as pd

from config import CSV_EXPORT_URL


def fetch_sheet_csv(sheet_id: str, gid: str) -> pd.DataFrame:
    import requests  # локальний імпорт, щоб офлайн-тести не тягнули requests без потреби

    url = CSV_EXPORT_URL.format(sheet_id=sheet_id, gid=gid)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    # ВАЖЛИВО: Google Sheets export віддає UTF-8, але сервер часто не шле
    # charset у Content-Type, тому requests вгадує кодування сам і іноді
    # хибно визначає його як ISO-8859-1 -> кирилиця перетворюється на
    # кракозябри ("Ð¡ÑÐµÐ´ÑÑÐ²Ð¾..."). Примусово декодуємо байти як UTF-8.
    return pd.read_csv(io.BytesIO(resp.content), header=None, dtype=str, encoding="utf-8")


def fetch_all(sources) -> dict:
    """sources: список dict з sheet_id/gid/name -> {name: DataFrame}"""
    out = {}
    for src in sources:
        try:
            out[src["name"]] = fetch_sheet_csv(src["sheet_id"], src["gid"])
            print(f"  OK  {src['name']} ({src.get('label', '')})", file=sys.stderr)
        except Exception as e:
            print(f"  FAIL {src['name']}: {e}", file=sys.stderr)
    return out
