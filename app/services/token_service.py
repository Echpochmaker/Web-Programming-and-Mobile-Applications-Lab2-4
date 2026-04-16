from datetime import datetime, timedelta
from app.core.cache import cache
from jose import jwt
from app.models.token_doc import Token
import hashlib
import secrets
from typing import Optional, Tuple
import os
import uuid

class TokenService:
    ACCESS_SECRET = os.getenv("JWT_ACCESS_SECRET", "default_access_secret_change_me")
    REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET", "default_refresh_secret_change_me")
    ACCESS_EXPIRATION = int(os.getenv("JWT_ACCESS_EXPIRATION", "15").replace('m', ''))
    REFRESH_EXPIRATION = int(os.getenv("JWT_REFRESH_EXPIRATION", "7").replace('d', ''))
    
    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def generate_access_token(user_id: str) -> Tuple[str, datetime, str]:
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
    def generate_refresh_token(user_id: str) -> Tuple[str, datetime]:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=TokenService.REFRESH_EXPIRATION)
        return token, expires_at
    
    @staticmethod
    async def create_token_pair(user_id: str, user_agent: str = None, ip: str = None) -> Tuple[str, str]:
        access_token, access_expires, jti = TokenService.generate_access_token(user_id)
        refresh_token, refresh_expires = TokenService.generate_refresh_token(user_id)
        
        cache_key = f"testing:auth:user:{user_id}:access:{jti}"
        cache.set(cache_key, "valid", ttl=TokenService.ACCESS_EXPIRATION * 60)
        
        token_record = Token(
            user_id=user_id,
            access_token_hash=TokenService.hash_token(access_token),
            refresh_token_hash=TokenService.hash_token(refresh_token),
            access_expires_at=access_expires,
            refresh_expires_at=refresh_expires,
            user_agent=user_agent,
            ip_address=ip
        )
        await token_record.insert()
        
        return access_token, refresh_token
    
    @staticmethod
    async def refresh_tokens(refresh_token: str, user_agent: str = None, ip: str = None) -> Optional[Tuple[str, str]]:
        token_hash = TokenService.hash_token(refresh_token)
        
        collection = Token.get_motor_collection()
        doc = await collection.find_one({
            "refresh_token_hash": token_hash,
            "is_revoked": False,
            "refresh_expires_at": {"$gt": datetime.utcnow()}
        })
        
        if not doc:
            return None
        
        token_record = Token(**doc)
        
        return await TokenService.create_token_pair(token_record.user_id, user_agent, ip)
    
    @staticmethod
    async def revoke_tokens(user_id: str, all_sessions: bool = False, current_token_hash: str = None):
        collection = Token.get_motor_collection()
        query = {"user_id": user_id, "is_revoked": False}
        
        if not all_sessions and current_token_hash:
            query["refresh_token_hash"] = current_token_hash
        
        await collection.update_many(query, {"$set": {"is_revoked": True}})