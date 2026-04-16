from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from datetime import datetime, timedelta
import httpx
import secrets
import os
from jose import jwt

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

oauth_states = {}

def set_token_cookies(response: Response, access_token: str, refresh_token: str):
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
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")

@router.post("/register", status_code=201)
async def register(user_data: UserRegister):
    existing = await UserService.get_by_login(user_data.email or "")
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    user = await UserService.create_user(user_data)
    return {"message": "User created successfully", "user_id": str(user.id)}

@router.post("/login")
async def login(
    user_data: UserLogin,
    request: Request,
    response: Response
):
    user = await UserService.get_by_login(user_data.login)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not UserService.verify_password(user_data.password, user.password_hash, user.salt):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token, refresh_token = await TokenService.create_token_pair(
        str(user.id),
        request.headers.get("user-agent"),
        request.client.host
    )
    
    set_token_cookies(response, access_token, refresh_token)
    
    cache.delete(f"testing:users:profile:{str(user.id)}")
    
    return {"message": "Login successful"}

@router.post("/refresh")
async def refresh(request: Request, response: Response):
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

@router.get("/whoami", response_model=AuthResponse)
async def whoami(user: User = Depends(get_current_user)):
    cache_key = f"testing:users:profile:{str(user.id)}"
    
    cached = cache.get(cache_key)
    if cached:
        # Возвращаем AuthResponse с данными из кеша
        return AuthResponse(
            user=UserResponse(
                id=cached["id"],
                email=cached["email"],
                phone=cached["phone"],
                created_at=datetime.fromisoformat(cached["created_at"]) if cached.get("created_at") else None
            ),
            message="Authenticated (cached)"
        )
    
    # Создаём словарь для кеша
    user_dict = {
        "id": str(user.id),
        "email": user.email,
        "phone": user.phone,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
    cache.set(cache_key, user_dict, ttl=300)
    
    # Возвращаем AuthResponse с данными пользователя
    return AuthResponse(
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            phone=user.phone,
            created_at=user.created_at
        ),
        message="Authenticated"
    )

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user)
):
    access_token = request.cookies.get("access_token")
    if access_token:
        try:
            payload = jwt.decode(access_token, TokenService.ACCESS_SECRET, algorithms=["HS256"])
            jti = payload.get("jti")
            if jti:
                TokenService.revoke_access_token(str(user.id), jti)
        except:
            pass
    
    cache.delete(f"testing:users:profile:{str(user.id)}")
    clear_token_cookies(response)
    return {"message": "Logged out"}

@router.post("/logout-all")
async def logout_all(
    response: Response,
    user: User = Depends(get_current_user)
):
    cache.delete_pattern(f"testing:auth:user:{str(user.id)}:access:*")
    cache.delete(f"testing:users:profile:{str(user.id)}")
    clear_token_cookies(response)
    return {"message": "All sessions terminated"}

@router.get("/oauth/yandex")
async def yandex_oauth():
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

@router.get("/oauth/yandex/callback")
async def yandex_callback(
    code: str,
    request: Request,
    response: Response
):
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
    
    user = await UserService.get_by_oauth_id("yandex", yandex_id)
    if not user:
        user = await UserService.create_oauth_user("yandex", yandex_id, email)
    
    access_token, refresh_token = await TokenService.create_token_pair(
        str(user.id),
        request.headers.get("user-agent"),
        request.client.host
    )
    
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
    
    return {
        "success": True,
        "message": "OAuth успешен",
        "user": {
            "id": str(user.id),
            "email": user.email
        }
    }

@router.post("/forgot-password")
async def forgot_password(request_data: ForgotPasswordRequest):
    user = await UserService.get_by_login(request_data.email)
    
    if user:
        reset_token = await UserService.create_password_reset_token(request_data.email)
        print(f"\n=== PASSWORD RESET ===")
        print(f"Email: {request_data.email}")
        print(f"Token: {reset_token}")
        print(f"Reset link: http://localhost:4200/reset-password?token={reset_token}")
        print(f"=== ===\n")
    
    return {"message": "If the email exists, a reset link has been sent"}

@router.post("/reset-password")
async def reset_password(request_data: ResetPasswordRequest):
    user = await UserService.reset_password(request_data.token, request_data.new_password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    return {"message": "Password reset successful"}