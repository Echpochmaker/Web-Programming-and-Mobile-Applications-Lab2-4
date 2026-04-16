from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.core.cache import cache
from app.core.auth import get_current_user, get_optional_user
from app.services.test_service import TestService
from app.schemas.test import TestCreate, TestUpdate, TestResponse, PaginatedResponse, serialize_test
from app.models.user_doc import User

router = APIRouter(prefix="/tests", tags=["tests"])

@router.get(
    "/",
    response_model=PaginatedResponse,
    summary="Получить список тестов",
)
async def get_tests(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_optional_user)
):
    cache_key = f"testing:tests:list:page:{page}:limit:{limit}"
    
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    items, total = await TestService.get_all(page, limit)
    total_pages = (total + limit - 1) // limit
    
    # Сериализуем объекты в словари
    serializable_items = []
    for item in items:
        serializable_items.append({
            "id": str(item.id),
            "title": item.title,
            "description": item.description,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "owner_id": str(item.owner_id),
            "questions": []  # вопросы не кешируем
        })
    
    response = {
        "data": serializable_items,
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
    }
    
    cache.set(cache_key, response, ttl=300)
    return response

@router.post(
    "/",
    response_model=TestResponse,
    status_code=201,
)
async def create_test(
    test_data: TestCreate,
    current_user: User = Depends(get_current_user)
):
    test_dict = test_data.model_dump()
    test_dict['owner_id'] = str(current_user.id)
    
    result = await TestService.create(test_dict)
    
    # Сериализуем результат для ответа
    response_data = {
        "id": str(result.id),
        "title": result.title,
        "description": result.description,
        "created_at": result.created_at,
        "updated_at": result.updated_at,
        "owner_id": str(result.owner_id),
        "questions": []
    }
    
    cache.delete_pattern("testing:tests:list:*")
    
    return response_data

@router.get(
    "/{test_id}",
    response_model=TestResponse,
)
async def get_test(
    test_id: str,
    current_user: User = Depends(get_optional_user)
):
    test = await TestService.get_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Сериализуем результат для ответа
    response_data = {
        "id": str(test.id),
        "title": test.title,
        "description": test.description,
        "created_at": test.created_at,
        "updated_at": test.updated_at,
        "owner_id": str(test.owner_id),
        "questions": []
    }
    
    return response_data

@router.put(
    "/{test_id}",
    response_model=TestResponse,
)
async def update_test(
    test_id: str,
    test_data: TestUpdate,
    current_user: User = Depends(get_current_user)
):
    test = await TestService.get_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if test.owner_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    result = await TestService.update(test_id, test_data)
    
    # Сериализуем результат для ответа
    response_data = {
        "id": str(result.id),
        "title": result.title,
        "description": result.description,
        "created_at": result.created_at,
        "updated_at": result.updated_at,
        "owner_id": str(result.owner_id),
        "questions": []
    }
    
    cache.delete_pattern("testing:tests:list:*")
    
    return response_data

@router.patch(
    "/{test_id}",
    response_model=TestResponse,
)
async def partial_update_test(
    test_id: str,
    test_data: TestUpdate,
    current_user: User = Depends(get_current_user)
):
    test = await TestService.get_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if test.owner_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    result = await TestService.update(test_id, test_data)
    
    # Сериализуем результат для ответа
    response_data = {
        "id": str(result.id),
        "title": result.title,
        "description": result.description,
        "created_at": result.created_at,
        "updated_at": result.updated_at,
        "owner_id": str(result.owner_id),
        "questions": []
    }
    
    cache.delete_pattern("testing:tests:list:*")
    
    return response_data

@router.delete(
    "/{test_id}",
    status_code=204,
)
async def delete_test(
    test_id: str,
    current_user: User = Depends(get_current_user)
):
    test = await TestService.get_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if test.owner_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    await TestService.delete(test_id)
    
    cache.delete_pattern("testing:tests:list:*")
    
    return None