# src/parsers/belta_parser.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from .base_parser import BaseParser
from src.config import REQUEST_TIMEOUT

class BeltaParser(BaseParser):
    """Парсер для сайта БелТА - проверенная логика (работала в начале)"""
    
    def __init__(self, source_config):
        super().__init__(source_config)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
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
        """Парсит HTML и извлекает новости - проверенная логика из первого проекта"""
        if not raw_html:
            return []
        
        soup = BeautifulSoup(raw_html, 'html.parser')
        news_items = []
        
        # --- ВОЗВРАЩАЕМСЯ К ПРОВЕРЕННОЙ ЛОГИКЕ: ищем все div и article с 'news' или 'item' в классе ---
        # Это работало в самом начале проекта, когда парсили только БелТА
        for block in soup.find_all(['div', 'article'], 
                                   class_=lambda c: c and ('news' in c.lower() or 'item' in c.lower()) if c else False):
            
            # --- ИЗВЛЕКАЕМ ВРЕМЯ ---
            time_tag = block.find('time')
            time_str = time_tag.text.strip() if time_tag else ""
            
            # --- ИЗВЛЕКАЕМ КАТЕГОРИЮ ---
            category_tag = block.find(['span', 'a'], 
                                     class_=lambda c: c and ('category' in c.lower() or 'tag' in c.lower() or 'rubric' in c.lower() or 'date_rubric' in c.lower()) if c else False)
            category = category_tag.text.strip() if category_tag else ""
            
            # --- ИЗВЛЕКАЕМ ЗАГОЛОВОК ---
            # Ищем span с классом lenta_item_title (как в вашем примере)
            title_span = block.find('span', class_=lambda c: c and ('lenta_item_title' in c or 'title' in c.lower()) if c else False)
            if title_span:
                title = title_span.text.strip()
            else:
                # Если не нашли, ищем по старым классам
                title_tag = block.find(['h2', 'h3', 'a'], 
                                      class_=lambda c: c and ('title' in c.lower() or 'headline' in c.lower() or 'link' in c.lower()) if c else False)
                if not title_tag:
                    title_tag = block.find('a')
                title = title_tag.text.strip() if title_tag else ""
            
            # --- ИЗВЛЕКАЕМ ОПИСАНИЕ ---
            desc_span = block.find('span', class_=lambda c: c and ('lenta_textsmall' in c or 'textsmall' in c or 'desc' in c.lower()) if c else False)
            if desc_span:
                description = desc_span.get_text(separator=" ", strip=True)
            else:
                # Ищем по старым классам
                desc_tag = block.find(['p', 'div'], 
                                     class_=lambda c: c and ('desc' in c.lower() or 'announce' in c.lower() or 'text' in c.lower()) if c else False)
                description = desc_tag.text.strip() if desc_tag else ""
            
            # --- Если есть заголовок и он достаточно длинный ---
            if title and len(title) > 10:
                # --- ФОРМИРУЕМ ДАТУ: используем СЕГОДНЯШНЮЮ дату + время из новости ---
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
        
        # --- Если не нашли по классам, пробуем альтернативный метод ---
        if not news_items:
            print("   ⚠️ Не найдено по классам, ищу ссылки с датами...")
            for link in soup.find_all('a', href=True):
                parent = link.find_parent()
                if parent and parent.find('time'):
                    time_str = parent.find('time').text.strip()
                    title = link.text.strip()
                    if title and len(title) > 10:
                        news_items.append({
                            "source": self.source.get('name', 'БелТА'),
                            "date": self._parse_date_with_today(time_str),
                            "time": time_str,
                            "category": "",
                            "title": title,
                            "description": "",
                            "text": title
                        })
        
        print(f"   ✅ Спарсено новостей: {len(news_items)}")
        
        # --- ДИАГНОСТИКА: показываем первые 5 новостей ---
        for i, item in enumerate(news_items[:5]):
            print(f"   📝 Новость {i+1}: {item['title'][:60]}...")
            print(f"      Дата: {item['date']}")
            if item['category']:
                print(f"      Категория: {item['category']}")
        
        return news_items
    
    def _parse_date_with_today(self, time_str):
        """
        Парсит время и возвращает datetime с СЕГОДНЯШНЕЙ датой.
        Если время не указано, возвращает сегодняшнюю дату с 00:00.
        """
        today = date.today()
        
        if not time_str:
            return datetime(today.year, today.month, today.day, 0, 0)
        
        try:
            # Пробуем распарсить время в формате HH:MM
            time_parts = time_str.strip().split(':')
            if len(time_parts) == 2:
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                return datetime(today.year, today.month, today.day, hour, minute)
        except:
            pass
        
        # Если не удалось распарсить, возвращаем сегодня с 00:00
        return datetime(today.year, today.month, today.day, 0, 0)
