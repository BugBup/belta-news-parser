import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from github_models import GitHubModelsClient # Условный импорт для примера

# --- Конфигурация ---
NEWS_URL = "https://belta.by/all_news"
OUTPUT_FILE = "digest.md"

# Инициализация клиента для GitHub Models
# В реальном GitHub Actions переменная GITHUB_TOKEN доступна автоматически
client = GitHubModelsClient(
    model="gpt-4o-mini",
    token=os.environ.get("GITHUB_TOKEN")
)

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

    # Находим все блоки новостей (по структуре сайта)
    # Используем универсальный поиск: ищем элементы с датой/временем и заголовком
    for item in soup.find_all(['div', 'article'], class_=lambda c: c and ('news' in c.lower() or 'item' in c.lower())):
        # Извлекаем время
        time_tag = item.find('time')
        time = time_tag.text.strip() if time_tag else ""

        # Извлекаем категорию (обычно перед заголовком)
        category_tag = item.find('a', class_=lambda c: c and 'category' in c.lower()) or \
                       item.find('span', class_=lambda c: c and 'category' in c.lower())
        category = category_tag.text.strip() if category_tag else ""

        # Извлекаем заголовок
        title_tag = item.find(['h2', 'h3', 'a'], class_=lambda c: c and ('title' in c.lower() or 'headline' in c.lower())) or \
                    item.find('a', class_=lambda c: c and 'link' in c.lower())
        title = title_tag.text.strip() if title_tag else ""

        # Извлекаем краткое описание
        desc_tag = item.find('p', class_=lambda c: c and ('desc' in c.lower() or 'announce' in c.lower())) or \
                   item.find('div', class_=lambda c: c and ('desc' in c.lower() or 'announce' in c.lower()))
        description = desc_tag.text.strip() if desc_tag else ""

        # Если есть заголовок - добавляем новость
        if title:
            news_items.append({
                "time": time,
                "category": category,
                "title": title,
                "description": description
            })

    # Если не нашли новости по классам - пробуем найти по структуре ссылок с датами
    if not news_items:
        for link in soup.find_all('a', href=True):
            # Ищем ссылки, ведущие на новости (содержат дату в URL или рядом)
            parent = link.find_parent()
            if parent and parent.find('time'):
                time = parent.find('time').text.strip()
                title = link.text.strip()
                if title and len(title) > 10:  # Фильтруем короткие ссылки
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
        news_text += f"[{item['time']}] {item['category']} - {item['title']}\n"
        if item['description']:
            news_text += f"   {item['description']}\n"

    # Запрос к ИИ
    prompt = f"""
    Ты - помощник, который составляет краткий дайджест новостей.
    На основе приведенного ниже списка новостей за сегодня, составь структурированный дайджест.

    Правила:
    1. Сгруппируй новости по темам (политика, экономика, происшествия, общество, культура, спорт, мир и т.д.).
    2. Для каждой группы напиши 1-2 предложения, обобщающие события.
    3. В конце добавь раздел "Главное", выделив 2-3 самые важные новости дня.
    4. Используй формат Markdown для структурирования.

    {news_text}
    """

    try:
        response = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка при обращении к ИИ: {e}")
        return f"Не удалось сгенерировать дайджест.\n\n{news_text}"

def save_digest(digest):
    """Сохраняет дайджест в файл"""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# Дайджест новостей Беларуси\n\n")
        f.write(f"**Дата:** {datetime.now().strftime('%d.%m.%Y')}\n\n")
        f.write(digest)
        f.write(f"\n\n---\n*Сгенерировано автоматически {datetime.now().strftime('%H:%M:%S')}*")

def main():
    print("Начинаю парсинг новостей с belta.by...")
    news = parse_news()
    print(f"Найдено новостей: {len(news)}")

    if news:
        print("Формирую дайджест через ИИ...")
        digest = create_digest(news)
        save_digest(digest)
        print(f"✅ Дайджест сохранен в файл {OUTPUT_FILE}")
    else:
        print("❌ Новости не найдены. Проверьте структуру сайта.")

if __name__ == "__main__":
    main()
