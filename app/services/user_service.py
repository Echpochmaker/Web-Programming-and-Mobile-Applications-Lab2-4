from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.auth import UserRegister
import bcrypt
import secrets
from typing import Optional
from datetime import datetime, timedelta

class UserService:
    @staticmethod
    def hash_password(password: str) -> tuple[str, str]:
        """Генерирует соль и хеш пароля"""
        salt = bcrypt.gensalt().decode('utf-8')
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt.encode('utf-8')).decode('utf-8')
        return password_hash, salt
    
    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """Проверяет пароль"""
        # Соль уже включена в хеш в bcrypt, но для демонстрации оставляем
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    def create_user(db: Session, user_data: UserRegister) -> User:
        """Создает нового пользователя"""
        password_hash, salt = UserService.hash_password(user_data.password)
        
        user = User(
            email=user_data.email,
            phone=user_data.phone,
            password_hash=password_hash,
            salt=salt
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_by_login(db: Session, login: str) -> Optional[User]:
        """Ищет пользователя по email или телефону"""
        return db.query(User).filter(
            (User.email == login) | (User.phone == login),
            User.deleted_at.is_(None)
        ).first()
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    
    @staticmethod
    def get_by_oauth_id(db: Session, provider: str, provider_id: str) -> Optional[User]:
        """Ищет пользователя по OAuth ID"""
        if provider == 'yandex':
            return db.query(User).filter(User.yandex_id == provider_id, User.deleted_at.is_(None)).first()
        elif provider == 'vk':
            return db.query(User).filter(User.vk_id == provider_id, User.deleted_at.is_(None)).first()
        return None
    
    @staticmethod
    def create_oauth_user(db: Session, provider: str, provider_id: str, email: Optional[str] = None) -> User:
        """Создает пользователя через OAuth"""
        user_data = {}
        if provider == 'yandex':
            user_data['yandex_id'] = provider_id
        elif provider == 'vk':
            user_data['vk_id'] = provider_id
        
        if email:
            user_data['email'] = email
        
        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    # ----- НОВЫЕ МЕТОДЫ ДЛЯ СБРОСА ПАРОЛЯ -----
    @staticmethod
    def create_password_reset_token(db: Session, email: str) -> Optional[str]:
        """Создает токен для сброса пароля (действителен 1 час)"""
        user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()
        if not user:
            return None
        
        # Генерируем безопасный токен
        reset_token = secrets.token_urlsafe(32)
        
        # Сохраняем токен и время истечения
        user.reset_password_token = reset_token
        user.reset_password_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        
        return reset_token
    
    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> Optional[User]:
        """Сбрасывает пароль по токену"""
        user = db.query(User).filter(
            User.reset_password_token == token,
            User.reset_password_expires > datetime.utcnow(),
            User.deleted_at.is_(None)
        ).first()
        
        if not user:
            return None
        
        # Хешируем новый пароль
        password_hash, salt = UserService.hash_password(new_password)
        user.password_hash = password_hash
        user.salt = salt
        
        # Очищаем токен сброса
        user.reset_password_token = None
        user.reset_password_expires = None
        
        db.commit()
        db.refresh(user)
        return user