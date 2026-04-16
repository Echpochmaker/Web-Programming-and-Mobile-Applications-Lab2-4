from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile
from fastapi.responses import StreamingResponse
from app.core.auth import get_current_user
from app.models.user_doc import User
from app.services.file_service import file_service
from app.schemas.file import FileUploadResponse

router = APIRouter(prefix="/files", tags=["files"])

ALLOWED_MIME_TYPES = ["image/png", "image/jpeg", "image/jpg"]
MAX_FILE_SIZE = 10 * 1024 * 1024

@router.post("/", response_model=FileUploadResponse, status_code=201)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    current_user: User = Depends(get_current_user)
):
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {MAX_FILE_SIZE} bytes")
    
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {ALLOWED_MIME_TYPES}")
    
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

@router.get("/{file_id}")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    stream, file = await file_service.get_file_stream(file_id, str(current_user.id))
    if not stream:
        raise HTTPException(status_code=404, detail="File not found")
    
    return StreamingResponse(
        stream,
        media_type=file.mimetype,
        headers={
            "Content-Disposition": f'attachment; filename="{file.original_name}"',
            "Content-Length": str(file.size)
        }
    )

@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    success = await file_service.delete_file(file_id, str(current_user.id))
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return None