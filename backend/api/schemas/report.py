from pydantic import BaseModel


class ReportGenerateRequest(BaseModel):
    run_id: str
    format: str = "pdf"


class ReportMetaResponse(BaseModel):
    report_id: str
    run_id: str
    format: str
    generated_at: str
    requested_by: str
    pdf_path: str | None = None
    csv_path: str | None = None
    exception_count: int = 0
