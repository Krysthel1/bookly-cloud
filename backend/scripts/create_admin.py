"""
Script seguro para asignar el rol de administrador desde el servidor.
Uso:
    python scripts/create_admin.py --email admin@bookly.pe --name "Administrador BOOKLY"
"""
import argparse
import os
import sys
from uuid import UUID, uuid4

from sqlalchemy import select

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config.settings import get_settings
from app.database.session import SessionLocal
from app.models.operations import AuditLog
from app.models.user import Profile, Role, UserRole


def resolve_supabase_user_id(email: str) -> UUID | None:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_secret_key:
        return None
    try:
        import httpx

        base_url = settings.supabase_url.rstrip("/")
        secret = settings.supabase_secret_key.strip()
        resp = httpx.get(
            f"{base_url}/auth/v1/admin/users",
            headers={"apikey": secret, "Authorization": f"Bearer {secret}"},
            timeout=15.0,
        )
        resp.raise_for_status()
        users = resp.json().get("users", [])
        for user in users:
            if (user.get("email") or "").lower() == email.lower():
                return UUID(str(user["id"]))
    except Exception as exc:
        print(f"[WARN] No se pudo consultar Supabase Auth Admin API: {exc}")
    return None


def assign_admin_role(email: str, full_name: str, user_id: str | None = None) -> None:
    with SessionLocal() as db:
        admin_role = db.scalar(select(Role).where(Role.name == "admin"))
        customer_role = db.scalar(select(Role).where(Role.name == "customer"))
        if not admin_role:
            admin_role = Role(name="admin", description="Administrador BOOKLY")
            db.add(admin_role)
            db.flush()
        if not customer_role:
            customer_role = Role(name="customer", description="Cliente BOOKLY")
            db.add(customer_role)
            db.flush()

        profile = db.scalar(select(Profile).where(Profile.email == email.lower()))
        if not profile:
            resolved_id = UUID(user_id) if user_id else resolve_supabase_user_id(email)
            if not resolved_id:
                resolved_id = uuid4()
                print(
                    "[INFO] Usuario no encontrado en Supabase Auth; creando perfil con UUID generado. "
                    "Para producción, registra primero al usuario en Supabase Auth y pasa --user-id."
                )
            profile = Profile(
                id=resolved_id,
                email=email.lower(),
                full_name=full_name,
                is_active=True,
            )
            db.add(profile)
            db.flush()

        for role in (customer_role, admin_role):
            exists = db.scalar(
                select(UserRole).where(
                    UserRole.user_id == profile.id, UserRole.role_id == role.id
                )
            )
            if not exists:
                db.add(UserRole(user_id=profile.id, role_id=role.id, assigned_by=profile.id))

        db.add(
            AuditLog(
                actor_id=profile.id,
                action="ADMIN_ROLE_ASSIGNED",
                entity_type="profile",
                entity_id=str(profile.id),
                new_values={"email": profile.email, "role": "admin"},
            )
        )
        db.commit()
        print(f"[OK] Rol 'admin' asignado correctamente a {profile.email} (ID: {profile.id})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Asignar rol administrador en BOOKLY")
    parser.add_argument("--email", required=True, help="Correo del usuario administrador")
    parser.add_argument("--name", default="Administrador BOOKLY", help="Nombre completo")
    parser.add_argument("--user-id", default=None, help="UUID de auth.users en Supabase (opcional)")
    args = parser.parse_args()
    assign_admin_role(args.email, args.name, args.user_id)
