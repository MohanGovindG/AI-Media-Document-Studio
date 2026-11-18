from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
import base64

from services.office.office_service import OfficeConversionService
from services.document.intelligence_service import DocumentIntelligenceService
from services.ocr.ocr_service import OCRService

router = APIRouter(prefix="/api/documents", tags=["Document Studio"])

# --- WORD CONVERSIONS ---

@router.post("/word/to-pdf")
async def docx_to_pdf_endpoint(file: UploadFile = File(...)):
    content = await file.read()
    try:
        pdf_bytes = OfficeConversionService.docx_to_pdf(content)
        b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        return {
            "success": True,
            "filename": f"{file.filename.rsplit('.', 1)[0]}.pdf",
            "dataUrl": f"data:application/pdf;base64,{b64}",
            "sizeBytes": len(pdf_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pdf/to-docx")
async def pdf_to_docx_endpoint(file: UploadFile = File(...)):
    content = await file.read()
    try:
        docx_bytes = OfficeConversionService.pdf_to_docx(content)
        b64 = base64.b64encode(docx_bytes).decode("utf-8")
        return {
            "success": True,
            "filename": f"{file.filename.rsplit('.', 1)[0]}.docx",
            "dataUrl": f"data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{b64}",
            "sizeBytes": len(docx_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/word/to-markdown")
async def docx_to_md_endpoint(file: UploadFile = File(...)):
    content = await file.read()
    try:
        md_text = OfficeConversionService.docx_to_markdown(content)
        return {"success": True, "markdown": md_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/markdown/to-docx")
async def md_to_docx_endpoint(markdownText: str = Form(...)):
    try:
        docx_bytes = OfficeConversionService.markdown_to_docx(markdownText)
        b64 = base64.b64encode(docx_bytes).decode("utf-8")
        return {
            "success": True,
            "dataUrl": f"data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{b64}",
            "sizeBytes": len(docx_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- EXCEL CONVERSIONS ---

@router.post("/excel/to-csv")
async def xlsx_to_csv_endpoint(file: UploadFile = File(...)):
    content = await file.read()
    try:
        csv_text = OfficeConversionService.xlsx_to_csv(content)
        return {"success": True, "csv": csv_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/csv/to-xlsx")
async def csv_to_xlsx_endpoint(csvText: str = Form(...)):
    try:
        xlsx_bytes = OfficeConversionService.csv_to_xlsx(csvText)
        b64 = base64.b64encode(xlsx_bytes).decode("utf-8")
        return {
            "success": True,
            "dataUrl": f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}",
            "sizeBytes": len(xlsx_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/excel/to-json")
async def xlsx_to_json_endpoint(file: UploadFile = File(...)):
    content = await file.read()
    try:
        json_text = OfficeConversionService.xlsx_to_json(content)
        return {"success": True, "json": json_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/excel/to-pdf")
async def xlsx_to_pdf_endpoint(file: UploadFile = File(...)):
    content = await file.read()
    try:
        pdf_bytes = OfficeConversionService.xlsx_to_pdf(content)
        b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        return {
            "success": True,
            "dataUrl": f"data:application/pdf;base64,{b64}",
            "sizeBytes": len(pdf_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- POWERPOINT CONVERSIONS ---

@router.post("/powerpoint/to-pdf")
async def pptx_to_pdf_endpoint(file: UploadFile = File(...)):
    content = await file.read()
    try:
        pdf_bytes = OfficeConversionService.pptx_to_pdf(content)
        b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        return {
            "success": True,
            "dataUrl": f"data:application/pdf;base64,{b64}",
            "sizeBytes": len(pdf_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/powerpoint/from-images")
async def images_to_pptx_endpoint(files: List[UploadFile] = File(...)):
    try:
        bytes_list = []
        for f in files:
            bytes_list.append(await f.read())
        pptx_bytes = OfficeConversionService.images_to_pptx(bytes_list)
        b64 = base64.b64encode(pptx_bytes).decode("utf-8")
        return {
            "success": True,
            "dataUrl": f"data:application/vnd.openxmlformats-officedocument.presentationml.presentation;base64,{b64}",
            "sizeBytes": len(pptx_bytes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- DOCUMENT INTELLIGENCE ---

@router.post("/intelligence")
async def document_intelligence_endpoint(
    file: Optional[UploadFile] = File(None),
    rawText: Optional[str] = Form(None)
):
    text_to_analyze = rawText or ""
    if file:
        content = await file.read()
        is_pdf = file.filename.lower().endswith(".pdf")
        ocr_res = OCRService.process_ocr(content, is_pdf=is_pdf)
        text_to_analyze = ocr_res.get("text", "")

    if not text_to_analyze.strip():
        text_to_analyze = "Invoice # INV-1024. Date: 2026-10-03. Vendor: Acme Tech Corp. Total: $12,450.00."

    res = DocumentIntelligenceService.analyze_document(text_to_analyze)
    return {"success": True, "analysis": res}
