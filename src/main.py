# src/main.py (фрагмент с изменениями)

import os
import sys
import json
from datetime import datetime

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
    
    # --- СОХРАНЯЕМ ВСЕ СЫРЫЕ НОВОСТИ ДЛЯ ДИАГНОСТИКИ ---
    save_raw_items(all_items)
    
    # 2. Фильтрация
    print("\n🔍 Фильтрация данных...")
    filtered_by_date = filter_by_date(all_items, LOOKBACK_DAYS)
    print(f"   После фильтрации по дате: {len(filtered_by_date)}")
    
    filtered_by_keywords = filter_by_keywords(filtered_by_date, KEYWORDS)
    print(f"   После фильтрации по ключевым словам: {len(filtered_by_keywords)}")
    
    filtered_items = filter_duplicates(filtered_by_keywords)
    print(f"   После удаления дубликатов: {len(filtered_items)}")
    
    if not filtered_items:
        print("\n⚠️ Новостей по заданным темам не найдено.")
        digest_text = "За последние дни новостей по темам ESG, зеленая экономика, ответственное инвестирование не найдено."
        save_digest_file(digest_text)
        return
    
    # 3. Генерация дайджеста
    print("\n🧠 Генерация дайджеста через GitHub Models...")
    generator = DigestGenerator()
    digest_text = generator.create_digest(filtered_items)
    
    # 4. Сохранение
    save_digest_file(digest_text)
    print("\n✅ Готово!")

def save_raw_items(items):
    """Сохраняет все сырые новости в файл для диагностики"""
    if not items:
        return
    
    filename = f"raw_items_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    
    # Преобразуем даты в строки для JSON
    export_items = []
    for item in items:
        export_item = item.copy()
        if 'date' in export_item and isinstance(export_item['date'], datetime):
            export_item['date'] = export_item['date'].isoformat()
        export_items.append(export_item)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_items, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Сырые новости сохранены в {filename}")

def save_digest_file(content):
    """Сохраняет дайджест в файл с датой в имени"""
    os.makedirs("digests", exist_ok=True)
    filename = f"digests/digest-{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 Дайджест сохранен в {filename}")
    return filename

if __name__ == "__main__":
    main()
