from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.cache import cache
from app.core.auth import get_current_user, get_optional_user
from app.services.test_service import TestService
from app.schemas.test import TestCreate, TestUpdate, TestResponse, PaginatedResponse, serialize_test
from app.models.user import User

router = APIRouter(prefix="/tests", tags=["tests"])

@router.get(
    "/",
    response_model=PaginatedResponse,
    summary="Получить список тестов",
)
def get_tests(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_optional_user)
):
    cache_key = f"testing:tests:list:page:{page}:limit:{limit}"
    
    # Проверяем кеш
    cached = cache.get(cache_key)
    if cached:
        print(f"Cache HIT: {cache_key}")
        return cached
    
    print(f"Cache MISS: {cache_key}")
    
    # Получаем из БД
    items, total = TestService.get_all(db, page, limit)
    total_pages = (total + limit - 1) // limit
    
    # Сериализуем объекты
    serializable_items = [serialize_test(item) for item in items]
    
    response = {
        "data": serializable_items,
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
    }
    
    # Сохраняем в кеш
    cache.set(cache_key, response, ttl=300)
    print(f"Saved to cache: {cache_key}")
    
    return response

@router.post(
    "/",
    response_model=TestResponse,
    status_code=201,
)
def create_test(
    test_data: TestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    test_data_dict = test_data.model_dump()
    test_data_dict['owner_id'] = current_user.id

    result = TestService.create(db, test_data_dict)

    cache.delete_pattern("testing:tests:list:*")
    print("Cache invalidated: testing:tests:list:*")

    return result

@router.get(
    "/{test_id}",
    response_model=TestResponse,
)
def get_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    test = TestService.get_by_id(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test

@router.put(
    "/{test_id}",
    response_model=TestResponse,
)
def update_test(
    test_id: int,
    test_data: TestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    test = TestService.get_by_id(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if test.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    result = TestService.update(db, test_id, test_data)
    
    # Инвалидация кеша
    cache.delete_pattern("testing:tests:list:*")
    print(f"Cache invalidated: testing:tests:list:*")
    
    return result

@router.patch(
    "/{test_id}",
    response_model=TestResponse,
)
def partial_update_test(
    test_id: int,
    test_data: TestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    test = TestService.get_by_id(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if test.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    result = TestService.update(db, test_id, test_data)
    
    # Инвалидация кеша
    cache.delete_pattern("testing:tests:list:*")
    print(f"Cache invalidated: testing:tests:list:*")
    
    return result

@router.delete(
    "/{test_id}",
    status_code=204,
)
def delete_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    test = TestService.get_by_id(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if test.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    TestService.delete(db, test_id)
    
    # Инвалидация кеша
    cache.delete_pattern("testing:tests:list:*")
    print(f"Cache invalidated: testing:tests:list:*")
    
    return None