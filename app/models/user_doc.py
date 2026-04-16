from beanie import Document, Indexed
from datetime import datetime
from typing import Optional
from pydantic import Field

class User(Document):
    email: Optional[Indexed(str, unique=True)] = None
    phone: Optional[Indexed(str, unique=True)] = None
    password_hash: Optional[str] = None
    salt: Optional[str] = None
    yandex_id: Optional[Indexed(str, unique=True)] = None
    vk_id: Optional[Indexed(str, unique=True)] = None
    avatar_file_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    reset_password_token: Optional[str] = None
    reset_password_expires: Optional[datetime] = None
    
    class Settings:
        name = "users"
        indexes = [
            "email",
            "phone",
            "yandex_id",
            "vk_id",
            "reset_password_token"
        ]
    
    def is_deleted(self) -> bool:
        return self.deleted_at is not None