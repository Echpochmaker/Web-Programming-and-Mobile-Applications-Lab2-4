from app.models.test_doc import Test
from app.models.result_doc import TestResult
from app.models.user_doc import User
from datetime import datetime
from typing import List, Optional, Tuple
from bson import ObjectId

class ResultService:
    
    @staticmethod
    async def get_available_tests(
        user_id: str, 
        page: int = 1, 
        limit: int = 10,
        search: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        skip = (page - 1) * limit
        
        query = {"owner_id": {"$ne": user_id}, "deleted_at": None}
        
        if search:
            query["title"] = {"$regex": search, "$options": "i"}
        
        test_query = Test.find(query)
        total = await test_query.count()
        tests = await test_query.skip(skip).limit(limit).to_list()
        
        result = []
        for test in tests:
            questions_count = len([q for q in test.questions if not q.deleted_at])
            attempts = await TestResult.find({
                "test_id": str(test.id),
                "user_id": user_id
            }).count()
            
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
        try:
            test = await Test.get(ObjectId(test_id))
        except:
            return None
            
        if not test or test.deleted_at:
            return None
        
        total_questions = len([q for q in test.questions if not q.deleted_at])
        result = TestResult(
            user_id=user_id,
            test_id=test_id,
            test_title=test.title,
            total_questions=total_questions,
            status="in_progress"
        )
        await result.insert()
        
        questions_data = []
        for q in test.questions:
            if not q.deleted_at:
                answers = [
                    {"id": str(a.id), "text": a.text}
                    for a in q.answers if not a.deleted_at
                ]
                questions_data.append({
                    "id": str(q.id),
                    "text": q.text,
                    "answers": answers
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
        try:
            result = await TestResult.get(ObjectId(answer_data["result_id"]))
        except:
            return None
            
        if not result or result.status != "in_progress":
            return None
        
        try:
            test = await Test.get(ObjectId(result.test_id))
        except:
            return None
            
        if not test:
            return None
        
        question = None
        for q in test.questions:
            if str(q.id) == answer_data["question_id"] and not q.deleted_at:
                question = q
                break
        
        if not question:
            return None
        
        selected_answer = None
        for a in question.answers:
            if str(a.id) == answer_data["selected_answer_id"] and not a.deleted_at:
                selected_answer = a
                break
        
        existing = None
        for a in result.answers:
            if a.question_id == answer_data["question_id"]:
                existing = a
                break
        
        if existing:
            existing.selected_answer_id = answer_data["selected_answer_id"]
            existing.selected_answer_text = selected_answer.text if selected_answer else None
        else:
            user_answer = {
                "id": ObjectId(),
                "question_id": answer_data["question_id"],
                "question_text": question.text,
                "selected_answer_id": answer_data["selected_answer_id"],
                "selected_answer_text": selected_answer.text if selected_answer else None
            }
            result.answers.append(user_answer)
            existing = user_answer
        
        await result.save()
        
        if isinstance(existing, dict):
            return {
                "id": str(existing["id"]),
                "question_id": existing["question_id"],
                "selected_answer_id": existing["selected_answer_id"]
            }
        else:
            return {
                "id": str(existing.id),
                "question_id": existing.question_id,
                "selected_answer_id": existing.selected_answer_id
            }
    
    @staticmethod
    async def finish_test(result_id: str) -> Optional[dict]:
        try:
            result = await TestResult.get(ObjectId(result_id))
        except:
            return None
            
        if not result or result.status != "in_progress":
            return None
        
        try:
            test = await Test.get(ObjectId(result.test_id))
        except:
            return None
        
        if not test:
            return None
        
        correct_count = 0
        correct_answers_map = {}
        
        for q in test.questions:
            if not q.deleted_at:
                for a in q.answers:
                    if a.is_correct and not a.deleted_at:
                        correct_answers_map[str(q.id)] = str(a.id)
                        break
        
        for answer in result.answers:
            question_id = answer.get("question_id") if isinstance(answer, dict) else answer.question_id
            selected_id = answer.get("selected_answer_id") if isinstance(answer, dict) else answer.selected_answer_id
            
            if question_id in correct_answers_map:
                is_correct = (selected_id == correct_answers_map[question_id])
                if isinstance(answer, dict):
                    answer["is_correct"] = is_correct
                    answer["correct_answer_id"] = correct_answers_map[question_id]
                else:
                    answer.is_correct = is_correct
                    answer.correct_answer_id = correct_answers_map[question_id]
                
                if is_correct:
                    correct_count += 1
        
        result.correct_answers = correct_count
        result.score = (correct_count / result.total_questions) * 100 if result.total_questions > 0 else 0
        result.completed_at = datetime.utcnow()
        result.status = "completed"
        await result.save()
        
        author_email = "Unknown"
        if test and test.owner_id:
            try:
                author = await User.get(ObjectId(test.owner_id))
                if author:
                    author_email = author.email
            except:
                pass
        
        answers_data = []
        for a in result.answers:
            if isinstance(a, dict):
                answers_data.append({
                    "id": str(a["id"]),
                    "question_id": a["question_id"],
                    "question_text": a["question_text"],
                    "selected_answer_id": a.get("selected_answer_id"),
                    "selected_answer_text": a.get("selected_answer_text"),
                    "is_correct": a.get("is_correct"),
                    "correct_answer_id": a.get("correct_answer_id"),
                    "correct_answer_text": a.get("correct_answer_text")
                })
            else:
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
            "author_email": author_email,
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
        try:
            result = await TestResult.get(ObjectId(result_id))
        except:
            return None
            
        if not result or result.user_id != user_id:
            return None
        
        try:
            test = await Test.get(ObjectId(result.test_id))
            author = await User.get(ObjectId(test.owner_id)) if test else None
            author_email = author.email if author else "Unknown"
        except:
            author_email = "Unknown"
        
        answers_data = []
        for a in result.answers:
            if isinstance(a, dict):
                answers_data.append({
                    "id": str(a["id"]),
                    "question_id": a["question_id"],
                    "question_text": a["question_text"],
                    "selected_answer_id": a.get("selected_answer_id"),
                    "selected_answer_text": a.get("selected_answer_text"),
                    "is_correct": a.get("is_correct"),
                    "correct_answer_id": a.get("correct_answer_id"),
                    "correct_answer_text": a.get("correct_answer_text")
                })
            else:
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
            "author_email": author_email,
            "score": result.score,
            "correct_answers": result.correct_answers,
            "total_questions": result.total_questions,
            "started_at": result.started_at,
            "completed_at": result.completed_at,
            "status": result.status,
            "answers": answers_data
        }
    
    @staticmethod
    async def get_user_results(user_id: str, page: int = 1, limit: int = 10) -> Tuple[List[dict], int]:
        skip = (page - 1) * limit
        
        query = TestResult.find({
            "user_id": user_id, 
            "status": "completed"
        }).sort(-TestResult.completed_at)
        
        total = await query.count()
        results = await query.skip(skip).limit(limit).to_list()
        
        items = []
        for r in results:
            try:
                test = await Test.get(ObjectId(r.test_id))
                author = await User.get(ObjectId(test.owner_id)) if test else None
                author_email = author.email if author else "Unknown"
            except:
                author_email = "Unknown"
                
            items.append({
                "id": str(r.id),
                "user_id": r.user_id,
                "test_id": r.test_id,
                "test_title": r.test_title,
                "author_email": author_email,
                "score": r.score,
                "correct_answers": r.correct_answers,
                "total_questions": r.total_questions,
                "started_at": r.started_at,
                "completed_at": r.completed_at,
                "status": r.status
            })
    
        return items, total


result_service = ResultService()