from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from app.core.auth import get_current_user, get_optional_user
from app.services.test_service import TestService
from app.schemas.test import TestCreate, TestUpdate, TestResponse, PaginatedResponse
from app.core.cache import cache

router = APIRouter(prefix="/tests", tags=["tests"])

def serialize_test(test) -> dict:
    """Сериализует тест для JSON ответа"""
    questions_data = []
    
    if hasattr(test, 'questions') and test.questions:
        for q in test.questions:
            if hasattr(q, 'deleted_at') and q.deleted_at:
                continue
                
            answers_data = []
            if hasattr(q, 'answers') and q.answers:
                for a in q.answers:
                    if hasattr(a, 'deleted_at') and a.deleted_at:
                        continue
                    answers_data.append({
                        "id": str(a.id) if hasattr(a, 'id') else None,
                        "text": a.text if hasattr(a, 'text') else "",
                        "is_correct": a.is_correct if hasattr(a, 'is_correct') else False,
                        "created_at": a.created_at.isoformat() if hasattr(a, 'created_at') and a.created_at else None,
                        "updated_at": a.updated_at.isoformat() if hasattr(a, 'updated_at') and a.updated_at else None
                    })
            
            questions_data.append({
                "id": str(q.id) if hasattr(q, 'id') else None,
                "test_id": str(test.id) if hasattr(test, 'id') else None,
                "text": q.text if hasattr(q, 'text') else "",
                "answers": answers_data,
                "created_at": q.created_at.isoformat() if hasattr(q, 'created_at') and q.created_at else None,
                "updated_at": q.updated_at.isoformat() if hasattr(q, 'updated_at') and q.updated_at else None
            })
    
    return {
        "id": str(test.id) if hasattr(test, 'id') else None,
        "title": test.title if hasattr(test, 'title') else "",
        "description": test.description if hasattr(test, 'description') else None,
        "owner_id": str(test.owner_id) if hasattr(test, 'owner_id') else None,
        "questions": questions_data,
        "created_at": test.created_at.isoformat() if hasattr(test, 'created_at') and test.created_at else None,
        "updated_at": test.updated_at.isoformat() if hasattr(test, 'updated_at') and test.updated_at else None
    }


@router.get(
    "/",
    response_model=PaginatedResponse,
    summary="Получить список тестов",
    description="Возвращает список всех тестов с пагинацией. Доступно всем пользователям (авторизация опциональна).",
    response_description="Список тестов с метаданными пагинации",
    responses={
        200: {"description": "Успешный запрос - возвращен список тестов"},
        401: {"description": "Не авторизован (если требуется)"}
    }
)
async def get_tests(
    page: int = Query(1, ge=1, description="Номер страницы (начиная с 1)"),
    limit: int = Query(10, ge=1, le=100, description="Количество элементов на странице (1-100)"),
    current_user = Depends(get_optional_user)
):
    """
    Возвращает список тестов с пагинацией.
    
    - **page**: номер страницы
    - **limit**: количество записей на странице
    """
    cache_key = f"testing:tests:list:page:{page}:limit:{limit}"
    
    cached = cache.get(cache_key)
    if cached:
        print(f"Cache HIT: {cache_key}")
        return cached
    
    print(f"Cache MISS: {cache_key}")
    
    items, total = await TestService.get_all(page, limit)
    total_pages = (total + limit - 1) // limit
    
    serialized_items = [serialize_test(item) for item in items]
    
    response = {
        "data": serialized_items,
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
    }
    
    cache.set(cache_key, response, ttl=300)
    print(f"Saved to cache: {cache_key}")
    
    return response


@router.post(
    "/",
    response_model=TestResponse,
    status_code=201,
    summary="Создать новый тест",
    description="Создает новый тест. Требуется авторизация. Владелец теста - текущий пользователь.",
    response_description="Созданный тест с ID и метаданными",
    responses={
        201: {"description": "Тест успешно создан"},
        400: {"description": "Неверные данные в запросе"},
        401: {"description": "Не авторизован - требуется вход в систему"}
    }
)
async def create_test(
    test_data: TestCreate,
    current_user = Depends(get_current_user)
):
    """
    Создает новый тест.
    
    - **title**: название теста (обязательно)
    - **description**: описание теста (опционально)
    - **questions**: список вопросов (опционально, можно добавить позже)
    """
    test_dict = test_data.model_dump()
    test_dict['owner_id'] = str(current_user.id)
    
    test = await TestService.create(test_dict)
    
    cache.delete_pattern("testing:tests:list:*")
    print("Cache invalidated: testing:tests:list:*")
    
    return serialize_test(test)


@router.get(
    "/{test_id}",
    response_model=TestResponse,
    summary="Получить тест по ID",
    description="Возвращает конкретный тест по его уникальному идентификатору.",
    response_description="Полные данные теста, включая вопросы и ответы",
    responses={
        200: {"description": "Тест найден и возвращен"},
        400: {"description": "Неверный формат идентификатора теста"},
        404: {"description": "Тест с указанным ID не найден"}
    }
)
async def get_test(
    test_id: str,
    current_user = Depends(get_optional_user)
):
    """
    Возвращает тест по ID.
    
    - **test_id**: уникальный идентификатор теста (ObjectId)
    """
    try:
        ObjectId(test_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid test_id format")
    
    test = await TestService.get_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    return serialize_test(test)


@router.patch(
    "/{test_id}",
    response_model=TestResponse,
    summary="Обновить тест",
    description="Обновляет данные существующего теста. Только владелец может редактировать.",
    response_description="Обновленный тест",
    responses={
        200: {"description": "Тест успешно обновлен"},
        400: {"description": "Неверный формат ID или данные запроса"},
        401: {"description": "Не авторизован - требуется вход в систему"},
        403: {"description": "Доступ запрещен - вы не владелец теста"},
        404: {"description": "Тест с указанным ID не найден"}
    }
)
async def update_test(
    test_id: str,
    test_data: TestUpdate,
    current_user = Depends(get_current_user)
):
    """
    Частичное обновление теста (PATCH).
    
    - **test_id**: уникальный идентификатор теста
    - **title**: новое название (опционально)
    - **description**: новое описание (опционально)
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
    
    updated_test = await TestService.update(test_id, test_data)
    
    cache.delete_pattern("testing:tests:list:*")
    print("Cache invalidated: testing:tests:list:*")
    
    return serialize_test(updated_test)


@router.delete(
    "/{test_id}",
    status_code=204,
    summary="Удалить тест",
    description="Мягкое удаление теста (помечается как удаленный, но не удаляется физически). Только владелец может удалить.",
    responses={
        204: {"description": "Тест успешно удален"},
        400: {"description": "Неверный формат идентификатора теста"},
        401: {"description": "Не авторизован - требуется вход в систему"},
        403: {"description": "Доступ запрещен - вы не владелец теста"},
        404: {"description": "Тест с указанным ID не найден"}
    }
)
async def delete_test(
    test_id: str,
    current_user = Depends(get_current_user)
):
    """
    Удаляет тест (мягкое удаление).
    
    - **test_id**: уникальный идентификатор теста
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
    
    await TestService.delete(test_id)
    
    cache.delete_pattern("testing:tests:list:*")
    print("Cache invalidated: testing:tests:list:*")
    
    return None