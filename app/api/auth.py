from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import httpx
import secrets
import os
from jose import jwt

from app.core.database import get_db
from app.core.cache import cache
from app.core.auth import get_current_user, get_optional_user
from app.services.user_service import UserService
from app.services.token_service import TokenService
from app.schemas.auth import (
    UserRegister, UserLogin, UserResponse, AuthResponse,
    ForgotPasswordRequest, ResetPasswordRequest
)
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["authentication"])

# Хранилище для state
oauth_states = {}

def set_token_cookies(response: Response, access_token: str, refresh_token: str):
    """Устанавливает токены в HttpOnly cookies"""
    print(f"=== SETTING COOKIES ===")
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=900,
        path="/",
        samesite="lax"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=604800,
        path="/",
        samesite="lax"
    )
    print(f"Cookies установлены")

def clear_token_cookies(response: Response):
    """Удаляет токены из cookies"""
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")

@router.post(
    "/register",
    status_code=201,
    summary="Регистрация нового пользователя",
)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """Регистрация нового пользователя"""
    if user_data.email:
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")
    
    if user_data.phone:
        existing = db.query(User).filter(User.phone == user_data.phone).first()
        if existing:
            raise HTTPException(status_code=409, detail="Phone already registered")
    
    user = UserService.create_user(db, user_data)
    return {"message": "User created successfully", "user_id": user.id}

