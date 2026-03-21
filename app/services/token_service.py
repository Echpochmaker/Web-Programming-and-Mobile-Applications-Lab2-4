from datetime import datetime, timedelta
from jose import jwt
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.token import Token
import hashlib
import secrets
from typing import Optional, Tuple
import os

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
    def generate_access_token(user_id: int) -> Tuple[str, datetime]:
        """Генерирует Access Token и возвращает его вместе с датой истечения"""
        expires_at = datetime.utcnow() + timedelta(minutes=TokenService.ACCESS_EXPIRATION)
        payload = {
            "sub": str(user_id),
            "exp": expires_at,
            "type": "access"
        }
        token = jwt.encode(payload, TokenService.ACCESS_SECRET, algorithm="HS256")
        return token, expires_at
    
    @staticmethod
    def generate_refresh_token(user_id: int) -> Tuple[str, datetime]:
        """Генерирует Refresh Token"""
        # Случайный токен (не JWT для возможности отзыва)
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
            return None  # токен истек
        except jwt.JWTError:
            return None  # невалидный токен
    
    @staticmethod
    def create_token_pair(db: Session, user_id: int, user_agent: str = None, ip: str = None) -> Tuple[str, str]:
        """Создает пару токенов и сохраняет их в БД"""
        access_token, access_expires = TokenService.generate_access_token(user_id)
        refresh_token, refresh_expires = TokenService.generate_refresh_token(user_id)
        
        # Хешируем токены для хранения
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
        
        # Ищем токен в БД
        token_record = db.query(Token).filter(
            Token.refresh_token_hash == token_hash,
            Token.is_revoked == False,
            Token.refresh_expires_at > datetime.utcnow()
        ).first()
        
        if not token_record:
            return None
        
        # Генерируем новые токены
        return TokenService.create_token_pair(
            db, 
            token_record.user_id, 
            user_agent, 
            ip
        )
    
    @staticmethod
    def revoke_tokens(db: Session, user_id: int, all_sessions: bool = False, current_token_hash: str = None):
        """Отзывает токены пользователя"""
        query = db.query(Token).filter(Token.user_id == user_id, Token.is_revoked == False)
        
        if not all_sessions and current_token_hash:
            # Отзываем только текущую сессию
            query = query.filter(Token.refresh_token_hash == current_token_hash)
        
        query.update({"is_revoked": True})
        db.commit()