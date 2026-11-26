from uuid import UUID
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.session import get_db
from app.exceptions.handlers import ForbiddenException, UnauthorizedException
from app.models.user import Profile, Role, UserRole
from app.security.jwt import verify_supabase_token

bearer_scheme = HTTPBearer(auto_error=False)


def _provision_customer_profile(db: Session, payload: dict) -> Profile:
    """
    Crea el perfil local vinculado al usuario autenticado en Supabase Auth si aún no existe,
    asignando únicamente el rol 'customer' por defecto.
    """
    user_id = UUID(str(payload["sub"]))
    email = (payload.get("email") or f"{user_id}@bookly.local").lower()
    user_meta = payload.get("user_metadata") or {}
    full_name = user_meta.get("full_name") or user_meta.get("name") or email.split("@")[0]

    profile = db.scalar(
        select(Profile)
        .options(selectinload(Profile.user_roles).selectinload(UserRole.role))
        .where(Profile.id == user_id)
    )
    if profile:
        return profile

    customer_role = db.scalar(select(Role).where(Role.name == "customer"))
    if not customer_role:
        customer_role = Role(name="customer", description="Cliente de BOOKLY")
        db.add(customer_role)
        db.flush()

    profile = Profile(
        id=user_id,
        email=email,
        full_name=full_name,
        is_active=True,
    )
    db.add(profile)
    db.flush()

    db.add(UserRole(user_id=profile.id, role_id=customer_role.id))
    db.commit()

    return db.scalar(
        select(Profile)
        .options(selectinload(Profile.user_roles).selectinload(UserRole.role))
        .where(Profile.id == user_id)
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Profile:
    if not credentials or not credentials.credentials:
        raise UnauthorizedException("Se requiere iniciar sesión para continuar.")

    payload = verify_supabase_token(credentials.credentials)
    sub = payload.get("sub")
    if not sub:
        raise UnauthorizedException("Token sin identificador de usuario (sub).")

    try:
        user_id = UUID(str(sub))
    except ValueError as exc:
        raise UnauthorizedException("Identificador de usuario inválido en el token.") from exc

    profile = db.scalar(
        select(Profile)
        .options(selectinload(Profile.user_roles).selectinload(UserRole.role))
        .where(Profile.id == user_id, Profile.deleted_at.is_(None))
    )
    if not profile:
        profile = _provision_customer_profile(db, payload)

    if not profile.is_active:
        raise ForbiddenException("Tu cuenta está desactivada. Contacta con soporte.")

    return profile


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Profile | None:
    if not credentials or not credentials.credentials:
        return None
    try:
        return get_current_user(credentials, db)
    except UnauthorizedException:
        return None


def require_admin(current_user: Profile = Depends(get_current_user)) -> Profile:
    if "admin" not in current_user.role_names:
        raise ForbiddenException("Se requieren permisos de administrador para esta operación.")
    return current_user
