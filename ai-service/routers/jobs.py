from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from typing import List, Optional
import json
import base64

from services.jobs.job_manager import JobManager
from services.conversion.conversion_engine import ConversionEngine
from services.workflow.workflow_engine import WorkflowEngine

router = APIRouter(prefix="/api/jobs", tags=["Jobs & Automation"])

@router.get("")
async def list_jobs_endpoint():
    return JobManager.list_jobs()

@router.get("/{job_id}")
async def get_job_endpoint(job_id: str):
    job = JobManager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/{job_id}/cancel")
async def cancel_job_endpoint(job_id: str):
    res = JobManager.cancel_job(job_id)
    return {"success": res}

@router.get("/{job_id}/download-zip")
async def download_job_zip(job_id: str):
    zip_bytes = JobManager.get_job_zip(job_id)
    if not zip_bytes:
        raise HTTPException(status_code=404, detail="No ZIP archive for this job")
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{job_id}_results.zip"'}
    )

@router.post("/batch")
async def process_batch_job(
    files: List[UploadFile] = File(...),
    targetFormat: str = Form("WEBP"),
    quality: int = Form(85),
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None),
    jobName: Optional[str] = Form(None)
):
    total = len(files)
    job_id = JobManager.create_batch_job(
        job_name=jobName or f"Batch {targetFormat.upper()} Conversion ({total} files)",
        total_items=total,
        job_type="BATCH_CONVERT"
    )

    zip_file_entries = []

    for f in files:
        try:
            content = await f.read()
            converted_bytes, telemetry = ConversionEngine.process_conversion(
                file_bytes=content,
                target_format=targetFormat,
                filename=f.filename,
                quality=quality,
                width=width,
                height=height
            )
            out_filename = f"{f.filename.rsplit('.', 1)[0]}.{targetFormat.lower()}"
            zip_file_entries.append((out_filename, converted_bytes))

            b64 = base64.b64encode(converted_bytes).decode("utf-8")
            JobManager.update_job_progress(job_id, {
                "filename": out_filename,
                "originalName": f.filename,
                "success": True,
                "telemetry": telemetry,
                "dataUrl": f"data:image/{targetFormat.lower()};base64,{b64}",
                "sizeBytes": len(converted_bytes)
            })
        except Exception as e:
            JobManager.update_job_progress(job_id, {
                "originalName": f.filename,
                "success": False,
                "error": str(e)
            })

    JobManager.create_job_zip(job_id, zip_file_entries)
    return JobManager.get_job(job_id)

@router.post("/workflow")
async def execute_workflow_job(
    files: List[UploadFile] = File(...),
    workflowJson: str = Form(...) # JSON pipeline steps
):
    steps = json.loads(workflowJson)
    job_id = JobManager.create_batch_job(
        job_name=f"Workflow Pipeline ({len(files)} files)",
        total_items=len(files),
        job_type="WORKFLOW"
    )

    zip_file_entries = []

    for f in files:
        try:
            content = await f.read()
            out_bytes, out_name, logs = WorkflowEngine.execute_pipeline(
                file_bytes=content,
                filename=f.filename,
                pipeline_steps=steps
            )
            zip_file_entries.append((out_name, out_bytes))
            b64 = base64.b64encode(out_bytes).decode("utf-8")
            JobManager.update_job_progress(job_id, {
                "filename": out_name,
                "originalName": f.filename,
                "success": True,
                "stepLogs": logs,
                "dataUrl": f"data:image/png;base64,{b64}",
                "sizeBytes": len(out_bytes)
            })
        except Exception as e:
            JobManager.update_job_progress(job_id, {
                "originalName": f.filename,
                "success": False,
                "error": str(e)
            })

    JobManager.create_job_zip(job_id, zip_file_entries)
    return JobManager.get_job(job_id)
