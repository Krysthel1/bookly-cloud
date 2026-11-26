from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str | None = None


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: EmailStr
    full_name: str
    phone: str | None = None
    avatar_url: str | None = None
    is_active: bool
    roles: list[str] = Field(default_factory=list)
    created_at: datetime


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    avatar_url: str | None = Field(default=None, max_length=500)


class AdminUserOut(ProfileOut):
    orders_count: int = 0
    total_spent: float = 0.0


class AdminUserDetailOut(AdminUserOut):
    updated_at: datetime


class AddressCreate(BaseModel):
    label: str = Field(default="Casa", min_length=2, max_length=60)
    recipient_name: str = Field(min_length=2, max_length=150)
    phone: str = Field(min_length=6, max_length=30)
    street_address: str = Field(min_length=4, max_length=255)
    district: str = Field(min_length=2, max_length=100)
    city: str = Field(min_length=2, max_length=100)
    region: str = Field(min_length=2, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    reference: str | None = Field(default=None, max_length=255)
    is_default: bool = False


class AddressUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=2, max_length=60)
    recipient_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = Field(default=None, min_length=6, max_length=30)
    street_address: str | None = Field(default=None, min_length=4, max_length=255)
    district: str | None = Field(default=None, min_length=2, max_length=100)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    region: str | None = Field(default=None, min_length=2, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    reference: str | None = Field(default=None, max_length=255)
    is_default: bool | None = None


class AddressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    label: str
    recipient_name: str
    phone: str
    street_address: str
    district: str
    city: str
    region: str
    postal_code: str | None = None
    reference: str | None = None
    is_default: bool
    created_at: datetime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    message: str
    type: str
    is_read: bool
    link: str | None = None
    created_at: datetime
