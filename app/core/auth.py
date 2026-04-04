from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt
from typing import Optional
import os
from app.core.cache import cache
from jose import jwt

from app.core.database import get_db
from app.services.user_service import UserService
from app.services.token_service import TokenService

def get_token_from_cookie(request: Request) -> Optional[str]:
    return request.cookies.get("access_token")

def get_token_from_header(request: Request) -> Optional[str]:
    """Извлекает токен из заголовка Authorization"""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "")
    return None

def get_refresh_token_from_cookie(request: Request) -> Optional[str]:
    return request.cookies.get("refresh_token")

# Зависимость для получения текущего пользователя
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    # Сначала проверяем заголовок (для localStorage)
    token = get_token_from_header(request)
    
    # Если нет в заголовке, проверяем куки
    if not token:
        token = get_token_from_cookie(request)
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(token, TokenService.ACCESS_SECRET, algorithms=["HS256"])
        user_id = int(payload.get("sub"))
        jti = payload.get("jti")
        
        # Проверяем, что JTI существует в Redis (токен не отозван)
        cache_key = f"testing:auth:user:{user_id}:access:{jti}"
        if not cache.get(cache_key):
            print(f"❌ Token revoked: {cache_key}")
            raise HTTPException(status_code=401, detail="Token revoked")
        
        print(f"Token valid: {cache_key}")
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

# Опциональная зависимость (для эндпоинтов, где авторизация не обязательна)
async def get_optional_user(
    request: Request,
    db: Session = Depends(get_db)
):
    # Сначала проверяем заголовок
    token = get_token_from_header(request)
    
    # Если нет в заголовке, проверяем куки
    if not token:
        token = get_token_from_cookie(request)
    
    if not token:
        return None
    
    user_id = TokenService.verify_access_token(token)
    if not user_id:
        return None
    
    return UserService.get_by_id(db, user_id)