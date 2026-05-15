from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse
import httpx
import secrets
import os
from datetime import datetime, timedelta
from app.core.queue import QueueService
from app.core.cache import cache
from app.core.auth import get_current_user, get_optional_user
from app.services.user_service import UserService
from app.services.token_service import TokenService
from app.schemas.auth import (
    UserRegister, UserLogin, UserResponse, AuthResponse,
    ForgotPasswordRequest, ResetPasswordRequest
)
from app.models.user_doc import User

router = APIRouter(prefix="/auth", tags=["authentication"])

# Хранилище для state (OAuth)
oauth_states = {}

def set_token_cookies(response: Response, access_token: str, refresh_token: str):
    """Устанавливает токены в HttpOnly cookies"""
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

def clear_token_cookies(response: Response):
    """Удаляет токены из cookies"""
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


@router.post(
    "/register",
    status_code=201,
    summary="Регистрация нового пользователя",
    description="Создает новую учетную запись. Требуется email и пароль, телефон опционален.",
    responses={
        201: {"description": "Пользователь успешно создан"},
        400: {"description": "Неверные данные (неверный формат email или телефона)"},
        409: {"description": "Пользователь с таким email или телефоном уже существует"}
    }
)
async def register(user_data: UserRegister):
    """
    Регистрация нового пользователя.
    
    - **email**: email пользователя (обязательно, если не указан телефон)
    - **phone**: телефон в международном формате (опционально)
    - **password**: пароль, минимум 8 символов
    """
    if user_data.email:
        existing = await User.find_one({"email": user_data.email})
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")
    
    if user_data.phone:
        existing = await User.find_one({"phone": user_data.phone})
        if existing:
            raise HTTPException(status_code=409, detail="Phone already registered")
        
    user = await UserService.create_user(user_data)
    
    # Публикуем событие в RabbitMQ (асинхронно, не ждём)
    import asyncio
    asyncio.create_task(
        QueueService.publish(
            routing_key='user.registered',
            payload={
                "userId": str(user.id),
                "email": user.email,
                "displayName": user.email.split('@')[0] if user.email else 'User'
            }
        )
    )
    
    return {"message": "User created successfully", "user_id": str(user.id)}


@router.post(
    "/login",
    summary="Вход в систему",
    description="Аутентифицирует пользователя и устанавливает JWT токены в HttpOnly cookies.",
    responses={
        200: {"description": "Успешный вход, токены установлены в cookies"},
        401: {"description": "Неверные учетные данные (логин или пароль)"}
    }
)
async def login(
    user_data: UserLogin,
    request: Request,
    response: Response
):
    """
    Вход пользователя в систему.
    
    - **login**: email или телефон пользователя
    - **password**: пароль
    
    При успешном входе устанавливаются cookies:
    - **access_token**: JWT токен доступа (действителен 15 минут)
    - **refresh_token**: токен обновления (действителен 7 дней)
    """
    user = await UserService.get_by_login(user_data.login)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.password_hash or not user.salt:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not UserService.verify_password(user_data.password, user.password_hash, user.salt):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token, refresh_token = await TokenService.create_token_pair(
        str(user.id),
        request.headers.get("user-agent"),
        request.client.host
    )
    
    set_token_cookies(response, access_token, refresh_token)
    
    cache.delete(f"testing:users:profile:{user.id}")
    
    return {"message": "Login successful"}


