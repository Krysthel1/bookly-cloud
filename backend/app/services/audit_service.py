from typing import Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.operations import AuditLog


def record_audit_log(
    db: Session,
    *,
    actor_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: str | UUID,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    return entry
