# src/config.py

import os

# --- Источники данных ---
SOURCES = {
    "belta": {
        "name": "БелТА",
        "url": "https://belta.by/all_news",
        "type": "website"
    },
    "telegram_econ": {
        "name": "Экономика Беларуси (Telegram)",
        "url": "https://telegram.me/s/econ_gov_by?before=1505",
        "type": "telegram"
    },
    "telegram_gov": {
        "name": "Правительство Беларуси (Telegram)",
        "url": "https://telegram.me/s/government_by",
        "type": "telegram"
    }
}

# --- Ключевые слова для фильтрации ---
KEYWORDS = [
    "ESG",
    "зелёная экономика",
    "ответственное инвестирование",
    "финансовая отчётность",
    "устойчивое развитие", 
    "Молодежный совет"
]

# --- Настройки почты ---
EMAIL_CONFIG = {
    "to": "vaniaschulga2004@mail.ru",
    "subject": "📊 Ежедневный дайджест по инвестициям и ESG"
}

# --- Настройки периода (количество дней назад) ---
LOOKBACK_DAYS = 2  # Берем данные за сегодня и вчера

# --- Настройки парсинга ---
MAX_ITEMS_PER_SOURCE = 50  # Максимальное количество элементов с одного источника
REQUEST_TIMEOUT = 30       # Таймаут запроса в секундах

# Переменные окружения для чувствительных данных
# (будут храниться в GitHub Secrets)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
