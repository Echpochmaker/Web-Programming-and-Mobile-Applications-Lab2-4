from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.test_service import TestService
from app.schemas.test import QuestionCreate, QuestionResponse, AnswerOptionCreate, AnswerOptionResponse

router = APIRouter(prefix="/tests/{test_id}/questions", tags=["questions"])

def get_test_or_404(db: Session, test_id: int):
    test = TestService.get_by_id(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test

@router.get(
    "/", 
    response_model=List[QuestionResponse],
    summary="Получить все вопросы теста",
    description="Возвращает список вопросов для указанного теста. Доступно всем пользователям.",
    responses={
        200: {
            "description": "Список вопросов успешно получен",
            "content": {
                "application/json": {
                    "example": [
                        {
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
                                }
                            ],
                            "created_at": "2026-03-18T12:00:00.000Z",
                            "updated_at": None
                        }
                    ]
                }
            }
        },
        404: {
            "description": "Тест не найден",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Test not found"
                    }
                }
            }
        }
    }
)
def get_questions(
    test_id: int,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=100, description="Максимальное количество записей")
):
    get_test_or_404(db, test_id)
    return TestService.get_questions(db, test_id, skip, limit)

@router.post(
    "/", 
    response_model=QuestionResponse, 
    status_code=201,
    summary="Создать новый вопрос",
    description="Создает новый вопрос для указанного теста. Требуется авторизация (только владелец теста).",
    responses={
        201: {
            "description": "Вопрос успешно создан",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "test_id": 1,
                        "text": "Сколько будет 2+2?",
                        "answers": [],
                        "created_at": "2026-03-18T12:00:00.000Z",
                        "updated_at": None
                    }
                }
            }
        },
        401: {
            "description": "Не авторизован",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authenticated"
                    }
                }
            }
        },
        403: {
            "description": "Недостаточно прав (не владелец теста)",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not enough permissions"
                    }
                }
            }
        },
        404: {
            "description": "Тест не найден"
        },
        422: {
            "description": "Ошибка валидации данных"
        }
    }
)
def create_question(
    test_id: int,
    question_data: QuestionCreate,
    db: Session = Depends(get_db)
):
    get_test_or_404(db, test_id)
    return TestService.create_question(db, test_id, question_data)

@router.get(
    "/{question_id}", 
    response_model=QuestionResponse,
    summary="Получить вопрос по ID",
    description="Возвращает информацию о конкретном вопросе по его идентификатору.",
    responses={
        200: {
            "description": "Вопрос найден",
            "content": {
                "application/json": {
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
                            }
                        ],
                        "created_at": "2026-03-18T12:00:00.000Z",
                        "updated_at": None
                    }
                }
            }
        },
        404: {
            "description": "Вопрос не найден",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Question not found"
                    }
                }
            }
        }
    }
)
def get_question(
    test_id: int,
    question_id: int,
    db: Session = Depends(get_db)
):
    get_test_or_404(db, test_id)
    question = TestService.get_question_by_id(db, question_id)
    if not question or question.test_id != test_id:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.put(
    "/{question_id}", 
    response_model=QuestionResponse,
    summary="Полностью обновить вопрос",
    description="Обновляет текст вопроса. Требуется авторизация (только владелец теста).",
    responses={
        200: {
            "description": "Вопрос успешно обновлен",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "test_id": 1,
                        "text": "Обновленный текст вопроса",
                        "answers": [],
                        "created_at": "2026-03-18T12:00:00.000Z",
                        "updated_at": "2026-03-18T13:00:00.000Z"
                    }
                }
            }
        },
        401: {
            "description": "Не авторизован"
        },
        403: {
            "description": "Недостаточно прав (не владелец теста)"
        },
        404: {
            "description": "Вопрос не найден"
        }
    }
)
def update_question(
    test_id: int,
    question_id: int,
    question_data: QuestionCreate,
    db: Session = Depends(get_db)
):
    get_test_or_404(db, test_id)
    question = TestService.update_question(db, question_id, question_data)
    if not question or question.test_id != test_id:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.delete(
    "/{question_id}", 
    status_code=204,
    summary="Удалить вопрос",
    description="Мягко удаляет вопрос (помечает как удаленный). Требуется авторизация (только владелец теста).",
    responses={
        204: {
            "description": "Вопрос успешно удален (мягкое удаление)"
        },
        401: {
            "description": "Не авторизован"
        },
        403: {
            "description": "Недостаточно прав (не владелец теста)"
        },
        404: {
            "description": "Вопрос не найден"
        }
    }
)
def delete_question(
    test_id: int,
    question_id: int,
    db: Session = Depends(get_db)
):
    get_test_or_404(db, test_id)
    question = TestService.delete_question(db, question_id)
    if not question or question.test_id != test_id:
        raise HTTPException(status_code=404, detail="Question not found")
    return None