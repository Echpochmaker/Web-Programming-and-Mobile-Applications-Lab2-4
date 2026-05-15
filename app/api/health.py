from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.core.cache import cache
from app.core.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def liveness():
    """
    Liveness Probe: проверка, что приложение живо.
    Kubernetes перезапустит под, если этот эндпоинт не отвечает.
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/ready")
async def readiness():
    """
    Readiness Probe: проверка готовности принимать трафик.
    Kubernetes исключит под из балансировки, если вернёт ошибку.
    """
    checks = {}
    healthy = True
    
    # 1. Проверка MongoDB
    try:
        from app.models.user_doc import User
        await User.find_one()
        checks["mongodb"] = "ok"
    except Exception as e:
        checks["mongodb"] = f"error: {str(e)}"
        healthy = False
    
    # 2. Проверка Redis
    try:
        if cache.client and cache.client.ping():
            checks["redis"] = "ok"
        else:
            checks["redis"] = "error: no connection"
            healthy = False
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"
        healthy = False
    
    # 3. Проверка RabbitMQ
    try:
        from app.core.queue import QueueService
        if hasattr(QueueService, '_connection') and QueueService._connection:
            if not QueueService._connection.is_closed:
                checks["rabbitmq"] = "ok"
            else:
                checks["rabbitmq"] = "error: connection closed"
                healthy = False
        else:
            checks["rabbitmq"] = "error: not initialized"
            healthy = False
    except Exception as e:
        checks["rabbitmq"] = f"error: {str(e)}"
        healthy = False
    
    # 4. Проверка MinIO
    try:
        from app.services.storage_service import storage_service
        bucket_exists = storage_service.client.bucket_exists(settings.MINIO_BUCKET)
        if bucket_exists:
            checks["minio"] = "ok"
        else:
            checks["minio"] = "error: bucket not found"
            healthy = False
    except Exception as e:
        checks["minio"] = f"error: {str(e)}"
        healthy = False
    
    status_code = 200 if healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if healthy else "degraded",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@router.get("")
async def health():
    """Общий статус сервиса"""
    return {
        "status": "ok",
        "service": "testing-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }