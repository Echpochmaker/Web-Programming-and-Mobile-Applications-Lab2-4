from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FileUploadResponse(BaseModel):
    file_id: str
    original_name: str
    size: int
    mimetype: str
    created_at: datetime
    url: Optional[str] = None

class FileResponse(BaseModel):
    file_id: str
    original_name: str
    size: int
    mimetype: str
    created_at: datetime