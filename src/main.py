# src/main.py

import os
import sys
import json
import re
from datetime import datetime, date

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
    """Дополняет JSON-файл новыми данными (универсальная проверка дубликатов)"""
    os.makedirs("digests", exist_ok=True)
    
    # Загружаем существующие данные
    existing_data = {"statistics": stats, "items": [], "keywords": keywords_used}
    
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            print(f"   📂 Файл {filename} загружен, уже есть {len(existing_data.get('items', []))} записей")
        except Exception as e:
            print(f"   ⚠️ Не удалось прочитать {filename}: {e}, создаю новый")
    
    # Преобразуем даты в строки для JSON
    export_items = []
    for item in new_items:
        export_item = item.copy()
        if 'date' in export_item and isinstance(export_item['date'], datetime):
            export_item['date'] = export_item['date'].isoformat()
        export_items.append(export_item)
    
    # Получаем существующие элементы
    if 'items' in existing_data and isinstance(existing_data['items'], list):
        existing_items = existing_data['items']
    else:
        existing_items = []
    
    # --- УНИВЕРСАЛЬНАЯ ПРОВЕРКА ДУБЛИКАТОВ ПО source + title ---
    existing_keys = set()
    for item in existing_items:
        source = item.get('source', '').strip()
        title = item.get('title', '').strip()
        if source and title:
            key = f"{source.lower()}|{title.lower()}"
            existing_keys.add(key)
    
    # Фильтруем новые элементы
    new_unique_items = []
    for item in export_items:
        source = item.get('source', '').strip()
        title = item.get('title', '').strip()
        
        if not source:
            print(f"   ⚠️ Пропуск: нет источника у новости")
            continue
            
        if not title:
            print(f"   ⚠️ Пропуск: нет заголовка у новости из {source}")
            continue
        
        key = f"{source.lower()}|{title.lower()}"
        if key in existing_keys:
            print(f"   ℹ️ Дубликат: '{title[:40]}...' (источник: {source})")
        else:
            new_unique_items.append(item)
            existing_keys.add(key)
            print(f"   ✅ Новая запись: '{title[:40]}...' (источник: {source})")
    
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

def save_digest_file(content):
    """Сохраняет дайджест в файл"""
    os.makedirs("digests", exist_ok=True)
    filename = f"digests/digest-{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 Дайджест сохранен в {filename}")
    return filename

