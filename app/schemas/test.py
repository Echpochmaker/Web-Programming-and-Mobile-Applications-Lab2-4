from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# ---- Схемы для вариантов ответов ----
class AnswerOptionBase(BaseModel):
    text: str = Field(..., description="Текст варианта ответа", example="4")
    is_correct: bool = Field(False, description="Флаг правильности ответа", example=True)

class AnswerOptionCreate(AnswerOptionBase):
    pass

class AnswerOptionResponse(AnswerOptionBase):
    id: str = Field(..., description="Уникальный идентификатор варианта ответа")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата последнего обновления")

    class Config:
        from_attributes = True

# ---- Схемы для вопросов ----
class QuestionBase(BaseModel):
    text: str = Field(..., description="Текст вопроса", example="Сколько будет 2+2?")

class QuestionCreate(QuestionBase):
    answers: List[AnswerOptionCreate] = Field([], description="Список вариантов ответа для вопроса")

class QuestionResponse(QuestionBase):
    id: str = Field(..., description="Уникальный идентификатор вопроса")
    test_id: str = Field(..., description="ID теста, к которому относится вопрос")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата последнего обновления")
    answers: List[AnswerOptionResponse] = Field([], description="Список вариантов ответа")

    class Config:
        from_attributes = True

# ---- Базовые схемы для теста ----
class TestBase(BaseModel):
    title: str = Field(..., description="Название теста", example="Основы Python")
    description: Optional[str] = Field(None, description="Описание теста", example="Проверка знаний Python")

class TestCreate(TestBase):
    questions: List[QuestionCreate] = Field([], description="Список вопросов теста (опционально)")

class TestUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Новое название теста", example="Обновленное название")
    description: Optional[str] = Field(None, description="Новое описание теста", example="Обновленное описание")

class TestResponse(TestBase):
    id: str  # было int, стало str
    created_at: datetime
    updated_at: Optional[datetime] = None
    questions: List[QuestionResponse] = []
    owner_id: str  # было Optional[int], стало str

    class Config:
        from_attributes = True

class PaginatedResponse(BaseModel):
    data: List[TestResponse] = Field(..., description="Массив тестов на текущей странице")
    meta: dict = Field(..., description="Мета-информация о пагинации")

# Функция для сериализации теста
def serialize_test(test) -> dict:
    return {
        "id": str(test.id),
        "title": test.title,
        "description": test.description,
        "created_at": test.created_at.isoformat() if test.created_at else None,
        "updated_at": test.updated_at.isoformat() if test.updated_at else None,
        "owner_id": str(test.owner_id),
        "questions": []
    }