# src/parsers/belta_parser.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from .base_parser import BaseParser
from src.config import REQUEST_TIMEOUT

class BeltaParser(BaseParser):
    """Парсер для сайта БелТА - проверенная логика из первого проекта"""
    
    def __init__(self, source_config):
        super().__init__(source_config)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
    
    def fetch_data(self):
        """Загружает HTML-страницу БелТА"""
        try:
            print(f"   🌐 Загрузка: {self.source['url']}")
            response = requests.get(
                self.source['url'], 
                headers=self.headers, 
                timeout=REQUEST_TIMEOUT, 
                allow_redirects=True
            )
            response.raise_for_status()
            print(f"   ✅ Статус: {response.status_code}, длина: {len(response.text)} символов")
            return response.text
        except Exception as e:
            print(f"   ❌ Ошибка загрузки БелТА: {e}")
            return None
    
    def parse_data(self, raw_html):
        """Парсит HTML - ПРОВЕРЕННАЯ ЛОГИКА из первого проекта"""
        if not raw_html:
            return []
        
        soup = BeautifulSoup(raw_html, 'html.parser')
        news_items = []

        # --- ОСНОВНАЯ ЛОГИКА: Ищем все div и article, у которых в классе есть 'news' или 'item' ---
        # Это работает рекурсивно, обходя все уровни вложенности
        for item in soup.find_all(['div', 'article'], class_=lambda c: c and ('news' in c.lower() or 'item' in c.lower())):
            try:
                # Извлекаем время
                time_tag = item.find('time')
                time_str = time_tag.text.strip() if time_tag else ""
                
                # Извлекаем категорию (если есть)
                category_tag = item.find(['span', 'a'], class_=lambda c: c and ('category' in c.lower() or 'tag' in c.lower() or 'rubric' in c.lower() or 'date_rubric' in c.lower()))
                category = category_tag.text.strip() if category_tag else ""
                
                # Извлекаем заголовок
                # Ищем по классам 'title' или 'headline', или просто берем первый 'a' внутри блока
                title_tag = item.find(['h2', 'h3', 'a'], class_=lambda c: c and ('title' in c.lower() or 'headline' in c.lower() or 'link' in c.lower() or 'lenta_item_title' in c))
                if not title_tag:
                    # Если не нашли по классам, ищем любой тег 'a' внутри блока
                    title_tag = item.find('a')
                title = title_tag.text.strip() if title_tag else ""
                
                # Извлекаем краткое описание (если есть)
                desc_tag = item.find(['p', 'div'], class_=lambda c: c and ('desc' in c.lower() or 'announce' in c.lower() or 'text' in c.lower() or 'lenta_textsmall' in c))
                description = desc_tag.text.strip() if desc_tag else ""
                
                # Если есть заголовок и он достаточно длинный (больше 10 символов), считаем это новостью
                if title and len(title) > 10:
                    # Формируем дату с сегодняшним днём
                    news_date = self._parse_date_with_today(time_str)
                    
                    news_items.append({
                        "source": self.source.get('name', 'БелТА'),
                        "date": news_date,
                        "time": time_str,
                        "category": category,
                        "title": title,
                        "description": description,
                        "text": f"{title}. {description}" if description else title
                    })
            except Exception as e:
                print(f"   ⚠️ Ошибка при парсинге элемента: {e}")
                continue

        # Если новостей не найдено — выводим предупреждение
        if not news_items:
            print("   ⚠️ Не найдено новостей. Проверьте структуру сайта.")
        else:
            print(f"   ✅ Найдено новостей: {len(news_items)}")

        # --- ДИАГНОСТИКА: показываем первые 5 новостей ---
        for i, item in enumerate(news_items[:5]):
            print(f"   📝 Новость {i+1}: {item['title'][:60]}...")
            if item['category']:
                print(f"      Категория: {item['category']}")
            if item['time']:
                print(f"      Время: {item['time']}")

        return news_items
    
    def _parse_date_with_today(self, time_str):
        """Возвращает сегодняшнюю дату + время из строки"""
        today = date.today()
        
        if not time_str:
            return datetime(today.year, today.month, today.day, 0, 0)
        
        try:
            time_parts = time_str.strip().split(':')
            if len(time_parts) == 2:
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                return datetime(today.year, today.month, today.day, hour, minute)
        except:
            pass
        
        return datetime(today.year, today.month, today.day, 0, 0)
