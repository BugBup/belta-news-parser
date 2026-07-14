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
            response = requests.get(
                self.source['url'], 
                headers=self.headers, 
                timeout=REQUEST_TIMEOUT, 
                allow_redirects=True
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"❌ Ошибка загрузки Telegram-канала {self.source.get('name')}: {e}")
            return None
    
    def parse_data(self, raw_html):
        """Парсит HTML веб-страницы Telegram и извлекает сообщения"""
        if not raw_html:
            return []
        
        soup = BeautifulSoup(raw_html, 'html.parser')
        messages = []
        
        # Ищем все блоки сообщений (обычно div с классом 'message')
        for message_div in soup.find_all('div', class_=lambda c: c and 'message' in c.lower()):
            # Извлекаем текст сообщения
            text_div = message_div.find('div', class_=lambda c: c and 'text' in c.lower())
            if not text_div:
                continue
            
            text = text_div.get_text(strip=True)
            
            # Извлекаем дату
            date_div = message_div.find('div', class_=lambda c: c and 'date' in c.lower())
            date_str = date_div.get_text(strip=True) if date_div else ""
            
            # Извлекаем ссылку на сообщение (если есть)
            link_tag = message_div.find('a', class_=lambda c: c and 'message_link' in c.lower())
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
