from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# Базовая схема для теста
class TestBase(BaseModel):
    title: str
    description: Optional[str] = None

# Схема для создания
class TestCreate(TestBase):
    pass

# Схема для обновления (все поля опциональны – для PATCH и PUT)
class TestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

# Схема для ответа (то, что возвращаем клиенту)
class TestResponse(TestBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # позволяет работать с ORM-объектами

# Параметры пагинации
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Номер страницы")
    limit: int = Field(10, ge=1, le=100, description="Количество элементов на странице")

# Пагинированный ответ
class PaginatedResponse(BaseModel):
    data: List[TestResponse]
    meta: dict