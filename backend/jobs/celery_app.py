from backend.config import get_settings

settings = get_settings()

try:
    from celery import Celery

    celery_app = Celery(
        "reconciliation",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=[
            "backend.jobs.ingest_jobs",
            "backend.jobs.reconciliation_jobs",
            "backend.jobs.report_jobs",
        ],
    )

    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_track_started=True,
        task_routes={
            "backend.jobs.ingest_jobs.*": {"queue": "ingestion"},
            "backend.jobs.reconciliation_jobs.*": {"queue": "reconciliation"},
            "backend.jobs.report_jobs.*": {"queue": "reports"},
        },
        task_max_retries=3,
        task_default_retry_delay=30,
    )
except Exception:
    celery_app = None
