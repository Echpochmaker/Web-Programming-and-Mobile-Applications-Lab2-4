from datetime import datetime, timedelta
from app.core.cache import cache
from jose import jwt
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.token import Token
import hashlib
import secrets
from typing import Optional, Tuple
import os
import uuid

class TokenService:
    # Загружаем секреты из окружения
    ACCESS_SECRET = os.getenv("JWT_ACCESS_SECRET", "default_access_secret_change_me")
    REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET", "default_refresh_secret_change_me")
    ACCESS_EXPIRATION = int(os.getenv("JWT_ACCESS_EXPIRATION", "15").replace('m', ''))  # минуты
    REFRESH_EXPIRATION = int(os.getenv("JWT_REFRESH_EXPIRATION", "7").replace('d', ''))  # дни
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Хеширует токен для хранения в БД"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def generate_access_token(user_id: int) -> Tuple[str, datetime, str]:
        """Генерирует Access Token с JTI и возвращает его вместе с датой истечения и JTI"""
        jti = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=TokenService.ACCESS_EXPIRATION)
        payload = {
            "sub": str(user_id),
            "exp": expires_at,
            "type": "access",
            "jti": jti
        }
        token = jwt.encode(payload, TokenService.ACCESS_SECRET, algorithm="HS256")
        return token, expires_at, jti
    
    @staticmethod
    def generate_refresh_token(user_id: int) -> Tuple[str, datetime]:
        """Генерирует Refresh Token"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=TokenService.REFRESH_EXPIRATION)
        return token, expires_at
    
    @staticmethod
    def verify_access_token(token: str) -> Optional[int]:
        """Проверяет Access Token и возвращает user_id"""
        try:
            payload = jwt.decode(token, TokenService.ACCESS_SECRET, algorithms=["HS256"])
            return int(payload.get("sub"))
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    @staticmethod
    def create_token_pair(db: Session, user_id: int, user_agent: str = None, ip: str = None) -> Tuple[str, str]:
        """Создает пару токенов и сохраняет их в БД и Redis"""
        access_token, access_expires, jti = TokenService.generate_access_token(user_id)
        refresh_token, refresh_expires = TokenService.generate_refresh_token(user_id)
        
        # Сохраняем JTI в Redis для проверки активных сессий
        cache_key = f"testing:auth:user:{user_id}:access:{jti}"
        cache.set(cache_key, "valid", ttl=TokenService.ACCESS_EXPIRATION * 60)
        print(f"💾 JTI saved to Redis: {cache_key}")
        
        # Хешируем токены для хранения в БД
        token_record = Token(
            user_id=user_id,
            access_token_hash=TokenService.hash_token(access_token),
            refresh_token_hash=TokenService.hash_token(refresh_token),
            access_expires_at=access_expires,
            refresh_expires_at=refresh_expires,
            user_agent=user_agent,
            ip_address=ip
        )
        db.add(token_record)
        db.commit()
        
        return access_token, refresh_token
    
    @staticmethod
    def refresh_tokens(db: Session, refresh_token: str, user_agent: str = None, ip: str = None) -> Optional[Tuple[str, str]]:
        """Обновляет пару токенов по Refresh Token"""
        token_hash = TokenService.hash_token(refresh_token)
        
        token_record = db.query(Token).filter(
            Token.refresh_token_hash == token_hash,
            Token.is_revoked == False,
            Token.refresh_expires_at > datetime.utcnow()
        ).first()
        
        if not token_record:
            return None
        
        return TokenService.create_token_pair(db, token_record.user_id, user_agent, ip)
    
    @staticmethod
    def revoke_tokens(db: Session, user_id: int, all_sessions: bool = False, current_token_hash: str = None):
        """Отзывает токены пользователя"""
        query = db.query(Token).filter(Token.user_id == user_id, Token.is_revoked == False)
        
        if not all_sessions and current_token_hash:
            query = query.filter(Token.refresh_token_hash == current_token_hash)
        
        query.update({"is_revoked": True})
        db.commit()
    
    @staticmethod
    def revoke_access_token(user_id: int, jti: str):
        """Отзывает access токен по JTI"""
        cache_key = f"testing:auth:user:{user_id}:access:{jti}"
        cache.delete(cache_key)
        print(f"🗑️ JTI revoked: {cache_key}")