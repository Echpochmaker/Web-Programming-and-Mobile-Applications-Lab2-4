from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import re

# Регистрация
class UserRegister(BaseModel):
    email: Optional[EmailStr] = Field(
        None, 
        description="Email пользователя. Должен быть уникальным.",
        example="user@example.com"
    )
    phone: Optional[str] = Field(
        None, 
        description="Телефон пользователя в международном формате",
        example="+79991234567"
    )
    password: str = Field(
        ..., 
        min_length=8,
        description="Пароль пользователя. Минимум 8 символов.",
        example="strongpassword123"
    )
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not re.match(r'^\+?[0-9]{10,15}$', v):
            raise ValueError('Invalid phone number format')
        return v
    
    @validator('email')
    def validate_email_or_phone(cls, v, values):
        if not v and not values.get('phone'):
            raise ValueError('Either email or phone is required')
        return v

# Вход
class UserLogin(BaseModel):
    login: str = Field(
        ..., 
        description="Email или телефон пользователя",
        example="user@example.com"
    )
    password: str = Field(
        ..., 
        description="Пароль пользователя",
        example="strongpassword123"
    )

# Ответ с информацией о пользователе (без чувствительных данных)
class UserResponse(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор пользователя")
    email: Optional[str] = Field(None, description="Email пользователя")
    phone: Optional[str] = Field(None, description="Телефон пользователя")
    created_at: datetime = Field(..., description="Дата регистрации")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "phone": "+79991234567",
                "created_at": "2026-03-18T12:00:00.000Z"
            }
        }

# Запрос на сброс пароля
class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(
        ..., 
        description="Email для восстановления пароля",
        example="user@example.com"
    )

# Сброс пароля
class ResetPasswordRequest(BaseModel):
    token: str = Field(
        ..., 
        description="Токен для сброса пароля из email-письма (выводится в консоль)",
        example="abc123def456..."
    )
    new_password: str = Field(
        ..., 
        min_length=8,
        description="Новый пароль. Минимум 8 символов.",
        example="newstrongpassword123"
    )

# Ответ после аутентификации (для /whoami)
class AuthResponse(BaseModel):
    user: UserResponse = Field(..., description="Информация о пользователе")
    message: str = Field(..., description="Сообщение о статусе аутентификации", example="Authenticated")

# OAuth callback (внутренняя схема)
class OAuthCallback(BaseModel):
    code: str = Field(..., description="Код авторизации от Яндекса")
    state: str = Field(..., description="Параметр state для защиты от CSRF")