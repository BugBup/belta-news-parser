# src/main.py

import os
import sys
import json
from datetime import datetime
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import SOURCES, KEYWORDS, LOOKBACK_DAYS, MAX_ITEMS_PER_SOURCE
from src.parsers.belta_parser import BeltaParser
from src.parsers.telegram_parser import TelegramParser
from src.filters import filter_by_keywords, filter_by_date, filter_duplicates
from src.digest_generator import DigestGenerator

# --- ПОСТОЯННЫЕ ИМЕНА ФАЙЛОВ ---
DATE_FILTERED_FILE = "digests/after_date_filter.json"
FINAL_FILTERED_FILE = "digests/final_filtered.json"

def append_to_json_file(filename, new_items, stats, keywords_used):
    """Дополняет JSON-файл новыми данными без дубликатов"""
    os.makedirs("digests", exist_ok=True)
    
    # Загружаем существующие данные, если файл есть
    existing_data = {"statistics": stats, "items": [], "keywords": keywords_used}
    
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            print(f"   📂 Файл {filename} загружен, уже есть {len(existing_data.get('items', []))} записей")
        except:
            print(f"   ⚠️ Не удалось прочитать {filename}, создаю новый")
    
    # Преобразуем даты в строки для JSON
    export_items = []
    for item in new_items:
        export_item = item.copy()
        if 'date' in export_item and isinstance(export_item['date'], datetime):
            export_item['date'] = export_item['date'].isoformat()
        export_items.append(export_item)
    
    # Добавляем новые элементы к существующим
    if 'items' in existing_data and isinstance(existing_data['items'], list):
        existing_items = existing_data['items']
    else:
        existing_items = []
    
    # --- УЛУЧШЕННАЯ ПРОВЕРКА ДУБЛИКАТОВ ---
    # Создаём множество существующих заголовков (в нижнем регистре, обрезанные)
    existing_titles = set()
    for item in existing_items:
        title = item.get('title', '').lower().strip()
        if title:
            existing_titles.add(title)
    
    # Фильтруем новые элементы, которых ещё нет
    new_unique_items = []
    for item in export_items:
        title = item.get('title', '').lower().strip()
        # Проверяем по заголовку
        if title and title not in existing_titles:
            new_unique_items.append(item)
            existing_titles.add(title)  # Добавляем, чтобы не дублировать в рамках одной партии
        else:
            print(f"   ℹ️ Дубликат: '{item.get('title', '')[:40]}...'")
    
    if new_unique_items:
        existing_items.extend(new_unique_items)
        existing_data['items'] = existing_items
        existing_data['statistics'] = stats
        existing_data['keywords'] = keywords_used
        existing_data['last_updated'] = datetime.now().isoformat()
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            print(f"   ✅ Добавлено {len(new_unique_items)} новых записей в {filename}")
            print(f"   📊 Всего записей в файле: {len(existing_items)}")
        except Exception as e:
            print(f"   ❌ Ошибка при сохранении в {filename}: {e}")
    else:
        print(f"   ℹ️ Новых записей нет, файл {filename} не обновлён")

def main():
    print("🚀 Запуск парсинга новостей...")
    
    # 1. Сбор данных из всех источников
    all_items = []
    
    for source_key, source_config in SOURCES.items():
        print(f"\n📡 Обработка источника: {source_config.get('name', source_key)}")
        
        if source_config.get('type') == 'telegram':
            parser = TelegramParser(source_config)
        else:
            parser = BeltaParser(source_config)
        
        raw_data = parser.fetch_data()
        if not raw_data:
            print(f"   ❌ Не удалось загрузить данные")
            continue
        
        parsed_items = parser.parse_data(raw_data)
        print(f"   ✅ Спарсено элементов: {len(parsed_items)}")
        
        if len(parsed_items) > MAX_ITEMS_PER_SOURCE:
            parsed_items = parsed_items[:MAX_ITEMS_PER_SOURCE]
        
        all_items.extend(parsed_items)
    
    print(f"\n📊 Всего собрано элементов: {len(all_items)}")
    
    # 2. Фильтрация по дате
    print("\n🔍 Фильтрация по дате...")
    filtered_by_date = filter_by_date(all_items, LOOKBACK_DAYS)
    print(f"   ✅ После фильтрации по дате: {len(filtered_by_date)} элементов")
    
    # --- СОХРАНЯЕМ В ПОСТОЯННЫЙ ФАЙЛ after_date_filter.json (ДОПОЛНЯЕМ) ---
    append_to_json_file(
        DATE_FILTERED_FILE,
        filtered_by_date,
        {
            "stage": "after_date_filter",
            "total_before": len(all_items),
            "total_after": len(filtered_by_date),
            "date_cutoff": LOOKBACK_DAYS,
            "timestamp": datetime.now().isoformat()
        },
        KEYWORDS
    )
    
    # 3. Фильтрация по ключевым словам
    print("\n🔍 Фильтрация по ключевым словам...")
    filtered_by_keywords = filter_by_keywords(filtered_by_date, KEYWORDS)
    print(f"   ✅ После фильтрации по ключевым словам: {len(filtered_by_keywords)} элементов")
    
    # 4. Удаление дубликатов
    print("\n🔍 Удаление дубликатов...")
    filtered_items = filter_duplicates(filtered_by_keywords)
    print(f"   ✅ После удаления дубликатов: {len(filtered_items)} элементов")
    
    # --- СОХРАНЯЕМ В ПОСТОЯННЫЙ ФАЙЛ final_filtered.json (ДОПОЛНЯЕМ) ---
    append_to_json_file(
        FINAL_FILTERED_FILE,
        filtered_items,
        {
            "stage": "final",
            "total_collected": len(all_items),
            "after_date_filter": len(filtered_by_date),
            "after_keyword_filter": len(filtered_by_keywords),
            "after_dedup": len(filtered_items),
            "timestamp": datetime.now().isoformat()
        },
        KEYWORDS
    )
    
    if not filtered_items:
        print("\n⚠️ Новостей по заданным темам не найдено.")
        digest_text = "За последние дни новостей по темам ESG, зеленая экономика, ответственное инвестирование не найдено."
        save_digest_file(digest_text)
        return
    
    # 5. Генерация дайджеста
    print("\n🧠 Генерация дайджеста через GitHub Models...")
    generator = DigestGenerator()
    digest_text = generator.create_digest(filtered_items)
    
    # 6. Сохранение дайджеста
    save_digest_file(digest_text)
    print("\n✅ Готово!")

def save_digest_file(content):
    """Сохраняет дайджест в файл"""
    os.makedirs("digests", exist_ok=True)
    filename = f"digests/digest-{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 Дайджест сохранен в {filename}")
    return filename

if __name__ == "__main__":
    main()
