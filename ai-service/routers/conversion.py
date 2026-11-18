from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response, JSONResponse
from typing import Optional, List
import base64

from services.conversion.conversion_engine import ConversionEngine
from services.conversion.conversion_matrix import ConversionMatrix
from services.conversion.format_detector import FormatDetector

router = APIRouter(prefix="/api/images", tags=["Conversion"])

@router.get("/formats")
async def get_all_formats():
    """Returns dynamic format capability matrix."""
    return ConversionMatrix.get_all_formats()

@router.get("/formats/{format_name}")
async def get_format_targets(format_name: str):
    """Returns compatible target formats for a given source format."""
    return ConversionMatrix.get_targets_for_format(format_name)

@router.post("/detect")
async def detect_format(file: UploadFile = File(...)):
    """Magic byte inspection on uploaded file."""
    content = await file.read()
    detection = FormatDetector.detect_format(content, file.filename)
    return detection

@router.post("/convert")
async def convert_image(
    file: UploadFile = File(...),
    targetFormat: str = Form("WEBP"),
    quality: int = Form(85),
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None),
    keepAspectRatio: bool = Form(True),
    dpi: Optional[int] = Form(None),
    backgroundColor: str = Form("#FFFFFF"),
    preserveMetadata: bool = Form(True),
    lossless: bool = Form(False),
    targetSizeKb: Optional[int] = Form(None)
):
    """Universal conversion endpoint for 15+ formats with full telemetry."""
    content = await file.read()
    try:
        converted_bytes, telemetry = ConversionEngine.process_conversion(
            file_bytes=content,
            target_format=targetFormat,
            filename=file.filename,
            quality=quality,
            width=width,
            height=height,
            keep_aspect_ratio=keepAspectRatio,
            dpi=dpi,
            background_color=backgroundColor,
            preserve_metadata=preserveMetadata,
            lossless=lossless,
            target_size_kb=targetSizeKb
        )

        b64_data = base64.b64encode(converted_bytes).decode("utf-8")
        out_ext = targetFormat.lower()

        return {
            "success": True,
            "filename": f"{file.filename.rsplit('.', 1)[0]}.{out_ext}",
            "telemetry": telemetry,
            "dataUrl": f"data:image/{out_ext};base64,{b64_data}",
            "sizeBytes": len(converted_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
