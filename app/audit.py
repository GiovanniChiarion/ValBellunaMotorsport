from datetime import UTC, datetime

from flask import g, request
from sqlalchemy.orm import Session

from app.models import AuditLog


def log_action(
    db: Session,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    user_id: int | None = None,
    race_id: int | None = None,
    field: str | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
    description: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    actor_name: str | None = None,
) -> AuditLog:
    try:
        if ip_address is None:
            forwarded = request.headers.get("X-Forwarded-For")
            ip_address = forwarded.split(",")[0].strip() if forwarded else request.remote_addr

        if user_agent is None:
            user_agent = request.headers.get("User-Agent", "")[:255]

        if user_id is None or actor_name is None:
            current = getattr(g, "current_user", None)
            if current:
                if user_id is None:
                    user_id = current.id
                if actor_name is None:
                    actor_name = current.nome
    except RuntimeError:
        pass

    log = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        race_id=race_id,
        field=field,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        actor_name=actor_name,
        timestamp=datetime.now(UTC),
    )
    db.add(log)
    db.flush()
    return log
