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
    async def get_questions(test_id: str, skip: int = 0, limit: int = 100) -> List[dict]:
        test = await TestService.get_by_id(test_id)
        if not test:
            return []
        
        questions = []
        for q in test.questions:
            if not q.deleted_at:
                q_dict = q.model_dump()
                q_dict["id"] = str(q.id)
                q_dict["test_id"] = test_id
                q_dict["answers"] = []
                for a in q.answers:
                    if not a.deleted_at:
                        a_dict = a.model_dump()
                        a_dict["id"] = str(a.id)
                        q_dict["answers"].append(a_dict)
                questions.append(q_dict)
        
        return questions[skip:skip+limit]

    @staticmethod
    async def add_question(test_id: str, question_data: dict) -> Optional[dict]:
        test = await TestService.get_by_id(test_id)
        if not test:
            return None
        
        # Создаём вопрос
        question = Question(
            text=question_data.get('text'),
            answers=[]
        )
        
        # Добавляем ответы если есть
        if 'answers' in question_data and question_data['answers']:
            for answer_data in question_data['answers']:
                answer = AnswerOption(
                    text=answer_data.get('text'),
                    is_correct=answer_data.get('is_correct', False)
                )
                question.answers.append(answer)
        
        test.questions.append(question)
        test.updated_at = datetime.utcnow()
        await test.save()
        
        # Возвращаем данные
        result = question.model_dump()
        result["id"] = str(question.id)
        result["test_id"] = test_id
        result["answers"] = []
        for a in question.answers:
            a_dict = a.model_dump()
            a_dict["id"] = str(a.id)
            result["answers"].append(a_dict)
        
        return result

    @staticmethod
    async def delete_question(test_id: str, question_id: str) -> Optional[bool]:
        test = await TestService.get_by_id(test_id)
        if not test:
            return None
        
        for q in test.questions:
            if str(q.id) == question_id and not q.deleted_at:
                q.deleted_at = datetime.utcnow()
                test.updated_at = datetime.utcnow()
                await test.save()
                return True
        return None

    @staticmethod
    async def create_answer(question_id: str, answer_data: dict) -> Optional[dict]:
        try:
            test = await Test.find_one({"questions.id": ObjectId(question_id)})
        except:
            return None
            
        if not test:
            return None
        
        for q in test.questions:
            if str(q.id) == question_id and not q.deleted_at:
                answer = AnswerOption(
                    text=answer_data.get('text'),
                    is_correct=answer_data.get('is_correct', False)
                )
                q.answers.append(answer)
                test.updated_at = datetime.utcnow()
                await test.save()
                
                result = answer.model_dump()
                result["id"] = str(answer.id)
                return result
        return None

    @staticmethod
    async def get_test_by_question_id(question_id: str) -> Optional[Test]:
        try:
            test = await Test.find_one({"questions.id": ObjectId(question_id)})
            return test
        except:
            return None

    @staticmethod
    async def get_answers(question_id: str) -> List[dict]:
        try:
            test = await Test.find_one({"questions.id": ObjectId(question_id)})
        except:
            return []
            
        if not test:
            return []
        
        for q in test.questions:
            if str(q.id) == question_id and not q.deleted_at:
                return [
                    {**a.model_dump(), "id": str(a.id)}
                    for a in q.answers if not a.deleted_at
                ]
        return []

    @staticmethod
    async def update_answer(question_id: str, answer_id: str, answer_data: dict) -> Optional[dict]:
        try:
            test = await Test.find_one({"questions.id": ObjectId(question_id)})
        except:
            return None
            
        if not test:
            return None
        
        for q in test.questions:
            if str(q.id) == question_id and not q.deleted_at:
                for a in q.answers:
                    if str(a.id) == answer_id and not a.deleted_at:
                        if 'text' in answer_data:
                            a.text = answer_data['text']
                        if 'is_correct' in answer_data:
                            a.is_correct = answer_data['is_correct']
                        a.updated_at = datetime.utcnow()
                        test.updated_at = datetime.utcnow()
                        await test.save()
                        
                        result = a.model_dump()
                        result["id"] = str(a.id)
                        return result
        return None

    @staticmethod
    async def delete_answer(question_id: str, answer_id: str) -> Optional[bool]:
        try:
            test = await Test.find_one({"questions.id": ObjectId(question_id)})
        except:
            return None
            
        if not test:
            return None
        
        for q in test.questions:
            if str(q.id) == question_id and not q.deleted_at:
                for a in q.answers:
                    if str(a.id) == answer_id and not a.deleted_at:
                        a.deleted_at = datetime.utcnow()
                        test.updated_at = datetime.utcnow()
                        await test.save()
                        return True
        return False