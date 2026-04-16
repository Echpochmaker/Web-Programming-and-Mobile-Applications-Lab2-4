from beanie import Document
from datetime import datetime
from typing import Optional
from pydantic import Field

class Token(Document):
    user_id: str
    access_token_hash: str
    refresh_token_hash: str
    access_expires_at: datetime
    refresh_expires_at: datetime
    is_revoked: bool = False
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "tokens"
        indexes = [
            "user_id",
            "refresh_token_hash"
        ]