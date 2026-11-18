from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import base64

from services.image.image_service import ImageService
from services.conversion.metadata_handler import MetadataHandler
from services.conversion.compression_engine import CompressionEngine

router = APIRouter(prefix="/api/images", tags=["Image Studio"])

@router.post("/remove-background")
async def remove_bg(
    file: UploadFile = File(...),
    replacementColor: Optional[str] = Form(None)
):
    content = await file.read()
    try:
        res_bytes = ImageService.remove_background(content, replacementColor)
        b64 = base64.b64encode(res_bytes).decode("utf-8")
        return {
            "success": True,
            "dataUrl": f"data:image/png;base64,{b64}",
            "sizeBytes": len(res_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/filter")
async def apply_image_filters(
    file: UploadFile = File(...),
    brightness: float = Form(1.0),
    contrast: float = Form(1.0),
    saturation: float = Form(1.0),
    sharpness: float = Form(1.0),
    blurRadius: float = Form(0.0),
    filterPreset: Optional[str] = Form(None)
):
    content = await file.read()
    try:
        res_bytes = ImageService.apply_filters(
            content,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            sharpness=sharpness,
            blur_radius=blurRadius,
            filter_preset=filterPreset
        )
        b64 = base64.b64encode(res_bytes).decode("utf-8")
        return {
            "success": True,
            "dataUrl": f"data:image/png;base64,{b64}",
            "sizeBytes": len(res_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/watermark")
async def apply_watermark_endpoint(
    file: UploadFile = File(...),
    text: Optional[str] = Form(None),
    watermarkFile: Optional[UploadFile] = File(None),
    opacity: float = Form(0.5),
    position: str = Form("bottom-right"),
    fontSize: int = Form(36),
    colorHex: str = Form("#FFFFFF")
):
    content = await file.read()
    wm_bytes = await watermarkFile.read() if watermarkFile else None
    try:
        res_bytes = ImageService.apply_watermark(
            content,
            text=text,
            watermark_image_bytes=wm_bytes,
            opacity=opacity,
            position=position,
            font_size=fontSize,
            color_hex=colorHex
        )
        b64 = base64.b64encode(res_bytes).decode("utf-8")
        return {
            "success": True,
            "dataUrl": f"data:image/png;base64,{b64}",
            "sizeBytes": len(res_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/metadata")
async def inspect_metadata(file: UploadFile = File(...)):
    content = await file.read()
    meta = MetadataHandler.extract_metadata(content)
    return meta

@router.post("/compress")
async def compress_image_endpoint(
    file: UploadFile = File(...),
    quality: int = Form(80),
    targetSizeKb: Optional[int] = Form(None),
    lossless: bool = Form(False),
    targetFormat: str = Form("WEBP")
):
    content = await file.read()
    try:
        out_bytes, telemetry = CompressionEngine.compress_image(
            content,
            quality=quality,
            target_size_kb=targetSizeKb,
            lossless=lossless,
            target_format=targetFormat
        )
        b64 = base64.b64encode(out_bytes).decode("utf-8")
        fmt = targetFormat.lower()
        return {
            "success": True,
            "telemetry": telemetry,
            "dataUrl": f"data:image/{fmt};base64,{b64}",
            "sizeBytes": len(out_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
