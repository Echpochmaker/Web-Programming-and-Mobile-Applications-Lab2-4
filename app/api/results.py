from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.test import Question, AnswerOption, Test
from app.services.result_service import ResultService
from app.services.test_service import TestService
from app.schemas.result import (
    TestResultCreate, TestResultResponse, TestResultListResponse,
    TestAvailableResponse, TestAvailableListResponse, AnswerSubmission, UserAnswerResponse
)

router = APIRouter(prefix="/results", tags=["results"])

@router.get(
    "/available",
    response_model=TestAvailableListResponse,
    summary="Получить доступные тесты",
    description="Возвращает список тестов, которые можно пройти (чужие тесты)"
)
def get_available_tests(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(10, ge=1, le=100, description="Элементов на странице"),
    current_user: User = Depends(get_current_user)
):
    items, total = ResultService.get_available_tests(db, current_user.id, page, limit)
    total_pages = (total + limit - 1) // limit
    return {
        "data": items,
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
    }

@router.post(
    "/start/{test_id}",
    response_model=TestResultResponse,
    summary="Начать прохождение теста",
    description="Создает запись о начале теста и возвращает вопросы"
)
def start_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Проверяем, что тест существует
    test = TestService.get_by_id(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Нельзя проходить свой тест
    if test.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot take your own test")
    
    result = ResultService.start_test(db, test_id, current_user.id)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to start test")
    
    # Дополняем ответ вопросами
    questions = ResultService.get_test_questions(db, test_id)
    
    # Преобразуем в ответ
    return {
        "id": result.id,
        "user_id": result.user_id,
        "test_id": result.test_id,
        "test_title": test.title,
        "score": result.score,
        "correct_answers": result.correct_answers,
        "total_questions": result.total_questions,
        "started_at": result.started_at,
        "completed_at": result.completed_at,
        "status": result.status,
        "questions": questions
    }

@router.post(
    "/answer",
    response_model=UserAnswerResponse,
    summary="Отправить ответ",
    description="Сохраняет ответ пользователя на вопрос"
)
def submit_answer(
    answer_data: AnswerSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    answer = ResultService.submit_answer(db, answer_data)
    if not answer:
        raise HTTPException(status_code=400, detail="Failed to save answer")
    
    # Получаем дополнительную информацию для ответа
    question = answer.question
    # Находим правильный ответ на вопрос
    correct_answer = db.query(AnswerOption).filter(
        AnswerOption.question_id == answer.question_id,
        AnswerOption.is_correct == True
    ).first()
    
    return {
        "id": answer.id,
        "question_id": answer.question_id,
        "question_text": question.text,
        "selected_answer_id": answer.selected_answer_id,
        "selected_answer_text": answer.selected_answer.text if answer.selected_answer else None,
        "is_correct": answer.is_correct,
        "correct_answer_id": correct_answer.id if correct_answer else None,
        "correct_answer_text": correct_answer.text if correct_answer else None
    }

@router.post(
    "/finish/{result_id}",
    response_model=TestResultResponse,
    summary="Завершить тест",
    description="Подсчитывает результат и завершает прохождение"
)
def finish_test(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = ResultService.finish_test(db, result_id)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to finish test")
    
    # Получаем название теста
    test = db.query(Test).filter(Test.id == result.test_id).first()
    
    # Преобразуем ответы в нужный формат
    answers = []
    for answer in result.answers:
        question = answer.question
        correct_answer = db.query(AnswerOption).filter(
            AnswerOption.question_id == answer.question_id,
            AnswerOption.is_correct == True
        ).first()
        
        answers.append({
            "id": answer.id,
            "question_id": answer.question_id,
            "question_text": question.text,
            "selected_answer_id": answer.selected_answer_id,
            "selected_answer_text": answer.selected_answer.text if answer.selected_answer else None,
            "is_correct": answer.is_correct,
            "correct_answer_id": correct_answer.id if correct_answer else None,
            "correct_answer_text": correct_answer.text if correct_answer else None
        })
    
    return {
        "id": result.id,
        "user_id": result.user_id,
        "test_id": result.test_id,
        "test_title": test.title if test else "Unknown",
        "score": result.score,
        "correct_answers": result.correct_answers,
        "total_questions": result.total_questions,
        "started_at": result.started_at,
        "completed_at": result.completed_at,
        "status": result.status,
        "answers": answers
    }

@router.get(
    "/{result_id}",
    response_model=TestResultResponse,
    summary="Получить результат",
    description="Возвращает результат прохождения теста с ответами"
)
def get_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = ResultService.get_result(db, result_id, current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    # Получаем название теста
    test = db.query(Test).filter(Test.id == result.test_id).first()
    
    # Преобразуем ответы в нужный формат
    answers = []
    for answer in result.answers:
        question = answer.question
        correct_answer = db.query(AnswerOption).filter(
            AnswerOption.question_id == answer.question_id,
            AnswerOption.is_correct == True
        ).first()
        
        answers.append({
            "id": answer.id,
            "question_id": answer.question_id,
            "question_text": question.text,
            "selected_answer_id": answer.selected_answer_id,
            "selected_answer_text": answer.selected_answer.text if answer.selected_answer else None,
            "is_correct": answer.is_correct,
            "correct_answer_id": correct_answer.id if correct_answer else None,
            "correct_answer_text": correct_answer.text if correct_answer else None
        })
    
    return {
        "id": result.id,
        "user_id": result.user_id,
        "test_id": result.test_id,
        "test_title": test.title if test else "Unknown",
        "score": result.score,
        "correct_answers": result.correct_answers,
        "total_questions": result.total_questions,
        "started_at": result.started_at,
        "completed_at": result.completed_at,
        "status": result.status,
        "answers": answers
    }

@router.get(
    "/",
    response_model=TestResultListResponse,
    summary="Мои результаты",
    description="Возвращает список всех результатов пользователя"
)
def get_my_results(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(10, ge=1, le=100, description="Элементов на странице"),
    current_user: User = Depends(get_current_user)
):
    items, total = ResultService.get_user_results(db, current_user.id, page, limit)
    total_pages = (total + limit - 1) // limit
    return {
        "data": items,
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
    }