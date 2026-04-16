from minio import Minio
from minio.error import S3Error
from app.core.config import settings
import uuid
from typing import Tuple, BinaryIO
import logging

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL
        )
        self.bucket = settings.MINIO_BUCKET
        logger.info(f"MinIO connected. Using bucket: {self.bucket}")
    
    async def upload_file(
        self, 
        file_data: BinaryIO, 
        original_name: str, 
        mimetype: str, 
        size: int
    ) -> Tuple[str, str]:
        object_key = f"{uuid.uuid4()}_{original_name}"
        
        try:
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=object_key,
                data=file_data,
                length=size,
                content_type=mimetype,
                part_size=5 * 1024 * 1024
            )
            logger.info(f"File uploaded: {object_key}")
            return object_key, original_name
        except S3Error as e:
            logger.error(f"MinIO upload error: {e}")
            raise
    
    def get_file_stream(self, object_key: str):
        try:
            response = self.client.get_object(self.bucket, object_key)
            return response
        except S3Error as e:
            logger.error(f"MinIO get error: {e}")
            raise
    
    def delete_file(self, object_key: str) -> bool:
        try:
            self.client.remove_object(self.bucket, object_key)
            logger.info(f"File deleted: {object_key}")
            return True
        except S3Error as e:
            logger.error(f"MinIO delete error: {e}")
            return False

storage_service = StorageService()