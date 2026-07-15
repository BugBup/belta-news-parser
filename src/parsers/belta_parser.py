# src/parsers/belta_parser.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from .base_parser import BaseParser
from src.config import REQUEST_TIMEOUT

class BeltaParser(BaseParser):
    """Парсер для сайта БелТА - надёжная логика"""
    
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
        """Парсит HTML - гарантированно находит все новости"""
        if not raw_html:
            return []
        
        soup = BeautifulSoup(raw_html, 'html.parser')
        news_items = []
        
        # --- ИЩЕМ ВСЕ БЛОКИ С КЛАССОМ news_item ---
        # Это самый надёжный способ: все новости на БелТА находятся в блоках с этим классом
        news_blocks = soup.find_all('div', class_='news_item')
        print(f"   📋 Найдено блоков news_item: {len(news_blocks)}")
        
        for block in news_blocks:
            try:
                # --- 1. ИЗВЛЕКАЕМ ВРЕМЯ И КАТЕГОРИЮ ИЗ .date ---
                date_div = block.find('div', class_='date')
                time_str = ""
                category = ""
                
                if date_div:
                    # Время - это текст до тега a
                    for content in date_div.contents:
                        if isinstance(content, str) and content.strip():
                            time_str = content.strip()
                            break
                    
                    # Категория - в a.date_rubric
                    cat_tag = date_div.find('a', class_='date_rubric')
                    category = cat_tag.text.strip() if cat_tag else ""
                
                # --- 2. ИЗВЛЕКАЕМ ССЫЛКУ ---
                link_tag = block.find('a', href=True)
                if not link_tag:
                    continue
                
                # --- 3. ИЗВЛЕКАЕМ ЗАГОЛОВОК ---
                title_span = link_tag.find('span', class_='lenta_item_title')
                title = title_span.text.strip() if title_span else ""
                
                # Если не нашли через span, берём title из ссылки
                if not title:
                    title = link_tag.get('title', '').strip()
                
                # Если всё ещё нет, берём текст ссылки
                if not title:
                    title = link_tag.text.strip()
                
                # Пропускаем, если заголовок слишком короткий
                if not title or len(title) < 10:
                    continue
                
                # --- 4. ИЗВЛЕКАЕМ ОПИСАНИЕ ---
                desc_span = link_tag.find('span', class_='lenta_textsmall')
                description = desc_span.get_text(separator=" ", strip=True) if desc_span else ""
                
                # --- 5. ФОРМИРУЕМ ДАТУ С СЕГОДНЯШНИМ ДНЁМ ---
                news_date = self._parse_date_with_today(time_str)
                
                # --- 6. СОХРАНЯЕМ ---
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
                print(f"   ⚠️ Ошибка при парсинге блока: {e}")
                continue
        
        # --- ЗАПАСНОЙ ВАРИАНТ: если не нашли news_item ---
        if not news_items:
            print("   ⚠️ Не найдено news_item. Ищу все div с lenta_item...")
            for block in soup.find_all('div', class_=lambda c: c and 'lenta_item' in c.split() if c else False):
                # Аналогичная логика, но с другим классом
                link_tag = block.find('a', href=True)
                if not link_tag:
                    continue
                
                title_span = link_tag.find('span', class_='lenta_item_title')
                title = title_span.text.strip() if title_span else ""
                if not title or len(title) < 10:
                    continue
                
                desc_span = link_tag.find('span', class_='lenta_textsmall')
                description = desc_span.get_text(separator=" ", strip=True) if desc_span else ""
                
                # Пытаемся извлечь время из date
                date_div = block.find('div', class_='date')
                time_str = ""
                if date_div:
                    for content in date_div.contents:
                        if isinstance(content, str) and content.strip():
                            time_str = content.strip()
                            break
                
                news_items.append({
                    "source": self.source.get('name', 'БелТА'),
                    "date": self._parse_date_with_today(time_str),
                    "time": time_str,
                    "category": "",
                    "title": title,
                    "description": description,
                    "text": f"{title}. {description}" if description else title
                })
        
        print(f"   ✅ Спарсено новостей: {len(news_items)}")
        
        # --- ДИАГНОСТИКА: показываем первые 5 новостей ---
        for i, item in enumerate(news_items[:5]):
            print(f"   📝 Новость {i+1}: {item['title'][:60]}...")
            if item['category']:
                print(f"      Категория: {item['category']}")
        
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
