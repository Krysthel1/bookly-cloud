from uuid import UUID
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.integrations.supabase.storage import SupabaseStorageService
from app.models.user import Profile
from app.schemas.common import MessageResponse
from app.schemas.user import (
    AddressCreate,
    AddressOut,
    AddressUpdate,
    NotificationOut,
    ProfileOut,
    ProfileUpdate,
)
from app.services import user_service

router = APIRouter(tags=["Autenticación y Usuarios"])


@router.get("/auth/me", response_model=ProfileOut)
def auth_me(current_user: Profile = Depends(get_current_user)):
    return user_service.serialize_profile(current_user)


@router.get("/users/me", response_model=ProfileOut)
def get_me(current_user: Profile = Depends(get_current_user)):
    return user_service.serialize_profile(current_user)


@router.patch("/users/me", response_model=ProfileOut)
def patch_me(
    payload: ProfileUpdate,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return user_service.update_profile(db, current_user, payload)


@router.post("/users/me/avatar", response_model=ProfileOut)
async def upload_my_avatar(
    file: UploadFile = File(...),
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    storage = SupabaseStorageService()
    uploaded = await storage.upload_image(
        file, bucket_type="avatars", folder=str(current_user.id), max_width=512
    )
    return user_service.update_profile(
        db, current_user, ProfileUpdate(avatar_url=uploaded["url"])
    )


@router.get("/users/me/addresses", response_model=list[AddressOut])
def get_my_addresses(
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return user_service.list_addresses(db, current_user)


@router.post("/users/me/addresses", response_model=AddressOut, status_code=status.HTTP_201_CREATED)
def add_my_address(
    payload: AddressCreate,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return user_service.create_address(db, current_user, payload)


@router.patch("/users/me/addresses/{address_id}", response_model=AddressOut)
def edit_my_address(
    address_id: UUID,
    payload: AddressUpdate,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return user_service.update_address(db, current_user, address_id, payload)


@router.delete("/users/me/addresses/{address_id}", response_model=MessageResponse)
def remove_my_address(
    address_id: UUID,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_service.delete_address(db, current_user, address_id)
    return MessageResponse(message="Dirección eliminada correctamente.")


@router.get("/users/me/notifications", response_model=list[NotificationOut])
def get_my_notifications(
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return user_service.list_notifications(db, current_user)


@router.patch("/users/me/notifications/{notification_id}/read", response_model=NotificationOut)
def read_notification(
    notification_id: UUID,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return user_service.mark_notification_read(db, current_user, notification_id)
