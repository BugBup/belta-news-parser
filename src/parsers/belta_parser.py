# src/parsers/belta_parser.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from .base_parser import BaseParser
from src.config import REQUEST_TIMEOUT

class BeltaParser(BaseParser):
    """Парсер для сайта БелТА — улучшенная версия с использованием title из ссылки"""
    
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
        """Парсит HTML и извлекает новости с использованием title из ссылки"""
        if not raw_html:
            return []
        
        soup = BeautifulSoup(raw_html, 'html.parser')
        news_items = []

        # --- ИЩЕМ ВСЕ БЛОКИ, ГДЕ ЕСТЬ ССЫЛКА С АТРИБУТОМ title ---
        # Это самый надёжный способ: каждая новость — это ссылка с title
        for link in soup.find_all('a', title=True):
            # Проверяем, что ссылка ведёт на новость (содержит /news/, /economics/, /world/ и т.д.)
            href = link.get('href', '')
            if not href or not any(x in href for x in ['/news/', '/economics/', '/world/', '/society/', '/regions/', '/comments/', '/sport/', '/culture/', '/incidents/']):
                continue
            
            # Извлекаем заголовок (из текста ссылки или из span.lenta_item_title)
            title_span = link.find('span', class_='lenta_item_title')
            title = title_span.text.strip() if title_span else link.text.strip()
            
            # Пропускаем мусор
            if not title or len(title) < 10 or 'фотохроника' in title.lower():
                continue
            
            # --- ИЗВЛЕКАЕМ ОПИСАНИЕ ИЗ АТРИБУТА title ССЫЛКИ ---
            description = link.get('title', '').strip()
            
            # Если описание пустое, пробуем взять из lenta_textsmall
            if not description:
                desc_span = link.find('span', class_='lenta_textsmall')
                if desc_span:
                    description = desc_span.get_text(separator=" ", strip=True)
            
            # --- ИЗВЛЕКАЕМ ВРЕМЯ И КАТЕГОРИЮ ИЗ БЛОКА .date ---
            # Ищем родительский блок news_item или lenta_item
            parent_block = link.find_parent('div', class_=lambda c: c and ('news_item' in c or 'lenta_item' in c) if c else False)
            time_str = ""
            category = ""
            
            if parent_block:
                date_div = parent_block.find('div', class_='date')
                if date_div:
                    # Время — первый текстовый узел
                    for content in date_div.contents:
                        if isinstance(content, str) and content.strip():
                            time_str = content.strip()
                            break
                    # Категория — в a.date_rubric
                    cat_tag = date_div.find('a', class_='date_rubric')
                    category = cat_tag.text.strip() if cat_tag else ""
            
            # Если не нашли родительский блок, пробуем найти date рядом со ссылкой
            if not time_str:
                date_div = link.find_previous('div', class_='date')
                if date_div:
                    for content in date_div.contents:
                        if isinstance(content, str) and content.strip():
                            time_str = content.strip()
                            break
                    cat_tag = date_div.find('a', class_='date_rubric') if date_div else None
                    category = cat_tag.text.strip() if cat_tag else ""
            
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

        # Если новостей не найдено — пробуем запасной метод
        if not news_items:
            print("   ⚠️ Не найдено новостей через title. Пробую запасной метод...")
            for item in soup.find_all(['div', 'article'], class_=lambda c: c and ('news_item' in c or 'lenta_item' in c) if c else False):
                link = item.find('a', href=True)
                if not link:
                    continue
                
                title_span = link.find('span', class_='lenta_item_title')
                title = title_span.text.strip() if title_span else link.text.strip()
                if not title or len(title) < 10 or 'фотохроника' in title.lower():
                    continue
                
                description = link.get('title', '')
                if not description:
                    desc_span = link.find('span', class_='lenta_textsmall')
                    description = desc_span.get_text(separator=" ", strip=True) if desc_span else ""
                
                date_div = item.find('div', class_='date')
                time_str = ""
                category = ""
                if date_div:
                    for content in date_div.contents:
                        if isinstance(content, str) and content.strip():
                            time_str = content.strip()
                            break
                    cat_tag = date_div.find('a', class_='date_rubric')
                    category = cat_tag.text.strip() if cat_tag else ""
                
                news_items.append({
                    "source": self.source.get('name', 'БелТА'),
                    "date": self._parse_date_with_today(time_str),
                    "time": time_str,
                    "category": category,
                    "title": title,
                    "description": description,
                    "text": f"{title}. {description}" if description else title
                })

        if not news_items:
            print("   ❌ Новостей не найдено. Проверьте структуру сайта.")
        else:
            print(f"   ✅ Найдено новостей: {len(news_items)}")

        # --- ДИАГНОСТИКА: показываем первые 5 новостей ---
        for i, item in enumerate(news_items[:5]):
            print(f"   📝 Новость {i+1}: {item['title'][:60]}...")
            if item['category']:
                print(f"      Категория: {item['category']}")
            if item['time']:
                print(f"      Время: {item['time']}")
            if item['description']:
                print(f"      Описание: {item['description'][:60]}...")

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
