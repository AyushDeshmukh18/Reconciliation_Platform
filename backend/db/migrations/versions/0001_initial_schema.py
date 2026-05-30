"""initial schema

Revision ID: 0001
Revises:
Create Date: 2024-05-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(128), nullable=False, unique=True),
        sa.Column("email", sa.String(256), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(256), nullable=False),
        sa.Column("role", sa.Enum("admin", "analyst", "viewer", name="user_role_enum"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "platform_transactions",
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("merchant_id", sa.String(128), nullable=False),
        sa.Column("amount_minor_units", sa.BigInteger(), nullable=False),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default="INR"),
        sa.Column(
            "transaction_status",
            sa.Enum("pending", "success", "failed", "reversed", "voided", name="transaction_status_enum"),
            nullable=False,
        ),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("idempotency_key", sa.String(256), nullable=True),
        sa.Column("parent_transaction_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_file_hash", sa.String(64), nullable=False),
        sa.Column("raw_record", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(["parent_transaction_id"], ["platform_transactions.transaction_id"]),
    )
    op.create_index("ix_platform_transactions_merchant_id", "platform_transactions", ["merchant_id"])
    op.create_index("ix_platform_transactions_created_at_utc", "platform_transactions", ["created_at_utc"])
    op.create_index("ix_platform_transactions_idempotency_key", "platform_transactions", ["idempotency_key"], unique=True)
    op.create_index("ix_platform_tx_merchant_created", "platform_transactions", ["merchant_id", "created_at_utc"])

    op.create_table(
        "bank_settlements",
        sa.Column("settlement_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("batch_id", sa.String(128), nullable=False),
        sa.Column("transaction_reference", sa.String(256), nullable=False),
        sa.Column("settled_amount_minor_units", sa.BigInteger(), nullable=False),
        sa.Column("fee_amount_minor_units", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("net_settled_amount_minor_units", sa.BigInteger(), nullable=False),
        sa.Column("value_date_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processing_date_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "settlement_status",
            sa.Enum("settled", "reversed", "returned", "held", name="settlement_status_enum"),
            nullable=False,
        ),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("batch_sequence_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("raw_record", postgresql.JSONB(), nullable=False),
    )
    op.create_index("ix_bank_settlements_batch_id", "bank_settlements", ["batch_id"])
    op.create_index("ix_bank_settlements_value_date_utc", "bank_settlements", ["value_date_utc"])
    op.create_index("ix_bank_settlements_transaction_reference", "bank_settlements", ["transaction_reference"])
    op.create_index("ix_bank_settlement_batch_value", "bank_settlements", ["batch_id", "value_date_utc"])

    op.create_table(
        "reconciliation_runs",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("triggered_by", sa.String(128), nullable=False),
        sa.Column("started_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("queued", "running", "completed", "failed", "retrying", name="run_status_enum"),
            nullable=False,
        ),
        sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("matched_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unmatched_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("partially_matched_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("flagged_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_monetary_exposure_minor_units", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("celery_task_id", sa.String(256), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(256), nullable=False, unique=True),
        sa.Column("date_range_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("date_range_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("progress_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("progress_message", sa.String(512), nullable=True),
    )

    op.create_table(
        "rule_configs",
        sa.Column("rule_id", sa.String(64), primary_key=True),
        sa.Column("gap_type", sa.String(64), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("conditions", postgresql.JSONB(), nullable=False),
        sa.Column("confidence_base", sa.Numeric(5, 2), nullable=False),
        sa.Column("recommended_action", sa.String(512), nullable=False),
        sa.Column("description", sa.String(1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )

    op.create_table(
        "reconciliation_results",
        sa.Column("result_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform_transaction_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("bank_settlement_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "match_type",
            sa.Enum("exact", "fuzzy", "composite", "unmatched", name="match_type_enum"),
            nullable=False,
        ),
        sa.Column(
            "gap_type",
            sa.Enum(
                "timing_gap",
                "rounding_difference",
                "duplicate_entry",
                "orphan_refund",
                "partial_settlement",
                "failed_reversal",
                "split_settlement",
                "stale_retry",
                "settlement_truncation",
                "status_mismatch",
                "idempotency_failure",
                "unclassified",
                name="gap_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("gap_confidence", sa.Numeric(5, 2), nullable=False),
        sa.Column("monetary_difference_minor_units", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column(
            "recon_status",
            sa.Enum(
                "unprocessed",
                "matched",
                "partially_matched",
                "flagged",
                "manually_resolved",
                "closed",
                name="recon_status_enum",
            ),
            nullable=False,
            server_default="unprocessed",
        ),
        sa.Column("rule_id_fired", sa.String(64), nullable=True),
        sa.Column("rule_evaluation_trace", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("gap_explanation", sa.Text(), nullable=True),
        sa.Column("resolution_suggestion", sa.Text(), nullable=True),
        sa.Column("requires_secondary_review", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at_utc", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["reconciliation_runs.run_id"]),
        sa.ForeignKeyConstraint(["platform_transaction_id"], ["platform_transactions.transaction_id"]),
        sa.ForeignKeyConstraint(["bank_settlement_id"], ["bank_settlements.settlement_id"]),
    )
    op.create_index("ix_reconciliation_results_gap_type", "reconciliation_results", ["gap_type"])
    op.create_index("ix_reconciliation_results_recon_status", "reconciliation_results", ["recon_status"])
    op.create_index("ix_reconciliation_results_run_id", "reconciliation_results", ["run_id"])
    op.create_index(
        "ix_reconciliation_results_platform_transaction_id",
        "reconciliation_results",
        ["platform_transaction_id"],
    )
    op.create_index("ix_recon_results_run_gap", "reconciliation_results", ["run_id", "gap_type"])

    op.create_table(
        "resolution_notes",
        sa.Column("note_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("result_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analyst_id", sa.String(128), nullable=False),
        sa.Column("note_text", sa.Text(), nullable=False),
        sa.Column("is_ai_suggested", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["result_id"], ["reconciliation_results.result_id"]),
    )

    op.create_table(
        "audit_logs",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("before_state", postgresql.JSONB(), nullable=True),
        sa.Column("after_state", postgresql.JSONB(), nullable=True),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=True),
    )
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"])
    op.create_index("ix_audit_logs_created_at_utc", "audit_logs", ["created_at_utc"])
    op.create_index("ix_audit_logs_correlation_id", "audit_logs", ["correlation_id"])
    op.create_index("ix_audit_entity_created", "audit_logs", ["entity_id", "created_at_utc"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("resolution_notes")
    op.drop_table("reconciliation_results")
    op.drop_table("rule_configs")
    op.drop_table("reconciliation_runs")
    op.drop_table("bank_settlements")
    op.drop_table("platform_transactions")
    op.drop_table("users")
    for enum_name in [
        "recon_status_enum",
        "gap_type_enum",
        "match_type_enum",
        "run_status_enum",
        "settlement_status_enum",
        "transaction_status_enum",
        "user_role_enum",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
