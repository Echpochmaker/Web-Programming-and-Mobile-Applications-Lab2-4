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
    id: int = Field(..., description="Уникальный идентификатор варианта ответа")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата последнего обновления")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "text": "4",
                "is_correct": True,
                "created_at": "2026-03-18T12:00:00.000Z",
                "updated_at": None
            }
        }

# ---- Схемы для вопросов ----
class QuestionBase(BaseModel):
    text: str = Field(..., description="Текст вопроса", example="Сколько будет 2+2?")

class QuestionCreate(QuestionBase):
    answers: List[AnswerOptionCreate] = Field(
        [], 
        description="Список вариантов ответа для вопроса"
    )

class QuestionResponse(QuestionBase):
    id: int = Field(..., description="Уникальный идентификатор вопроса")
    test_id: int = Field(..., description="ID теста, к которому относится вопрос")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата последнего обновления")
    answers: List[AnswerOptionResponse] = Field([], description="Список вариантов ответа")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "test_id": 1,
                "text": "Сколько будет 2+2?",
                "answers": [
                    {
                        "id": 1,
                        "text": "4",
                        "is_correct": True,
                        "created_at": "2026-03-18T12:00:00.000Z",
                        "updated_at": None
                    },
                    {
                        "id": 2,
                        "text": "5",
                        "is_correct": False,
                        "created_at": "2026-03-18T12:00:00.000Z",
                        "updated_at": None
                    }
                ],
                "created_at": "2026-03-18T12:00:00.000Z",
                "updated_at": None
            }
        }

    @classmethod
    def from_orm(cls, obj):
        obj.answers = obj.answer_options
        return super().from_orm(obj)

# ---- Базовые схемы для теста ----
class TestBase(BaseModel):
    title: str = Field(..., description="Название теста", example="Основы Python")
    description: Optional[str] = Field(None, description="Описание теста", example="Проверка знаний Python")

# Схема для создания (может содержать вопросы)
class TestCreate(TestBase):
    questions: List[QuestionCreate] = Field(
        [], 
        description="Список вопросов теста (опционально)"
    )

# Схема для обновления (все поля опциональны – для PATCH и PUT)
class TestUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Новое название теста", example="Обновленное название")
    description: Optional[str] = Field(None, description="Новое описание теста", example="Обновленное описание")

# Схема для ответа (включает вопросы)
class TestResponse(TestBase):
    id: int = Field(..., description="Уникальный идентификатор теста")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата последнего обновления")
    questions: List[QuestionResponse] = Field([], description="Список вопросов теста")
    owner_id: Optional[int] = Field(None, description="ID владельца теста")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "Основы Python",
                "description": "Тест на знание Python",
                "created_at": "2026-03-18T12:00:00.000Z",
                "updated_at": None,
                "questions": [],
                "owner_id": 1
            }
        }

# Параметры пагинации
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Номер страницы", example=1)
    limit: int = Field(10, ge=1, le=100, description="Количество элементов на странице", example=10)

# Пагинированный ответ
class PaginatedResponse(BaseModel):
    data: List[TestResponse] = Field(..., description="Массив тестов на текущей странице")
    meta: dict = Field(
        ..., 
        description="Мета-информация о пагинации",
        example={
            "total": 42,
            "page": 1,
            "limit": 10,
            "total_pages": 5
        }
    )

# Функция для сериализации теста (для кеширования)
def serialize_test(test) -> dict:
    """Преобразует объект Test в JSON-сериализуемый словарь"""
    return {
        "id": test.id,
        "title": test.title,
        "description": test.description,
        "created_at": test.created_at.isoformat() if test.created_at else None,
        "updated_at": test.updated_at.isoformat() if test.updated_at else None,
        "owner_id": test.owner_id,
        "questions": []  # вопросы не кешируем для простоты
    }