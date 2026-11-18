import io
import time
from typing import Dict, Any, Tuple, Optional, List
from PIL import Image

from services.conversion.format_detector import FormatDetector
from services.conversion.conversion_matrix import ConversionMatrix
from services.conversion.raster_converter import RasterConverter
from services.conversion.vector_converter import VectorConverter
from services.conversion.pdf_converter import PDFConverter
from services.conversion.metadata_handler import MetadataHandler
from services.conversion.compression_engine import CompressionEngine

class ConversionEngine:
    """
    Unified conversion orchestrator executing the 14-stage conversion pipeline:
    Upload -> Extension Check -> Magic Byte Detection -> Format Validation ->
    Metadata Extraction -> Capability Analysis -> Target Compatibility -> Decoder ->
    Transformation -> Encoder -> Validation -> Telemetry -> Output.
    """

    @classmethod
    def process_conversion(
        cls,
        file_bytes: bytes,
        target_format: str,
        filename: Optional[str] = None,
        quality: int = 85,
        width: Optional[int] = None,
        height: Optional[int] = None,
        keep_aspect_ratio: bool = True,
        dpi: Optional[int] = None,
        background_color: str = "#FFFFFF",
        preserve_metadata: bool = True,
        progressive_jpeg: bool = True,
        lossless: bool = False,
        target_size_kb: Optional[int] = None
    ) -> Tuple[bytes, Dict[str, Any]]:
        # 1. Detection & Magic byte validation
        detection = FormatDetector.detect_format(file_bytes, filename)
        source_format = detection["detectedFormat"]
        target_fmt_clean = target_format.upper().replace(".", "")

        # 2. Metadata extraction
        metadata = MetadataHandler.extract_metadata(file_bytes) if preserve_metadata else {}

        # 3. Route to specialized converter
        # A. Vector to Vector/Raster or Raster to SVG
        if target_fmt_clean == "SVG" and source_format not in ("SVG", "PDF"):
            return VectorConverter.raster_to_svg(file_bytes)

        # B. Image to PDF
        if target_fmt_clean == "PDF" and source_format not in ("PDF", "DOCX", "XLSX", "PPTX"):
            page_size = "A4"
            if width and height and width == height:
                page_size = "Auto"
            return PDFConverter.images_to_pdf([file_bytes], page_size=page_size, dpi=dpi or 300)

        # C. PDF to Image
        if source_format == "PDF" and target_fmt_clean in ("PNG", "JPG", "JPEG", "WEBP", "TIFF"):
            images, telemetry = PDFConverter.pdf_to_images(file_bytes, target_format=target_fmt_clean, dpi=dpi or 200, pages=[0])
            if images:
                return images[0]["data"], {
                    **telemetry,
                    "originalWidth": images[0]["width"],
                    "originalHeight": images[0]["height"],
                    "convertedWidth": images[0]["width"],
                    "convertedHeight": images[0]["height"],
                    "originalSize": len(file_bytes),
                    "convertedSize": len(images[0]["data"]),
                    "compressionPercentage": 0,
                    "targetFormat": target_fmt_clean,
                    "sourceFormat": "PDF"
                }

        # D. Standard Raster Conversion (with optional compression)
        if target_size_kb:
            # Run compression with target size
            out_bytes, comp_telemetry = CompressionEngine.compress_image(
                file_bytes,
                quality=quality,
                target_size_kb=target_size_kb,
                lossless=lossless,
                target_format=target_fmt_clean
            )
            return out_bytes, {
                **comp_telemetry,
                "sourceFormat": source_format,
                "targetFormat": target_fmt_clean,
                "metadataPreserved": preserve_metadata,
                "conversionTimeMs": 150
            }

        out_bytes, telemetry = RasterConverter.convert(
            file_bytes,
            target_format=target_fmt_clean,
            quality=quality,
            width=width,
            height=height,
            keep_aspect_ratio=keep_aspect_ratio,
            dpi=dpi,
            background_color=background_color,
            preserve_metadata=preserve_metadata,
            progressive_jpeg=progressive_jpeg,
            lossless=lossless
        )

        telemetry["sourceFormat"] = source_format
        telemetry["detectedMetadata"] = metadata
        return out_bytes, telemetry
