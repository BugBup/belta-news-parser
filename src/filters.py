# src/filters.py

from datetime import datetime, timedelta, date
import re

def filter_by_date(items, days_back=2):
    """
    Фильтрует элементы по дате за последние N дней.
    Теперь корректно обрабатывает datetime и date объекты.
    """
    if days_back <= 0:
        return items
    
    today = date.today()
    cutoff_date = today - timedelta(days=days_back)
    filtered = []
    
    print(f"\n   📅 Фильтрация по дате (последние {days_back} дней)")
    print(f"   📊 Всего элементов на входе: {len(items)}")
    print(f"   📅 Дата отсечения: {cutoff_date}")
    
    for item in items:
        item_date = item.get('date')
        
        # Если дата не указана - оставляем (на всякий случай)
        if not item_date:
            filtered.append(item)
            continue
        
        # Приводим к date для сравнения
        if isinstance(item_date, datetime):
            item_date = item_date.date()
        elif isinstance(item_date, date):
            pass  # уже date
        else:
            # Если строка - пытаемся распарсить
            try:
                if isinstance(item_date, str):
                    # Пробуем isoformat
                    dt = datetime.fromisoformat(item_date)
                    item_date = dt.date()
                else:
                    filtered.append(item)
                    continue
            except:
                filtered.append(item)
                continue
        
        # Сравниваем
        if item_date >= cutoff_date:
            filtered.append(item)
    
    print(f"   📊 После фильтрации по дате: {len(filtered)} элементов")
    return filtered

def filter_by_keywords(items, keywords):
    """Фильтрует список новостей по наличию ключевых слов"""
    filtered = []
    
    print(f"\n   🔍 Фильтрация по ключевым словам: {keywords}")
    print(f"   📊 Всего элементов на входе: {len(items)}")
    
    for i, item in enumerate(items):
        search_text = " ".join([
            item.get('title', ''),
            item.get('description', ''),
            item.get('text', ''),
            item.get('category', '')
        ]).lower()
        
        matched = False
        for keyword in keywords:
            if re.search(keyword.lower(), search_text):
                item['matched_keyword'] = keyword
                filtered.append(item)
                print(f"   ✅ Совпадение! '{keyword}' в элементе {i+1}")
                matched = True
                break
    
    print(f"   📊 После фильтрации по ключевым словам: {len(filtered)} элементов")
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
        text = item.get('text', '').lower().strip()[:100]
        
        if title and title in seen_titles:
            continue
        if text and text in seen_texts:
            continue
        
        if title:
            seen_titles.add(title)
        if text:
            seen_texts.add(text)
        filtered.append(item)
    
    print(f"   📊 После удаления дубликатов: {len(filtered)} элементов")
    return filtered
