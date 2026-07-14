# src/parsers/telegram_parser.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
from .base_parser import BaseParser
from src.config import REQUEST_TIMEOUT

class TelegramParser(BaseParser):
    """Парсер для публичных Telegram-каналов через веб-версию"""
    
    def __init__(self, source_config):
        super().__init__(source_config)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            "Connection": "keep-alive",
        }
    
    def fetch_data(self):
        """Загружает веб-страницу канала"""
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
            print(f"   ❌ Ошибка загрузки: {e}")
            return None
    
    def parse_data(self, raw_html):
        """Парсит HTML веб-страницы Telegram и извлекает сообщения"""
        if not raw_html:
            return []
        
        soup = BeautifulSoup(raw_html, 'html.parser')
        messages = []
        
        # --- ДИАГНОСТИКА: Ищем все возможные блоки сообщений ---
        # Способ 1: Ищем div с классом, содержащим 'message'
        message_divs = soup.find_all('div', class_=lambda c: c and 'message' in c.lower() if c else False)
        print(f"   📋 Найдено div с 'message': {len(message_divs)}")
        
        # Способ 2: Ищем div с классом, содержащим 'post'
        post_divs = soup.find_all('div', class_=lambda c: c and 'post' in c.lower() if c else False)
        print(f"   📋 Найдено div с 'post': {len(post_divs)}")
        
        # Способ 3: Ищем div с классом 'tgme_widget_message' (классический класс Telegram)
        tg_divs = soup.find_all('div', class_='tgme_widget_message')
        print(f"   📋 Найдено div с 'tgme_widget_message': {len(tg_divs)}")
        
        # --- ПАРСИНГ: Используем все найденные способы ---
        all_candidates = []
        all_candidates.extend(message_divs)
        all_candidates.extend(post_divs)
        all_candidates.extend(tg_divs)
        
        # Удаляем дубликаты (по id или по содержимому)
        seen = set()
        unique_candidates = []
        for div in all_candidates:
            div_id = div.get('id', '')
            if div_id and div_id in seen:
                continue
            if div_id:
                seen.add(div_id)
            unique_candidates.append(div)
        
        print(f"   📋 Уникальных кандидатов: {len(unique_candidates)}")
        
        for message_div in unique_candidates:
            # Извлекаем текст сообщения
            text_div = message_div.find('div', class_=lambda c: c and ('text' in c.lower() or 'message' in c.lower()) if c else False)
            if not text_div:
                text_div = message_div.find('div', class_='tgme_widget_message_text')
            
            if not text_div:
                continue
            
            text = text_div.get_text(strip=True)
            
            # Пропускаем очень короткие сообщения
            if len(text) < 5:
                continue
            
            # Извлекаем дату
            date_div = message_div.find('div', class_=lambda c: c and 'date' in c.lower() if c else False)
            date_str = date_div.get_text(strip=True) if date_div else ""
            
            # Извлекаем ссылку на сообщение
            link_tag = message_div.find('a', class_=lambda c: c and ('message_link' in c.lower() or 'date' in c.lower()) if c else False)
            message_url = link_tag.get('href') if link_tag else None
            
            # Парсим дату
            parsed_date = self._parse_telegram_date(date_str)
            
            messages.append({
                "source": self.source.get('name', 'Telegram'),
                "date": parsed_date,
                "date_str": date_str,
                "text": text,
                "url": message_url,
                "raw_html": str(text_div)
            })
        
        print(f"   ✅ Спарсено сообщений: {len(messages)}")
        
        # --- ДИАГНОСТИКА: Показываем первые 3 сообщения ---
        for i, msg in enumerate(messages[:3]):
            print(f"   📝 Пример {i+1}: {msg['text'][:100]}...")
        
        return messages
    
    def _parse_telegram_date(self, date_str):
        """Парсит дату из Telegram (формат может быть разным)"""
        if not date_str:
            return datetime.now()
        
        # Пробуем разные форматы
        formats = [
            "%b %d, %Y",      # Feb 15, 2025
            "%Y-%m-%d",       # 2025-02-15
            "%d.%m.%Y",       # 15.02.2025
            "%H:%M",          # 15:30 (текущий день)
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except:
                continue
        
        # Если не удалось распарсить, возвращаем сегодня
        return datetime.now()
