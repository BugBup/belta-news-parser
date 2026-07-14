# src/main.py

import os
import sys
import json
from datetime import datetime
import traceback
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import SOURCES, KEYWORDS, LOOKBACK_DAYS, MAX_ITEMS_PER_SOURCE
from src.parsers.belta_parser import BeltaParser
from src.parsers.telegram_parser import TelegramParser
from src.filters import filter_by_keywords, filter_by_date, filter_duplicates
from src.digest_generator import DigestGenerator

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
    
    # --- ДИАГНОСТИКА: показываем первые 5 элементов ---
    print("\n🔍 ДИАГНОСТИКА: Первые 5 элементов (текст для поиска):")
    for i, item in enumerate(all_items[:5]):
        search_text = " ".join([
            item.get('title', ''),
            item.get('description', ''),
            item.get('text', ''),
            item.get('category', '')
        ])
        print(f"   {i+1}. {search_text[:100]}...")
    
    # 2. Фильтрация по дате (первый этап)
    print("\n🔍 Фильтрация по дате...")
    filtered_by_date = filter_by_date(all_items, LOOKBACK_DAYS)
    print(f"   ✅ После фильтрации по дате: {len(filtered_by_date)} элементов")
    
    # --- СОХРАНЯЕМ ДАННЫЕ ПОСЛЕ ФИЛЬТРАЦИИ ПО ДАТЕ (ДО КЛЮЧЕВЫХ СЛОВ) ---
    save_items_with_stats(
        items=filtered_by_date,
        filename_prefix="after_date_filter",
        stats={
            "stage": "after_date_filter",
            "total_before": len(all_items),
            "total_after": len(filtered_by_date),
            "date_cutoff": LOOKBACK_DAYS
        }
    )
    
    # --- ДИАГНОСТИКА: проверяем, есть ли ключевые слова в этих данных ---
    print("\n🔍 ДИАГНОСТИКА: Проверка наличия ключевых слов в данных после фильтрации по дате:")
    keyword_found = False
    for kw in KEYWORDS:
        count = 0
        for item in filtered_by_date[:20]:  # Проверяем первые 20
            search_text = " ".join([
                item.get('title', ''),
                item.get('description', ''),
                item.get('text', ''),
                item.get('category', '')
            ]).lower()
            if re.search(kw.lower(), search_text):
                count += 1
        if count > 0:
            print(f"   ✅ Ключевое слово '{kw}' найдено в {count} элементах (из первых 20)")
            keyword_found = True
        else:
            print(f"   ❌ Ключевое слово '{kw}' не найдено в первых 20 элементах")
    
    if not keyword_found:
        print("\n   ⚠️ ВНИМАНИЕ: В отфильтрованных по дате данных нет ключевых слов!")
        print("   💡 Это значит, что либо в новостях действительно нет этих слов,")
        print("   💡 либо парсер не извлекает текст правильно.")
        print("   💡 Проверьте файл after_date_filter_*.json в папке digests.")
    
    # 3. Фильтрация по ключевым словам (второй этап)
    print("\n🔍 Фильтрация по ключевым словам...")
    filtered_by_keywords = filter_by_keywords(filtered_by_date, KEYWORDS)
    print(f"   ✅ После фильтрации по ключевым словам: {len(filtered_by_keywords)} элементов")
    
    # 4. Удаление дубликатов
    print("\n🔍 Удаление дубликатов...")
    filtered_items = filter_duplicates(filtered_by_keywords)
    print(f"   ✅ После удаления дубликатов: {len(filtered_items)} элементов")
    
    # --- СОХРАНЯЕМ ИТОГОВЫЕ ОТФИЛЬТРОВАННЫЕ ДАННЫЕ ---
    save_items_with_stats(
        items=filtered_items,
        filename_prefix="final_filtered",
        stats={
            "stage": "final",
            "total_collected": len(all_items),
            "after_date_filter": len(filtered_by_date),
            "after_keyword_filter": len(filtered_by_keywords),
            "after_dedup": len(filtered_items)
        }
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

def save_items_with_stats(items, filename_prefix, stats):
    """Сохраняет элементы с метаданными в файл"""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    os.makedirs("digests", exist_ok=True)
    filename = f"digests/{filename_prefix}_{timestamp}.json"
    
    # Преобразуем даты для JSON
    export_items = []
    for item in items:
        export_item = item.copy()
        if 'date' in export_item and isinstance(export_item['date'], datetime):
            export_item['date'] = export_item['date'].isoformat()
        export_items.append(export_item)
    
    export_data = {
        "statistics": stats,
        "items": export_items,
        "keywords": KEYWORDS
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Данные сохранены в {filename}")
        print(f"   📊 Элементов: {len(export_items)}")
    except Exception as e:
        print(f"   ❌ Ошибка при сохранении: {e}")

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
