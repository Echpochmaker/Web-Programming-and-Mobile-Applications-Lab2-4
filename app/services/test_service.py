from app.models.test_doc import Test, Question, AnswerOption
from app.schemas.test import TestUpdate
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId

class TestService:
    
    @staticmethod
    async def get_all(page: int = 1, limit: int = 10):
        skip = (page - 1) * limit
        query = Test.find(Test.deleted_at == None)
        total = await query.count()
        items = await query.skip(skip).limit(limit).to_list()
        return items, total

    @staticmethod
    async def get_by_id(test_id: str) -> Optional[Test]:
        try:
            test = await Test.get(ObjectId(test_id))
            if test and test.deleted_at:
                return None
            return test
        except:
            return None

    @staticmethod
    async def create(test_data: Dict[str, Any]) -> Test:
        test = Test(**test_data)
        await test.insert()
        return test

    @staticmethod
    async def update(test_id: str, test_data: TestUpdate) -> Optional[Test]:
        test = await TestService.get_by_id(test_id)
        if not test:
            return None
        
        update_data = test_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(test, key, value)
        
        test.updated_at = datetime.utcnow()
        await test.save()
        return test

    @staticmethod
    async def delete(test_id: str) -> Optional[Test]:
        test = await TestService.get_by_id(test_id)
        if not test:
            return None
        
        test.soft_delete()
        await test.save()
        return test

    @staticmethod
    async def get_questions(test_id: str, skip: int = 0, limit: int = 100) -> List[Question]:
        test = await TestService.get_by_id(test_id)
        if not test:
            return []
        
        questions = [q for q in test.questions if not q.deleted_at]
        return questions[skip:skip+limit]

    @staticmethod
    async def get_question_by_id(test_id: str, question_id: str) -> Optional[Question]:
        test = await TestService.get_by_id(test_id)
        if not test:
            return None
        
        for q in test.questions:
            if str(q.id) == question_id and not q.deleted_at:
                return q
        return None

    @staticmethod
    async def add_question(test_id: str, question_data: dict) -> Optional[Question]:
        test = await TestService.get_by_id(test_id)
        if not test:
            return None
        
        question = Question(**question_data)
        test.questions.append(question)
        test.updated_at = datetime.utcnow()
        await test.save()
        return question

    @staticmethod
    async def update_question(test_id: str, question_id: str, question_data: dict) -> Optional[Question]:
        test = await TestService.get_by_id(test_id)
        if not test:
            return None
        
        for q in test.questions:
            if str(q.id) == question_id and not q.deleted_at:
                q.text = question_data.get("text", q.text)
                test.updated_at = datetime.utcnow()
                await test.save()
                return q
        return None

    @staticmethod
    async def delete_question(test_id: str, question_id: str) -> Optional[Question]:
        test = await TestService.get_by_id(test_id)
        if not test:
            return None
        
        for q in test.questions:
            if str(q.id) == question_id and not q.deleted_at:
                q.deleted_at = datetime.utcnow()
                test.updated_at = datetime.utcnow()
                await test.save()
                return q
        return None

    @staticmethod
    async def get_answers(question_id: str) -> List[AnswerOption]:
        # Найти вопрос во всех тестах
        test = await Test.find_one({"questions.id": question_id})
        if not test:
            return []
        
        for q in test.questions:
            if str(q.id) == question_id and not q.deleted_at:
                return [a for a in q.answers if not a.deleted_at]
        return []

    @staticmethod
    async def get_test_by_question_id(question_id: str) -> Optional[Test]:
        test = await Test.find_one({"questions.id": question_id})
        return test

    @staticmethod
    async def create_answer(question_id: str, answer_data: dict) -> Optional[AnswerOption]:
        test = await Test.find_one({"questions.id": question_id})
        if not test:
            return None
        
        for q in test.questions:
            if str(q.id) == question_id and not q.deleted_at:
                answer = AnswerOption(**answer_data)
                q.answers.append(answer)
                test.updated_at = datetime.utcnow()
                await test.save()
                return answer
        return None

    @staticmethod
    async def update_answer(question_id: str, answer_id: str, answer_data: dict) -> Optional[AnswerOption]:
        test = await Test.find_one({"questions.id": question_id})
        if not test:
            return None
        
        for q in test.questions:
            if str(q.id) == question_id and not q.deleted_at:
                for a in q.answers:
                    if str(a.id) == answer_id and not a.deleted_at:
                        a.text = answer_data.get("text", a.text)
                        a.is_correct = answer_data.get("is_correct", a.is_correct)
                        test.updated_at = datetime.utcnow()
                        await test.save()
                        return a
        return None

    @staticmethod
    async def delete_answer(question_id: str, answer_id: str) -> Optional[AnswerOption]:
        test = await Test.find_one({"questions.id": question_id})
        if not test:
            return None
        
        for q in test.questions:
            if str(q.id) == question_id and not q.deleted_at:
                for a in q.answers:
                    if str(a.id) == answer_id and not a.deleted_at:
                        a.deleted_at = datetime.utcnow()
                        test.updated_at = datetime.utcnow()
                        await test.save()
                        return a
        return None