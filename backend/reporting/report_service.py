import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.models.reconciliation_result import ReconciliationResult, ReconStatus
from backend.api.models.reconciliation_run import ReconciliationRun
from backend.audit.audit_service import audit_service
from backend.config import get_settings
from backend.reporting.pdf_generator import generate_csv_report, generate_pdf_report


class ReportService:
    def __init__(self):
        self.settings = get_settings()
        self.reports_dir = Path(self.settings.REPORTS_DIR)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _meta_path(self, report_id: str) -> Path:
        return self.reports_dir / f"{report_id}.meta.json"

    async def generate(
        self,
        db: AsyncSession,
        run_id: str,
        fmt: str,
        requested_by: str,
    ) -> dict:
        run = await db.get(ReconciliationRun, run_id)
        if not run:
            raise ValueError("Run not found")

        results = (
            await db.scalars(
                select(ReconciliationResult).where(
                    ReconciliationResult.run_id == run_id,
                    ReconciliationResult.recon_status.in_(
                        [ReconStatus.flagged, ReconStatus.partially_matched, ReconStatus.unprocessed]
                    ),
                )
            )
        ).all()

        run_data = {
            "run_id": run.run_id,
            "triggered_by": run.triggered_by,
            "total_records": run.total_records,
            "matched_count": run.matched_count,
            "flagged_count": run.flagged_count,
            "unmatched_count": run.unmatched_count,
            "total_monetary_exposure_minor_units": run.total_monetary_exposure_minor_units,
        }

        result_rows = []
        for r in results:
            # Resolve linked platform and bank amounts to produce realistic report columns
            platform_amount = None
            bank_amount = None
            transaction_ref = r.platform_transaction_id or ""
            if r.platform_transaction_id:
                pt = await db.get(PlatformTransaction, r.platform_transaction_id)
                if pt:
                    platform_amount = pt.amount_minor_units
            if r.bank_settlement_id:
                bs = await db.get(BankSettlement, r.bank_settlement_id)
                if bs:
                    bank_amount = bs.net_settled_amount_minor_units
                    if not transaction_ref:
                        transaction_ref = bs.transaction_reference or ""

            result_rows.append(
                {
                    "result_id": r.result_id,
                    "gap_type": r.gap_type.value,
                    "gap_confidence": float(r.gap_confidence),
                    "recon_status": r.recon_status.value,
                    "monetary_difference": r.monetary_difference_minor_units,
                    "platform_amount": platform_amount if platform_amount is not None else 0,
                    "bank_amount": bank_amount if bank_amount is not None else 0,
                    "transaction_id": transaction_ref,
                    "rule_id_fired": r.rule_id_fired or "",
                }
            )

        report_id = str(uuid.uuid4())
        pdf_path = None
        csv_path = None

        if fmt in ("pdf", "both"):
            pdf_path = str(self.reports_dir / f"{report_id}.pdf")
            await generate_pdf_report(run_data, result_rows, pdf_path)

        if fmt in ("csv", "both"):
            csv_path = str(self.reports_dir / f"{report_id}.zip")
            await generate_csv_report(run_data, result_rows, csv_path)

        meta = {
            "report_id": report_id,
            "run_id": run_id,
            "format": fmt,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "requested_by": requested_by,
            "pdf_path": pdf_path,
            "csv_path": csv_path,
            "exception_count": len(result_rows),
        }
        self._meta_path(report_id).write_text(json.dumps(meta, indent=2))

        await audit_service.log_event(
            db,
            event_type="REPORT_GENERATED",
            entity_id=report_id,
            entity_type="report",
            actor=requested_by,
            correlation_id=str(uuid.uuid4()),
            after_state=meta,
        )
        await db.commit()
        return meta

    def list_reports(self) -> list[dict]:
        reports = []
        for meta_file in self.reports_dir.glob("*.meta.json"):
            try:
                reports.append(json.loads(meta_file.read_text()))
            except json.JSONDecodeError:
                continue
        reports.sort(key=lambda x: x.get("generated_at", ""), reverse=True)
        return reports

    def get_report_path(self, report_id: str, file_type: str) -> Path | None:
        meta_file = self._meta_path(report_id)
        if not meta_file.exists():
            return None
        meta = json.loads(meta_file.read_text())
        path_key = "pdf_path" if file_type == "pdf" else "csv_path"
        path = meta.get(path_key)
        return Path(path) if path and Path(path).exists() else None


report_service = ReportService()
