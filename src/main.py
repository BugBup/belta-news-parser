# src/main.py

import os
import sys
import json
from datetime import datetime

# Добавляем путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import SOURCES, KEYWORDS, EMAIL_CONFIG, LOOKBACK_DAYS, MAX_ITEMS_PER_SOURCE
from src.parsers.belta_parser import BeltaParser
from src.parsers.telegram_parser import TelegramParser
from src.filters import filter_by_keywords, filter_by_date, filter_duplicates
from src.digest_generator import DigestGenerator
from src.email_sender import EmailSender

def main():
    print("🚀 Запуск парсинга новостей...")
    
    # 1. Сбор данных из всех источников
    all_items = []
    
    for source_key, source_config in SOURCES.items():
        print(f"\n📡 Обработка источника: {source_config.get('name', source_key)}")
        
        # Выбираем парсер в зависимости от типа
        if source_config.get('type') == 'telegram':
            parser = TelegramParser(source_config)
        else:
            parser = BeltaParser(source_config)
        
        # Загружаем данные
        raw_data = parser.fetch_data()
        if not raw_data:
            print(f"   ❌ Не удалось загрузить данные")
            continue
        
        # Парсим данные
        parsed_items = parser.parse_data(raw_data)
        print(f"   ✅ Спарсено элементов: {len(parsed_items)}")
        
        # Ограничиваем количество
        if len(parsed_items) > MAX_ITEMS_PER_SOURCE:
            parsed_items = parsed_items[:MAX_ITEMS_PER_SOURCE]
        
        all_items.extend(parsed_items)
    
    print(f"\n📊 Всего собрано элементов: {len(all_items)}")
    
    # 2. Фильтрация
    print("\n🔍 Фильтрация данных...")
    
    # Фильтрация по дате (за последние 2 дня)
    filtered_by_date = filter_by_date(all_items, LOOKBACK_DAYS)
    print(f"   После фильтрации по дате: {len(filtered_by_date)}")
    
    # Фильтрация по ключевым словам
    filtered_by_keywords = filter_by_keywords(filtered_by_date, KEYWORDS)
    print(f"   После фильтрации по ключевым словам: {len(filtered_by_keywords)}")
    
    # Удаление дубликатов
    filtered_items = filter_duplicates(filtered_by_keywords)
    print(f"   После удаления дубликатов: {len(filtered_items)}")
    
    if not filtered_items:
        print("\n⚠️ Новостей по заданным темам не найдено.")
        # Создаем пустой дайджест
        digest_text = "За последние дни новостей по темам ESG, зеленая экономика, ответственное инвестирование не найдено."
        save_digest_file(digest_text)
        send_email(digest_text)
        return
    
    # 3. Генерация дайджеста через ИИ
    print("\n🧠 Генерация дайджеста через GitHub Models...")
    generator = DigestGenerator()
    digest_text = generator.create_digest(filtered_items)
    
    # 4. Сохранение и отправка
    save_digest_file(digest_text)
    send_email(digest_text)
    
    print("\n✅ Готово!")

def save_digest_file(content):
    """Сохраняет дайджест в файл"""
    filename = f"digest-{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 Дайджест сохранен в {filename}")
    return filename

def send_email(content):
    """Отправляет email с дайджестом"""
    sender = EmailSender(EMAIL_CONFIG)
    sender.send(content)

if __name__ == "__main__":
    main()
