from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user
from app.models.user_doc import User
from app.models.file_doc import File
from datetime import datetime
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest
from bson import ObjectId

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get(
    "/",
    response_model=ProfileResponse,
    summary="Получить профиль пользователя",
    description="Возвращает данные профиля текущего авторизованного пользователя.",
    response_description="Данные профиля пользователя",
    responses={
        200: {"description": "Профиль успешно получен"},
        401: {"description": "Не авторизован - требуется вход в систему"}
    }
)
async def get_profile(current_user: User = Depends(get_current_user)):
    """
    Возвращает профиль текущего пользователя.
    
    Поля ответа:
    - **id**: уникальный идентификатор пользователя
    - **email**: email пользователя
    - **phone**: телефон пользователя (опционально)
    - **avatar_file_id**: ID файла аватара (опционально)
    - **created_at**: дата регистрации
    """
    return ProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        phone=current_user.phone,
        avatar_file_id=current_user.avatar_file_id,
        created_at=current_user.created_at
    )


@router.post(
    "/",
    response_model=ProfileResponse,
    summary="Обновить профиль пользователя",
    description="Обновляет данные профиля текущего авторизованного пользователя. Позволяет установить или удалить аватар.",
    response_description="Обновленные данные профиля",
    responses={
        200: {"description": "Профиль успешно обновлен"},
        400: {"description": "Неверные данные (файл не существует или поврежден)"},
        401: {"description": "Не авторизован - требуется вход в систему"},
        403: {"description": "Доступ запрещен - файл принадлежит другому пользователю"},
        404: {"description": "Файл аватара не найден"}
    }
)
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Обновляет профиль текущего пользователя.
    
    - **avatar_file_id**: ID файла для аватара (опционально). 
      - Если указан, файл должен быть предварительно загружен через POST /files/
      - Если null или пустая строка, аватар удаляется
      - Проверяется владение файлом (файл должен принадлежать пользователю)
    """
    print(f"Updating profile for user {current_user.id}")
    print(f"Request data: {request.model_dump()}")
    
    # Проверяем avatar_file_id
    if hasattr(request, 'avatar_file_id'):
        print(f"Setting avatar_file_id to: {request.avatar_file_id}")
        
        if request.avatar_file_id is not None and request.avatar_file_id != "":
            # Проверяем, что файл существует и принадлежит пользователю
            try:
                file = await File.find_one({
                    "file_id": request.avatar_file_id, 
                    "deleted_at": None
                })
                if not file:
                    raise HTTPException(status_code=404, detail="Файл аватара не найден")
                if file.user_id != str(current_user.id):
                    raise HTTPException(status_code=403, detail="Файл принадлежит другому пользователю")
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Ошибка проверки файла: {str(e)}")
        
        # Обновляем поле (включая None/null)
        current_user.avatar_file_id = request.avatar_file_id if request.avatar_file_id else None
    else:
        print("No avatar_file_id in request")
    
    current_user.updated_at = datetime.utcnow()
    await current_user.save()
    
    print(f"Profile updated. New avatar_file_id: {current_user.avatar_file_id}")
    
    return ProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        phone=current_user.phone,
        avatar_file_id=current_user.avatar_file_id,
        created_at=current_user.created_at
    )