from sqlalchemy.orm import Session
from app.models.test import Test
from app.schemas.test import TestCreate, TestUpdate
from datetime import datetime

class TestService:
    @staticmethod
    def get_all(db: Session, page: int = 1, limit: int = 10):
        query = db.query(Test).filter(Test.deleted_at.is_(None))
        total = query.count()
        items = query.offset((page - 1) * limit).limit(limit).all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, test_id: int):
        return db.query(Test).filter(Test.id == test_id, Test.deleted_at.is_(None)).first()

    @staticmethod
    def create(db: Session, test_data: TestCreate):
        test = Test(**test_data.model_dump())
        db.add(test)
        db.commit()
        db.refresh(test)
        return test

    @staticmethod
    def update(db: Session, test_id: int, test_data: TestUpdate):
        test = db.query(Test).filter(Test.id == test_id, Test.deleted_at.is_(None)).first()
        if not test:
            return None
        # Обновляем только переданные поля
        for field, value in test_data.model_dump(exclude_unset=True).items():
            setattr(test, field, value)
        db.commit()
        db.refresh(test)
        return test

    @staticmethod
    def delete(db: Session, test_id: int):
        test = db.query(Test).filter(Test.id == test_id, Test.deleted_at.is_(None)).first()
        if not test:
            return None
        test.deleted_at = datetime.utcnow()
        db.commit()
        return test