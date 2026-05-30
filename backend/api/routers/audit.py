import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.models.audit_log import AuditLog
from backend.api.schemas.audit import AuditLogResponse
from backend.db.base import get_db

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogResponse])
async def list_audit(
    db: AsyncSession = Depends(get_db),
    event_type: str | None = None,
    entity_id: str | None = None,
    actor: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    q = select(AuditLog)
    if event_type:
        q = q.where(AuditLog.event_type == event_type)
    if entity_id:
        q = q.where(AuditLog.entity_id == entity_id)
    if actor:
        q = q.where(AuditLog.actor == actor)
    offset = (page - 1) * page_size
    rows = (await db.scalars(q.order_by(AuditLog.created_at_utc.desc()).offset(offset).limit(page_size))).all()
    return [
        AuditLogResponse(
            event_id=r.event_id,
            event_type=r.event_type,
            entity_id=r.entity_id,
            entity_type=r.entity_type,
            actor=r.actor,
            before_state=r.before_state,
            after_state=r.after_state,
            created_at_utc=r.created_at_utc,
            correlation_id=r.correlation_id,
            file_hash=r.file_hash,
        )
        for r in rows
    ]


@router.get("/entity/{entity_id}", response_model=list[AuditLogResponse])
async def audit_by_entity(entity_id: str, db: AsyncSession = Depends(get_db)):
    rows = (
        await db.scalars(
            select(AuditLog).where(AuditLog.entity_id == entity_id).order_by(AuditLog.created_at_utc.desc())
        )
    ).all()
    return [
        AuditLogResponse(
            event_id=r.event_id,
            event_type=r.event_type,
            entity_id=r.entity_id,
            entity_type=r.entity_type,
            actor=r.actor,
            before_state=r.before_state,
            after_state=r.after_state,
            created_at_utc=r.created_at_utc,
            correlation_id=r.correlation_id,
            file_hash=r.file_hash,
        )
        for r in rows
    ]


@router.get("/export")
async def export_audit(db: AsyncSession = Depends(get_db)):
    rows = (await db.scalars(select(AuditLog).order_by(AuditLog.created_at_utc.asc()))).all()
    data = [
        {
            "event_id": str(r.event_id),
            "event_type": r.event_type,
            "entity_id": str(r.entity_id),
            "entity_type": r.entity_type,
            "actor": r.actor,
            "before_state": r.before_state,
            "after_state": r.after_state,
            "created_at_utc": r.created_at_utc.isoformat(),
            "correlation_id": str(r.correlation_id),
            "file_hash": r.file_hash,
        }
        for r in rows
    ]
    return JSONResponse(content=data)
