from beanie import Document
from datetime import datetime
from typing import Optional, List
from pydantic import Field

class UserAnswer(Document):
    question_id: str
    question_text: str
    selected_answer_id: Optional[str] = None
    selected_answer_text: Optional[str] = None
    is_correct: Optional[bool] = None
    correct_answer_id: Optional[str] = None
    correct_answer_text: Optional[str] = None
    
    class Settings:
        name = "user_answers"
        use_state_management = True

class TestResult(Document):
    user_id: str
    test_id: str
    test_title: str
    score: Optional[float] = None
    correct_answers: int = 0
    total_questions: int
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: str = "in_progress"
    answers: List[UserAnswer] = []
    
    class Settings:
        name = "test_results"
        indexes = [
            "user_id",
            "test_id",
            "status"
        ]