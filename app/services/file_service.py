from app.models.file_doc import File
from app.services.storage_service import storage_service
from app.core.cache import cache
from datetime import datetime
from typing import Optional, BinaryIO
import logging

logger = logging.getLogger(__name__)

class FileService:
    
    @staticmethod
    async def create_file(
        user_id: str,
        file_data: BinaryIO,
        original_name: str,
        mimetype: str,
        size: int
    ) -> File:
        object_key, saved_name = await storage_service.upload_file(
            file_data, original_name, mimetype, size
        )
        
        file = File(
            user_id=user_id,
            original_name=original_name,
            object_key=object_key,
            size=size,
            mimetype=mimetype,
            bucket=storage_service.bucket
        )
        await file.insert()
        
        cache.delete(f"testing:files:user:{user_id}:list")
        
        return file
    
    @staticmethod
    async def get_file(file_id: str, user_id: str) -> Optional[File]:
        cache_key = f"testing:files:{file_id}:meta"
        cached = cache.get(cache_key)
        if cached:
            file = File(**cached)
        else:
            file = await File.find_one({"file_id": file_id, "deleted_at": None})
            if file:
                cache.set(cache_key, file.dict(), ttl=300)
        
        if not file or file.user_id != user_id:
            return None
        
        return file
    
    @staticmethod
    async def delete_file(file_id: str, user_id: str) -> bool:
        file = await File.find_one({"file_id": file_id, "deleted_at": None})
        if not file or file.user_id != user_id:
            return False
        
        storage_service.delete_file(file.object_key)
        
        file.soft_delete()
        await file.save()
        
        cache.delete(f"testing:files:{file_id}:meta")
        cache.delete(f"testing:files:user:{user_id}:list")
        
        return True
    
    @staticmethod
    async def get_file_stream(file_id: str, user_id: str):
        file = await FileService.get_file(file_id, user_id)
        if not file:
            return None, None
        
        stream = storage_service.get_file_stream(file.object_key)
        return stream, file

file_service = FileService()