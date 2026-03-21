from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.auth import get_current_user, get_optional_user
from app.services.test_service import TestService
from app.schemas.test import TestCreate, TestUpdate, TestResponse, PaginatedResponse
from app.models.user import User

router = APIRouter(prefix="/tests", tags=["tests"])

@router.get(
    "/",
    response_model=PaginatedResponse,
    summary="Получить список тестов",
    description="Возвращает список тестов с пагинацией. Доступен всем пользователям.",
    responses={
        200: {
            "description": "Список тестов успешно получен",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": 1,
                                "title": "Основы Python",
                                "description": "Тест на знание Python",
                                "created_at": "2026-03-18T12:00:00.000Z",
                                "updated_at": None,
                                "questions": [],
                                "owner_id": 1
                            }
                        ],
                        "meta": {
                            "total": 42,
                            "page": 1,
                            "limit": 10,
                            "total_pages": 5
                        }
                    }
                }
            }
        },
        422: {
            "description": "Ошибка валидации параметров пагинации"
        }
    }
)
def get_tests(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Номер страницы (начиная с 1)"),
    limit: int = Query(10, ge=1, le=100, description="Количество элементов на странице (1-100)"),
    current_user: User = Depends(get_optional_user)
):
    items, total = TestService.get_all(db, page, limit)
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
    "/",
    response_model=TestResponse,
    status_code=201,
    summary="Создать новый тест",
    description="Создает тест для авторизованного пользователя. Тест привязывается к текущему пользователю.",
    responses={
        201: {
            "description": "Тест успешно создан",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Основы Python",
                        "description": "Тест на знание Python",
                        "created_at": "2026-03-18T12:00:00.000Z",
                        "updated_at": None,
                        "questions": [],
                        "owner_id": 1
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
        422: {
            "description": "Ошибка валидации данных"
        }
    }
)
def create_test(
    test_data: TestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    test_data_dict = test_data.model_dump()
    test_data_dict['owner_id'] = current_user.id
    return TestService.create(db, test_data_dict)

@router.get(
    "/{test_id}",
    response_model=TestResponse,
    summary="Получить тест по ID",
    description="Возвращает информацию о конкретном тесте по его идентификатору.",
    responses={
        200: {
            "description": "Тест найден",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Основы Python",
                        "description": "Тест на знание Python",
                        "created_at": "2026-03-18T12:00:00.000Z",
                        "updated_at": None,
                        "questions": [],
                        "owner_id": 1
                    }
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
    summary="Полностью обновить тест",
    description="Обновляет все поля теста. Доступно только владельцу теста.",
    responses={
        200: {
            "description": "Тест успешно обновлен",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Обновленное название",
                        "description": "Новое описание",
                        "created_at": "2026-03-18T12:00:00.000Z",
                        "updated_at": "2026-03-18T13:00:00.000Z",
                        "questions": [],
                        "owner_id": 1
                    }
                }
            }
        },
        401: {
            "description": "Не авторизован"
        },
        403: {
            "description": "Недостаточно прав",
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
        }
    }
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

    test = TestService.update(db, test_id, test_data)
    return test

@router.patch(
    "/{test_id}",
    response_model=TestResponse,
    summary="Частично обновить тест",
    description="Обновляет отдельные поля теста. Доступно только владельцу теста.",
    responses={
        200: {
            "description": "Тест успешно обновлен",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Обновленное название",
                        "description": "Старое описание",
                        "created_at": "2026-03-18T12:00:00.000Z",
                        "updated_at": "2026-03-18T13:00:00.000Z",
                        "questions": [],
                        "owner_id": 1
                    }
                }
            }
        },
        401: {
            "description": "Не авторизован"
        },
        403: {
            "description": "Недостаточно прав",
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
        }
    }
)
def partial_update_test(
    test_id: int,
    test_data: TestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Частичное обновление теста"""
    test = TestService.get_by_id(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    if test.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    test = TestService.update(db, test_id, test_data)
    return test

@router.delete(
    "/{test_id}",
    status_code=204,
    summary="Удалить тест",
    description="Мягко удаляет тест (помечает как удаленный). Доступно только владельцу теста.",
    responses={
        204: {
            "description": "Тест успешно удален (мягкое удаление)"
        },
        401: {
            "description": "Не авторизован"
        },
        403: {
            "description": "Недостаточно прав",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not enough permissions"
                    }
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
    return None