# src/filters.py

from datetime import datetime, timedelta
import re

def filter_by_keywords(items, keywords):
    """
    Фильтрует список новостей по наличию ключевых слов.
    Возвращает только те элементы, которые содержат хотя бы одно ключевое слово.
    """
    filtered = []
    
    for item in items:
        # Объединяем все текстовые поля для поиска
        search_text = " ".join([
            item.get('title', ''),
            item.get('description', ''),
            item.get('text', ''),
            item.get('category', '')
        ]).lower()
        
        # Проверяем наличие каждого ключевого слова
        for keyword in keywords:
            if re.search(keyword.lower(), search_text):
                # Добавляем информацию о совпадении
                item['matched_keyword'] = keyword
                filtered.append(item)
                break  # Добавляем элемент только один раз
    
    return filtered

def filter_by_date(items, days_back=2):
    """
    Фильтрует элементы по дате.
    Возвращает только элементы за последние 'days_back' дней.
    """
    if days_back <= 0:
        return items
    
    today = datetime.now().date()
    cutoff_date = today - timedelta(days=days_back)
    filtered = []
    
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
    
    return filtered

def filter_duplicates(items):
    """
    Удаляет дубликаты по заголовку или тексту.
    """
    seen_titles = set()
    seen_texts = set()
    filtered = []
    
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
    
    return filtered
