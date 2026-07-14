# src/parsers/belta_parser.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .base_parser import BaseParser
from src.config import REQUEST_TIMEOUT

class BeltaParser(BaseParser):
    """Парсер для сайта БелТА - точная структура по вашему примеру"""
    
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
        """Парсит HTML и извлекает новости из структуры БелТА"""
        if not raw_html:
            return []
        
        soup = BeautifulSoup(raw_html, 'html.parser')
        news_items = []
        
        # --- ИЩЕМ БЛОКИ НОВОСТЕЙ ПО КЛАССУ news_item lenta_item ---
        blocks = soup.find_all('div', class_=lambda c: c and ('news_item' in c or 'lenta_item' in c) if c else False)
        print(f"   📋 Найдено блоков новостей: {len(blocks)}")
        
        for block in blocks:
            # --- ИЗВЛЕКАЕМ ВРЕМЯ И КАТЕГОРИЮ ---
            date_div = block.find('div', class_='date')
            time = ""
            category = ""
            
            if date_div:
                # Время - это текст до тега a
                time = date_div.contents[0].strip() if date_div.contents else ""
                # Категория - в теге a с классом date_rubric
                category_tag = date_div.find('a', class_='date_rubric')
                category = category_tag.text.strip() if category_tag else ""
            
            # --- ИЗВЛЕКАЕМ ССЫЛКУ НА НОВОСТЬ ---
            link_tag = block.find('a', href=lambda h: h and ('/news/' in h or '/economics/' in h or '/comments/' in h or '/society/' in h))
            if not link_tag:
                link_tag = block.find('a', href=True)
            
            if not link_tag:
                continue
            
            href = link_tag.get('href', '')
            if href and not href.startswith('http'):
                href = f"https://belta.by{href}"
            
            # --- ИЗВЛЕКАЕМ ЗАГОЛОВОК ---
            title_span = link_tag.find('span', class_='lenta_item_title')
            title = title_span.text.strip() if title_span else ""
            
            # Если заголовок не найден, пробуем взять текст из link_tag
            if not title:
                title = link_tag.text.strip()
            
            # Пропускаем, если заголовок слишком короткий
            if not title or len(title) < 10:
                continue
            
            # --- ИЗВЛЕКАЕМ ОПИСАНИЕ ---
            desc_span = link_tag.find('span', class_='lenta_textsmall')
            description = ""
            if desc_span:
                # Извлекаем текст, включая текст из вложенных div
                description = desc_span.get_text(separator=" ", strip=True)
            
            # --- ФОРМИРУЕМ ЗАПИСЬ ---
            news_items.append({
                "source": self.source.get('name', 'БелТА'),
                "date": self._parse_time(time),
                "time": time,
                "category": category,
                "title": title,
                "description": description,
                "text": f"{title}. {description}" if description else title,
                "url": href
            })
        
        # --- Если не нашли новости, пробуем альтернативный метод ---
        if not news_items:
            print("   ⚠️ Не найдено блоков news_item, ищу ссылки с датами...")
            for link in soup.find_all('a', href=True):
                parent = link.find_parent()
                if parent and parent.find('div', class_='date'):
                    date_div = parent.find('div', class_='date')
                    time = date_div.contents[0].strip() if date_div.contents else ""
                    title = link.text.strip()
                    if title and len(title) > 10:
                        news_items.append({
                            "source": self.source.get('name', 'БелТА'),
                            "date": datetime.now(),
                            "time": time,
                            "category": "",
                            "title": title,
                            "description": "",
                            "text": title,
                            "url": link.get('href', '')
                        })
        
        print(f"   ✅ Спарсено новостей: {len(news_items)}")
        
        # --- ДИАГНОСТИКА: показываем первые 5 новостей ---
        for i, item in enumerate(news_items[:5]):
            print(f"   📝 Новость {i+1}: {item['title'][:60]}...")
            if item['category']:
                print(f"      Категория: {item['category']}")
            if item['description']:
                print(f"      Описание: {item['description'][:60]}...")
        
        return news_items
    
    def _parse_time(self, time_str):
        """Парсит время из строки (формат 15:53)"""
        if not time_str:
            return datetime.now()
        try:
            return datetime.strptime(time_str.strip(), "%H:%M")
        except:
            return datetime.now()
