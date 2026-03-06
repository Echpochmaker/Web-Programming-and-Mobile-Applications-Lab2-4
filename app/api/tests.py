from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.test_service import TestService
from app.schemas.test import TestCreate, TestUpdate, TestResponse, PaginatedResponse

router = APIRouter(prefix="/tests", tags=["tests"])

@router.get("/", response_model=PaginatedResponse)
def get_tests(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
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

@router.get("/{test_id}", response_model=TestResponse)
def get_test(test_id: int, db: Session = Depends(get_db)):
    test = TestService.get_by_id(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test

@router.post("/", response_model=TestResponse, status_code=201)
def create_test(test_data: TestCreate, db: Session = Depends(get_db)):
    # Здесь можно добавить проверку на уникальность title и вернуть 409 при конфликте
    return TestService.create(db, test_data)

@router.put("/{test_id}", response_model=TestResponse)
def update_test(test_id: int, test_data: TestUpdate, db: Session = Depends(get_db)):
    test = TestService.update(db, test_id, test_data)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test

@router.patch("/{test_id}", response_model=TestResponse)
def partial_update_test(test_id: int, test_data: TestUpdate, db: Session = Depends(get_db)):
    test = TestService.update(db, test_id, test_data)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test

@router.delete("/{test_id}", status_code=204)
def delete_test(test_id: int, db: Session = Depends(get_db)):
    test = TestService.delete(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return None