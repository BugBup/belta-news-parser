import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- Конфигурация ---
NEWS_URL = "https://belta.by/all_news"
OUTPUT_FILE = "digest.md"

# Получаем токен из переменных окружения (в GitHub Actions он доступен автоматически)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
# Модель для использования через GitHub Models
MODEL_NAME = "gpt-4o-mini"  # Бесплатная модель

def call_github_models(prompt):
    """
    Отправляет запрос к GitHub Models API.
    Документация: https://docs.github.com/en/rest/models
    """
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN не найден в переменных окружения")

    # URL для API GitHub Models
    url = "https://models.inference.github.com/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Ты — полезный ассистент, который составляет дайджесты новостей."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 2000,
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при обращении к GitHub Models: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Ответ сервера: {e.response.text}")
        return None

def parse_news():
    """Парсит новости с belta.by/all_news"""
    try:
        response = requests.get(NEWS_URL, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Ошибка загрузки страницы: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    news_items = []

    # Парсим новости из структуры сайта belta.by
    # Ищем все блоки с классом, содержащим 'news' или 'item'
    for item in soup.find_all(['div', 'article'], class_=lambda c: c and ('news' in c.lower() or 'item' in c.lower() or 'post' in c.lower())):
        # Извлекаем время
        time_tag = item.find('time')
        time = time_tag.text.strip() if time_tag else ""
        
        # Извлекаем категорию
        category_tag = item.find(['span', 'a'], class_=lambda c: c and ('category' in c.lower() or 'tag' in c.lower()))
        category = category_tag.text.strip() if category_tag else ""
        
        # Извлекаем заголовок
        title_tag = item.find(['h2', 'h3', 'a'], class_=lambda c: c and ('title' in c.lower() or 'headline' in c.lower()))
        if not title_tag:
            title_tag = item.find('a', class_=lambda c: c and 'link' in c.lower())
        title = title_tag.text.strip() if title_tag else ""
        
        # Извлекаем краткое описание
        desc_tag = item.find(['p', 'div'], class_=lambda c: c and ('desc' in c.lower() or 'announce' in c.lower() or 'text' in c.lower()))
        description = desc_tag.text.strip() if desc_tag else ""
        
        if title:
            news_items.append({
                "time": time,
                "category": category,
                "title": title,
                "description": description
            })

    # Если не нашли через классы - пробуем найти через ссылки с датами
    if not news_items:
        for link in soup.find_all('a', href=True):
            parent = link.find_parent()
            if parent and parent.find('time'):
                time = parent.find('time').text.strip()
                title = link.text.strip()
                if title and len(title) > 10:
                    news_items.append({
                        "time": time,
                        "category": "",
                        "title": title,
                        "description": ""
                    })

    return news_items

def create_digest(news_list):
    """Формирует дайджест новостей с помощью ИИ"""
    if not news_list:
        return "За сегодня новостей не найдено."

    # Формируем текст для ИИ
    news_text = "Список новостей за сегодня:\n\n"
    for item in news_list:
        news_text += f"[{item['time']}] "
        if item['category']:
            news_text += f"({item['category']}) "
        news_text += f"{item['title']}\n"
        if item['description']:
            news_text += f"   {item['description']}\n"
        news_text += "\n"

    prompt = f"""
    Ты - помощник, который составляет краткий дайджест новостей Беларуси.
    На основе приведенного ниже списка новостей за сегодня, составь структурированный дайджест.

    Правила:
    1. Сгруппируй новости по темам (политика, экономика, происшествия, общество, культура, спорт, мир и т.д.).
    2. Для каждой группы напиши 1-2 предложения, обобщающие события.
    3. В конце добавь раздел "Главное", выделив 2-3 самые важные новости дня.
    4. Используй формат Markdown для структурирования (заголовки, списки).

    Новости:
    {news_text}
    """

    print("Отправляю запрос к GitHub Models...")
    response = call_github_models(prompt)
    
    if response and 'choices' in response:
        return response['choices'][0]['message']['content']
    else:
        print("Не удалось получить ответ от модели. Возвращаю сырые новости.")
        return f"**Не удалось сгенерировать дайджест.**\n\n{news_text}"

def save_digest(digest):
    """Сохраняет дайджест в файл"""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# 📰 Дайджест новостей Беларуси\n\n")
        f.write(f"**Дата:** {datetime.now().strftime('%d.%m.%Y')}\n\n")
        f.write(digest)
        f.write(f"\n\n---\n*Сгенерировано автоматически {datetime.now().strftime('%H:%M:%S')}*")

def main():
    print("🚀 Начинаю парсинг новостей с belta.by...")
    news = parse_news()
    print(f"📊 Найдено новостей: {len(news)}")

    if news:
        print("🧠 Формирую дайджест через GitHub Models...")
        digest = create_digest(news)
        save_digest(digest)
        print(f"✅ Дайджест сохранен в файл {OUTPUT_FILE}")
    else:
        print("❌ Новости не найдены. Проверьте структуру сайта.")

if __name__ == "__main__":
    main()
