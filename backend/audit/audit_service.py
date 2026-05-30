import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.models.audit_log import AuditLog


class AuditService:
    async def log_event(
        self,
        db: AsyncSession,
        event_type: str,
        entity_id: str,
        entity_type: str,
        actor: str,
        correlation_id: str,
        before_state: dict[str, Any] | None = None,
        after_state: dict[str, Any] | None = None,
        file_hash: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            entity_id=entity_id,
            entity_type=entity_type,
            actor=actor,
            before_state=before_state,
            after_state=after_state,
            correlation_id=correlation_id,
            file_hash=file_hash,
        )
        db.add(entry)
        await db.flush()
        return entry


audit_service = AuditService()
