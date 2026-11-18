from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import base64

from services.enhancement.enhancement_service import EnhancementService

router = APIRouter(prefix="/api/images", tags=["Enhancement"])

@router.post("/upscale")
async def upscale_image(
    file: UploadFile = File(...),
    scaleFactor: int = Form(2)
):
    content = await file.read()
    try:
        out_bytes, telemetry = EnhancementService.upscale(content, scale_factor=scaleFactor)
        b64 = base64.b64encode(out_bytes).decode("utf-8")
        return {
            "success": True,
            "telemetry": telemetry,
            "dataUrl": f"data:image/png;base64,{b64}",
            "sizeBytes": len(out_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enhance")
async def enhance_image_endpoint(
    file: UploadFile = File(...),
    mode: str = Form("auto"),
    intensity: float = Form(1.0)
):
    content = await file.read()
    try:
        out_bytes, telemetry = EnhancementService.enhance_image(content, mode=mode, intensity=intensity)
        b64 = base64.b64encode(out_bytes).decode("utf-8")
        return {
            "success": True,
            "telemetry": telemetry,
            "dataUrl": f"data:image/png;base64,{b64}",
            "sizeBytes": len(out_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
