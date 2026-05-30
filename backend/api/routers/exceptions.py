import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.api.models.platform_transaction import PlatformTransaction
from backend.api.models.reconciliation_result import ReconciliationResult, ReconStatus
from backend.api.models.resolution_note import ResolutionNote
from backend.api.schemas.exception import (
    BulkResolveRequest,
    DryRunRequest,
    DryRunResponse,
    ExceptionDetail,
    ExceptionListItem,
    ResolutionNoteCreate,
    ResolutionNoteSchema,
    RuleEvaluation,
    StatusUpdateRequest,
)
from backend.api.services.ollama_service import ollama_service
from backend.audit.audit_service import audit_service
from backend.db.base import get_db
from backend.rules.rule_engine import RuleEngine

router = APIRouter(prefix="/exceptions", tags=["exceptions"])

VALID_TRANSITIONS = {
    ReconStatus.flagged: {ReconStatus.manually_resolved},
    ReconStatus.manually_resolved: {ReconStatus.closed},
    ReconStatus.matched: {ReconStatus.closed},
}


@router.get("", response_model=list[ExceptionListItem])
async def list_exceptions(
    db: AsyncSession = Depends(get_db),
    gap_type: str | None = None,
    recon_status: str | None = None,
    merchant_id: str | None = None,
    amount_min: int | None = None,
    amount_max: int | None = None,
    run_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
):
    q = select(ReconciliationResult, PlatformTransaction.merchant_id).outerjoin(
        PlatformTransaction,
        ReconciliationResult.platform_transaction_id == PlatformTransaction.transaction_id,
    )
    if gap_type:
        q = q.where(ReconciliationResult.gap_type == gap_type)
    if recon_status:
        q = q.where(ReconciliationResult.recon_status == recon_status)
    if merchant_id:
        q = q.where(PlatformTransaction.merchant_id == merchant_id)
    if run_id:
        q = q.where(ReconciliationResult.run_id == run_id)
    if amount_min is not None:
        q = q.where(ReconciliationResult.monetary_difference_minor_units >= amount_min)
    if amount_max is not None:
        q = q.where(ReconciliationResult.monetary_difference_minor_units <= amount_max)

    offset = (page - 1) * page_size
    rows = (
        await db.execute(
            q.order_by(ReconciliationResult.created_at_utc.desc()).offset(offset).limit(page_size)
        )
    ).all()

    return [
        ExceptionListItem(
            result_id=r.result_id,
            run_id=r.run_id,
            gap_type=r.gap_type.value,
            gap_confidence=float(r.gap_confidence),
            recon_status=r.recon_status.value,
            monetary_difference_minor_units=r.monetary_difference_minor_units,
            platform_transaction_id=r.platform_transaction_id,
            bank_settlement_id=r.bank_settlement_id,
            created_at_utc=r.created_at_utc,
            merchant_id=merchant_id_value,
            requires_secondary_review=r.requires_secondary_review,
        )
        for r, merchant_id_value in rows
    ]


async def _build_detail(db: AsyncSession, result: ReconciliationResult) -> ExceptionDetail:
    from backend.api.models.bank_settlement import BankSettlement
    from backend.api.schemas.exception import BankSettlementSchema, PlatformTransactionSchema

    platform = None
    bank = None
    merchant_id = None
    if result.platform_transaction_id:
        pt = await db.get(PlatformTransaction, result.platform_transaction_id)
        if pt:
            merchant_id = pt.merchant_id
            platform = PlatformTransactionSchema(
                transaction_id=pt.transaction_id,
                merchant_id=pt.merchant_id,
                amount_minor_units=pt.amount_minor_units,
                currency_code=pt.currency_code,
                transaction_status=pt.transaction_status.value,
                created_at_utc=pt.created_at_utc,
                idempotency_key=pt.idempotency_key,
                parent_transaction_id=pt.parent_transaction_id,
            )
    if result.bank_settlement_id:
        bs = await db.get(BankSettlement, result.bank_settlement_id)
        if bs:
            bank = BankSettlementSchema(
                settlement_id=bs.settlement_id,
                batch_id=bs.batch_id,
                transaction_reference=bs.transaction_reference,
                settled_amount_minor_units=bs.settled_amount_minor_units,
                fee_amount_minor_units=bs.fee_amount_minor_units,
                net_settled_amount_minor_units=bs.net_settled_amount_minor_units,
                value_date_utc=bs.value_date_utc,
                processing_date_utc=bs.processing_date_utc,
                settlement_status=bs.settlement_status.value,
                file_hash=bs.file_hash,
            )

    notes = (
        await db.scalars(
            select(ResolutionNote).where(ResolutionNote.result_id == result.result_id).order_by(ResolutionNote.created_at_utc)
        )
    ).all()

    return ExceptionDetail(
        result_id=result.result_id,
        run_id=result.run_id,
        gap_type=result.gap_type.value,
        gap_confidence=float(result.gap_confidence),
        recon_status=result.recon_status.value,
        monetary_difference_minor_units=result.monetary_difference_minor_units,
        platform_transaction_id=result.platform_transaction_id,
        bank_settlement_id=result.bank_settlement_id,
        created_at_utc=result.created_at_utc,
        merchant_id=merchant_id,
        requires_secondary_review=result.requires_secondary_review,
        platform_transaction=platform,
        bank_settlement=bank,
        rule_evaluation_trace=result.rule_evaluation_trace or [],
        gap_explanation=result.gap_explanation,
        resolution_suggestion=result.resolution_suggestion,
        resolution_notes=[
            ResolutionNoteSchema(
                note_id=n.note_id,
                analyst_id=n.analyst_id,
                note_text=n.note_text,
                is_ai_suggested=n.is_ai_suggested,
                created_at_utc=n.created_at_utc,
            )
            for n in notes
        ],
    )


