from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session, selectinload

from app.exceptions.handlers import NotFoundException
from app.models.commerce import Address, Order
from app.models.operations import Notification
from app.models.user import Profile, UserRole
from app.repositories.pagination import paginate_query
from app.schemas.user import (
    AddressCreate,
    AddressUpdate,
    AdminUserDetailOut,
    AdminUserOut,
    ProfileOut,
    ProfileUpdate,
)


def serialize_profile(profile: Profile) -> ProfileOut:
    return ProfileOut(
        id=profile.id,
        email=profile.email,
        full_name=profile.full_name,
        phone=profile.phone,
        avatar_url=profile.avatar_url,
        is_active=profile.is_active,
        roles=profile.role_names,
        created_at=profile.created_at,
    )


def update_profile(db: Session, user: Profile, payload: ProfileUpdate) -> ProfileOut:
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return serialize_profile(user)


# --- Direcciones ---
def list_addresses(db: Session, user: Profile) -> list[Address]:
    return list(
        db.scalars(
            select(Address)
            .where(Address.user_id == user.id, Address.deleted_at.is_(None))
            .order_by(Address.is_default.desc(), Address.created_at.desc())
        ).all()
    )


def create_address(db: Session, user: Profile, payload: AddressCreate) -> Address:
    if payload.is_default:
        db.execute(
            update(Address)
            .where(Address.user_id == user.id, Address.deleted_at.is_(None))
            .values(is_default=False)
        )
    address = Address(user_id=user.id, **payload.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def update_address(db: Session, user: Profile, address_id: UUID, payload: AddressUpdate) -> Address:
    address = db.scalar(
        select(Address).where(
            Address.id == address_id, Address.user_id == user.id, Address.deleted_at.is_(None)
        )
    )
    if not address:
        raise NotFoundException("Dirección no encontrada.")

    if payload.is_default:
        db.execute(
            update(Address)
            .where(Address.user_id == user.id, Address.deleted_at.is_(None), Address.id != address_id)
            .values(is_default=False)
        )
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(address, k, v)
    db.commit()
    db.refresh(address)
    return address


def delete_address(db: Session, user: Profile, address_id: UUID) -> None:
    address = db.scalar(
        select(Address).where(
            Address.id == address_id, Address.user_id == user.id, Address.deleted_at.is_(None)
        )
    )
    if not address:
        raise NotFoundException("Dirección no encontrada.")
    address.deleted_at = datetime.now(timezone.utc)
    db.commit()


# --- Notificaciones ---
def list_notifications(db: Session, user: Profile) -> list[Notification]:
    return list(
        db.scalars(
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc())
            .limit(50)
        ).all()
    )


def mark_notification_read(db: Session, user: Profile, notification_id: UUID) -> Notification:
    notif = db.scalar(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id)
    )
    if not notif:
        raise NotFoundException("Notificación no encontrada.")
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


# --- Admin Clientes ---
def admin_list_users(db: Session, *, search: str | None = None, is_active: bool | None = None, page: int = 1, page_size: int = 20):
    query = (
        select(Profile)
        .options(selectinload(Profile.user_roles).selectinload(UserRole.role))
        .where(Profile.deleted_at.is_(None))
        .order_by(Profile.created_at.desc())
    )
    if search:
        term = f"%{search.strip()}%"
        query = query.where(or_(Profile.full_name.ilike(term), Profile.email.ilike(term)))
    if is_active is not None:
        query = query.where(Profile.is_active.is_(is_active))

    users, meta = paginate_query(db, query, page=page, page_size=page_size)
    out = []
    for u in users:
        stats = db.execute(
            select(func.count(Order.id), func.coalesce(func.sum(Order.total), 0)).where(
                Order.user_id == u.id, Order.status != "cancelado"
            )
        ).one()
        out.append(
            AdminUserOut(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                phone=u.phone,
                avatar_url=u.avatar_url,
                is_active=u.is_active,
                roles=u.role_names,
                created_at=u.created_at,
                orders_count=int(stats[0] or 0),
                total_spent=float(stats[1] or 0),
            )
        )
    return out, meta


def admin_get_user_detail(db: Session, user_id: UUID) -> AdminUserDetailOut:
    user = db.scalar(
        select(Profile)
        .options(selectinload(Profile.user_roles).selectinload(UserRole.role))
        .where(Profile.id == user_id, Profile.deleted_at.is_(None))
    )
    if not user:
        raise NotFoundException("Usuario no encontrado.")
    stats = db.execute(
        select(func.count(Order.id), func.coalesce(func.sum(Order.total), 0)).where(
            Order.user_id == user.id, Order.status != "cancelado"
        )
    ).one()
    return AdminUserDetailOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        roles=user.role_names,
        created_at=user.created_at,
        updated_at=user.updated_at,
        orders_count=int(stats[0] or 0),
        total_spent=float(stats[1] or 0),
    )
