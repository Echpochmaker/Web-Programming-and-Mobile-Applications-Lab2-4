from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.core.auth import get_current_user
from app.models.user_doc import User
from app.services.result_service import ResultService

router = APIRouter(prefix="/results", tags=["results"])

@router.get("/available")
async def get_available_tests(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    items, total = await ResultService.get_available_tests(str(current_user.id), page, limit)
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

@router.post("/start/{test_id}")
async def start_test(
    test_id: str,
    current_user: User = Depends(get_current_user)
):
    result = await ResultService.start_test(test_id, str(current_user.id))
    if not result:
        raise HTTPException(status_code=400, detail="Failed to start test")
    
    return result

@router.post("/answer")
async def submit_answer(
    answer_data: dict,
    current_user: User = Depends(get_current_user)
):
    answer = await ResultService.submit_answer(answer_data)
    if not answer:
        raise HTTPException(status_code=400, detail="Failed to save answer")
    return answer

@router.post("/finish/{result_id}")
async def finish_test(
    result_id: str,
    current_user: User = Depends(get_current_user)
):
    result = await ResultService.finish_test(result_id)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to finish test")
    return result

@router.get("/{result_id}")
async def get_result(
    result_id: str,
    current_user: User = Depends(get_current_user)
):
    result = await ResultService.get_result(result_id, str(current_user.id))
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result

@router.get("/")
async def get_my_results(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    items, total = await ResultService.get_user_results(str(current_user.id), page, limit)
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