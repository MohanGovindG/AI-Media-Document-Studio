import io
import time
import uuid
import zipfile
import threading
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

class JobManager:
    """
    Asynchronous job queue & batch manager:
    Tracks batch jobs, progresses, cancellation, and creates downloadable ZIP archives.
    """

    _jobs: Dict[str, Dict[str, Any]] = {}
    _executor = ThreadPoolExecutor(max_workers=4)
    _lock = threading.Lock()

    @classmethod
    def create_batch_job(cls, job_name: str, total_items: int, job_type: str = "CONVERSION") -> str:
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        with cls._lock:
            cls._jobs[job_id] = {
                "id": job_id,
                "name": job_name,
                "type": job_type,
                "status": "QUEUED", # QUEUED, PROCESSING, COMPLETED, FAILED, CANCELLED
                "totalItems": total_items,
                "completedItems": 0,
                "failedItems": 0,
                "progressPercentage": 0.0,
                "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "completedAt": None,
                "items": [],
                "zipData": None,
                "error": None
            }
        return job_id

    @classmethod
    def update_job_progress(cls, job_id: str, item_result: Dict[str, Any]):
        with cls._lock:
            if job_id not in cls._jobs:
                return
            job = cls._jobs[job_id]
            job["items"].append(item_result)
            if item_result.get("success", True):
                job["completedItems"] += 1
            else:
                job["failedItems"] += 1

            total = max(1, job["totalItems"])
            processed = job["completedItems"] + job["failedItems"]
            job["progressPercentage"] = round((processed / total) * 100, 1)

            if processed >= total:
                job["status"] = "COMPLETED" if job["failedItems"] == 0 else "COMPLETED_WITH_ERRORS"
                job["completedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            else:
                job["status"] = "PROCESSING"

    @classmethod
    def get_job(cls, job_id: str) -> Optional[Dict[str, Any]]:
        with cls._lock:
            job = cls._jobs.get(job_id)
            if not job:
                return None
            # Return copy without heavy binary payload
            res = dict(job)
            res["hasZip"] = job.get("zipData") is not None
            if "zipData" in res:
                del res["zipData"]
            return res

    @classmethod
    def list_jobs(cls) -> List[Dict[str, Any]]:
        with cls._lock:
            res = []
            for j in cls._jobs.values():
                c = dict(j)
                c["hasZip"] = j.get("zipData") is not None
                if "zipData" in c:
                    del c["zipData"]
                res.append(c)
            return sorted(res, key=lambda x: x["createdAt"], reverse=True)

    @classmethod
    def cancel_job(cls, job_id: str) -> bool:
        with cls._lock:
            if job_id in cls._jobs:
                cls._jobs[job_id]["status"] = "CANCELLED"
                return True
            return False

    @classmethod
    def create_job_zip(cls, job_id: str, files: List[Tuple[str, bytes]]) -> bytes:
        out_buf = io.BytesIO()
        with zipfile.ZipFile(out_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname, fbytes in files:
                zf.writestr(fname, fbytes)
        zip_bytes = out_buf.getvalue()
        with cls._lock:
            if job_id in cls._jobs:
                cls._jobs[job_id]["zipData"] = zip_bytes
        return zip_bytes

    @classmethod
    def get_job_zip(cls, job_id: str) -> Optional[bytes]:
        with cls._lock:
            if job_id in cls._jobs:
                return cls._jobs[job_id].get("zipData")
            return None
