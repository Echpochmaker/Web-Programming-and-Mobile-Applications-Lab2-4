from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import httpx
import secrets
import os

from app.core.database import get_db
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
    description="Создает нового пользователя с указанным email и паролем. Email должен быть уникальным.",
    responses={
        201: {
            "description": "Пользователь успешно создан",
            "content": {
                "application/json": {
                    "example": {
                        "message": "User created successfully",
                        "user_id": 1
                    }
                }
            }
        },
        409: {
            "description": "Email или телефон уже зарегистрированы",
            "content": {
                "application/json": {
                    "examples": {
                        "email_exists": {
                            "summary": "Email уже существует",
                            "value": {"detail": "Email already registered"}
                        },
                        "phone_exists": {
                            "summary": "Телефон уже существует",
                            "value": {"detail": "Phone already registered"}
                        }
                    }
                }
            }
        },
        422: {
            "description": "Ошибка валидации данных"
        }
    }
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
    description="Аутентификация пользователя по email/телефону и паролю. Устанавливает HttpOnly cookies с токенами.",
    responses={
        200: {
            "description": "Успешный вход",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Login successful"
                    }
                }
            }
        },
        401: {
            "description": "Неверные учетные данные",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid credentials"
                    }
                }
            }
        }
    }
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
    
    return {"message": "Login successful"}

@router.post(
    "/refresh",
    summary="Обновление токенов",
    description="Обновляет пару токенов (access и refresh) с использованием действующего refresh token из cookie.",
    responses={
        200: {
            "description": "Токены успешно обновлены",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Tokens refreshed"
                    }
                }
            }
        },
        401: {
            "description": "Отсутствует или недействительный refresh token",
            "content": {
                "application/json": {
                    "examples": {
                        "no_token": {
                            "summary": "Нет токена",
                            "value": {"detail": "No refresh token"}
                        },
                        "invalid_token": {
                            "summary": "Недействительный токен",
                            "value": {"detail": "Invalid refresh token"}
                        }
                    }
                }
            }
        }
    }
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
    description="Возвращает данные аутентифицированного пользователя. Требует валидный access token.",
    responses={
        200: {
            "description": "Данные пользователя",
            "content": {
                "application/json": {
                    "example": {
                        "user": {
                            "id": 1,
                            "email": "user@example.com",
                            "phone": "+79991234567",
                            "created_at": "2026-03-18T12:00:00.000Z"
                        },
                        "message": "Authenticated"
                    }
                }
            }
        },
        401: {
            "description": "Не авторизован",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authenticated"
                    }
                }
            }
        }
    }
)
async def whoami(
    user: User = Depends(get_current_user)
):
    """Информация о текущем пользователе"""
    return AuthResponse(user=user, message="Authenticated")

@router.post(
    "/logout",
    summary="Выход из текущей сессии",
    description="Завершает текущую сессию пользователя, удаляя refresh token из базы и очищая cookies.",
    responses={
        200: {
            "description": "Успешный выход",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Logged out"
                    }
                }
            }
        },
        401: {
            "description": "Не авторизован"
        }
    }
)
async def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Выход из текущей сессии"""
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        token_hash = TokenService.hash_token(refresh_token)
        TokenService.revoke_tokens(db, user.id, all_sessions=False, current_token_hash=token_hash)
    
    clear_token_cookies(response)
    return {"message": "Logged out"}

@router.post(
    "/logout-all",
    summary="Выход из всех сессий",
    description="Завершает все сессии пользователя, отзывая все refresh токены и очищая cookies.",
    responses={
        200: {
            "description": "Все сессии завершены",
            "content": {
                "application/json": {
                    "example": {
                        "message": "All sessions terminated"
                    }
                }
            }
        },
        401: {
            "description": "Не авторизован"
        }
    }
)
async def logout_all(
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Выход из всех сессий"""
    TokenService.revoke_tokens(db, user.id, all_sessions=True)
    clear_token_cookies(response)
    return {"message": "All sessions terminated"}

@router.get(
    "/oauth/yandex",
    summary="Инициация входа через Яндекс",
    description="Генерирует URL для перенаправления пользователя на страницу авторизации Яндекса.",
    responses={
        200: {
            "description": "URL для авторизации",
            "content": {
                "application/json": {
                    "example": {
                        "auth_url": "https://oauth.yandex.ru/authorize?response_type=code&client_id=...&redirect_uri=http://localhost:4200/auth/oauth/yandex/callback&state=..."
                    }
                }
            }
        }
    }
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
    description="Обрабатывает код авторизации от Яндекса, создает пользователя и устанавливает cookies.",
    responses={
        200: {
            "description": "Успешная авторизация через Яндекс",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "OAuth успешен",
                        "user": {
                            "id": 1,
                            "email": "user@yandex.ru"
                        }
                    }
                }
            }
        },
        400: {
            "description": "Ошибка при обмене кода",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid state"
                    }
                }
            }
        }
    }
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
    description="Отправляет запрос на сброс пароля. Токен для сброса выводится в консоль (вместо email).",
    responses={
        200: {
            "description": "Запрос принят",
            "content": {
                "application/json": {
                    "example": {
                        "message": "If the email exists, a reset link has been sent"
                    }
                }
            }
        },
        400: {
            "description": "Ошибка валидации"
        }
    }
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
    description="Устанавливает новый пароль с использованием токена из запроса на сброс.",
    responses={
        200: {
            "description": "Пароль успешно изменен",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Password reset successful"
                    }
                }
            }
        },
        400: {
            "description": "Недействительный или истекший токен",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid or expired token"
                    }
                }
            }
        },
        422: {
            "description": "Ошибка валидации (пароль слишком короткий)"
        }
    }
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