from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from bson import ObjectId
from app.core.auth import get_current_user, get_optional_user
from app.services.test_service import TestService
from app.schemas.test import QuestionCreate, QuestionResponse

router = APIRouter(prefix="/tests/{test_id}/questions", tags=["questions"])

def serialize_question(question, test_id: str) -> dict:
    """Сериализует вопрос для JSON ответа"""
    answers_data = []
    if hasattr(question, 'answers') and question.answers:
        for a in question.answers:
            if hasattr(a, 'deleted_at') and a.deleted_at:
                continue
            answers_data.append({
                "id": str(a.id) if hasattr(a, 'id') else None,
                "text": a.text if hasattr(a, 'text') else "",
                "is_correct": a.is_correct if hasattr(a, 'is_correct') else False,
                "created_at": a.created_at.isoformat() if hasattr(a, 'created_at') and a.created_at else None,
                "updated_at": a.updated_at.isoformat() if hasattr(a, 'updated_at') and a.updated_at else None
            })
    
    return {
        "id": str(question.id) if hasattr(question, 'id') else None,
        "test_id": test_id,
        "text": question.text if hasattr(question, 'text') else "",
        "answers": answers_data,
        "created_at": question.created_at.isoformat() if hasattr(question, 'created_at') and question.created_at else None,
        "updated_at": question.updated_at.isoformat() if hasattr(question, 'updated_at') and question.updated_at else None
    }


@router.get(
    "/",
    response_model=List[QuestionResponse],
    summary="Получить список вопросов теста",
    description="Возвращает все вопросы указанного теста с пагинацией.",
    response_description="Список вопросов с вариантами ответов",
    responses={
        200: {"description": "Успешный запрос - возвращен список вопросов"},
        400: {"description": "Неверный формат идентификатора теста"},
        404: {"description": "Тест не найден"}
    }
)
async def get_questions(
    test_id: str,
    skip: int = Query(0, ge=0, description="Количество пропускаемых вопросов"),
    limit: int = Query(100, ge=1, le=100, description="Максимальное количество вопросов")
):
    """
    Возвращает список вопросов для указанного теста.
    
    - **test_id**: уникальный идентификатор теста (ObjectId)
    - **skip**: сколько вопросов пропустить (для пагинации)
    - **limit**: максимальное количество возвращаемых вопросов
    """
    try:
        ObjectId(test_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid test_id format")
    
    test = await TestService.get_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    questions = []
    if hasattr(test, 'questions') and test.questions:
        for q in test.questions:
            if not (hasattr(q, 'deleted_at') and q.deleted_at):
                questions.append(serialize_question(q, test_id))
    
    return questions[skip:skip+limit]


@router.post(
    "/",
    response_model=QuestionResponse,
    status_code=201,
    summary="Создать новый вопрос",
    description="Добавляет новый вопрос в указанный тест. Требуется авторизация (только владелец теста).",
    response_description="Созданный вопрос с ID и метаданными",
    responses={
        201: {"description": "Вопрос успешно создан"},
        400: {"description": "Неверный формат идентификатора теста"},
        401: {"description": "Не авторизован - требуется вход в систему"},
        403: {"description": "Доступ запрещен - вы не владелец теста"},
        404: {"description": "Тест не найден"},
        500: {"description": "Ошибка сервера при создании вопроса"}
    }
)
async def create_question(
    test_id: str,
    question_data: QuestionCreate,
    current_user = Depends(get_current_user)
):
    """
    Создает новый вопрос в тесте.
    
    - **test_id**: уникальный идентификатор теста
    - **text**: текст вопроса
    - **answers**: список вариантов ответа (можно добавить позже)
    """
    try:
        ObjectId(test_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid test_id format")
    
    test = await TestService.get_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    if test.owner_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    question = await TestService.add_question(test_id, question_data.model_dump())
    if not question:
        raise HTTPException(status_code=500, detail="Failed to create question")
    
    return question


@router.delete(
    "/{question_id}",
    status_code=204,
    summary="Удалить вопрос",
    description="Мягкое удаление вопроса из теста. Требуется авторизация (только владелец теста).",
    responses={
        204: {"description": "Вопрос успешно удален"},
        400: {"description": "Неверный формат идентификатора теста"},
        401: {"description": "Не авторизован - требуется вход в систему"},
        403: {"description": "Доступ запрещен - вы не владелец теста"},
        404: {"description": "Вопрос не найден"}
    }
)
async def delete_question(
    test_id: str,
    question_id: str,
    current_user = Depends(get_current_user)
):
    """
    Удаляет вопрос из теста (мягкое удаление).
    
    - **test_id**: уникальный идентификатор теста
    - **question_id**: уникальный идентификатор вопроса
    """
    try:
        ObjectId(test_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid test_id format")
    
    test = await TestService.get_by_id(test_id)
    if not test or test.owner_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    result = await TestService.delete_question(test_id, question_id)
    if not result:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return None