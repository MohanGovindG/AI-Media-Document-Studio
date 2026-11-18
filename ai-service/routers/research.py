from fastapi import APIRouter, UploadFile, File, HTTPException
from services.research.benchmark_service import BenchmarkService
from services.conversion.conversion_engine import ConversionEngine
import base64

router = APIRouter(prefix="/api/research", tags=["Research Lab"])

@router.post("/evaluate")
async def evaluate_pair(
    originalFile: UploadFile = File(...),
    processedFile: UploadFile = File(...)
):
    orig_bytes = await originalFile.read()
    proc_bytes = await processedFile.read()
    try:
        metrics = BenchmarkService.evaluate_quality(orig_bytes, proc_bytes)
        return {"success": True, "metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/benchmark-suite")
async def run_benchmark_suite(file: UploadFile = File(...)):
    """Runs automated multi-format conversion benchmark matrix on image (PNG, WEBP, AVIF, JPG)."""
    orig_bytes = await file.read()
    results = []

    formats_to_test = [
        {"fmt": "WEBP", "q": 85},
        {"fmt": "WEBP", "q": 65},
        {"fmt": "JPG", "q": 85},
        {"fmt": "JPG", "q": 60},
        {"fmt": "PNG", "q": 100}
    ]

    for test in formats_to_test:
        try:
            converted_bytes, telemetry = ConversionEngine.process_conversion(
                file_bytes=orig_bytes,
                target_format=test["fmt"],
                quality=test["q"]
            )
            # Evaluate quality vs original
            eval_metrics = BenchmarkService.evaluate_quality(orig_bytes, converted_bytes)
            results.append({
                "format": test["fmt"],
                "quality": test["q"],
                "fileSize": len(converted_bytes),
                "savings": eval_metrics["savingsPercentage"],
                "psnr": eval_metrics["psnr"],
                "ssim": eval_metrics["ssim"],
                "qualityScore": eval_metrics["qualityScore"],
                "conversionTimeMs": telemetry.get("conversionTimeMs", 100)
            })
        except Exception:
            continue

    return {"success": True, "results": results}
