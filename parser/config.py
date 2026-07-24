"""
Реєстр джерел: внутрішній каталог + прайс-листи постачальників.

Кожен запис — це один лист (вкладка) Google Sheets. Один файл може мати
кілька вкладок (gid) — тоді просто додай кілька записів з одним sheet_id.

CSV_EXPORT_URL шаблон працює для будь-якого Google Sheets, що відкритий
"для перегляду за посиланням" — не потребує авторизації.
"""

CSV_EXPORT_URL = "https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

CATALOG = {
    "name": "catalog_geckon",
    "sheet_id": "1CnJLOZdT0H8ajAFjQX1HqUYa6lUq4er1c3qiDtAOw-I",
    "gid": "982588628",
}

SUPPLIERS = [
    {
        "name": "icracked",
        "label": "iCracked Apple Запчасти",
        "sheet_id": "18yUVyK6hpZO_e7m4dPVcpssEfmqNMOHqWwoVqVZoPwE",
        "gid": "574878022",       # АКБ iPhone / MacBook / iPad
        "currency": "USD",
        "parser": "icracked",
    },
    # Інші вкладки того ж файлу iCracked (LCD, корпуса, тач/скло, шлейф) —
    # gid для кожної треба донабрати окремо, поточний доступ через web_fetch
    # весь час повертав першу вкладку. Додати сюди, коли gid будуть підтверджені.
    {
        "name": "ocapro",
        "label": "OCAPRO.xls",
        "sheet_id": "1g25xDpreiwFiGhpMjj3kpt-S7_B7jfs3",
        "gid": "538839518",
        "currency": "UAH",
        "parser": "ocapro",
    },
    {
        "name": "refparts",
        "label": "REFparts price",
        "sheet_id": "1YUqoR1dShzgAICtwobFLNa1DVtLDoBh6_QKwd8TMQdI",
        "gid": "552982975",
        "currency": "USD",       # опт-ціни вже у $ (в шапці лише довідковий курс)
        "parser": "refparts",
    },
    {
        "name": "levelparts",
        "label": "Price (Корпуси/Батареї, @levelpart_s)",
        "sheet_id": "1d7W9shdYh6pSxHuA_B4mj0sDyAdXpMPZgrrzxw7bM8g",
        "gid": "672822659",
        "currency": "USD",
        "parser": "levelparts",
    },
    {
        "name": "uparts",
        "label": "UParts b2b",
        "sheet_id": "19pPHdC3uF47iWRVKWBBbNKfVKRcZCLnDYG2xtnUEA44",
        "gid": "263992546",
        "currency": "USD",
        "parser": "uparts",
    },
]

# Курс UAH->USD для постачальників, що цінують у гривні (потрібно оновлювати).
UAH_TO_USD_RATE = 41.7
