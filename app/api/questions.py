from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.core.auth import get_current_user, get_optional_user
from app.services.test_service import TestService
from app.schemas.test import QuestionCreate, QuestionResponse

router = APIRouter(prefix="/tests/{test_id}/questions", tags=["questions"])

@router.get("/", response_model=List[QuestionResponse])
async def get_questions(
    test_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    questions = await TestService.get_questions(test_id, skip, limit)
    return questions

@router.post("/", response_model=QuestionResponse, status_code=201)
async def create_question(
    test_id: str,
    question_data: QuestionCreate,
    current_user = Depends(get_current_user)
):
    test = await TestService.get_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    if test.owner_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    question = await TestService.add_question(test_id, question_data.model_dump())
    return question

@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    test_id: str,
    question_id: str,
    current_user = Depends(get_optional_user)
):
    question = await TestService.get_question_by_id(test_id, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
    test_id: str,
    question_id: str,
    question_data: QuestionCreate,
    current_user = Depends(get_current_user)
):
    test = await TestService.get_by_id(test_id)
    if not test or test.owner_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    question = await TestService.update_question(test_id, question_id, question_data.model_dump())
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.delete("/{question_id}", status_code=204)
async def delete_question(
    test_id: str,
    question_id: str,
    current_user = Depends(get_current_user)
):
    test = await TestService.get_by_id(test_id)
    if not test or test.owner_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    result = await TestService.delete_question(test_id, question_id)
    if not result:
        raise HTTPException(status_code=404, detail="Question not found")
    return None