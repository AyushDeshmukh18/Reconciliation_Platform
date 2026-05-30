from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: UUID
    event_type: str
    entity_id: UUID
    entity_type: str
    actor: str
    before_state: dict | None
    after_state: dict | None
    created_at_utc: datetime
    correlation_id: UUID
    file_hash: str | None = None
