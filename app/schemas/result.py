from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# ========== Схемы для результатов ==========

class AnswerSubmission(BaseModel):
    """Отправка ответа на вопрос"""
    result_id: str = Field(..., description="ID результата теста")
    question_id: str = Field(..., description="ID вопроса")
    selected_answer_id: str = Field(..., description="ID выбранного варианта ответа")

class UserAnswerResponse(BaseModel):
    """Ответ пользователя на вопрос (для результатов)"""
    id: str
    question_id: str
    question_text: str
    selected_answer_id: Optional[str] = None
    selected_answer_text: Optional[str] = None
    is_correct: Optional[bool] = None
    correct_answer_id: Optional[str] = None
    correct_answer_text: Optional[str] = None

    class Config:
        from_attributes = True

class TestResultCreate(BaseModel):
    """Начало прохождения теста"""
    test_id: str

class TestResultResponse(BaseModel):
    """Результат прохождения теста"""
    id: str
    user_id: str
    test_id: str
    test_title: str
    author_email: Optional[str] = None
    score: Optional[float] = None
    correct_answers: int
    total_questions: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    answers: List[UserAnswerResponse] = []

    class Config:
        from_attributes = True

class TestResultListResponse(BaseModel):
    """Список результатов с пагинацией"""
    data: List[TestResultResponse]
    meta: dict = Field(..., example={
        "total": 42,
        "page": 1,
        "limit": 10,
        "total_pages": 5
    })

class TestAvailableResponse(BaseModel):
    """Тест, доступный для прохождения"""
    id: str
    title: str
    description: Optional[str] = None
    author_email: str
    questions_count: int
    attempts_count: Optional[int] = None
    user_attempts: int = 0

    class Config:
        from_attributes = True

class TestAvailableListResponse(BaseModel):
    """Список доступных тестов с пагинацией"""
    data: List[TestAvailableResponse]
    meta: dict = Field(..., example={
        "total": 42,
        "page": 1,
        "limit": 10,
        "total_pages": 5
    })