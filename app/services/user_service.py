from app.models.user_doc import User
from app.schemas.auth import UserRegister
import bcrypt
import secrets
from typing import Optional
from datetime import datetime, timedelta
from bson import ObjectId

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
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    async def create_user(user_data: UserRegister) -> User:
        """Создает нового пользователя"""
        password_hash, salt = UserService.hash_password(user_data.password)
        
        user = User(
            email=user_data.email,
            phone=user_data.phone,
            password_hash=password_hash,
            salt=salt
        )
        await user.insert()
        return user
    
    @staticmethod
    async def get_by_login(login: str) -> Optional[User]:
        """Ищет пользователя по email или телефону"""
        collection = User.get_motor_collection()
        doc = await collection.find_one({
            "$or": [
                {"email": login},
                {"phone": login}
            ],
            "deleted_at": None
        })
        if doc:
            return User(**doc)
        return None
    
    @staticmethod
    async def get_by_id(user_id: str) -> Optional[User]:
        """Ищет пользователя по ID"""
        try:
            user = await User.get(ObjectId(user_id))
            if user and user.deleted_at:
                return None
            return user
        except:
            return None
    
    @staticmethod
    async def get_by_email(email: str) -> Optional[User]:
        """Ищет пользователя по email"""
        collection = User.get_motor_collection()
        doc = await collection.find_one({"email": email, "deleted_at": None})
        if doc:
            return User(**doc)
        return None
    
    @staticmethod
    async def get_by_oauth_id(provider: str, provider_id: str) -> Optional[User]:
        """Ищет пользователя по OAuth ID"""
        collection = User.get_motor_collection()
        if provider == 'yandex':
            doc = await collection.find_one({"yandex_id": provider_id, "deleted_at": None})
        elif provider == 'vk':
            doc = await collection.find_one({"vk_id": provider_id, "deleted_at": None})
        else:
            return None
        
        if doc:
            return User(**doc)
        return None
    
    @staticmethod
    async def create_oauth_user(provider: str, provider_id: str, email: Optional[str] = None) -> User:
        """Создает пользователя через OAuth"""
        user_data = {}
        if provider == 'yandex':
            user_data['yandex_id'] = provider_id
        elif provider == 'vk':
            user_data['vk_id'] = provider_id
        
        if email:
            user_data['email'] = email
        
        user = User(**user_data)
        await user.insert()
        return user
    
    @staticmethod
    async def create_password_reset_token(email: str) -> Optional[str]:
        """Создает токен для сброса пароля (действителен 1 час)"""
        user = await UserService.get_by_email(email)
        if not user:
            return None
        
        reset_token = secrets.token_urlsafe(32)
        user.reset_password_token = reset_token
        user.reset_password_expires = datetime.utcnow() + timedelta(hours=1)
        await user.save()
        
        return reset_token
    
    @staticmethod
    async def reset_password(token: str, new_password: str) -> Optional[User]:
        """Сбрасывает пароль по токену"""
        collection = User.get_motor_collection()
        doc = await collection.find_one({
            "reset_password_token": token,
            "reset_password_expires": {"$gt": datetime.utcnow()},
            "deleted_at": None
        })
        
        if not doc:
            return None
        
        user = User(**doc)
        password_hash, salt = UserService.hash_password(new_password)
        user.password_hash = password_hash
        user.salt = salt
        user.reset_password_token = None
        user.reset_password_expires = None
        
        await user.save()
        return user