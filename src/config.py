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
        "url": "https://telegram.me/s/econ_gov_by",
        "type": "telegram"
    },
    "telegram_gov": {
        "name": "Правительство Беларуси (Telegram)",
        "url": "https://telegram.me/s/government_by",
        "type": "telegram"
    },
    "telegram_banki24": {
        "name": "Банки 24 (Telegram)",
        "url": "https://telegram.me/s/banki24_news",
        "type": "telegram"
    },
    "telegram_eabr": {
        "name": "ЕАБР Евразийский банк развития (Telegram)",
        "url": "https://telegram.me/s/eabr_bank",
        "type": "telegram"
    },
    "telegram_belrynok": {
        "name": "Белорусы и рынок (Telegram)",
        "url": "https://telegram.me/s/belrynok",
        "type": "telegram"
    },
    "telegram_egazeta": {
        "name": "Экономическая газета | Новости экономики Беларуси (Telegram)",
        "url": "https://telegram.me/s/EGazeta",
        "type": "telegram"
    },
    "telegram_bisi": {
        "name": "БИСИ | think tank (Telegram)",
        "url": "https://telegram.me/s/BISRby",
        "type": "telegram"
    },
      "telegram_scst": {
        "name": "ГКНТ (Telegram)",
        "url": "https://telegram.me/s/scst_by",
        "type": "telegram"
    },
      "telegram_pul": {
        "name": "Пул Первого (Telegram)",
        "url": "https://telegram.me/s/pul_1",
        "type": "telegram"
    }
    
}

# --- Ключевые слова для фильтрации ---
KEYWORDS = [
    "ESG",
    "зелёная экономика",
    "ответственное инвестирование",
    "финансовая отчётность",
    "устойчивое развитие"
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
