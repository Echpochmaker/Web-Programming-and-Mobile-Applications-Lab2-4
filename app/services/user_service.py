from app.models import User
from app.schemas.auth import UserRegister
import bcrypt
import secrets
from typing import Optional
from datetime import datetime, timedelta

class UserService:
    @staticmethod
    def hash_password(password: str) -> tuple[str, str]:
        salt = bcrypt.gensalt().decode('utf-8')
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt.encode('utf-8')).decode('utf-8')
        return password_hash, salt
    
    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    async def create_user(user_data: UserRegister) -> User:
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
        user = await User.find_one(
            {"$or": [{"email": login}, {"phone": login}], "deleted_at": None}
        )
        return user
    
    @staticmethod
    async def get_by_id(user_id: str) -> Optional[User]:
        from bson import ObjectId
        user = await User.get(ObjectId(user_id))
        if user and user.deleted_at:
            return None
        return user
    
    @staticmethod
    async def get_by_oauth_id(provider: str, provider_id: str) -> Optional[User]:
        if provider == 'yandex':
            user = await User.find_one({"yandex_id": provider_id, "deleted_at": None})
            return user
        elif provider == 'vk':
            user = await User.find_one({"vk_id": provider_id, "deleted_at": None})
            return user
        return None
    
    @staticmethod
    async def create_oauth_user(provider: str, provider_id: str, email: Optional[str] = None) -> User:
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
        user = await User.find_one({"email": email, "deleted_at": None})
        if not user:
            return None
        
        reset_token = secrets.token_urlsafe(32)
        user.reset_password_token = reset_token
        user.reset_password_expires = datetime.utcnow() + timedelta(hours=1)
        await user.save()
        
        return reset_token
    
    @staticmethod
    async def reset_password(token: str, new_password: str) -> Optional[User]:
        user = await User.find_one({
            "reset_password_token": token,
            "reset_password_expires": {"$gt": datetime.utcnow()},
            "deleted_at": None
        })
        
        if not user:
            return None
        
        password_hash, salt = UserService.hash_password(new_password)
        user.password_hash = password_hash
        user.salt = salt
        user.reset_password_token = None
        user.reset_password_expires = None
        
        await user.save()
        return user