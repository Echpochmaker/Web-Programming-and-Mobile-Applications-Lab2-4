from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, unique=True, index=True, nullable=True)

    # Поля для локальной аутентификации
    password_hash = Column(String, nullable=True)
    salt = Column(String, nullable=True)

    # Поля для OAuth
    yandex_id = Column(String, unique=True, index=True, nullable=True)
    vk_id = Column(String, unique=True, index=True, nullable=True)

    # Стандартные поля
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Связи - ИСПРАВЛЕНО!
    tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")
    tests = relationship("Test", back_populates="owner")  # было 'items', стало 'tests'
    # Добавь после существующих связей
    test_results = relationship("TestResult", back_populates="user", cascade="all, delete-orphan")

     # Поля для сброса пароля
    reset_password_token = Column(String, nullable=True, index=True)
    reset_password_expires = Column(DateTime(timezone=True), nullable=True)