from app.models.test_doc import Test, Question
from app.models.result_doc import TestResult, UserAnswer
from app.models.user_doc import User
from datetime import datetime
from typing import List, Optional
from bson import ObjectId

class ResultService:
    
    @staticmethod
    async def get_available_tests(user_id: str, page: int = 1, limit: int = 10):
        skip = (page - 1) * limit
        
        query = Test.find({"owner_id": {"$ne": user_id}, "deleted_at": None})
        total = await query.count()
        tests = await query.skip(skip).limit(limit).to_list()
        
        result = []
        for test in tests:
            questions_count = len(test.questions)
            attempts = await TestResult.find({
                "test_id": str(test.id),
                "user_id": user_id
            }).count()
            
            # Получаем автора
            author = await User.get(ObjectId(test.owner_id))
            
            result.append({
                "id": str(test.id),
                "title": test.title,
                "description": test.description,
                "author_email": author.email if author else "Unknown",
                "questions_count": questions_count,
                "user_attempts": attempts
            })
        
        return result, total
    
    @staticmethod
    async def start_test(test_id: str, user_id: str) -> Optional[dict]:
        test = await Test.get(ObjectId(test_id))
        if not test or test.deleted_at:
            return None
        
        total_questions = len(test.questions)
        result = TestResult(
            user_id=user_id,
            test_id=test_id,
            test_title=test.title,
            total_questions=total_questions,
            status="in_progress"
        )
        await result.insert()
        
        # Возвращаем вопросы с ответами
        questions_data = []
        for q in test.questions:
            if not q.deleted_at:
                questions_data.append({
                    "id": str(q.id),
                    "text": q.text,
                    "answers": [{"id": str(a.id), "text": a.text, "is_correct": a.is_correct} for a in q.answers if not a.deleted_at]
                })
        
        return {
            "id": str(result.id),
            "user_id": result.user_id,
            "test_id": result.test_id,
            "test_title": result.test_title,
            "total_questions": result.total_questions,
            "started_at": result.started_at,
            "status": result.status,
            "questions": questions_data
        }
    
    @staticmethod
    async def submit_answer(answer_data: dict) -> Optional[dict]:
        result = await TestResult.get(ObjectId(answer_data["result_id"]))
        if not result or result.status != "in_progress":
            return None
        
        test = await Test.get(ObjectId(result.test_id))
        if not test:
            return None
        
        # Находим вопрос и правильный ответ
        question = None
        correct_answer = None
        for q in test.questions:
            if str(q.id) == answer_data["question_id"]:
                question = q
                for a in q.answers:
                    if a.is_correct and not a.deleted_at:
                        correct_answer = a
                break
        
        if not question:
            return None
        
        selected_answer = None
        for a in question.answers:
            if str(a.id) == answer_data["selected_answer_id"]:
                selected_answer = a
                break
        
        is_correct = selected_answer and selected_answer.is_correct
        
        user_answer = UserAnswer(
            question_id=answer_data["question_id"],
            question_text=question.text,
            selected_answer_id=answer_data["selected_answer_id"],
            selected_answer_text=selected_answer.text if selected_answer else None,
            is_correct=is_correct,
            correct_answer_id=str(correct_answer.id) if correct_answer else None,
            correct_answer_text=correct_answer.text if correct_answer else None
        )
        
        result.answers.append(user_answer)
        await result.save()
        
        return {
            "id": str(user_answer.id),
            "question_id": user_answer.question_id,
            "question_text": user_answer.question_text,
            "selected_answer_id": user_answer.selected_answer_id,
            "selected_answer_text": user_answer.selected_answer_text,
            "is_correct": user_answer.is_correct,
            "correct_answer_id": user_answer.correct_answer_id,
            "correct_answer_text": user_answer.correct_answer_text
        }
    
    @staticmethod
    async def finish_test(result_id: str) -> Optional[dict]:
        result = await TestResult.get(ObjectId(result_id))
        if not result or result.status != "in_progress":
            return None
        
        correct_count = sum(1 for a in result.answers if a.is_correct)
        score = (correct_count / result.total_questions) * 100 if result.total_questions > 0 else 0
        
        result.correct_answers = correct_count
        result.score = score
        result.completed_at = datetime.utcnow()
        result.status = "completed"
        await result.save()
        
        # Формируем ответ с деталями
        answers_data = []
        for a in result.answers:
            answers_data.append({
                "id": str(a.id),
                "question_id": a.question_id,
                "question_text": a.question_text,
                "selected_answer_id": a.selected_answer_id,
                "selected_answer_text": a.selected_answer_text,
                "is_correct": a.is_correct,
                "correct_answer_id": a.correct_answer_id,
                "correct_answer_text": a.correct_answer_text
            })
        
        return {
            "id": str(result.id),
            "user_id": result.user_id,
            "test_id": result.test_id,
            "test_title": result.test_title,
            "score": result.score,
            "correct_answers": result.correct_answers,
            "total_questions": result.total_questions,
            "started_at": result.started_at,
            "completed_at": result.completed_at,
            "status": result.status,
            "answers": answers_data
        }
    
    @staticmethod
    async def get_result(result_id: str, user_id: str) -> Optional[dict]:
        result = await TestResult.get(ObjectId(result_id))
        if not result or result.user_id != user_id:
            return None
        
        answers_data = []
        for a in result.answers:
            answers_data.append({
                "id": str(a.id),
                "question_id": a.question_id,
                "question_text": a.question_text,
                "selected_answer_id": a.selected_answer_id,
                "selected_answer_text": a.selected_answer_text,
                "is_correct": a.is_correct,
                "correct_answer_id": a.correct_answer_id,
                "correct_answer_text": a.correct_answer_text
            })
        
        return {
            "id": str(result.id),
            "user_id": result.user_id,
            "test_id": result.test_id,
            "test_title": result.test_title,
            "score": result.score,
            "correct_answers": result.correct_answers,
            "total_questions": result.total_questions,
            "started_at": result.started_at,
            "completed_at": result.completed_at,
            "status": result.status,
            "answers": answers_data
        }
    
    @staticmethod
    async def get_user_results(user_id: str, page: int = 1, limit: int = 10):
        skip = (page - 1) * limit
        
        # Исправленный вариант сортировки
        query = TestResult.find({"user_id": user_id, "status": "completed"}).sort(("completed_at", -1))
        total = await query.count()
        results = await query.skip(skip).limit(limit).to_list()
        
        items = []
        for r in results:
            items.append({
                "id": str(r.id),
                "user_id": r.user_id,
                "test_id": r.test_id,
                "test_title": r.test_title,
                "score": r.score,
                "correct_answers": r.correct_answers,
                "total_questions": r.total_questions,
                "started_at": r.started_at,
                "completed_at": r.completed_at,
                "status": r.status
            })
    
        return items, total