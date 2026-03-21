from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.test_service import TestService
from app.schemas.test import AnswerOptionCreate, AnswerOptionResponse

router = APIRouter(prefix="/questions/{question_id}/answers", tags=["answers"])

def get_question_or_404(db: Session, question_id: int):
    question = TestService.get_question_by_id(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.get(
    "/", 
    response_model=List[AnswerOptionResponse],
    summary="Получить все ответы на вопрос",
    description="Возвращает список вариантов ответа для указанного вопроса. Доступно всем пользователям.",
    responses={
        200: {
            "description": "Список ответов успешно получен",
            "content": {
                "application/json": {
                    "example": [
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
                    ]
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
def get_answers(question_id: int, db: Session = Depends(get_db)):
    get_question_or_404(db, question_id)
    return TestService.get_answers(db, question_id)

@router.post(
    "/", 
    response_model=AnswerOptionResponse, 
    status_code=201,
    summary="Создать новый ответ",
    description="Создает новый вариант ответа для указанного вопроса. Требуется авторизация (только владелец теста).",
    responses={
        201: {
            "description": "Ответ успешно создан",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "text": "4",
                        "is_correct": True,
                        "created_at": "2026-03-18T12:00:00.000Z",
                        "updated_at": None
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
        },
        422: {
            "description": "Ошибка валидации данных"
        }
    }
)
def create_answer(
    question_id: int,
    answer_data: AnswerOptionCreate,
    db: Session = Depends(get_db)
):
    get_question_or_404(db, question_id)
    return TestService.create_answer(db, question_id, answer_data)

@router.put(
    "/{answer_id}", 
    response_model=AnswerOptionResponse,
    summary="Обновить ответ",
    description="Обновляет текст и флаг правильности ответа. Требуется авторизация (только владелец теста).",
    responses={
        200: {
            "description": "Ответ успешно обновлен",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "text": "Обновленный текст ответа",
                        "is_correct": True,
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
            "description": "Ответ не найден"
        },
        422: {
            "description": "Ошибка валидации данных"
        }
    }
)
def update_answer(
    question_id: int,
    answer_id: int,
    answer_data: AnswerOptionCreate,
    db: Session = Depends(get_db)
):
    get_question_or_404(db, question_id)
    answer = TestService.update_answer(db, answer_id, answer_data)
    if not answer or answer.question_id != question_id:
        raise HTTPException(status_code=404, detail="Answer not found")
    return answer

@router.delete(
    "/{answer_id}", 
    status_code=204,
    summary="Удалить ответ",
    description="Мягко удаляет ответ (помечает как удаленный). Требуется авторизация (только владелец теста).",
    responses={
        204: {
            "description": "Ответ успешно удален (мягкое удаление)"
        },
        401: {
            "description": "Не авторизован"
        },
        403: {
            "description": "Недостаточно прав (не владелец теста)"
        },
        404: {
            "description": "Ответ не найден"
        }
    }
)
def delete_answer(
    question_id: int,
    answer_id: int,
    db: Session = Depends(get_db)
):
    get_question_or_404(db, question_id)
    answer = TestService.delete_answer(db, answer_id)
    if not answer or answer.question_id != question_id:
        raise HTTPException(status_code=404, detail="Answer not found")
    return None