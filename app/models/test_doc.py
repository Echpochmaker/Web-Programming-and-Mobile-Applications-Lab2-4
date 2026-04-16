from beanie import Document
from datetime import datetime
from typing import Optional, List
from pydantic import Field, BaseModel
from bson import ObjectId

# Встроенные документы (не наследуются от Document)
class AnswerOption(BaseModel):
    id: Optional[ObjectId] = Field(default_factory=ObjectId)
    text: str
    is_correct: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True

class Question(BaseModel):
    id: Optional[ObjectId] = Field(default_factory=ObjectId)
    text: str
    answers: List[AnswerOption] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True

# Основной документ (коллекция)
class Test(Document):
    title: str
    description: Optional[str] = None
    owner_id: str
    questions: List[Question] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    class Settings:
        name = "tests"
        indexes = [
            "owner_id",
            "deleted_at"
        ]
    
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
    
    def soft_delete(self):
        self.deleted_at = datetime.utcnow()