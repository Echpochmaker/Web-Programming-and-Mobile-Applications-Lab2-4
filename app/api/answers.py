from fastapi import APIRouter, Depends, HTTPException
from typing import List
from bson import ObjectId
from app.core.auth import get_current_user
from app.services.test_service import TestService
from app.schemas.test import AnswerOptionCreate, AnswerOptionResponse

router = APIRouter(prefix="/questions/{question_id}/answers", tags=["answers"])


@router.get(
    "/",
    response_model=List[AnswerOptionResponse],
    summary="Получить варианты ответов",
    description="Возвращает все варианты ответов для указанного вопроса.",
    response_description="Список вариантов ответа",
    responses={
        200: {"description": "Успешный запрос - возвращен список ответов"},
        400: {"description": "Неверный формат идентификатора вопроса"}
    }
)
async def get_answers(question_id: str):
    """
    Возвращает список вариантов ответа для указанного вопроса.
    
    - **question_id**: уникальный идентификатор вопроса (ObjectId)
    """
    try:
        ObjectId(question_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid question_id format")
    
    answers = await TestService.get_answers(question_id)
    return answers


@router.post(
    "/",
    response_model=AnswerOptionResponse,
    status_code=201,
    summary="Добавить вариант ответа",
    description="Создает новый вариант ответа для указанного вопроса. Требуется авторизация (только владелец теста).",
    response_description="Созданный вариант ответа с ID",
    responses={
        201: {"description": "Вариант ответа успешно создан"},
        400: {"description": "Неверный формат идентификатора вопроса"},
        401: {"description": "Не авторизован - требуется вход в систему"},
        403: {"description": "Доступ запрещен - вы не владелец теста"},
        500: {"description": "Ошибка сервера при создании ответа"}
    }
)
async def create_answer(
    question_id: str,
    answer_data: AnswerOptionCreate,
    current_user = Depends(get_current_user)
):
    """
    Создает новый вариант ответа для вопроса.
    
    - **question_id**: уникальный идентификатор вопроса
    - **text**: текст варианта ответа
    - **is_correct**: флаг правильности ответа (true/false)
    """
    try:
        ObjectId(question_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid question_id format")
    
    test = await TestService.get_test_by_question_id(question_id)
    if not test or test.owner_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    answer = await TestService.create_answer(question_id, answer_data.model_dump())
    if not answer:
        raise HTTPException(status_code=500, detail="Failed to create answer")
    
    return answer


@router.put(
    "/{answer_id}",
    response_model=AnswerOptionResponse,
    summary="Обновить вариант ответа",
    description="Обновляет существующий вариант ответа. Требуется авторизация (только владелец теста).",
    response_description="Обновленный вариант ответа",
    responses={
        200: {"description": "Вариант ответа успешно обновлен"},
        400: {"description": "Неверный формат идентификатора"},
        401: {"description": "Не авторизован - требуется вход в систему"},
        403: {"description": "Доступ запрещен - вы не владелец теста"},
        404: {"description": "Вариант ответа не найден"}
    }
)
async def update_answer(
    question_id: str,
    answer_id: str,
    answer_data: AnswerOptionCreate,
    current_user = Depends(get_current_user)
):
    """
    Обновляет вариант ответа.
    
    - **question_id**: уникальный идентификатор вопроса
    - **answer_id**: уникальный идентификатор варианта ответа
    - **text**: новый текст варианта ответа
    - **is_correct**: новый флаг правильности
    """
    try:
        ObjectId(question_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid question_id format")
    
    test = await TestService.get_test_by_question_id(question_id)
    if not test or test.owner_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    answer = await TestService.update_answer(question_id, answer_id, answer_data.model_dump())
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    return answer


@router.delete(
    "/{answer_id}",
    status_code=204,
    summary="Удалить вариант ответа",
    description="Мягкое удаление варианта ответа. Требуется авторизация (только владелец теста).",
    responses={
        204: {"description": "Вариант ответа успешно удален"},
        400: {"description": "Неверный формат идентификатора"},
        401: {"description": "Не авторизован - требуется вход в систему"},
        403: {"description": "Доступ запрещен - вы не владелец теста"},
        404: {"description": "Вариант ответа не найден"}
    }
)
async def delete_answer(
    question_id: str,
    answer_id: str,
    current_user = Depends(get_current_user)
):
    """
    Удаляет вариант ответа (мягкое удаление).
    
    - **question_id**: уникальный идентификатор вопроса
    - **answer_id**: уникальный идентификатор варианта ответа
    """
    try:
        ObjectId(question_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid question_id format")
    
    test = await TestService.get_test_by_question_id(question_id)
    if not test or test.owner_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    result = await TestService.delete_answer(question_id, answer_id)
    if not result:
        raise HTTPException(status_code=404, detail="Answer not found")
    return None