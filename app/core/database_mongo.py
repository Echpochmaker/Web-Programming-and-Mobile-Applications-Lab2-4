from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.models.user_doc import User
from app.models.token_doc import Token
from app.models.test_doc import Test
from app.models.result_doc import TestResult
from app.models.file_doc import File

async def init_mongodb():
    """Инициализация подключения к MongoDB"""
    try:
        client = AsyncIOMotorClient(settings.MONGO_URI)
        database = client.get_database()
        
        await init_beanie(
            database=database,
            document_models=[
                User,
                Token,
                Test,
                TestResult,
                File,
            ]
        )
        print("MongoDB connected and Beanie initialized")
        return client
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        raise