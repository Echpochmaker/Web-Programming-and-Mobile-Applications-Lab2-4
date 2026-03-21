from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# ========== Схемы для результатов ==========

class AnswerSubmission(BaseModel):
    """Отправка ответа на вопрос"""
    result_id: int = Field(..., description="ID результата теста")
    question_id: int = Field(..., description="ID вопроса")
    selected_answer_id: int = Field(..., description="ID выбранного варианта ответа")

class UserAnswerResponse(BaseModel):
    """Ответ пользователя на вопрос (для результатов)"""
    id: int
    question_id: int
    question_text: str
    selected_answer_id: Optional[int]
    selected_answer_text: Optional[str]
    is_correct: Optional[bool]
    correct_answer_id: int
    correct_answer_text: str

    class Config:
        from_attributes = True

class TestResultCreate(BaseModel):
    """Начало прохождения теста"""
    test_id: int

class TestResultResponse(BaseModel):
    """Результат прохождения теста"""
    id: int
    user_id: int
    test_id: int
    test_title: str
    score: Optional[float]
    correct_answers: int
    total_questions: int
    started_at: datetime
    completed_at: Optional[datetime]
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
    id: int
    title: str
    description: Optional[str]
    author_email: str
    questions_count: int
    attempts_count: Optional[int]
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