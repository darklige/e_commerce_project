from uuid import UUID

from fastapi import Request
from sqlmodel import Session

from app.domains.identity.models import (
    AUDIT_RESOURCE_ID_MAX_LENGTH,
    AUDIT_USER_AGENT_MAX_LENGTH,
    AuditLog,
)


def truncate_for_audit(value: str | None, max_length: int) -> str | None:
    if value is None:
        return None
    return value[:max_length]


def write_audit_log(
    session: Session,
    *,
    request: Request | None,
    action: str,
    resource_type: str,
    outcome: str,
    actor_user_id: UUID | None = None,
    resource_id: str | None = None,
    reason: str | None = None,
    details: str | None = None,
) -> None:
    ip_address = None
    user_agent = None
    if request is not None:
        ip_address = request.client.host if request.client else None
        user_agent = truncate_for_audit(
            request.headers.get("user-agent"), AUDIT_USER_AGENT_MAX_LENGTH
        )

    session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=truncate_for_audit(resource_id, AUDIT_RESOURCE_ID_MAX_LENGTH),
            outcome=outcome,
            ip_address=ip_address,
            user_agent=user_agent,
            reason=reason,
            details=details,
        )
    )
