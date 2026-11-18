import io
import re
from typing import Dict, Any, Optional
from PIL import Image

class FormatDetector:
    """
    Production-grade magic-byte and capability detection for images and documents.
    Never trusts file extensions alone.
    """

    MAGIC_SIGNATURES = [
        # (format, category, signature_checker_func)
        ("PNG", "RASTER", lambda b: b.startswith(b"\x89PNG\r\n\x1a\n")),
        ("JPEG", "RASTER", lambda b: b.startswith(b"\xff\xd8\xff")),
        ("GIF", "ANIMATION", lambda b: b.startswith(b"GIF87a") or b.startswith(b"GIF89a")),
        ("PDF", "DOCUMENT", lambda b: b.startswith(b"%PDF")),
        ("TIFF", "RASTER", lambda b: b.startswith(b"II*\x00") or b.startswith(b"MM\x00*")),
        ("WEBP", "RASTER", lambda b: len(b) >= 12 and b[:4] == b"RIFF" and b[8:12] == b"WEBP"),
        ("BMP", "RASTER", lambda b: b.startswith(b"BM")),
        ("ICO", "RASTER", lambda b: b.startswith(b"\x00\x00\x01\x00")),
        ("JP2", "RASTER", lambda b: b.startswith(b"\x00\x00\x00\x0c\x6a\x50\x20\x20") or b.startswith(b"\xff\x4f\xff\x51")),
        ("EPS", "VECTOR", lambda b: b.startswith(b"%!PS-Adobe") or b.startswith(b"\xc5\xd0\xd3\xc6")),
        ("HEIC", "HIGH_EFFICIENCY", lambda b: len(b) >= 12 and b[4:8] == b"ftyp" and b[8:12] in [b"heic", b"heix", b"hevc", b"heim", b"mif1"]),
        ("HEIF", "HIGH_EFFICIENCY", lambda b: len(b) >= 12 and b[4:8] == b"ftyp" and b[8:12] in [b"heif", b"heis"]),
        ("AVIF", "HIGH_EFFICIENCY", lambda b: len(b) >= 12 and b[4:8] == b"ftyp" and b[8:12] in [b"avif", b"avis"]),
        ("ZIP_DOCX_XLSX_PPTX", "DOCUMENT", lambda b: b.startswith(b"PK\x03\x04")),
    ]

    @classmethod
    def detect_svg(cls, byte_content: bytes) -> bool:
        """Inspects byte content for valid XML SVG structure."""
        prefix = byte_content[:1024].lower()
        if b"<svg" in prefix or (b"<?xml" in prefix and b"<svg" in byte_content[:4096].lower()):
            return True
        return False

    @classmethod
    def detect_format(cls, byte_content: bytes, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Inspect the actual file header bytes to determine format, dimensions, transparency, etc.
        """
        if not byte_content or len(byte_content) == 0:
            return {
                "detectedFormat": "UNKNOWN",
                "category": "UNKNOWN",
                "confidence": 0.0,
                "width": 0,
                "height": 0,
                "hasTransparency": False,
                "error": "Empty file content"
            }

        detected_format = "UNKNOWN"
        category = "UNKNOWN"
        confidence = 0.0

        # Check binary magic signatures
        for fmt, cat, checker in cls.MAGIC_SIGNATURES:
            try:
                if checker(byte_content):
                    detected_format = fmt
                    category = cat
                    confidence = 1.0
                    break
            except Exception:
                continue

        # Check SVG
        if detected_format == "UNKNOWN" and cls.detect_svg(byte_content):
            detected_format = "SVG"
            category = "VECTOR"
            confidence = 1.0

        # Handle Office zip-based files (DOCX, XLSX, PPTX)
        if detected_format == "ZIP_DOCX_XLSX_PPTX":
            if filename:
                ext = filename.split(".")[-1].upper()
                if ext in ["DOCX", "XLSX", "PPTX"]:
                    detected_format = ext
                else:
                    detected_format = "DOCX"
            else:
                detected_format = "DOCX"
            category = "DOCUMENT"

        # Fallback to extension check if binary signature was obscure (e.g., TGA)
        if detected_format == "UNKNOWN" and filename:
            ext = filename.split(".")[-1].upper()
            if ext in ["TGA", "TIF", "JPG", "DOC", "XLS", "PPT", "TXT", "CSV", "JSON", "RTF", "MD"]:
                detected_format = "JPEG" if ext == "JPG" else ("TIFF" if ext == "TIF" else ext)
                category = "DOCUMENT" if ext in ["DOC", "XLS", "PPT", "TXT", "CSV", "JSON", "RTF", "MD"] else "RASTER"
                confidence = 0.65

        # Extract metadata, dimensions, and transparency
        width = 0
        height = 0
        has_transparency = False
        frame_count = 1
        page_count = 1
        color_mode = "RGB"

        if category in ["RASTER", "ANIMATION", "HIGH_EFFICIENCY"]:
            try:
                with Image.open(io.BytesIO(byte_content)) as img:
                    width, height = img.size
                    color_mode = img.mode
                    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                        has_transparency = True
                    if getattr(img, "is_animated", False):
                        frame_count = getattr(img, "n_frames", 1)
            except Exception:
                pass
        elif detected_format == "PDF":
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(byte_content))
                page_count = len(reader.pages)
                if page_count > 0:
                    box = reader.pages[0].mediabox
                    width = int(box.width)
                    height = int(box.height)
            except Exception:
                pass
        elif detected_format == "SVG":
            try:
                # Try to parse width/height from SVG attributes
                text = byte_content[:2048].decode("utf-8", errors="ignore")
                w_match = re.search(r'width=["\']?(\d+)', text)
                h_match = re.search(r'height=["\']?(\d+)', text)
                if w_match and h_match:
                    width = int(w_match.group(1))
                    height = int(h_match.group(1))
                else:
                    width, height = 800, 600
                has_transparency = True
            except Exception:
                width, height = 800, 600
                has_transparency = True

        return {
            "detectedFormat": detected_format,
            "category": category,
            "confidence": confidence,
            "width": width,
            "height": height,
            "hasTransparency": has_transparency,
            "frameCount": frame_count,
            "pageCount": page_count,
            "colorMode": color_mode,
            "fileSizeBytes": len(byte_content)
        }
