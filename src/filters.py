# src/filters.py

import re
from datetime import datetime, timedelta, date
import nltk
from nltk.stem import SnowballStemmer

# Скачиваем нужные данные NLTK (один раз при запуске)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

# Инициализируем стеммер для русского языка
stemmer = SnowballStemmer("russian")

def normalize_word(word):
    """
    Приводит слово к основе (стему).
    Например: инвестиции → инвестиц, зелёные → зелён
    """
    try:
        return stemmer.stem(word.lower())
    except:
        return word.lower()

def normalize_text(text):
    """
    Приводит весь текст к основам слов.
    """
    if not text:
        return ""
    # Разбиваем на слова, удаляем знаки препинания
    words = re.findall(r'\b[а-яёa-z]+\b', text.lower())
    normalized_words = [normalize_word(word) for word in words]
    return " ".join(normalized_words)

def filter_by_keywords(items, keywords):
    """
    Фильтрует новости по ключевым словам со стеммингом.
    """
    filtered = []
    
    # Нормализуем ключевые слова (стемим каждое)
    normalized_keywords = []
    for kw in keywords:
        # Для фраз разбиваем на слова и стемим каждое
        words = re.findall(r'\b[а-яёa-z]+\b', kw.lower())
        stemmed_words = [normalize_word(w) for w in words]
        normalized_keywords.append(" ".join(stemmed_words))
    
    for item in items:
        # Собираем текст для поиска
        raw_text = " ".join([
            item.get('title', ''),
            item.get('description', ''),
            item.get('text', ''),
            item.get('category', '')
        ])
        
        # Нормализуем текст новости (стемим все слова)
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
