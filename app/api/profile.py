from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user
from app.models.user_doc import User
from app.models.file_doc import File
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest

router = APIRouter(prefix="/profile", tags=["profile"])

@router.get("/", response_model=ProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    return ProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        phone=current_user.phone,
        avatar_file_id=current_user.avatar_file_id,
        created_at=current_user.created_at
    )

@router.post("/", response_model=ProfileResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    # Обработка avatar_file_id (может быть null)
    if request.avatar_file_id is not None:
        if request.avatar_file_id:
            # Проверяем, что файл существует и принадлежит пользователю
            file = await File.find_one({"file_id": request.avatar_file_id, "deleted_at": None})
            if not file:
                raise HTTPException(status_code=404, detail="Avatar file not found")
            if file.user_id != str(current_user.id):
                raise HTTPException(status_code=403, detail="You don't own this file")
        # Устанавливаем avatar_file_id (может быть null или ID)
        current_user.avatar_file_id = request.avatar_file_id
        await current_user.save()
    
    return ProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        phone=current_user.phone,
        avatar_file_id=current_user.avatar_file_id,
        created_at=current_user.created_at
    )