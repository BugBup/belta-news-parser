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
            print(f"   ❌ Ошибка загрузки Telegram-канала {self.source.get('name')}: {e}")
            return None
    
    def parse_data(self, raw_html):
        """Парсит HTML веб-страницы Telegram и извлекает сообщения"""
        if not raw_html:
            return []
        
        soup = BeautifulSoup(raw_html, 'html.parser')
        messages = []
        
        # --- ИЩЕМ БЛОКИ СООБЩЕНИЙ ---
        # Используем основной класс Telegram
        message_divs = soup.find_all('div', class_='tgme_widget_message')
        print(f"   📋 Найдено блоков сообщений: {len(message_divs)}")
        
        for message_div in message_divs:
            # --- ИЗВЛЕКАЕМ ТЕКСТ СООБЩЕНИЯ ---
            text_div = message_div.find('div', class_='tgme_widget_message_text')
            if not text_div:
                continue
            
            text = text_div.get_text(strip=True)
            
            # Пропускаем очень короткие сообщения (меньше 10 символов)
            if len(text) < 10:
                continue
            
            # --- ИЗВЛЕКАЕМ ДАТУ И ВРЕМЯ ---
            date_tag = message_div.find('time', class_='time')
            date_str = ""
            if date_tag:
                date_str = date_tag.get('datetime', '')
            
            # Парсим дату из атрибута datetime
            parsed_date = self._parse_telegram_datetime(date_str)
            
            # --- ИЗВЛЕКАЕМ ССЫЛКУ ---
            link_tag = message_div.find('a', class_='tgme_widget_message_date')
            message_url = link_tag.get('href') if link_tag else None
            
            messages.append({
                "source": self.source.get('name', 'Telegram'),
                "date": parsed_date,
                "date_str": date_str,
                "text": text,
                "url": message_url,
                "raw_html": str(text_div)
            })
        
        # --- ДИАГНОСТИКА ---
        print(f"   ✅ Спарсено сообщений: {len(messages)}")
        for i, msg in enumerate(messages[:3]):
            print(f"   📝 Сообщение {i+1}: {msg['text'][:80]}...")
            print(f"      Дата: {msg['date']}")
        
        return messages
    
    def _parse_telegram_datetime(self, datetime_str):
        """
        Парсит дату из атрибута datetime тега time.
        Формат: 2026-07-09T09:10:19+00:00
        """
        if not datetime_str:
            return datetime.now()
        
        try:
            # Убираем временную зону (+00:00) для простоты
            dt_str = datetime_str.split('+')[0]
            return datetime.fromisoformat(dt_str)
        except:
            # Если не удалось распарсить, возвращаем сегодня
            return datetime.now()
