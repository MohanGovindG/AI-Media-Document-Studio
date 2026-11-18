import os
import sys
import io
import pytest
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import services
from services.conversion.format_detector import FormatDetector
from services.conversion.conversion_engine import ConversionEngine
from services.conversion.compression_engine import CompressionEngine
from services.conversion.pdf_converter import PDFConverter
from services.office.office_service import OfficeConversionService
from services.pdf.pdf_service import PDFService
from services.ocr.ocr_service import OCRService
from services.document.intelligence_service import DocumentIntelligenceService
from services.enhancement.enhancement_service import EnhancementService
from services.image.image_service import ImageService
from services.generation.ai_engine import AIEngine
from services.research.benchmark_service import BenchmarkService

def create_dummy_png(width=100, height=100, color=(255, 0, 0, 255)):
    img = Image.new("RGBA", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def create_dummy_jpg(width=100, height=100):
    img = Image.new("RGB", (width, height), (0, 255, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_magic_byte_detection():
    png_bytes = create_dummy_png()
    info = FormatDetector.detect_format(png_bytes, "sample.png")
    assert info["detectedFormat"] == "PNG"
    assert info["category"] == "RASTER"
    assert info["width"] == 100
    assert info["height"] == 100
    assert info["hasTransparency"] is True

    jpg_bytes = create_dummy_jpg()
    info_jpg = FormatDetector.detect_format(jpg_bytes, "fake_name.xyz")
    assert info_jpg["detectedFormat"] in ("JPG", "JPEG")
    assert info_jpg["category"] == "RASTER"

def test_raster_conversions():
    png_bytes = create_dummy_png(120, 80)
    
    # PNG -> JPG
    out_jpg, tel_jpg = ConversionEngine.process_conversion(png_bytes, target_format="JPG", quality=90, background_color="#FFFFFF")
    assert tel_jpg["targetFormat"] == "JPG"
    assert out_jpg is not None
    assert len(out_jpg) > 0

    # PNG -> WEBP
    out_webp, tel_webp = ConversionEngine.process_conversion(png_bytes, target_format="WEBP", quality=80)
    assert tel_webp["targetFormat"] == "WEBP"
    assert out_webp is not None

def test_compression_engine():
    png_bytes = create_dummy_png(500, 500)
    out_bytes, tel = CompressionEngine.compress_image(png_bytes, target_size_kb=50, quality=75, target_format="WEBP")
    assert len(out_bytes) > 0
    assert tel["compressedSize"] > 0
    assert tel["compressionPercentage"] >= 0

def test_pdf_studio_operations():
    png1 = create_dummy_png(200, 200)
    png2 = create_dummy_jpg(200, 200)
    
    # Create PDF from images
    pdf_bytes, _ = PDFConverter.images_to_pdf([png1, png2], page_size="A4")
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")

    # Extract PDF to images
    images, tel = PDFConverter.pdf_to_images(pdf_bytes, target_format="PNG", dpi=100)
    assert len(images) == 2

    # Rotate PDF
    rotated_pdf = PDFService.rotate_pages(pdf_bytes, degrees=90, page_indices=[0])
    assert len(rotated_pdf) > 0

    # Compress PDF
    comp_pdf, comp_tel = PDFService.compress_pdf(pdf_bytes)
    assert len(comp_pdf) > 0
    assert "compressionPercentage" in comp_tel

def test_office_service():
    # Markdown -> DOCX
    md = "# Title\n\n- Bullet 1\n- Bullet 2"
    docx_bytes = OfficeConversionService.markdown_to_docx(md)
    assert len(docx_bytes) > 0

    # DOCX -> Markdown
    extracted_md = OfficeConversionService.docx_to_markdown(docx_bytes)
    assert "Title" in extracted_md
    assert "Bullet 1" in extracted_md

    # DOCX -> PDF
    pdf_out = OfficeConversionService.docx_to_pdf(docx_bytes)
    assert pdf_out.startswith(b"%PDF")

def test_ocr_service():
    # Simple test image
    img = Image.new("RGB", (200, 100), (255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    
    res = OCRService.process_ocr(buf.getvalue(), is_pdf=False, language="eng")
    assert "text" in res
    assert "confidence" in res

def test_document_intelligence():
    text = "INVOICE #INV-2026-991\nDate: 2026-10-03\nVendor: Acme Corp\nTotal: $12,450.00"
    res = DocumentIntelligenceService.analyze_document(text)
    assert res["documentType"] == "invoice"
    assert res["entities"]["invoiceNumber"] == "INV-2026-991"
    assert res["entities"]["total"] == 12450.0

def test_enhancement_and_image_processing():
    img_bytes = create_dummy_jpg(100, 100)
    
    res_clahe, tel_clahe = EnhancementService.enhance_image(img_bytes, mode="lowlight", intensity=1.2)
    assert len(res_clahe) > 0
    assert "mode" in tel_clahe

    res_filtered = ImageService.apply_filters(img_bytes, brightness=1.1, contrast=1.2)
    assert len(res_filtered) > 0

def test_ai_prompt_assistant():
    res = AIEngine.enhance_prompt("cyberpunk city street", style="photorealistic")
    assert "cyberpunk" in res["enhancedPrompt"].lower()
    assert "photorealistic" in res["enhancedPrompt"].lower()

def test_benchmark_service():
    img1 = create_dummy_jpg(100, 100)
    img2 = create_dummy_jpg(100, 100)
    metrics = BenchmarkService.evaluate_quality(img1, img2)
    assert "psnr" in metrics
    assert "ssim" in metrics
    assert "mse" in metrics
