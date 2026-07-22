# src/digest_generator.py

import os
import json
import requests
from datetime import datetime

class DigestGenerator:
    """Генератор дайджеста через GitHub Models"""
    
    def __init__(self):
        self.token = os.environ.get("GITHUB_TOKEN")
        self.endpoint = "https://models.github.ai/inference/chat/completions"
        self.model = "openai/gpt-4o-mini"
    
    def create_digest(self, filtered_items):
        """Создает аналитический дайджест из отфильтрованных новостей"""
        if not filtered_items:
            return "Новостей по заданным темам за последние дни не найдено."
        
        prompt = self._build_prompt(filtered_items)
        response = self._call_model(prompt)
        
        if response:
            return response
        else:
            return self._build_fallback_digest(filtered_items)
    
    def _build_prompt(self, items):
        """Формирует промпт для ИИ"""
        news_text = self._format_news(items)
        
        return f"""
        Ты — профессиональный аналитик по устойчивому развитию, ESG-инвестициям и финансовым рынкам.
        
        На основе приведенных новостей, составь аналитический дайджест за последние дни.
        Сосредоточься на следующих темах:
        - ESG (экологическое, социальное и корпоративное управление)
        - Зеленая экономика и энергетика
        - Ответственное инвестирование
        - Финансовая отчетность и стандарты устойчивого развития
        - Регуляторные изменения в этих сферах
        
        Новости для анализа:
        {news_text}
        
        Требования к ответу:
        1. Используй структурированный формат Markdown.
        2. Начни с краткого резюме (2-3 предложения о ключевых трендах).
        3. Раздели новости по тематическим категориям с заголовками.
        4. В конце добавь раздел "Главные выводы" с 3-5 пунктами.
        5. Укажи источники, если это возможно, с ссылками на пост/новость.
        6. Ответ должен быть на русском языке.
        
        Твой ответ:
        """
    
    def _format_news(self, items):
        """Форматирует новости для промпта"""
        result = ""
        for i, item in enumerate(items, 1):
            source = item.get('source', 'Неизвестный источник')
            title = item.get('title', '')
            description = item.get('description', '')
            text = item.get('text', '')
            date = item.get('date', '')
            
            result += f"\nНовость {i}:\n"
            result += f"Источник: {source}\n"
            if date:
                result += f"Дата: {date}\n"
            if title:
                result += f"Заголовок: {title}\n"
            if description:
                result += f"Краткое описание: {description}\n"
            if text:
                result += f"Текст: {text}\n"
        
        return result
    
    def _call_model(self, prompt):
        """Отправляет запрос к GitHub Models"""
        if not self.token:
            print("⚠️ GITHUB_TOKEN не найден")
            return None
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Ты — профессиональный аналитик по ESG и инвестициям."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5,
            "max_tokens": 3000,
        }
        
        try:
            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"❌ Ошибка при вызове модели: {e}")
            return None
    
    def _build_fallback_digest(self, items):
        """Создает простой дайджест без ИИ (запасной вариант)"""
        result = "# 📊 Дайджест новостей\n\n"
        result += f"*Сформирован {datetime.now().strftime('%d.%m.%Y %H:%M')}*\n\n"
        result += "## Найденные новости\n\n"
        
        for item in items:
            title = item.get('title', 'Без заголовка')
            source = item.get('source', 'Неизвестный источник')
            description = item.get('description', '')
            matched = item.get('matched_keyword', '')
            
            result += f"### {title}\n"
            result += f"**Источник:** {source}\n"
            if matched:
                result += f"**Ключевое слово:** {matched}\n"
            if description:
                result += f"\n{description}\n"
            result += "\n---\n\n"
        
        return result
