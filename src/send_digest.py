# src/send_digest.py

import os
import sys
from datetime import datetime

# Добавляем путь к корню проекта
# Это нужно, чтобы Python мог найти модуль src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import EMAIL_CONFIG
from src.email_sender import EmailSender

def main():
    """Отправляет на почту самый свежий дайджест"""
    print("📧 Запуск отправки email...")
    
    # Находим самый свежий файл дайджеста
    digest_files = []
    digests_dir = "digests"
    
    if os.path.exists(digests_dir):
        for file in os.listdir(digests_dir):
            if file.startswith("digest-") and file.endswith(".md"):
                file_path = os.path.join(digests_dir, file)
                digest_files.append((file_path, os.path.getmtime(file_path)))
    
    if not digest_files:
        print("⚠️ Дажестов для отправки не найдено.")
        return
    
    # Сортируем по времени изменения (самый свежий последний)
    digest_files.sort(key=lambda x: x[1])
    latest_digest_path = digest_files[-1][0]
    
    print(f"📄 Найден дайджест: {latest_digest_path}")
    
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
