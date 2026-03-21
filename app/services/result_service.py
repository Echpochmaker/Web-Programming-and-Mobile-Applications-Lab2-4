from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from app.models.test import Test, Question, AnswerOption, TestResult, UserAnswer
from app.models.user import User
from app.schemas.result import AnswerSubmission
from datetime import datetime
from typing import List, Optional

class ResultService:
    
    @staticmethod
    def get_available_tests(db: Session, user_id: int, page: int = 1, limit: int = 10):
        """Получить тесты, доступные для прохождения (чужие тесты)"""
        query = db.query(Test).filter(
            Test.owner_id != user_id,  # не свои тесты
            Test.deleted_at.is_(None)
        )
        total = query.count()
        tests = query.offset((page - 1) * limit).limit(limit).all()
        
        # Дополняем информацией о количестве вопросов и попытках
        result = []
        for test in tests:
            questions_count = len(test.questions)
            # Сколько раз пользователь уже проходил этот тест
            attempts = db.query(TestResult).filter(
                TestResult.test_id == test.id,
                TestResult.user_id == user_id
            ).count()
            
            result.append({
                "id": test.id,
                "title": test.title,
                "description": test.description,
                "author_email": test.owner.email if test.owner else "Unknown",
                "questions_count": questions_count,
                "attempts_count": None,
                "user_attempts": attempts
            })
        
        return result, total
    
    @staticmethod
    def start_test(db: Session, test_id: int, user_id: int) -> TestResult:
        """Начать прохождение теста"""
        test = db.query(Test).filter(Test.id == test_id, Test.deleted_at.is_(None)).first()
        if not test:
            return None
        
        # Создаем запись о результате
        total_questions = len(test.questions)
        result = TestResult(
            user_id=user_id,
            test_id=test_id,
            total_questions=total_questions,
            status="in_progress"
        )
        db.add(result)
        db.commit()
        db.refresh(result)
        return result
    
    @staticmethod
    def get_test_questions(db: Session, test_id: int) -> List[Question]:
        """Получить все вопросы теста с ответами"""
        return db.query(Question).filter(
            Question.test_id == test_id,
            Question.deleted_at.is_(None)
        ).options(joinedload(Question.answer_options)).all()
    
    @staticmethod
    def submit_answer(db: Session, answer_data: AnswerSubmission) -> Optional[UserAnswer]:
        """Сохранить ответ пользователя на вопрос"""
        # Проверяем, что результат существует и ещё не завершён
        result = db.query(TestResult).filter(
            TestResult.id == answer_data.result_id,
            TestResult.status == "in_progress"
        ).first()
        if not result:
            return None
        
        # Получаем вопрос и правильный ответ
        question = db.query(Question).filter(Question.id == answer_data.question_id).first()
        if not question:
            return None
        
        # Проверяем, правильный ли ответ
        correct_answer = db.query(AnswerOption).filter(
            AnswerOption.question_id == answer_data.question_id,
            AnswerOption.is_correct == True,
            AnswerOption.deleted_at.is_(None)
        ).first()
        
        is_correct = False
        if correct_answer and correct_answer.id == answer_data.selected_answer_id:
            is_correct = True
        
        # Сохраняем ответ
        answer = UserAnswer(
            result_id=answer_data.result_id,
            question_id=answer_data.question_id,
            selected_answer_id=answer_data.selected_answer_id,
            is_correct=is_correct
        )
        db.add(answer)
        db.commit()
        db.refresh(answer)
        return answer
    
    @staticmethod
    def finish_test(db: Session, result_id: int) -> Optional[TestResult]:
        """Завершить тест и подсчитать результат"""
        result = db.query(TestResult).filter(
            TestResult.id == result_id,
            TestResult.status == "in_progress"
        ).first()
        if not result:
            return None
        
        # Получаем все ответы пользователя
        answers = db.query(UserAnswer).filter(UserAnswer.result_id == result_id).all()
        
        # Подсчитываем правильные ответы
        correct_count = sum(1 for a in answers if a.is_correct)
        score = (correct_count / result.total_questions) * 100 if result.total_questions > 0 else 0
        
        # Обновляем результат
        result.correct_answers = correct_count
        result.score = score
        result.completed_at = datetime.utcnow()
        result.status = "completed"
        
        db.commit()
        db.refresh(result)
        return result
    
    @staticmethod
    def get_result(db: Session, result_id: int, user_id: int) -> Optional[TestResult]:
        """Получить результат по ID с ответами"""
        return db.query(TestResult).filter(
            TestResult.id == result_id,
            TestResult.user_id == user_id
        ).options(
            joinedload(TestResult.answers).joinedload(UserAnswer.question),
            joinedload(TestResult.answers).joinedload(UserAnswer.selected_answer)
        ).first()
    
    @staticmethod
    def get_user_results(db: Session, user_id: int, page: int = 1, limit: int = 10):
        """Получить все результаты пользователя"""
        query = db.query(TestResult).filter(
            TestResult.user_id == user_id,
            TestResult.status == "completed"
        ).order_by(TestResult.completed_at.desc())
        
        total = query.count()
        results = query.offset((page - 1) * limit).limit(limit).all()
        return results, total