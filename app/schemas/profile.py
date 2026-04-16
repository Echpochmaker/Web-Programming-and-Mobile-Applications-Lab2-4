from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ProfileResponse(BaseModel):
    id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar_file_id: Optional[str] = None
    created_at: datetime

class ProfileUpdateRequest(BaseModel):
    avatar_file_id: Optional[str] = None  # может быть null или string