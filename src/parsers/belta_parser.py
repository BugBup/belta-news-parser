# src/parsers/belta_parser.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from .base_parser import BaseParser
from src.config import REQUEST_TIMEOUT

class BeltaParser(BaseParser):
    """Парсер для сайта БелТА - точный поиск новостных блоков"""
    
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
        """Парсит HTML - точный поиск блоков с новостями"""
        if not raw_html:
            return []
        
        soup = BeautifulSoup(raw_html, 'html.parser')
        news_items = []
        
        # --- ИЩЕМ ТОЛЬКО БЛОКИ С КЛАССОМ news_item lenta_item ---
        # Это точный класс блока новости на БелТА (из вашего примера)
        news_blocks = soup.find_all('div', class_=lambda c: c and 'news_item' in c.split() and 'lenta_item' in c.split() if c else False)
        
        # Если не нашли по точному совпадению, пробуем найти по частичному
        if not news_blocks:
            news_blocks = soup.find_all('div', class_=lambda c: c and ('news_item' in c or 'lenta_item' in c) if c else False)
        
        print(f"   📋 Найдено блоков новостей: {len(news_blocks)}")
        
        for block in news_blocks:
            # --- ИЗВЛЕКАЕМ ВРЕМЯ И КАТЕГОРИЮ ИЗ БЛОКА .date ---
            date_block = block.find('div', class_='date')
            time_str = ""
            category = ""
            
            if date_block:
                # Время - это первый текстовый узел в date_block
                for content in date_block.contents:
                    if isinstance(content, str) and content.strip():
                        time_str = content.strip()
                        break
                
                # Категория - в теге a с классом date_rubric
                category_tag = date_block.find('a', class_='date_rubric')
                category = category_tag.text.strip() if category_tag else ""
            
            # --- ИЗВЛЕКАЕМ ССЫЛКУ И ЗАГОЛОВОК ---
            # Ссылка - это первый тег a внутри блока (он оборачивает всю новость)
            link_tag = block.find('a', href=True)
            if not link_tag:
                continue
            
            # Заголовок - в span с классом lenta_item_title
            title_span = link_tag.find('span', class_='lenta_item_title')
            title = title_span.text.strip() if title_span else ""
            
            # Если заголовок не найден, пробуем взять текст из ссылки
            if not title:
                title = link_tag.text.strip()
            
            # Пропускаем мусор и короткие заголовки
            if not title or len(title) < 10:
                continue
            
            # --- ИЗВЛЕКАЕМ ОПИСАНИЕ ---
            desc_span = link_tag.find('span', class_='lenta_textsmall')
            description = desc_span.get_text(separator=" ", strip=True) if desc_span else ""
            
            # --- ФОРМИРУЕМ ДАТУ ---
            news_date = self._parse_date_with_today(time_str)
            
            # --- СОХРАНЯЕМ ---
            news_items.append({
                "source": self.source.get('name', 'БелТА'),
                "date": news_date,
                "time": time_str,
                "category": category,
                "title": title,
                "description": description,
                "text": f"{title}. {description}" if description else title
            })
        
        # --- ЕСЛИ НЕ НАШЛИ, ПРОБУЕМ ЗАПАСНОЙ ВАРИАНТ ---
        if not news_items:
            print("   ⚠️ Не найдено блоков news_item. Ищу все ссылки с датами...")
            # Ищем все ссылки, рядом с которыми есть блок с классом date
            for link in soup.find_all('a', href=True):
                # Проверяем, есть ли у родительского блока div с классом date
                parent = link.find_parent()
                if not parent:
                    continue
                
                date_block = parent.find('div', class_='date')
                if not date_block:
                    continue
                
                # Извлекаем время
                time_str = ""
                for content in date_block.contents:
                    if isinstance(content, str) and content.strip():
                        time_str = content.strip()
                        break
                
                # Заголовок - текст ссылки
                title = link.text.strip()
                if not title or len(title) < 10:
                    continue
                
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
            print(f"      Дата: {item['date']}, Категория: {item.get('category', 'нет')}")
        
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
