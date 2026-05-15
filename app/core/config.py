from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MongoDB
    MONGO_URI: str
    
    # JWT Settings
    JWT_ACCESS_SECRET: str
    JWT_REFRESH_SECRET: str
    JWT_ACCESS_EXPIRATION: str = "15m"
    JWT_REFRESH_EXPIRATION: str = "7d"
    
    # Yandex OAuth
    YANDEX_CLIENT_ID: str
    YANDEX_CLIENT_SECRET: str
    YANDEX_CALLBACK_URL: str
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    CACHE_TTL_DEFAULT: int = 300

    # MinIO
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minio_admin"
    MINIO_SECRET_KEY: str = "minio_secure_password_change_in_prod"
    MINIO_BUCKET: str = "testing-files"
    MINIO_USE_SSL: bool = False
    MAX_FILE_SIZE: int = 10_485_760

    # Optional VK OAuth
    VK_CLIENT_ID: Optional[str] = None
    VK_CLIENT_SECRET: Optional[str] = None
    VK_CALLBACK_URL: Optional[str] = None

    # RabbitMQ
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "student"
    RABBITMQ_PASS: str = "student_secure_rabbit_pass"
    
    # SMTP
    SMTP_HOST: str = "smtp.yandex.ru"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = ""
    SMTP_SECURE: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()