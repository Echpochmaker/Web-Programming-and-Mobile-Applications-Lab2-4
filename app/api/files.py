from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile
from fastapi.responses import StreamingResponse
from app.core.auth import get_current_user
from app.models.user_doc import User
from app.services.file_service import file_service
from app.schemas.file import FileUploadResponse

router = APIRouter(prefix="/files", tags=["files"])

ALLOWED_MIME_TYPES = ["image/png", "image/jpeg", "image/jpg"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post(
    "/",
    response_model=FileUploadResponse,
    status_code=201,
    summary="Загрузить файл",
    description="Загружает файл в объектное хранилище MinIO. Сохраняет метаданные в базе данных. Требуется авторизация.",
    response_description="Метаданные загруженного файла с ID и URL для скачивания",
    responses={
        201: {"description": "Файл успешно загружен"},
        400: {"description": "Неверный тип файла или превышен размер"},
        401: {"description": "Не авторизован - требуется вход в систему"}
    }
)
async def upload_file(
    file: UploadFile = FastAPIFile(..., description="Файл для загрузки (изображение PNG или JPEG)"),
    current_user: User = Depends(get_current_user)
):
    """
    Загружает файл в систему.
    
    - **file**: файл для загрузки (только PNG, JPEG, JPG)
    - Максимальный размер: 10 MB
    - Файл сохраняется в MinIO, метаданные - в MongoDB
    - Доступ к файлу имеет только владелец
    """
    # Определяем размер файла
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    # Валидация размера
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE // (1024*1024)} MB"
        )
    
    # Валидация MIME-типа
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Недопустимый тип файла. Разрешены: {', '.join(ALLOWED_MIME_TYPES)}"
        )
    
    # Загружаем файл
    uploaded_file = await file_service.create_file(
        user_id=str(current_user.id),
        file_data=file.file,
        original_name=file.filename,
        mimetype=file.content_type,
        size=size
    )
    
    return FileUploadResponse(
        file_id=uploaded_file.file_id,
        original_name=uploaded_file.original_name,
        size=uploaded_file.size,
        mimetype=uploaded_file.mimetype,
        created_at=uploaded_file.created_at,
        url=f"/files/{uploaded_file.file_id}"
    )


@router.get(
    "/{file_id}",
    summary="Скачать файл",
    description="Скачивает файл по его уникальному идентификатору. Доступен только владельцу файла.",
    responses={
        200: {
            "description": "Файл успешно получен",
            "content": {
                "image/png": {},
                "image/jpeg": {},
                "application/octet-stream": {}
            }
        },
        401: {"description": "Не авторизован - требуется вход в систему"},
        403: {"description": "Доступ запрещен - файл принадлежит другому пользователю"},
        404: {"description": "Файл не найден"}
    }
)
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Скачивает файл по ID.
    
    - **file_id**: уникальный идентификатор файла (UUID)
    - Файл возвращается как поток (streaming response)
    - Заголовки Content-Disposition и Content-Type устанавливаются автоматически
    """
    stream, file = await file_service.get_file_stream(file_id, str(current_user.id))
    if not stream:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    return StreamingResponse(
        stream,
        media_type=file.mimetype,
        headers={
            "Content-Disposition": f'attachment; filename="{file.original_name}"',
            "Content-Length": str(file.size)
        }
    )


@router.delete(
    "/{file_id}",
    status_code=204,
    summary="Удалить файл",
    description="Мягкое удаление файла: помечается как удаленный в базе данных и удаляется из MinIO. Доступен только владельцу.",
    responses={
        204: {"description": "Файл успешно удален"},
        401: {"description": "Не авторизован - требуется вход в систему"},
        403: {"description": "Доступ запрещен - файл принадлежит другому пользователю"},
        404: {"description": "Файл не найден"}
    }
)
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Удаляет файл (мягкое удаление).
    
    - **file_id**: уникальный идентификатор файла (UUID)
    - Файл помечается как удаленный в MongoDB
    - Физически удаляется из MinIO
    - Кеш метаданных инвалидируется
    """
    success = await file_service.delete_file(file_id, str(current_user.id))
    if not success:
        raise HTTPException(status_code=404, detail="Файл не найден")
    return None