from beanie import Document
from datetime import datetime
from typing import Optional
from pydantic import Field
from uuid import uuid4

class File(Document):
    file_id: str = Field(default_factory=lambda: str(uuid4()), unique=True)
    user_id: str = Field(index=True)
    original_name: str
    object_key: str
    size: int
    mimetype: str
    bucket: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    class Settings:
        name = "files"
        indexes = [
            "user_id",
            "file_id",
            "deleted_at"
        ]
    
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
    
    def soft_delete(self):
        self.deleted_at = datetime.utcnow()