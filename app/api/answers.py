from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.auth import get_current_user
from app.services.test_service import TestService
from app.schemas.test import AnswerOptionCreate, AnswerOptionResponse

router = APIRouter(prefix="/questions/{question_id}/answers", tags=["answers"])

@router.get("/", response_model=List[AnswerOptionResponse])
async def get_answers(question_id: str):
    answers = await TestService.get_answers(question_id)
    return answers

@router.post("/", response_model=AnswerOptionResponse, status_code=201)
async def create_answer(
    question_id: str,
    answer_data: AnswerOptionCreate,
    current_user = Depends(get_current_user)
):
    test = await TestService.get_test_by_question_id(question_id)
    if not test or test.owner_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    answer = await TestService.create_answer(question_id, answer_data.model_dump())
    return answer

@router.put("/{answer_id}", response_model=AnswerOptionResponse)
async def update_answer(
    question_id: str,
    answer_id: str,
    answer_data: AnswerOptionCreate,
    current_user = Depends(get_current_user)
):
    test = await TestService.get_test_by_question_id(question_id)
    if not test or test.owner_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    answer = await TestService.update_answer(question_id, answer_id, answer_data.model_dump())
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    return answer

@router.delete("/{answer_id}", status_code=204)
async def delete_answer(
    question_id: str,
    answer_id: str,
    current_user = Depends(get_current_user)
):
    test = await TestService.get_test_by_question_id(question_id)
    if not test or test.owner_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    result = await TestService.delete_answer(question_id, answer_id)
    if not result:
        raise HTTPException(status_code=404, detail="Answer not found")
    return None