@router.post(
    "/refresh",
    summary="Обновление токенов",
    description="Обновляет пару access/refresh токенов, используя действующий refresh токен из cookies.",
    responses={
        200: {"description": "Токены успешно обновлены"},
        401: {"description": "Refresh токен отсутствует или недействителен"}
    }
)
async def refresh(
    request: Request,
    response: Response
):
    """
    Обновление токенов доступа.
    
    Требует наличия refresh_token в cookies.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    
    result = await TokenService.refresh_tokens(
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
    description="Возвращает данные авторизованного пользователя. Использует кеш Redis для ускорения.",
    responses={
        200: {"description": "Данные пользователя"},
        401: {"description": "Не авторизован - требуется вход в систему"}
    }
)
async def whoami(user: User = Depends(get_current_user)):
    """
    Возвращает профиль текущего авторизованного пользователя.
    
    При первом запросе данные берутся из БД и кешируются на 5 минут.
    Повторные запросы возвращаются из кеша Redis.
    """
    cache_key = f"testing:users:profile:{user.id}"
    
    cached = cache.get(cache_key)
    if cached:
        return AuthResponse(user=UserResponse(**cached), message="Authenticated (cached)")
    
    user_dict = {
        "id": str(user.id),
        "email": user.email,
        "phone": user.phone,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
    cache.set(cache_key, user_dict, ttl=300)
    
    return AuthResponse(user=UserResponse(**user_dict), message="Authenticated")


@router.post(
    "/logout",
    summary="Выход из текущей сессии",
    description="Завершает текущую сессию: удаляет JTI из Redis, отзывает refresh токен, очищает cookies.",
    responses={
        200: {"description": "Успешный выход из системы"},
        401: {"description": "Не авторизован"}
    }
)
async def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user)
):
    """
    Выход из текущей сессии.
    
    - Удаляет JTI текущего access токена из Redis (мгновенная инвалидация)
    - Отзывает refresh токен в базе данных
    - Очищает cookies
    - Инвалидирует кеш профиля
    """
    cache.delete_pattern(f"testing:auth:user:{user.id}:access:*")
    
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        token_hash = TokenService.hash_token(refresh_token)
        await TokenService.revoke_tokens(str(user.id), all_sessions=False, 
                                         current_token_hash=token_hash)
    
    cache.delete(f"testing:users:profile:{user.id}")
    
    clear_token_cookies(response)
    return {"message": "Logged out"}


@router.post(
    "/logout-all",
    summary="Выход из всех сессий",
    description="Завершает ВСЕ активные сессии пользователя на всех устройствах.",
    responses={
        200: {"description": "Все сессии завершены"},
        401: {"description": "Не авторизован"}
    }
)
async def logout_all(
    response: Response,
    user: User = Depends(get_current_user)
):
    """
    Выход из всех сессий пользователя.
    
    - Удаляет все JTI пользователя из Redis
    - Отзывает все refresh токены в базе данных
    - Очищает cookies
    - Инвалидирует кеш профиля
    """
    cache.delete_pattern(f"testing:auth:user:{user.id}:access:*")
    
    await TokenService.revoke_tokens(str(user.id), all_sessions=True)
    
    cache.delete(f"testing:users:profile:{user.id}")
    
    clear_token_cookies(response)
    return {"message": "All sessions terminated"}


@router.get(
    "/oauth/yandex",
    summary="Инициация входа через Яндекс ID",
    description="Возвращает URL для перенаправления на страницу авторизации Яндекса (OAuth 2.0).",
    responses={
        200: {"description": "URL для авторизации"}
    }
)
async def yandex_oauth():
    """
    Инициирует OAuth 2.0 поток с Яндекс ID.
    
    Возвращает URL, на который нужно перенаправить пользователя.
    """
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
    "/yandex/callback",
    summary="Обработка callback от Яндекс OAuth",
    description="Callback URL для Яндекс OAuth. Обменивает код на токен, получает данные пользователя и создает сессию.",
    responses={
        200: {"description": "OAuth успешен, токены установлены"},
        400: {"description": "Ошибка получения токена от Яндекса"},
        500: {"description": "Внутренняя ошибка сервера"}
    }
)
async def yandex_callback(
    code: str,
    request: Request,
    response: Response
):
    """
    Обрабатывает callback от Яндекса после авторизации пользователя.
    
    - **code**: код авторизации от Яндекса
    """
    print(f"=== YANDEX CALLBACK ===")
    print(f"Code: {code}")
    
    try:
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
        
        if not yandex_token:
            print(f"Error getting token: {token_data}")
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                "https://login.yandex.ru/info",
                headers={"Authorization": f"OAuth {yandex_token}"}
            )
        
        user_info = user_response.json()
        yandex_id = str(user_info.get("id"))
        email = user_info.get("default_email")
        
        print(f"Yandex ID: {yandex_id}, Email: {email}")
        
        user = await UserService.get_by_oauth_id("yandex", yandex_id)
        if not user:
            print("Creating new user...")
            user = await UserService.create_oauth_user("yandex", yandex_id, email)
            print(f"User created: {user.id}")
        else:
            print(f"User found: {user.id}")
        
        access_token, refresh_token = await TokenService.create_token_pair(
            str(user.id),
            request.headers.get("user-agent"),
            request.client.host
        )
        
        set_token_cookies(response, access_token, refresh_token)
        
        cache.delete(f"testing:users:profile:{user.id}")
        
        print("Cookies set, returning success response")
        
        return {
            "success": True,
            "message": "OAuth успешен",
            "user": {
                "id": str(user.id),
                "email": user.email
            }
        }
        
    except Exception as e:
        print(f"ERROR in Yandex callback: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/forgot-password",
    summary="Запрос на сброс пароля",
    description="Отправляет токен для сброса пароля на email пользователя (в консоль для демонстрации).",
    responses={
        200: {"description": "Если email существует, токен отправлен"}
    }
)
async def forgot_password(request_data: ForgotPasswordRequest):
    """
    Запрос на восстановление пароля.
    
    - **email**: email пользователя для восстановления
    
    Токен сброса выводится в консоль Docker (для демонстрации).
    """
    reset_token = await UserService.create_password_reset_token(request_data.email)
    
    if reset_token:
        print(f"\n=== PASSWORD RESET ===")
        print(f"Email: {request_data.email}")
        print(f"Token: {reset_token}")
        print(f"Reset link: http://localhost:4200/reset-password?token={reset_token}")
        print(f"=== ===\n")
    
    return {"message": "If the email exists, a reset link has been sent"}


@router.post(
    "/reset-password",
    summary="Установка нового пароля",
    description="Устанавливает новый пароль по токену сброса.",
    responses={
        200: {"description": "Пароль успешно изменен"},
        400: {"description": "Недействительный или истекший токен"}
    }
)
async def reset_password(request_data: ResetPasswordRequest):
    """
    Установка нового пароля.
    
    - **token**: токен из письма для сброса пароля
    - **new_password**: новый пароль (минимум 8 символов)
    """
    user = await UserService.reset_password(request_data.token, request_data.new_password)
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    return {"message": "Password reset successful"}