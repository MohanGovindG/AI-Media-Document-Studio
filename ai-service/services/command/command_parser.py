import re
from typing import Dict, Any, List

class AICommandParser:
    """
    AI Command Parser & Smart Routing:
    Parses natural language user intentions into structured operation execution plans
    and provides Smart Convert preset optimization.
    """

    SMART_USE_CASES = {
        "website": {
            "title": "Website / Web Performance",
            "format": "WEBP",
            "quality": 82,
            "targetSizeKb": 250,
            "lossless": False,
            "description": "Optimized for ultra-fast web loading with excellent visual clarity."
        },
        "mobile": {
            "title": "Mobile App / iOS & Android",
            "format": "AVIF",
            "quality": 80,
            "targetSizeKb": 150,
            "lossless": False,
            "description": "Maximum data compression for high-density mobile displays."
        },
        "print": {
            "title": "High-Quality Printing",
            "format": "PDF",
            "quality": 100,
            "dpi": 300,
            "description": "300 DPI high-resolution CMYK print-ready document."
        },
        "social_media": {
            "title": "Social Media (Instagram/LinkedIn/X)",
            "format": "JPG",
            "quality": 92,
            "width": 1080,
            "height": 1080,
            "description": "Square 1080x1080 crisp JPEG with vibrant color profiles."
        },
        "ecommerce": {
            "title": "E-Commerce Product Listing",
            "format": "WEBP",
            "removeBg": True,
            "bgColor": "#FFFFFF",
            "width": 1200,
            "height": 1200,
            "quality": 88,
            "description": "Clean white background product shot compliant with Amazon & Shopify."
        },
        "max_quality": {
            "title": "Maximum Lossless Quality / Archival",
            "format": "PNG",
            "quality": 100,
            "lossless": True,
            "preserveMetadata": True,
            "description": "Pixel-perfect lossless conversion preserving all EXIF & color profiles."
        },
        "smallest_size": {
            "title": "Smallest File Size / Email Attachment",
            "format": "WEBP",
            "quality": 65,
            "targetSizeKb": 100,
            "description": "Aggressive size reduction tailored for email attachments and quick sharing."
        }
    }

    @classmethod
    def parse_command(cls, query: str) -> Dict[str, Any]:
        """
        Parses freeform prompt into structured operations, target module, and arguments.
        """
        q = query.lower()

        # 1. Background removal
        if any(k in q for k in ["remove background", "no background", "transparent", "cutout", "bg removal"]):
            return {
                "intent": "REMOVE_BACKGROUND",
                "module": "image/background-remover",
                "action": "Remove Background",
                "explanation": "Detected request to isolate foreground subject and eliminate background.",
                "suggestedParams": {"replacementColor": None}
            }

        # 2. PDF Creation or Image to PDF
        if any(k in q for k in ["to pdf", "make pdf", "turn into pdf", "create pdf", "convert to pdf"]):
            return {
                "intent": "CONVERT_TO_PDF",
                "module": "pdf/studio",
                "action": "Generate PDF Document",
                "explanation": "Routing to PDF Studio for document compilation.",
                "suggestedParams": {"pageSize": "A4", "dpi": 300}
            }

        # 3. Upscaling
        if any(k in q for k in ["upscale", "super resolution", "enlarge", "2x", "4x", "8x"]):
            scale = 4 if "4x" in q else (8 if "8x" in q else 2)
            return {
                "intent": "UPSCALE",
                "module": "image/upscaler",
                "action": f"Upscale Image {scale}x",
                "explanation": f"Detected Super-Resolution request for {scale}x enlargement.",
                "suggestedParams": {"scaleFactor": scale}
            }

        # 4. Compression
        if any(k in q for k in ["compress", "reduce size", "smaller", "kb", "mb"]):
            kb_match = re.search(r'(\d+)\s*kb', q)
            target_kb = int(kb_match.group(1)) if kb_match else 500
            return {
                "intent": "COMPRESS",
                "module": "image/compressor",
                "action": f"Compress Under {target_kb} KB",
                "explanation": f"Optimizing image size with target limit {target_kb} KB.",
                "suggestedParams": {"targetSizeKb": target_kb, "quality": 80}
            }

        # 5. OCR
        if any(k in q for k in ["ocr", "extract text", "read text", "tables from pdf", "scan text"]):
            export_fmt = "XLSX" if "excel" in q or "table" in q else "DOCX"
            return {
                "intent": "OCR_EXTRACTION",
                "module": "document/ocr",
                "action": "Optical Character Recognition",
                "explanation": f"Extracting text/tables with export to {export_fmt}.",
                "suggestedParams": {"exportFormat": export_fmt}
            }

        # 6. AI Generation
        if any(k in q for k in ["generate", "create image", "paint", "draw", "render", "ai image"]):
            return {
                "intent": "AI_GENERATE",
                "module": "ai/generator",
                "action": "Generate AI Image",
                "explanation": "Synthesizing custom imagery with neural diffusion.",
                "suggestedParams": {"prompt": query, "style": "photorealistic"}
            }

        # 7. Format conversion (e.g. to webp, to png, to jpg, to avif)
        for fmt in ["WEBP", "PNG", "JPG", "JPEG", "AVIF", "SVG", "TIFF", "DOCX", "XLSX", "PPTX"]:
            if f"to {fmt.lower()}" in q or f"{fmt.lower()}" in q:
                return {
                    "intent": "CONVERT_FORMAT",
                    "module": "image/converter",
                    "action": f"Convert to {fmt}",
                    "explanation": f"Routing file conversion to {fmt} format.",
                    "suggestedParams": {"targetFormat": fmt, "quality": 85}
                }

        # Default fallback
        return {
            "intent": "SMART_CONVERT",
            "module": "image/converter",
            "action": "Smart Image & Document Pipeline",
            "explanation": "Analyzed query. Ready to process files with automated presets.",
            "suggestedParams": {"targetFormat": "WEBP", "quality": 85}
        }
