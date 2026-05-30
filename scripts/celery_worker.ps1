# Run Celery worker from project root (works regardless of current directory)
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot
$env:PYTHONPATH = $ProjectRoot

$poolArgs = @()
if ($env:OS -match "Windows") {
    # Prefork pool fails on Windows with PermissionError; solo runs tasks in-process
    $poolArgs = @("--pool=solo", "--concurrency=1")
}

& "$ProjectRoot\venv\Scripts\celery.exe" -A backend.jobs.celery_app worker --loglevel=info -Q ingestion,reconciliation,reports @poolArgs @args
