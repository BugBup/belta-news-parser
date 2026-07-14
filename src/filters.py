# src/filters.py

from datetime import datetime, timedelta
import re

def filter_by_keywords(items, keywords):
    """
    Фильтрует список новостей по наличию ключевых слов.
    Возвращает только те элементы, которые содержат хотя бы одно ключевое слово.
    """
    filtered = []
    
    print(f"\n   🔍 Фильтрация по ключевым словам: {keywords}")
    print(f"   📊 Всего элементов на входе: {len(items)}")
    
    for i, item in enumerate(items):
        # Объединяем все текстовые поля для поиска
        search_text = " ".join([
            item.get('title', ''),
            item.get('description', ''),
            item.get('text', ''),
            item.get('category', '')
        ]).lower()
        
        # --- ДИАГНОСТИКА: Показываем первые 5 элементов ---
        if i < 5:
            print(f"   📝 Элемент {i+1}: текст начинается с '{search_text[:50]}...'")
        
        # Проверяем наличие каждого ключевого слова
        matched = False
        for keyword in keywords:
            if re.search(keyword.lower(), search_text):
                item['matched_keyword'] = keyword
                filtered.append(item)
                print(f"   ✅ Совпадение! Ключевое слово '{keyword}' найдено в элементе {i+1}")
                matched = True
                break  # Добавляем элемент только один раз
        
        if not matched and i < 5:
            print(f"   ❌ Нет совпадений в элементе {i+1}")
    
    print(f"   📊 После фильтрации: {len(filtered)} элементов")
    return filtered

def filter_by_date(items, days_back=2):
    """Фильтрует элементы по дате за последние N дней"""
    if days_back <= 0:
        return items
    
    today = datetime.now().date()
    cutoff_date = today - timedelta(days=days_back)
    filtered = []
    
    print(f"\n   📅 Фильтрация по дате (последние {days_back} дней)")
    print(f"   📊 Всего элементов на входе: {len(items)}")
    print(f"   📅 Дата отсечения: {cutoff_date}")
    
    for item in items:
        item_date = item.get('date')
        
        # Если дата не указана или не распарсилась, оставляем
        if not item_date:
            filtered.append(item)
            continue
        
        # Если дата в строковом формате, пытаемся распарсить
        if isinstance(item_date, str):
            try:
                item_date = datetime.strptime(item_date, "%Y-%m-%d").date()
            except:
                filtered.append(item)
                continue
        elif isinstance(item_date, datetime):
            item_date = item_date.date()
        
        # Сравниваем с cutoff_date
        if item_date >= cutoff_date:
            filtered.append(item)
    
    print(f"   📊 После фильтрации по дате: {len(filtered)} элементов")
    return filtered

def filter_duplicates(items):
    """Удаляет дубликаты по заголовку или тексту"""
    seen_titles = set()
    seen_texts = set()
    filtered = []
    
    print(f"\n   🔄 Удаление дубликатов")
    print(f"   📊 Всего элементов на входе: {len(items)}")
    
    for item in items:
        title = item.get('title', '').lower().strip()
        text = item.get('text', '').lower().strip()[:100]  # Берем первые 100 символов текста
        
        # Если заголовок уже видели, пропускаем
        if title and title in seen_titles:
            continue
        
        # Если текст уже видели, пропускаем
        if text and text in seen_texts:
            continue
        
        if title:
            seen_titles.add(title)
        if text:
            seen_texts.add(text)
        filtered.append(item)
    
    print(f"   📊 После удаления дубликатов: {len(filtered)} элементов")
    return filtered