def main():
    print("🚀 Запуск парсинга новостей...")
    
    all_items = []
    
    # Сбор данных из всех источников
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
    
    # --- РАЗДЕЛЯЕМ НОВОСТИ ПО ИСТОЧНИКАМ ---
    belta_items = []
    telegram_items = []
    
    for item in all_items:
        source = item.get('source', '')
        if 'БелТА' in source:
            belta_items.append(item)
        else:
            telegram_items.append(item)
    
    print(f"\n📊 Распределение по источникам:")
    print(f"   БелТА: {len(belta_items)} новостей")
    print(f"   Telegram: {len(telegram_items)} новостей")
    
    # --- ДИАГНОСТИКА: показываем 5 самых свежих постов ---
    if all_items:
        all_sorted = sorted(all_items, key=lambda x: x.get('date', datetime.min), reverse=True)
        print(f"\n📰 5 САМЫХ СВЕЖИХ ПОСТОВ ИЗ ВСЕХ ИСТОЧНИКОВ:")
        for i, item in enumerate(all_sorted[:5]):
            source = item.get('source', 'unknown')
            date_str = item.get('date', '')
            if isinstance(date_str, datetime):
                date_str = date_str.strftime('%Y-%m-%d %H:%M')
            elif isinstance(date_str, date):
                date_str = date_str.strftime('%Y-%m-%d')
            title = item.get('title', 'Без заголовка')[:60]
            print(f"      {i+1}. [{source}] [{date_str}] {title}...")
    
    # --- ФИЛЬТРАЦИЯ ПО ДАТЕ (для всех) ---
    print("\n🔍 Фильтрация по дате...")
    filtered_by_date_all = filter_by_date(all_items, LOOKBACK_DAYS)
    print(f"   ✅ После фильтрации по дате (все): {len(filtered_by_date_all)} элементов")
    
    # --- РАЗДЕЛЯЕМ ОТФИЛЬТРОВАННЫЕ ПО ДАТЕ ---
    belta_filtered_by_date = []
    telegram_filtered_by_date = []
    
    for item in filtered_by_date_all:
        source = item.get('source', '')
        if 'БелТА' in source:
            belta_filtered_by_date.append(item)
        else:
            telegram_filtered_by_date.append(item)
    
    print(f"\n   После фильтрации по дате:")
    print(f"      БелТА: {len(belta_filtered_by_date)} новостей")
    print(f"      Telegram: {len(telegram_filtered_by_date)} новостей")
    
    # --- ФИЛЬТРАЦИЯ ПО КЛЮЧЕВЫМ СЛОВАМ (для всех) ---
    print("\n🔍 Фильтрация по ключевым словам...")
    belta_filtered_by_keywords = filter_by_keywords(belta_filtered_by_date, KEYWORDS)
    telegram_filtered_by_keywords = filter_by_keywords(telegram_filtered_by_date, KEYWORDS)
    
    print(f"\n   После фильтрации по ключевым словам:")
    print(f"      БелТА: {len(belta_filtered_by_keywords)} новостей")
    print(f"      Telegram: {len(telegram_filtered_by_keywords)} новостей")
    
    # --- УДАЛЕНИЕ ДУБЛИКАТОВ (для всех) ---
    belta_final = filter_duplicates(belta_filtered_by_keywords)
    telegram_final = filter_duplicates(telegram_filtered_by_keywords)
    
    print(f"\n   После удаления дубликатов:")
    print(f"      БелТА: {len(belta_final)} новостей")
    print(f"      Telegram: {len(telegram_final)} новостей")
    
    # --- СОХРАНЯЕМ В after_date_filter.json ПО НОВОЙ ЛОГИКЕ ---
    # Для БелТА: только те, что прошли фильтр по ключевым словам (финальные)
    # Для Telegram: все, что прошли фильтр по дате (даже если без ключевых слов)
    
    items_to_save = belta_final + telegram_filtered_by_date
    
    print(f"\n💾 Сохраняем в after_date_filter.json:")
    print(f"      БелТА (только с ключевыми словами): {len(belta_final)}")
    print(f"      Telegram (все, что по дате): {len(telegram_filtered_by_date)}")
    print(f"      Итого: {len(items_to_save)}")
    
    append_to_json_file(
        DATE_FILTERED_FILE,
        items_to_save,
        {
            "stage": "after_date_filter",
            "total_before": len(all_items),
            "total_after": len(filtered_by_date_all),
            "belta_with_keywords": len(belta_final),
            "telegram_all": len(telegram_filtered_by_date),
            "date_cutoff": LOOKBACK_DAYS,
            "timestamp": datetime.now().isoformat()
        },
        KEYWORDS
    )
    
    # --- ФИНАЛЬНЫЙ ФАЙЛ (все, что прошло все фильтры) ---
    final_items = belta_final + telegram_final
    
    print(f"\n💾 Сохраняем в final_filtered.json:")
    print(f"      БелТА: {len(belta_final)}")
    print(f"      Telegram: {len(telegram_final)}")
    print(f"      Итого: {len(final_items)}")
    
    append_to_json_file(
        FINAL_FILTERED_FILE,
        final_items,
        {
            "stage": "final",
            "total_collected": len(all_items),
            "after_date_filter": len(filtered_by_date_all),
            "after_keyword_filter": len(belta_filtered_by_keywords) + len(telegram_filtered_by_keywords),
            "after_dedup": len(belta_final) + len(telegram_final),
            "timestamp": datetime.now().isoformat()
        },
        KEYWORDS
    )
    
    # --- ГЕНЕРАЦИЯ ДАЙДЖЕСТА (только из финальных) ---
    if not final_items:
        print("\n⚠️ Новостей по заданным темам не найдено.")
        digest_text = "За последние дни новостей по темам ESG, зеленая экономика, ответственное инвестирование не найдено."
        save_digest_file(digest_text)
        return
    
    print("\n🧠 Генерация дайджеста через GitHub Models...")
    generator = DigestGenerator()
    digest_text = generator.create_digest(final_items)
    
    save_digest_file(digest_text)
    print("\n✅ Готово!")

if __name__ == "__main__":
    main()
