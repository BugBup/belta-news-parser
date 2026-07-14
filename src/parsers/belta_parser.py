# src/parsers/belta_parser.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .base_parser import BaseParser
from src.config import REQUEST_TIMEOUT

class BeltaParser(BaseParser):
    """Парсер для сайта БелТА (проверенная версия)"""
    
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
        """Парсит HTML и извлекает новости (проверенная логика)"""
        if not raw_html:
            return []
        
        soup = BeautifulSoup(raw_html, 'html.parser')
        news_items = []
        
        # --- ИЩЕМ БЛОКИ НОВОСТЕЙ ПО КЛАССАМ (как в старой версии) ---
        for block in soup.find_all(['div', 'article'], 
                                   class_=lambda c: c and ('news' in c.lower() or 'item' in c.lower() or 'post' in c.lower()) if c else False):
            
            # Извлекаем время
            time_tag = block.find('time')
            time = time_tag.text.strip() if time_tag else ""
            
            # Извлекаем заголовок (ищем по классам title, headline, link)
            title_tag = block.find(['h2', 'h3', 'a'], 
                                  class_=lambda c: c and ('title' in c.lower() or 'headline' in c.lower() or 'link' in c.lower()) if c else False)
            if not title_tag:
                title_tag = block.find('a')
            title = title_tag.text.strip() if title_tag else ""
            
            # Извлекаем категорию
            category_tag = block.find(['span', 'a'], 
                                     class_=lambda c: c and ('category' in c.lower() or 'tag' in c.lower() or 'rubric' in c.lower()) if c else False)
            category = category_tag.text.strip() if category_tag else ""
            
            # Извлекаем описание (ищем p или div с классами desc, announce, text)
            desc_tag = block.find(['p', 'div'], 
                                 class_=lambda c: c and ('desc' in c.lower() or 'announce' in c.lower() or 'text' in c.lower()) if c else False)
            description = desc_tag.text.strip() if desc_tag else ""
            
            # Если есть заголовок и он достаточно длинный
            if title and len(title) > 10:
                news_items.append({
                    "source": self.source.get('name', 'БелТА'),
                    "date": self._parse_time(time),
                    "time": time,
                    "category": category,
                    "title": title,
                    "description": description,
                    "text": f"{title}. {description}" if description else title
                })
        
        # --- ЗАПАСНОЙ МЕТОД: если не нашли по классам ---
        if not news_items:
            print("   ⚠️ Не найдено блоков по классам, ищем ссылки с датами...")
            for link in soup.find_all('a', href=True):
                parent = link.find_parent()
                if parent and parent.find('time'):
                    time = parent.find('time').text.strip()
                    title = link.text.strip()
                    if title and len(title) > 10:
                        news_items.append({
                            "source": self.source.get('name', 'БелТА'),
                            "date": datetime.now(),
                            "time": time,
                            "category": "",
                            "title": title,
                            "description": "",
                            "text": title
                        })
        
        print(f"   ✅ Спарсено новостей: {len(news_items)}")
        return news_items
    
    def _parse_time(self, time_str):
        """Парсит время из строки"""
        if not time_str:
            return datetime.now()
        try:
            return datetime.strptime(time_str.strip(), "%H:%M")
        except:
            return datetime.now()
