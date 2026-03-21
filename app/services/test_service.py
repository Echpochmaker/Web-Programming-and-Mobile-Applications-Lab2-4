from sqlalchemy.orm import Session, selectinload
from app.models.test import Test, Question, AnswerOption
from app.schemas.test import TestCreate, TestUpdate, QuestionCreate, AnswerOptionCreate
from datetime import datetime
from typing import List, Optional, Dict, Any

class TestService:
    # ----- Тесты -----
    @staticmethod
    def get_all(db: Session, page: int = 1, limit: int = 10):
        query = db.query(Test).filter(Test.deleted_at.is_(None))
        total = query.count()
        items = query.offset((page - 1) * limit).limit(limit).all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, test_id: int) -> Optional[Test]:
        """Получить тест по ID с вопросами и ответами (только неудаленные)"""
        test = db.query(Test)\
            .filter(Test.id == test_id, Test.deleted_at.is_(None))\
            .options(
                selectinload(Test.questions).selectinload(Question.answer_options)
            )\
            .first()
        
        if test:
            # Фильтруем вопросы - оставляем только те, у которых deleted_at is None
            active_questions = []
            for question in test.questions:
                if question.deleted_at is None:
                    # Фильтруем ответы для каждого вопроса
                    active_answers = []
                    for answer in question.answer_options:
                        if answer.deleted_at is None:
                            active_answers.append(answer)
                    # Заменяем answer_options на отфильтрованные ответы
                    question.answer_options = active_answers
                    active_questions.append(question)
            
            # Заменяем вопросы на отфильтрованные
            test.questions = active_questions
        
        return test

    @staticmethod
    def create(db: Session, test_data: Dict[str, Any]) -> Test:
        """Создаёт тест, опционально с вопросами и ответами."""
        # Извлекаем owner_id из словаря
        owner_id = test_data.pop('owner_id', None)
        
        test = Test(
            title=test_data.get('title'),
            description=test_data.get('description'),
            owner_id=owner_id
        )
        db.add(test)
        db.flush()  # получаем id теста

        # Создаём вопросы, если они есть
        questions_data = test_data.get('questions', [])
        for q_data in questions_data:
            # Если q_data это словарь, преобразуем в объект
            if isinstance(q_data, dict):
                question = Question(text=q_data.get('text'), test_id=test.id)
                answers_data = q_data.get('answers', [])
            else:
                question = Question(text=q_data.text, test_id=test.id)
                answers_data = q_data.answers if hasattr(q_data, 'answers') else []
            
            db.add(question)
            db.flush()

            for a_data in answers_data:
                if isinstance(a_data, dict):
                    answer = AnswerOption(
                        text=a_data.get('text'),
                        is_correct=a_data.get('is_correct', False),
                        question_id=question.id
                    )
                else:
                    answer = AnswerOption(
                        text=a_data.text,
                        is_correct=a_data.is_correct if hasattr(a_data, 'is_correct') else False,
                        question_id=question.id
                    )
                db.add(answer)

        db.commit()
        db.refresh(test)
        return test

    @staticmethod
    def update(db: Session, test_id: int, test_data: TestUpdate) -> Optional[Test]:
        test = db.query(Test).filter(Test.id == test_id, Test.deleted_at.is_(None)).first()
        if not test:
            return None
        for field, value in test_data.model_dump(exclude_unset=True).items():
            setattr(test, field, value)
        db.commit()
        db.refresh(test)
        return test

    @staticmethod
    def delete(db: Session, test_id: int) -> Optional[Test]:
        test = db.query(Test).filter(Test.id == test_id, Test.deleted_at.is_(None)).first()
        if not test:
            return None
        test.deleted_at = datetime.utcnow()
        db.commit()
        return test

    # ----- Вопросы -----
    @staticmethod
    def get_questions(db: Session, test_id: int, skip: int = 0, limit: int = 100) -> List[Question]:
        return db.query(Question)\
            .filter(Question.test_id == test_id, Question.deleted_at.is_(None))\
            .options(selectinload(Question.answer_options))\
            .offset(skip).limit(limit).all()

    @staticmethod
    def get_question_by_id(db: Session, question_id: int) -> Optional[Question]:
        return db.query(Question)\
            .filter(Question.id == question_id, Question.deleted_at.is_(None))\
            .options(selectinload(Question.answer_options))\
            .first()

    @staticmethod
    def create_question(db: Session, test_id: int, question_data: QuestionCreate) -> Question:
        question = Question(text=question_data.text, test_id=test_id)
        db.add(question)
        db.flush()

        for a_data in question_data.answers:
            answer = AnswerOption(
                text=a_data.text,
                is_correct=a_data.is_correct,
                question_id=question.id
            )
            db.add(answer)

        db.commit()
        db.refresh(question)
        return question

    @staticmethod
    def update_question(db: Session, question_id: int, question_data: QuestionCreate) -> Optional[Question]:
        question = db.query(Question).filter(Question.id == question_id, Question.deleted_at.is_(None)).first()
        if not question:
            return None
        question.text = question_data.text
        db.commit()
        db.refresh(question)
        return question

    @staticmethod
    def delete_question(db: Session, question_id: int) -> Optional[Question]:
        question = db.query(Question).filter(Question.id == question_id, Question.deleted_at.is_(None)).first()
        if not question:
            return None
        question.deleted_at = datetime.utcnow()
        db.commit()
        return question

    # ----- Ответы -----
    @staticmethod
    def get_answers(db: Session, question_id: int) -> List[AnswerOption]:
        return db.query(AnswerOption).filter(
            AnswerOption.question_id == question_id,
            AnswerOption.deleted_at.is_(None)
        ).all()

    @staticmethod
    def create_answer(db: Session, question_id: int, answer_data: AnswerOptionCreate) -> AnswerOption:
        answer = AnswerOption(
            text=answer_data.text,
            is_correct=answer_data.is_correct,
            question_id=question_id
        )
        db.add(answer)
        db.commit()
        db.refresh(answer)
        return answer

    @staticmethod
    def update_answer(db: Session, answer_id: int, answer_data: AnswerOptionCreate) -> Optional[AnswerOption]:
        answer = db.query(AnswerOption).filter(AnswerOption.id == answer_id, AnswerOption.deleted_at.is_(None)).first()
        if not answer:
            return None
        answer.text = answer_data.text
        answer.is_correct = answer_data.is_correct
        db.commit()
        db.refresh(answer)
        return answer

    @staticmethod
    def delete_answer(db: Session, answer_id: int) -> Optional[AnswerOption]:
        answer = db.query(AnswerOption).filter(AnswerOption.id == answer_id, AnswerOption.deleted_at.is_(None)).first()
        if not answer:
            return None
        answer.deleted_at = datetime.utcnow()
        db.commit()
        return answer