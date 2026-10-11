import json
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.models.presentation import AuditLog


def log_audit_event(
    db: Session,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Record an audit trail event inside the active transaction."""
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details_json=json.dumps(details or {}, ensure_ascii=False),
    )
    db.add(log_entry)
    db.flush()
    return log_entry
