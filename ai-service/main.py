import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from routers.conversion import router as conversion_router
from routers.generation import router as generation_router
from routers.image_processing import router as image_router
from routers.enhancement import router as enhancement_router
from routers.pdf import router as pdf_router
from routers.document import router as document_router
from routers.ocr import router as ocr_router
from routers.jobs import router as jobs_router
from routers.research import router as research_router
from routers.command import router as command_router
from routers.assets import router as assets_router
from routers.auth import router as auth_router

app = FastAPI(
    title="AI Media & Document Studio — Engine API",
    description="Unified API Engine for AI Generation, Universal Conversion, PDF Studio, Office Studio, OCR, and Document Intelligence",
    version="2.0.0"
)

# Enable CORS for frontend Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all module routers
app.include_router(auth_router)
app.include_router(conversion_router)
app.include_router(generation_router)
app.include_router(image_router)
app.include_router(enhancement_router)
app.include_router(pdf_router)
app.include_router(document_router)
app.include_router(ocr_router)
app.include_router(jobs_router)
app.include_router(research_router)
app.include_router(command_router)
app.include_router(assets_router)

@app.get("/api/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "service": "AI Media & Document Studio Engine",
        "version": "2.0.0",
        "engines": {
            "imageConversion": "Active (15+ formats)",
            "aiGeneration": "Active",
            "pdfStudio": "Active (PyMuPDF & PyPDF)",
            "officeStudio": "Active (DOCX, XLSX, PPTX)",
            "ocrStudio": "Active",
            "documentIntelligence": "Active",
            "researchLab": "Active (PSNR/SSIM/MSE)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
