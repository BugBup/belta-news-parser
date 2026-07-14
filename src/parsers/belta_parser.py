# src/parsers/belta_parser.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .base_parser import BaseParser
from src.config import REQUEST_TIMEOUT

class BeltaParser(BaseParser):
    """Парсер для сайта БелТА"""
    
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
        """Парсит HTML и извлекает новости"""
        if not raw_html:
            return []
        
        soup = BeautifulSoup(raw_html, 'html.parser')
        news_items = []
        
        # --- ДИАГНОСТИКА: Ищем все возможные блоки новостей ---
        # Способ 1: Ищем div/article с классом, содержащим 'news' или 'item'
        blocks = soup.find_all(['div', 'article'], 
                              class_=lambda c: c and ('news' in c.lower() or 'item' in c.lower() or 'post' in c.lower()) if c else False)
        print(f"   📋 Найдено блоков с 'news'/'item': {len(blocks)}")
        
        # Способ 2: Ищем все ссылки с датами (запасной вариант)
        if not blocks:
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
            print(f"   📋 Найдено по ссылкам: {len(news_items)}")
            return news_items
        
        # --- ОСНОВНОЙ ПАРСИНГ ---
        for i, block in enumerate(blocks):
            # --- ИЗВЛЕКАЕМ ВРЕМЯ ---
            time_tag = block.find('time')
            time = time_tag.text.strip() if time_tag else ""
            
            # --- ИЗВЛЕКАЕМ КАТЕГОРИЮ (ИЩЕМ ТОЛЬКО ПРЯМЫХ ПОТОМКОВ) ---
            category = ""
            category_tag = block.find(['span', 'a'], 
                                     class_=lambda c: c and ('category' in c.lower() or 'tag' in c.lower() or 'rubric' in c.lower()) if c else False)
            if category_tag:
                category = category_tag.text.strip()
            
            # --- ИЗВЛЕКАЕМ ЗАГОЛОВОК (ГЛАВНЫЙ ЭЛЕМЕНТ) ---
            # Ищем по классам, содержащим 'title' или 'headline', затем 'link'
            title_tag = block.find(['h2', 'h3', 'a'], 
                                  class_=lambda c: c and ('title' in c.lower() or 'headline' in c.lower()) if c else False)
            if not title_tag:
                title_tag = block.find('a', class_=lambda c: c and 'link' in c.lower() if c else False)
            if not title_tag:
                # Если не нашли по классам, берем любой тег a внутри блока
                title_tag = block.find('a')
            title = title_tag.text.strip() if title_tag else ""
            
            # --- ИЗВЛЕКАЕМ ОПИСАНИЕ (НЕ ПУТАЕМ С ЗАГОЛОВКОМ) ---
            # Ищем ТОЛЬКО ТЕГИ p или div, но не заголовки
            desc_tag = None
            for tag in block.find_all(['p', 'div']):
                # Проверяем, что это не заголовок и не содержит только ссылку
                if tag.name in ['h1', 'h2', 'h3', 'h4']:
                    continue
                if tag.find('a') and len(tag.text.strip()) < 50:
                    continue
                if 'title' in tag.get('class', []) or 'headline' in tag.get('class', []):
                    continue
                desc_tag = tag
                break
            
            if not desc_tag:
                desc_tag = block.find('p', class_=lambda c: c and ('desc' in c.lower() or 'announce' in c.lower() or 'text' in c.lower()) if c else False)
            description = desc_tag.text.strip() if desc_tag else ""
            
            # --- ЧИСТИМ ОТ ДУБЛИРОВАНИЯ ---
            # Если заголовок совпадает с началом описания — убираем из описания
            if title and description.startswith(title):
                description = description[len(title):].strip()
            
            # Если описание слишком похоже на заголовок — очищаем
            if title and description and len(description) < 20 and title in description:
                description = ""
            
            # --- ФОРМИРУЕМ ЗАПИСЬ ---
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
                
                # --- ДИАГНОСТИКА: показываем первые 10 новостей ---
                if len(news_items) <= 10:
                    print(f"   📝 Новость {len(news_items)}: {title[:60]}...")
        
        print(f"   ✅ Спарсено новостей: {len(news_items)}")
        return news_items
    
    def _parse_time(self, time_str):
        """Парсит время из строки"""
        if not time_str:
            return datetime.now()
        try:
            # Пытаемся распарсить время
            return datetime.strptime(time_str.strip(), "%H:%M")
        except:
            return datetime.now()
