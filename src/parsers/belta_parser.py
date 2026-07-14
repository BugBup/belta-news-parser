# src/parsers/belta_parser.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .base_parser import BaseParser
from src.config import REQUEST_TIMEOUT

class BeltaParser(BaseParser):
    """Парсер для сайта БелТА - простая и надежная логика"""
    
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
        """Парсит HTML - простая логика: ищем все элементы с 'news' или 'item' в классе"""
        if not raw_html:
            return []
        
        soup = BeautifulSoup(raw_html, 'html.parser')
        news_items = []
        
        # --- ПРОСТАЯ ЛОГИКА: Ищем все div и article, у которых в классе есть 'news' или 'item' ---
        # Это работало раньше и должно работать сейчас
        blocks = soup.find_all(['div', 'article'], 
                              class_=lambda c: c and ('news' in c.lower() or 'item' in c.lower()) if c else False)
        
        print(f"   📋 Найдено блоков с 'news'/'item': {len(blocks)}")
        
        for block in blocks:
            # --- ИЗВЛЕКАЕМ ЗАГОЛОВОК ---
            # Ищем любой тег, который выглядит как заголовок
            title_tag = None
            
            # Сначала ищем по классам 'title' или 'headline'
            title_tag = block.find(['h2', 'h3', 'h4', 'a'], 
                                  class_=lambda c: c and ('title' in c.lower() or 'headline' in c.lower() or 'link' in c.lower()) if c else False)
            
            # Если не нашли, берем первый тег a или h2/h3 внутри блока
            if not title_tag:
                title_tag = block.find(['h2', 'h3', 'a'])
            
            # Если все еще нет, берем любой тег с текстом
            if not title_tag:
                title_tag = block.find(lambda tag: tag.name in ['h2', 'h3', 'h4', 'a', 'p'] and len(tag.text.strip()) > 20)
            
            if not title_tag:
                continue
                
            title = title_tag.text.strip()
            
            # Пропускаем слишком короткие заголовки
            if len(title) < 10:
                continue
            
            # --- ИЗВЛЕКАЕМ ВРЕМЯ (если есть) ---
            time_tag = block.find('time')
            time = time_tag.text.strip() if time_tag else ""
            
            # --- ИЗВЛЕКАЕМ КАТЕГОРИЮ (если есть) ---
            category_tag = block.find(['span', 'a'], 
                                     class_=lambda c: c and ('category' in c.lower() or 'tag' in c.lower() or 'rubric' in c.lower()) if c else False)
            category = category_tag.text.strip() if category_tag else ""
            
            # --- ИЗВЛЕКАЕМ ТЕКСТ (описание) ---
            # Берем весь текст из блока, но исключаем заголовок и служебные элементы
            # Удаляем из блока теги script, style, nav, footer
            for tag in block(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            
            # Удаляем сам заголовок из текста, чтобы он не дублировался
            if title_tag:
                title_tag.extract()
            
            # Получаем оставшийся текст
            full_text = block.get_text(separator=" ", strip=True)
            
            # Если текст слишком длинный, обрезаем
            if len(full_text) > 2000:
                full_text = full_text[:2000] + "..."
            
            # --- ФОРМИРУЕМ ЗАПИСЬ ---
            news_items.append({
                "source": self.source.get('name', 'БелТА'),
                "date": self._parse_time(time),
                "time": time,
                "category": category,
                "title": title,
                "description": full_text[:500] if full_text else "",  # Первые 500 символов как описание
                "text": f"{title}. {full_text}" if full_text else title
            })
        
        # --- Если не нашли по классам, пробуем альтернативный метод ---
        if not news_items:
            print("   ⚠️ Не найдено блоков по классам, ищу ссылки с датами...")
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
        
        # --- Показываем первые 3 новости для диагностики ---
        for i, item in enumerate(news_items[:3]):
            print(f"   📝 Новость {i+1}: {item['title'][:60]}...")
            if item['description']:
                print(f"      Описание: {item['description'][:60]}...")
        
        return news_items
    
    def _parse_time(self, time_str):
        """Парсит время из строки"""
        if not time_str:
            return datetime.now()
        try:
            return datetime.strptime(time_str.strip(), "%H:%M")
        except:
            return datetime.now()
