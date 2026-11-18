from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import base64
import json

from services.ocr.ocr_service import OCRService

router = APIRouter(prefix="/api/ocr", tags=["OCR Studio"])

@router.post("/process")
async def process_ocr_endpoint(
    file: UploadFile = File(...),
    language: str = Form("eng")
):
    content = await file.read()
    is_pdf = file.filename.lower().endswith(".pdf")
    try:
        results = OCRService.process_ocr(content, is_pdf=is_pdf, language=language)
        return {"success": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def export_ocr_endpoint(
    ocrData: str = Form(...), # JSON string of ocr results
    exportFormat: str = Form("DOCX")
):
    try:
        data = json.loads(ocrData)
        exported_bytes = OCRService.export_ocr_results(data, export_format=exportFormat)
        b64 = base64.b64encode(exported_bytes).decode("utf-8")
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if exportFormat.upper() == "DOCX" else "text/plain"
        return {
            "success": True,
            "exportFormat": exportFormat.upper(),
            "dataUrl": f"data:{mime};base64,{b64}",
            "sizeBytes": len(exported_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