@router.post(
    "/login",
    summary="Вход пользователя",
)
async def login(
    user_data: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Вход пользователя"""
    user = UserService.get_by_login(db, user_data.login)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not UserService.verify_password(user_data.password, user.password_hash, user.salt):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token, refresh_token = TokenService.create_token_pair(
        db, 
        user.id,
        request.headers.get("user-agent"),
        request.client.host
    )
    
    set_token_cookies(response, access_token, refresh_token)
    
    # Инвалидация кеша профиля при новом входе
    cache.delete(f"testing:users:profile:{user.id}")
    print(f"🗑️ Profile cache invalidated for user {user.id}")
    
    return {"message": "Login successful"}

@router.post(
    "/refresh",
    summary="Обновление токенов",
)
async def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Обновление токенов"""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    
    result = TokenService.refresh_tokens(
        db, 
        refresh_token,
        request.headers.get("user-agent"),
        request.client.host
    )
    
    if not result:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    access_token, new_refresh_token = result
    set_token_cookies(response, access_token, new_refresh_token)
    
    return {"message": "Tokens refreshed"}

@router.get(
    "/whoami",
    response_model=AuthResponse,
    summary="Информация о текущем пользователе",
)
async def whoami(
    user: User = Depends(get_current_user)
):
    cache_key = f"testing:users:profile:{user.id}"
    
    # Проверяем кеш
    cached = cache.get(cache_key)
    if cached:
        print(f"✅ Profile cache HIT: {cache_key}")
        # Восстанавливаем объект из кеша
        return AuthResponse(user=User(**cached), message="Authenticated (cached)")
    
    print(f"❌ Profile cache MISS: {cache_key}")
    
    # Сохраняем в кеш
    user_dict = {
        "id": user.id,
        "email": user.email,
        "phone": user.phone,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
    cache.set(cache_key, user_dict, ttl=300)
    print(f"💾 Profile saved to cache: {cache_key}")
    
    return AuthResponse(user=user, message="Authenticated")

@router.post(
    "/logout",
    summary="Выход из текущей сессии",
)
async def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Выход из текущей сессии"""
    
    # Удаляем ВСЕ JTI пользователя из Redis
    cache.delete_pattern(f"testing:auth:user:{user.id}:access:*")
    print(f"🗑️ All JTI revoked for user {user.id}")
    
    # Отзываем refresh токен в БД (текущую сессию)
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        token_hash = TokenService.hash_token(refresh_token)
        TokenService.revoke_tokens(db, user.id, all_sessions=False, current_token_hash=token_hash)
    
    # Инвалидация кеша профиля
    cache.delete(f"testing:users:profile:{user.id}")
    
    clear_token_cookies(response)
    return {"message": "Logged out"}

@router.post(
    "/logout-all",
    summary="Выход из всех сессий",
)
async def logout_all(
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Выход из всех сессий"""
    
    # Удаляем все JTI пользователя из Redis
    cache.delete_pattern(f"testing:auth:user:{user.id}:access:*")
    print(f"🗑️ All JTI revoked for user {user.id}")
    
    # Отзываем все refresh токены в БД
    TokenService.revoke_tokens(db, user.id, all_sessions=True)
    
    # Инвалидация кеша профиля
    cache.delete(f"testing:users:profile:{user.id}")
    
    clear_token_cookies(response)
    return {"message": "All sessions terminated"}

@router.get(
    "/oauth/yandex",
    summary="Инициация входа через Яндекс",
)
async def yandex_oauth(request: Request):
    """Инициирует вход через Yandex"""
    state = secrets.token_urlsafe(16)
    oauth_states[state] = datetime.utcnow()
    
    for s in list(oauth_states.keys()):
        if (datetime.utcnow() - oauth_states[s]).seconds > 600:
            del oauth_states[s]
    
    auth_url = (
        "https://oauth.yandex.ru/authorize"
        "?response_type=code"
        f"&client_id={os.getenv('YANDEX_CLIENT_ID')}"
        f"&redirect_uri={os.getenv('YANDEX_CALLBACK_URL')}"
        f"&state={state}"
    )
    return {"auth_url": auth_url}

@router.get(
    "/oauth/yandex/callback",
    summary="Обработка callback от Яндекса",
)
async def yandex_callback(
    code: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Обработка callback от Yandex"""
    
    # Обмениваем код на токен
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth.yandex.ru/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": os.getenv("YANDEX_CLIENT_ID"),
                "client_secret": os.getenv("YANDEX_CLIENT_SECRET")
            }
        )
    
    token_data = token_response.json()
    yandex_token = token_data.get("access_token")
    
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://login.yandex.ru/info",
            headers={"Authorization": f"OAuth {yandex_token}"}
        )
    
    user_info = user_response.json()
    yandex_id = user_info.get("id")
    email = user_info.get("default_email")
    
    user = UserService.get_by_oauth_id(db, "yandex", yandex_id)
    if not user:
        user = UserService.create_oauth_user(db, "yandex", yandex_id, email)
    
    # Создаем токены
    access_token, refresh_token = TokenService.create_token_pair(
        db, 
        user.id,
        request.headers.get("user-agent"),
        request.client.host
    )
    
    # Устанавливаем HttpOnly cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=900,
        path="/",
        samesite="lax"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=604800,
        path="/",
        samesite="lax"
    )
    
    # Возвращаем JSON
    return {
        "success": True,
        "message": "OAuth успешен",
        "user": {
            "id": user.id,
            "email": user.email
        }
    }

@router.post(
    "/forgot-password",
    summary="Запрос на сброс пароля",
)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """Запрос на сброс пароля"""
    user = db.query(User).filter(
        User.email == request_data.email,
        User.deleted_at.is_(None)
    ).first()
    
    if user:
        reset_token = secrets.token_urlsafe(32)
        user.reset_password_token = reset_token
        user.reset_password_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        
        print(f"\n=== PASSWORD RESET ===")
        print(f"Email: {request_data.email}")
        print(f"Token: {reset_token}")
        print(f"Reset link: http://localhost:4200/reset-password?token={reset_token}")
        print(f"=== ===\n")
    
    return {"message": "If the email exists, a reset link has been sent"}

@router.post(
    "/reset-password",
    summary="Установка нового пароля",
)
async def reset_password(
    request_data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Установка нового пароля"""
    user = db.query(User).filter(
        User.reset_password_token == request_data.token,
        User.reset_password_expires > datetime.utcnow(),
        User.deleted_at.is_(None)
    ).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    password_hash, salt = UserService.hash_password(request_data.new_password)
    user.password_hash = password_hash
    user.salt = salt
    user.reset_password_token = None
    user.reset_password_expires = None
    
    db.commit()
    
    return {"message": "Password reset successful"}