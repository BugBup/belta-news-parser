# src/send_digest.py

import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import EMAIL_CONFIG
from src.email_sender import EmailSender

def main():
    print("📧 Запуск отправки email...")
    
    # Находим самый свежий файл дайджеста за сегодня
    today = datetime.now().strftime('%Y-%m-%d')
    digests_dir = "digests"
    
    if not os.path.exists(digests_dir):
        print("⚠️ Папка digests не найдена")
        return
    
    # Ищем файлы дайджеста за сегодня
    today_files = []
    for file in os.listdir(digests_dir):
        if file.startswith("digest-") and file.endswith(".md"):
            file_path = os.path.join(digests_dir, file)
            # Проверяем, что файл за сегодня
            if today in file:
                today_files.append((file_path, os.path.getmtime(file_path)))
    
    # Если нет файлов за сегодня, берём самый свежий из всех
    if not today_files:
        print("⚠️ Файлов за сегодня не найдено, ищу самый свежий...")
        all_files = []
        for file in os.listdir(digests_dir):
            if file.startswith("digest-") and file.endswith(".md"):
                file_path = os.path.join(digests_dir, file)
                all_files.append((file_path, os.path.getmtime(file_path)))
        
        if not all_files:
            print("⚠️ Дажестов для отправки не найдено.")
            return
        
        all_files.sort(key=lambda x: x[1])
        latest_digest_path = all_files[-1][0]
    else:
        # Сортируем по времени и берём самый свежий
        today_files.sort(key=lambda x: x[1])
        latest_digest_path = today_files[-1][0]
    
    print(f"📄 Отправляю дайджест: {latest_digest_path}")
    
    # Читаем содержимое
    try:
        with open(latest_digest_path, 'r', encoding='utf-8') as f:
            digest_content = f.read()
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return
    
    # Отправляем
    sender = EmailSender(EMAIL_CONFIG)
    success = sender.send(digest_content, attachment_path=latest_digest_path)
    
    if success:
        print("✅ Email отправлен успешно!")
    else:
        print("❌ Не удалось отправить email")

if __name__ == "__main__":
    main()
