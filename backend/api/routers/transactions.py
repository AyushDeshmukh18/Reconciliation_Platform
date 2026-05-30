import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.models.bank_settlement import BankSettlement
from backend.api.models.platform_transaction import PlatformTransaction
from backend.api.schemas.platform_transaction import BankSettlementResponse, PlatformTransactionResponse
from backend.db.base import get_db

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/platform", response_model=list[PlatformTransactionResponse])
async def list_platform(
    db: AsyncSession = Depends(get_db),
    merchant_id: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    amount_min: int | None = None,
    amount_max: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
):
    q = select(PlatformTransaction)
    if merchant_id:
        q = q.where(PlatformTransaction.merchant_id == merchant_id)
    if status:
        q = q.where(PlatformTransaction.transaction_status == status)
    if amount_min is not None:
        q = q.where(PlatformTransaction.amount_minor_units >= amount_min)
    if amount_max is not None:
        q = q.where(PlatformTransaction.amount_minor_units <= amount_max)
    offset = (page - 1) * page_size
    rows = (await db.scalars(q.order_by(PlatformTransaction.created_at_utc.desc()).offset(offset).limit(page_size))).all()
    return [
        PlatformTransactionResponse(
            transaction_id=r.transaction_id,
            merchant_id=r.merchant_id,
            amount_minor_units=r.amount_minor_units,
            currency_code=r.currency_code,
            transaction_status=r.transaction_status.value,
            created_at_utc=r.created_at_utc,
            idempotency_key=r.idempotency_key,
            parent_transaction_id=r.parent_transaction_id,
            source_file_hash=r.source_file_hash,
        )
        for r in rows
    ]


@router.get("/platform/{transaction_id}", response_model=PlatformTransactionResponse)
async def get_platform(transaction_id: str, db: AsyncSession = Depends(get_db)):
    row = await db.get(PlatformTransaction, transaction_id)
    if not row:
        raise HTTPException(404, "Not found")
    return PlatformTransactionResponse(
        transaction_id=row.transaction_id,
        merchant_id=row.merchant_id,
        amount_minor_units=row.amount_minor_units,
        currency_code=row.currency_code,
        transaction_status=row.transaction_status.value,
        created_at_utc=row.created_at_utc,
        idempotency_key=row.idempotency_key,
        parent_transaction_id=row.parent_transaction_id,
        source_file_hash=row.source_file_hash,
    )


@router.get("/bank", response_model=list[BankSettlementResponse])
async def list_bank(
    db: AsyncSession = Depends(get_db),
    batch_id: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
):
    q = select(BankSettlement)
    if batch_id:
        q = q.where(BankSettlement.batch_id == batch_id)
    if status:
        q = q.where(BankSettlement.settlement_status == status)
    offset = (page - 1) * page_size
    rows = (await db.scalars(q.order_by(BankSettlement.value_date_utc.desc()).offset(offset).limit(page_size))).all()
    return [
        BankSettlementResponse(
            settlement_id=r.settlement_id,
            batch_id=r.batch_id,
            transaction_reference=r.transaction_reference,
            settled_amount_minor_units=r.settled_amount_minor_units,
            fee_amount_minor_units=r.fee_amount_minor_units,
            net_settled_amount_minor_units=r.net_settled_amount_minor_units,
            value_date_utc=r.value_date_utc,
            processing_date_utc=r.processing_date_utc,
            settlement_status=r.settlement_status.value,
            file_hash=r.file_hash,
            batch_sequence_number=r.batch_sequence_number,
        )
        for r in rows
    ]


@router.get("/bank/{settlement_id}", response_model=BankSettlementResponse)
async def get_bank(settlement_id: str, db: AsyncSession = Depends(get_db)):
    row = await db.get(BankSettlement, settlement_id)
    if not row:
        raise HTTPException(404, "Not found")
    return BankSettlementResponse(
        settlement_id=row.settlement_id,
        batch_id=row.batch_id,
        transaction_reference=row.transaction_reference,
        settled_amount_minor_units=row.settled_amount_minor_units,
        fee_amount_minor_units=row.fee_amount_minor_units,
        net_settled_amount_minor_units=row.net_settled_amount_minor_units,
        value_date_utc=row.value_date_utc,
        processing_date_utc=row.processing_date_utc,
        settlement_status=row.settlement_status.value,
        file_hash=row.file_hash,
        batch_sequence_number=row.batch_sequence_number,
    )
