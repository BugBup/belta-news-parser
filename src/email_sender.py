# src/email_sender.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

class EmailSender:
    """Отправляет email с дайджестом"""
    
    def __init__(self, config):
        self.to_email = config.get('to', '')
        self.subject = config.get('subject', 'Дайджест новостей')
        self.smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', 587))
        self.smtp_user = os.environ.get('SMTP_USER', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
    
    def send(self, digest_text, attachment_path=None):
        """
        Отправляет письмо с текстом дайджеста и опциональным вложением
        """
        if not self.to_email:
            print("⚠️ Email не указан")
            return False
        
        if not self.smtp_user or not self.smtp_password:
            print("⚠️ SMTP не настроен (пропущены SMTP_USER или SMTP_PASSWORD)")
            return False
        
        try:
            # Создаем письмо
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_user
            msg['To'] = self.to_email
            msg['Subject'] = self.subject
            
            # HTML-версия письма с красивым оформлением
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                    .footer {{ margin-top: 30px; font-size: 12px; color: #7f8c8d; text-align: center; }}
                </style>
            </head>
            <body>
                <h1>📊 Дайджест по инвестициям и ESG</h1>
                {digest_text}
                <div class="footer">
                    Автоматически сгенерировано {self._get_current_time()}<br>
                    Источники: БелТА, Telegram-каналы
                </div>
            </body>
            </html>
            """
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Если есть вложение
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    attach = MIMEBase('application', 'octet-stream')
                    attach.set_payload(f.read())
                    encoders.encode_base64(attach)
                    attach.add_header(
                        'Content-Disposition',
                        f'attachment; filename={os.path.basename(attachment_path)}'
                    )
                    msg.attach(attach)
            
            # Отправляем
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email отправлен на {self.to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при отправке email: {e}")
            return False
    
    def _get_current_time(self):
        """Возвращает текущее время в читаемом формате"""
        from datetime import datetime
        return datetime.now().strftime('%d.%m.%Y %H:%M')
