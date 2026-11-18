import io
import time
from typing import Dict, Any, Tuple, List, Optional
try:
    import pymupdf as fitz
except ImportError:
    import fitz

from PIL import Image

try:
    import pypdf
except ImportError:
    pypdf = None

class PDFConverter:
    """
    High-performance PDF conversion engine:
    - Images to PDF with layout (A4, Letter, Auto), margins, compression
    - PDF to Images (PNG, JPG, WEBP, TIFF) with configurable DPI
    - PDF to Text / Extract images
    """

    PAGE_SIZES = {
        "A4": (595.28, 841.89),
        "A3": (841.89, 1190.55),
        "A5": (419.53, 595.28),
        "Letter": (612.0, 792.0),
        "Legal": (612.0, 1008.0),
        "Auto": None
    }

    @classmethod
    def images_to_pdf(
        cls,
        image_bytes_list: List[bytes],
        page_size: str = "A4",
        orientation: str = "portrait", # 'portrait', 'landscape', 'auto'
        dpi: int = 300,
        margin_pt: float = 20.0
    ) -> Tuple[bytes, Dict[str, Any]]:
        start_time = time.time()
        doc = fitz.open()

        for img_bytes in image_bytes_list:
            img = Image.open(io.BytesIO(img_bytes))
            img_w, img_h = img.size

            if page_size == "Auto" or page_size not in cls.PAGE_SIZES or cls.PAGE_SIZES[page_size] is None:
                # Page matches image dimension in points (72 points = 1 inch)
                pw = (img_w / dpi) * 72.0
                ph = (img_h / dpi) * 72.0
            else:
                std_w, std_h = cls.PAGE_SIZES[page_size]
                if orientation == "landscape" or (orientation == "auto" and img_w > img_h):
                    pw, ph = max(std_w, std_h), min(std_w, std_h)
                else:
                    pw, ph = min(std_w, std_h), max(std_w, std_h)

            page = doc.new_page(width=pw, height=ph)

            # Fit image within page bounds considering margin
            usable_w = pw - (margin_pt * 2)
            usable_h = ph - (margin_pt * 2)

            scale = min(usable_w / img_w, usable_h / img_h)
            draw_w = img_w * scale
            draw_h = img_h * scale

            x0 = margin_pt + (usable_w - draw_w) / 2
            y0 = margin_pt + (usable_h - draw_h) / 2
            rect = fitz.Rect(x0, y0, x0 + draw_w, y0 + draw_h)

            page.insert_image(rect, stream=img_bytes)

        pdf_bytes = doc.tobytes(garbage=4, deflate=True)
        doc.close()
        duration_ms = int((time.time() - start_time) * 1000)

        telemetry = {
            "pageCount": len(image_bytes_list),
            "convertedSize": len(pdf_bytes),
            "conversionTimeMs": duration_ms,
            "targetFormat": "PDF"
        }
        return pdf_bytes, telemetry

    @classmethod
    def pdf_to_images(
        cls,
        pdf_bytes: bytes,
        target_format: str = "PNG",
        dpi: int = 200,
        pages: Optional[List[int]] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Converts PDF pages to images at high DPI."""
        start_time = time.time()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_count = len(doc)
        results = []

        target_pages = pages if pages else list(range(page_count))
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)

        for p_num in target_pages:
            if 0 <= p_num < page_count:
                page = doc.load_page(p_num)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img_data = pix.tobytes(target_format.lower() if target_format.lower() in ("png", "jpg", "jpeg") else "png")
                results.append({
                    "pageIndex": p_num,
                    "pageNumber": p_num + 1,
                    "width": pix.width,
                    "height": pix.height,
                    "data": img_data,
                    "format": target_format.upper(),
                    "sizeBytes": len(img_data)
                })

        doc.close()
        duration_ms = int((time.time() - start_time) * 1000)

        telemetry = {
            "pageCount": len(results),
            "totalPagesInPdf": page_count,
            "dpi": dpi,
            "conversionTimeMs": duration_ms
        }
        return results, telemetry

    @classmethod
    def extract_text(cls, pdf_bytes: bytes) -> str:
        """Extract plain text from PDF."""
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_pages = []
        for i, page in enumerate(doc):
            text_pages.append(f"--- Page {i + 1} ---\n" + page.get_text())
        doc.close()
        return "\n\n".join(text_pages)
