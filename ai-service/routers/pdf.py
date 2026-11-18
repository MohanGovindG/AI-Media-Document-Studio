from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
import json
import base64

from services.pdf.pdf_service import PDFService
from services.conversion.pdf_converter import PDFConverter

router = APIRouter(prefix="/api/pdf", tags=["PDF Studio"])

@router.post("/create")
async def create_pdf_from_images(
    files: List[UploadFile] = File(...),
    pageSize: str = Form("A4"),
    orientation: str = Form("portrait"),
    dpi: int = Form(300)
):
    try:
        bytes_list = []
        for f in files:
            bytes_list.append(await f.read())
        pdf_bytes, telemetry = PDFConverter.images_to_pdf(
            bytes_list,
            page_size=pageSize,
            orientation=orientation,
            dpi=dpi
        )
        b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        return {
            "success": True,
            "telemetry": telemetry,
            "dataUrl": f"data:application/pdf;base64,{b64}",
            "sizeBytes": len(pdf_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract")
async def extract_pdf_pages(
    file: UploadFile = File(...),
    targetFormat: str = Form("PNG"),
    dpi: int = Form(200)
):
    content = await file.read()
    try:
        pages, telemetry = PDFConverter.pdf_to_images(content, target_format=targetFormat, dpi=dpi)
        formatted_pages = []
        for p in pages:
            b64 = base64.b64encode(p["data"]).decode("utf-8")
            fmt = targetFormat.lower()
            formatted_pages.append({
                "pageIndex": p["pageIndex"],
                "pageNumber": p["pageNumber"],
                "width": p["width"],
                "height": p["height"],
                "sizeBytes": p["sizeBytes"],
                "dataUrl": f"data:image/{fmt};base64,{b64}"
            })
        return {
            "success": True,
            "telemetry": telemetry,
            "pages": formatted_pages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/merge")
async def merge_pdfs_endpoint(files: List[UploadFile] = File(...)):
    try:
        bytes_list = []
        for f in files:
            bytes_list.append(await f.read())
        out_bytes = PDFService.merge_pdfs(bytes_list)
        b64 = base64.b64encode(out_bytes).decode("utf-8")
        return {
            "success": True,
            "dataUrl": f"data:application/pdf;base64,{b64}",
            "sizeBytes": len(out_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/split")
async def split_pdf_endpoint(
    file: UploadFile = File(...),
    pageRanges: str = Form("1-1") # e.g. "1-2, 3-4" or "1,2,3"
):
    content = await file.read()
    try:
        ranges = [r.strip() for r in pageRanges.split(",") if r.strip()]
        results = PDFService.split_pdf(content, ranges)
        encoded_files = []
        for i, b in enumerate(results):
            b64 = base64.b64encode(b).decode("utf-8")
            encoded_files.append({
                "part": i + 1,
                "dataUrl": f"data:application/pdf;base64,{b64}",
                "sizeBytes": len(b)
            })
        return {
            "success": True,
            "parts": encoded_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compress")
async def compress_pdf_endpoint(file: UploadFile = File(...)):
    content = await file.read()
    try:
        out_bytes, telemetry = PDFService.compress_pdf(content)
        b64 = base64.b64encode(out_bytes).decode("utf-8")
        return {
            "success": True,
            "telemetry": telemetry,
            "dataUrl": f"data:application/pdf;base64,{b64}",
            "sizeBytes": len(out_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rotate")
async def rotate_pdf_endpoint(
    file: UploadFile = File(...),
    degrees: int = Form(90),
    pageIndices: Optional[str] = Form(None)
):
    content = await file.read()
    try:
        indices = json.loads(pageIndices) if pageIndices else None
        out_bytes = PDFService.rotate_pages(content, degrees=degrees, page_indices=indices)
        b64 = base64.b64encode(out_bytes).decode("utf-8")
        return {
            "success": True,
            "dataUrl": f"data:application/pdf;base64,{b64}",
            "sizeBytes": len(out_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reorder")
async def reorder_pdf_endpoint(
    file: UploadFile = File(...),
    pageOrder: str = Form("[0,1]") # JSON array of 0-based indices
):
    content = await file.read()
    try:
        order = json.loads(pageOrder)
        out_bytes = PDFService.reorder_and_delete_pages(content, order)
        b64 = base64.b64encode(out_bytes).decode("utf-8")
        return {
            "success": True,
            "dataUrl": f"data:application/pdf;base64,{b64}",
            "sizeBytes": len(out_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/watermark")
async def watermark_pdf_endpoint(
    file: UploadFile = File(...),
    text: str = Form("CONFIDENTIAL"),
    opacity: float = Form(0.3)
):
    content = await file.read()
    try:
        out_bytes = PDFService.watermark_pdf(content, text=text, opacity=opacity)
        b64 = base64.b64encode(out_bytes).decode("utf-8")
        return {
            "success": True,
            "dataUrl": f"data:application/pdf;base64,{b64}",
            "sizeBytes": len(out_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