@router.get("/{result_id}", response_model=ExceptionDetail)
async def get_exception(result_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.get(ReconciliationResult, result_id)
    if not result:
        raise HTTPException(404, "Exception not found")
    return await _build_detail(db, result)


@router.patch("/{result_id}/status", response_model=ExceptionDetail)
async def update_status(
    result_id: str,
    body: StatusUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.get(ReconciliationResult, result_id)
    if not result:
        raise HTTPException(404, "Exception not found")

    current = result.recon_status
    new_status = ReconStatus(body.new_status.value)

    if current == ReconStatus.flagged and new_status == ReconStatus.closed:
        raise HTTPException(422, "Flagged → Closed is blocked; resolve manually first")

    allowed = VALID_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        raise HTTPException(422, f"Invalid transition from {current.value} to {new_status.value}")

    if new_status == ReconStatus.manually_resolved:
        note_count = await db.scalar(
            select(func.count()).select_from(ResolutionNote).where(ResolutionNote.result_id == result_id)
        )
        if not note_count and not body.note:
            raise HTTPException(422, "Resolution note required for manually resolved status")
        if body.note:
            db.add(
                ResolutionNote(
                    note_id=str(uuid.uuid4()),
                    result_id=result_id,
                    analyst_id="system",
                    note_text=body.note,
                    is_ai_suggested=False,
                )
            )

    before = {"recon_status": current.value}
    result.recon_status = new_status
    await audit_service.log_event(
        db,
        event_type="STATUS_TRANSITION",
        entity_id=result_id,
        entity_type="reconciliation_result",
        actor="system",
        correlation_id=str(uuid.UUID(request.state.correlation_id)),
        before_state=before,
        after_state={"recon_status": new_status.value},
    )
    await db.commit()
    await db.refresh(result)
    return await _build_detail(db, result)


@router.post("/{result_id}/notes", response_model=ResolutionNoteSchema)
async def add_note(
    result_id: str,
    body: ResolutionNoteCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.get(ReconciliationResult, result_id)
    if not result:
        raise HTTPException(404, "Exception not found")
    note = ResolutionNote(
        note_id=str(uuid.uuid4()),
        result_id=result_id,
        analyst_id="system",
        note_text=body.note_text,
        is_ai_suggested=body.accept_ai_suggestion,
    )
    db.add(note)
    await audit_service.log_event(
        db,
        event_type="RESOLUTION_NOTE_ADDED",
        entity_id=result_id,
        entity_type="reconciliation_result",
        actor="system",
        correlation_id=str(uuid.UUID(request.state.correlation_id)),
        after_state={"note": body.note_text[:200]},
    )
    await db.commit()
    return ResolutionNoteSchema(
        note_id=note.note_id,
        analyst_id=note.analyst_id,
        note_text=note.note_text,
        is_ai_suggested=note.is_ai_suggested,
        created_at_utc=note.created_at_utc,
    )


@router.get("/{result_id}/notes", response_model=list[ResolutionNoteSchema])
async def list_notes(result_id: str, db: AsyncSession = Depends(get_db)):
    notes = (
        await db.scalars(
            select(ResolutionNote).where(ResolutionNote.result_id == result_id).order_by(ResolutionNote.created_at_utc)
        )
    ).all()
    return [
        ResolutionNoteSchema(
            note_id=n.note_id,
            analyst_id=n.analyst_id,
            note_text=n.note_text,
            is_ai_suggested=n.is_ai_suggested,
            created_at_utc=n.created_at_utc,
        )
        for n in notes
    ]


@router.post("/bulk-resolve")
async def bulk_resolve(
    body: BulkResolveRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    if not body.confirmation:
        raise HTTPException(422, "Confirmation required")
    updated = 0
    for rid in body.result_ids:
        result = await db.get(ReconciliationResult, rid)
        if not result or result.recon_status != ReconStatus.flagged:
            continue
        db.add(
            ResolutionNote(
                note_id=str(uuid.uuid4()),
                result_id=rid,
                analyst_id="system",
                note_text=body.note_text,
                is_ai_suggested=False,
            )
        )
        result.recon_status = ReconStatus.manually_resolved
        updated += 1
    await audit_service.log_event(
        db,
        event_type="BULK_RESOLVE_INITIATED",
        entity_id=str(uuid.uuid4()),
        entity_type="bulk_resolve",
        actor="system",
        correlation_id=str(uuid.UUID(request.state.correlation_id)),
        after_state={"count": updated},
    )
    await db.commit()
    return {"updated": updated}


@router.get("/{result_id}/suggest-resolution")
async def suggest_resolution(result_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.get(ReconciliationResult, result_id)
    if not result:
        raise HTTPException(404, "Exception not found")
    metadata = {"gap_type": result.gap_type.value, "result_id": str(result_id)}
    suggestion = await ollama_service.suggest_resolution(result.gap_type.value, metadata, [])
    result.resolution_suggestion = suggestion
    await db.commit()
    return {"suggestion": suggestion}


@router.post("/dry-run", response_model=DryRunResponse)
async def dry_run(body: DryRunRequest):
    engine = RuleEngine()
    outcome = engine.dry_run(body.transaction_record)
    return DryRunResponse(
        rules_evaluated=[RuleEvaluation(**r) for r in outcome["rules_evaluated"]],
        winning_rule=outcome["winning_rule"],
        gap_type=outcome["gap_type"],
        confidence=outcome["confidence"],
    )
