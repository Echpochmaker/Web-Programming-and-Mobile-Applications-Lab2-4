import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    async def send_welcome_email(to_email: str, display_name: str):
        """Отправка приветственного письма"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Добро пожаловать в Систему Тестирования!'
        msg['From'] = settings.SMTP_FROM
        msg['To'] = to_email
        
        text = f"""
Здравствуйте, {display_name}!

Спасибо за регистрацию в Системе Тестирования!
Ваш аккаунт успешно создан.

Для входа используйте: http://localhost:4200

С уважением,
Команда Системы Тестирования
        """
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Добро пожаловать, {display_name}!</h2>
            <p>Спасибо за регистрацию в <b>Системе Тестирования</b>!</p>
            <p>Ваш аккаунт успешно создан.</p>
            <p><a href="http://localhost:4200" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Войти в систему</a></p>
            <hr>
            <p style="color: #666;">С уважением, Команда Системы Тестирования</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        
        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASS,
                use_tls=settings.SMTP_SECURE,
            )
            logger.info(f"Welcome email sent to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise