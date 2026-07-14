# src/main.py

import os
import sys
import json
from datetime import datetime
import traceback

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
    
    # --- СОХРАНЕНИЕ СЫРЫХ НОВОСТЕЙ В ПАПКУ digests ---
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
    
    # 4. Сохранение дайджеста
    save_digest_file(digest_text)
    print("\n✅ Готово!")

def save_raw_items(items):
    """
    Сохраняет все сырые новости в файл для диагностики в папку digests.
    ВСЕГДА создает файл, даже если список пуст.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    # --- ИЗМЕНЕНИЕ: Сохраняем в папку digests ---
    os.makedirs("digests", exist_ok=True)
    filename = f"digests/raw_items_{timestamp}.json"
    
    absolute_path = os.path.abspath(filename)
    print(f"   📂 Попытка сохранить файл: {absolute_path}")
    
    # Преобразуем даты в строки для JSON
    export_items = []
    for item in items:
        export_item = item.copy()
        if 'date' in export_item and isinstance(export_item['date'], datetime):
            export_item['date'] = export_item['date'].isoformat()
        export_items.append(export_item)
    
    # Сохраняем файл
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_items, f, ensure_ascii=False, indent=2)
        
        # Проверяем, что файл действительно создан
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            print(f"   ✅ Файл успешно создан: {filename}")
            print(f"   📊 Размер файла: {file_size} байт")
            print(f"   📋 Записей в файле: {len(export_items)}")
        else:
            print(f"   ❌ Файл не найден после сохранения!")
    except Exception as e:
        print(f"   ❌ Ошибка при сохранении: {e}")
        print(f"   📋 Детали ошибки: {traceback.format_exc()}")

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
