import io
import time
from typing import Dict, Any, List, Optional, Tuple

try:
    import pymupdf as fitz
except ImportError:
    import fitz

try:
    import pypdf
except ImportError:
    pypdf = None

class PDFService:
    """
    Comprehensive PDF manipulation service:
    Merge, Split, Compress, Rotate, Reorder, Delete, Extract, Watermark, Password Protect.
    """

    @classmethod
    def merge_pdfs(cls, pdf_bytes_list: List[bytes]) -> bytes:
        doc = fitz.open()
        for b in pdf_bytes_list:
            sub = fitz.open(stream=b, filetype="pdf")
            doc.insert_pdf(sub)
            sub.close()
        out = doc.tobytes(garbage=4, deflate=True)
        doc.close()
        return out

    @classmethod
    def split_pdf(cls, pdf_bytes: bytes, page_ranges: List[str]) -> List[bytes]:
        """
        Splits PDF into multiple PDFs based on ranges (e.g. ['1-3', '4-5']).
        """
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        split_results = []

        for r in page_ranges:
            sub_doc = fitz.open()
            if "-" in r:
                start, end = map(int, r.split("-"))
                start_idx = max(0, start - 1)
                end_idx = min(total_pages, end)
                sub_doc.insert_pdf(doc, from_page=start_idx, to_page=end_idx - 1)
            else:
                p = int(r) - 1
                if 0 <= p < total_pages:
                    sub_doc.insert_pdf(doc, from_page=p, to_page=p)
            split_results.append(sub_doc.tobytes(garbage=4, deflate=True))
            sub_doc.close()

        doc.close()
        return split_results

    @classmethod
    def reorder_and_delete_pages(cls, pdf_bytes: bytes, page_indices: List[int]) -> bytes:
        """
        Reorders or deletes pages. page_indices contains 0-based indices in desired order.
        """
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        new_doc = fitz.open()

        for idx in page_indices:
            if 0 <= idx < len(doc):
                new_doc.insert_pdf(doc, from_page=idx, to_page=idx)

        out = new_doc.tobytes(garbage=4, deflate=True)
        new_doc.close()
        doc.close()
        return out

    @classmethod
    def rotate_pages(cls, pdf_bytes: bytes, degrees: int = 90, page_indices: Optional[List[int]] = None) -> bytes:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        target_indices = page_indices if page_indices is not None else list(range(len(doc)))

        for idx in target_indices:
            if 0 <= idx < len(doc):
                page = doc[idx]
                page.set_rotation((page.rotation + degrees) % 360)

        out = doc.tobytes(garbage=4, deflate=True)
        doc.close()
        return out

    @classmethod
    def compress_pdf(cls, pdf_bytes: bytes, image_quality: int = 70) -> Tuple[bytes, Dict[str, Any]]:
        start_time = time.time()
        orig_size = len(pdf_bytes)

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        # Deflate fonts and clean unused streams
        compressed = doc.tobytes(
            garbage=4,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True
        )
        doc.close()

        comp_size = len(compressed)
        savings = max(0.0, round(((orig_size - comp_size) / orig_size) * 100, 2)) if orig_size > 0 else 0.0

        telemetry = {
            "originalSize": orig_size,
            "convertedSize": comp_size,
            "compressionPercentage": savings,
            "processingTimeMs": int((time.time() - start_time) * 1000)
        }
        return compressed, telemetry

    @classmethod
    def watermark_pdf(cls, pdf_bytes: bytes, text: str = "CONFIDENTIAL", opacity: float = 0.3, font_size: int = 40) -> bytes:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            rect = page.rect
            center_x = rect.width / 2
            center_y = rect.height / 2
            # Offset point so text is visually centered
            text_len = len(text)
            approx_width = text_len * font_size * 0.28
            p = fitz.Point(center_x - approx_width, center_y)
            morph_pivot = fitz.Point(center_x, center_y)
            morph = (morph_pivot, fitz.Matrix(45))
            
            try:
                page.insert_text(
                    p,
                    text,
                    fontsize=font_size,
                    morph=morph,
                    color=(0.6, 0.6, 0.6),
                    overlay=True
                )
            except Exception:
                # Fallback to standard 0-deg insertion if morph not supported in old PyMuPDF
                page.insert_text(
                    fitz.Point(center_x - approx_width, center_y),
                    text,
                    fontsize=font_size,
                    color=(0.6, 0.6, 0.6),
                    overlay=True
                )
        out = doc.tobytes(garbage=4, deflate=True)
        doc.close()
        return out

    @classmethod
    def protect_pdf(cls, pdf_bytes: bytes, user_password: str, owner_password: Optional[str] = None) -> bytes:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        writer = pypdf.PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        writer.encrypt(user_password=user_password, owner_pwd=owner_password or user_password)
        out_buf = io.BytesIO()
        writer.write(out_buf)
        return out_buf.getvalue()
