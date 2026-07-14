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
# Используем актуальный эндпоинт для GitHub Models
MODELS_ENDPOINT = "https://models.github.ai/inference/chat/completions"
# Указываем модель с правильным префиксом
MODEL_NAME = "openai/gpt-4o-mini"

def call_github_models(prompt):
    """
    Отправляет запрос к актуальному GitHub Models API.
    Документация: https://docs.github.com/en/github-models
    """
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN не найден в переменных окружения")

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
        response = requests.post(MODELS_ENDPOINT, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при обращении к GitHub Models: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Ответ сервера: {e.response.text}")
        return None

def parse_news():
    """
    Парсит новости с belta.by/all_news используя рекурсивный поиск.
    Находит все элементы div и article, у которых в классе есть 'news' или 'item'.
    """
    
    # Заголовки для имитации браузера
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    
    try:
        response = requests.get(NEWS_URL, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()
        print(f"✅ Статус ответа: {response.status_code}")
    except requests.exceptions.Timeout:
        print("❌ Ошибка: Превышен таймаут ожидания ответа от сервера.")
        return []
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Ошибка подключения: {e}")
        print("   Возможно, сервер временно недоступен или блокирует запросы.")
        return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Другая ошибка при загрузке страницы: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    news_items = []

    # --- РЕКУРСИВНЫЙ ПОИСК: Ищем все div и article, у которых в классе есть 'news' или 'item' ---
    # find_all() по умолчанию работает рекурсивно, обходя все уровни вложенности
    for item in soup.find_all(['div', 'article'], class_=lambda c: c and ('news' in c.lower() or 'item' in c.lower())):
        # Извлекаем время
        time_tag = item.find('time')
        time = time_tag.text.strip() if time_tag else ""
        
        # Извлекаем категорию (если есть)
        category_tag = item.find(['span', 'a'], class_=lambda c: c and ('category' in c.lower() or 'tag' in c.lower() or 'rubric' in c.lower()))
        category = category_tag.text.strip() if category_tag else ""
        
        # Извлекаем заголовок
        # Ищем по классам 'title' или 'headline', или просто берем первый 'a' внутри блока
        title_tag = item.find(['h2', 'h3', 'a'], class_=lambda c: c and ('title' in c.lower() or 'headline' in c.lower() or 'link' in c.lower()))
        if not title_tag:
            # Если не нашли по классам, ищем любой тег 'a' внутри блока
            title_tag = item.find('a')
        title = title_tag.text.strip() if title_tag else ""
        
        # Извлекаем краткое описание (если есть)
        desc_tag = item.find(['p', 'div'], class_=lambda c: c and ('desc' in c.lower() or 'announce' in c.lower() or 'text' in c.lower()))
        description = desc_tag.text.strip() if desc_tag else ""
        
        # Если есть заголовок и он достаточно длинный (больше 10 символов), считаем это новостью
        if title and len(title) > 10:
            news_items.append({
                "time": time,
                "category": category,
                "title": title,
                "description": description
            })

    # Если новостей не найдено — выводим предупреждение
    if not news_items:
        print("⚠️ Не найдено новостей. Проверьте структуру сайта.")
    else:
        print(f"✅ Найдено новостей: {len(news_items)}")

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

    print("🧠 Отправляю запрос к GitHub Models...")
    response = call_github_models(prompt)
    
    if response and 'choices' in response:
        return response['choices'][0]['message']['content']
    else:
        print("⚠️ Не удалось получить ответ от модели. Возвращаю сырые новости.")
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
    
    if news:
        digest = create_digest(news)
        save_digest(digest)
        print(f"✅ Дайджест сохранен в файл {OUTPUT_FILE}")
    else:
        print("❌ Новости не найдены. Проверьте структуру сайта.")

if __name__ == "__main__":
    main()
