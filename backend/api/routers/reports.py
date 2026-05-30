import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from backend.api.schemas.report import ReportGenerateRequest, ReportMetaResponse
from backend.jobs.report_jobs import generate_report_task
from backend.reporting.report_service import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate")
async def generate_report(body: ReportGenerateRequest):
    task = generate_report_task.delay(body.run_id, body.format, "system")
    return {"task_id": task.id, "status": "queued", "run_id": body.run_id, "format": body.format}


@router.get("", response_model=list[ReportMetaResponse])
async def list_reports():
    return [ReportMetaResponse(**r) for r in report_service.list_reports()]


@router.get("/{report_id}/download")
async def download_report(report_id: str, file_type: str = "pdf"):
    path = report_service.get_report_path(report_id, file_type)
    if not path:
        raise HTTPException(404, "Report file not found")
    media = "application/pdf" if file_type == "pdf" else "application/zip"
    return FileResponse(path, media_type=media, filename=path.name)
