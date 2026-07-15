# src/filters.py

import re
from datetime import datetime, timedelta, date
import pymorphy2

# Инициализируем морфологический анализатор (один раз при запуске)
morph = pymorphy2.MorphAnalyzer()

def normalize_word(word):
    """Приводит слово к нормальной форме (лемме)"""
    try:
        parsed = morph.parse(word)[0]
        return parsed.normal_form
    except:
        return word.lower()

def normalize_text(text):
    """Приводит весь текст к нормальным формам слов"""
    if not text:
        return ""
    words = re.findall(r'\b[а-яёa-z]+\b', text.lower())
    normalized_words = [normalize_word(word) for word in words]
    return " ".join(normalized_words)

def filter_by_keywords(items, keywords):
    """
    Фильтрует новости по ключевым словам с морфологическим поиском.
    """
    filtered = []
    
    # Нормализуем ключевые слова (один раз для всех)
    normalized_keywords = [normalize_word(kw) for kw in keywords]
    
    for item in items:
        # Собираем текст для поиска
        raw_text = " ".join([
            item.get('title', ''),
            item.get('description', ''),
            item.get('text', ''),
            item.get('category', '')
        ])
        
        # Нормализуем текст новости
        normalized_text = normalize_text(raw_text)
        
        # Проверяем наличие каждого нормализованного ключевого слова
        for kw in normalized_keywords:
            if kw in normalized_text:
                item['matched_keyword'] = kw
                filtered.append(item)
                break
    
    return filtered

def filter_by_date(items, days_back=2):
    """Фильтрует по дате (без изменений)"""
    if days_back <= 0:
        return items
    
    today = date.today()
    cutoff_date = today - timedelta(days=days_back)
    filtered = []
    
    for item in items:
        item_date = item.get('date')
        if not item_date:
            filtered.append(item)
            continue
        
        if isinstance(item_date, datetime):
            item_date = item_date.date()
        elif isinstance(item_date, date):
            pass
        else:
            try:
                if isinstance(item_date, str):
                    dt = datetime.fromisoformat(item_date)
                    item_date = dt.date()
                else:
                    filtered.append(item)
                    continue
            except:
                filtered.append(item)
                continue
        
        if item_date >= cutoff_date:
            filtered.append(item)
    
    return filtered

def filter_duplicates(items):
    """Удаляет дубликаты"""
    seen_titles = set()
    seen_texts = set()
    filtered = []
    
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
    
    return filtered
