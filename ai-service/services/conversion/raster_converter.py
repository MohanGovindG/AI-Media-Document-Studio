import io
import time
from typing import Dict, Any, Tuple, Optional
from PIL import Image, ImageOps

class RasterConverter:
    """
    High-performance raster image conversion engine supporting 15+ formats,
    custom transparency background blending, DPI, resizing, and color mode translation.
    """

    FORMAT_MAP = {
        "JPG": "JPEG",
        "JPEG": "JPEG",
        "PNG": "PNG",
        "WEBP": "WEBP",
        "BMP": "BMP",
        "TIFF": "TIFF",
        "TIF": "TIFF",
        "GIF": "GIF",
        "ICO": "ICO",
        "TGA": "TGA",
        "JP2": "JPEG2000",
        "AVIF": "AVIF",
        "HEIC": "HEIF",
        "HEIF": "HEIF"
    }

    @classmethod
    def convert(
        cls,
        image_bytes: bytes,
        target_format: str,
        quality: int = 85,
        width: Optional[int] = None,
        height: Optional[int] = None,
        keep_aspect_ratio: bool = True,
        dpi: Optional[int] = None,
        background_color: str = "#FFFFFF",
        preserve_metadata: bool = True,
        progressive_jpeg: bool = True,
        lossless: bool = False
    ) -> Tuple[bytes, Dict[str, Any]]:
        start_time = time.time()
        orig_size = len(image_bytes)
        target_fmt_clean = target_format.upper().replace(".", "")
        pil_format = cls.FORMAT_MAP.get(target_fmt_clean, target_fmt_clean)

        # Open image
        img = Image.open(io.BytesIO(image_bytes))
        orig_w, orig_h = img.size
        orig_has_transparency = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)

        # Handle Orientation from EXIF if present
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Resizing
        if width or height:
            if keep_aspect_ratio:
                if width and height:
                    img.thumbnail((width, height), Image.Resampling.LANCZOS)
                elif width:
                    new_h = int(orig_h * (width / orig_w))
                    img = img.resize((width, new_h), Image.Resampling.LANCZOS)
                elif height:
                    new_w = int(orig_w * (height / orig_h))
                    img = img.resize((new_w, height), Image.Resampling.LANCZOS)
            else:
                target_w = width or orig_w
                target_h = height or orig_h
                img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

        converted_w, converted_h = img.size
        transparency_preserved = False

        # Handle color modes and transparency
        if pil_format in ("JPEG", "BMP", "JPEG2000"):
            # Target formats without alpha support -> Blend with background color
            if img.mode in ("RGBA", "LA", "P"):
                # Parse hex color
                hex_col = background_color.lstrip("#")
                if len(hex_col) == 6:
                    bg_rgb = tuple(int(hex_col[i:i+2], 16) for i in (0, 2, 4))
                else:
                    bg_rgb = (255, 255, 255)

                bg_image = Image.new("RGB", img.size, bg_rgb)
                if img.mode == "RGBA":
                    bg_image.paste(img, mask=img.split()[3])
                else:
                    bg_image.paste(img.convert("RGB"))
                img = bg_image
            elif img.mode != "RGB":
                img = img.convert("RGB")
        elif pil_format == "ICO":
            # Windows icon usually requires RGBA and square size (e.g. 256x256 max)
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            if img.width > 256 or img.height > 256:
                img.thumbnail((256, 256), Image.Resampling.LANCZOS)
                converted_w, converted_h = img.size
            transparency_preserved = True
        else:
            if orig_has_transparency:
                transparency_preserved = True
                if img.mode != "RGBA":
                    img = img.convert("RGBA")

        # Save buffer
        out_buf = io.BytesIO()
        save_params = {}

        if pil_format == "JPEG":
            save_params["quality"] = quality
            save_params["progressive"] = progressive_jpeg
            save_params["optimize"] = True
        elif pil_format == "WEBP":
            save_params["quality"] = quality
            save_params["lossless"] = lossless
            save_params["method"] = 6
        elif pil_format == "PNG":
            save_params["optimize"] = True
            save_params["compress_level"] = 6
        elif pil_format == "TIFF":
            save_params["compression"] = "tiff_lzw"

        if dpi:
            save_params["dpi"] = (dpi, dpi)

        if preserve_metadata and "exif" in img.info:
            save_params["exif"] = img.info["exif"]

        try:
            img.save(out_buf, format=pil_format, **save_params)
        except Exception:
            # Fallback for formats that might fail with some parameters
            img.convert("RGB").save(out_buf, format="JPEG", quality=quality)
            pil_format = "JPEG"

        converted_bytes = out_buf.getvalue()
        converted_size = len(converted_bytes)
        duration_ms = int((time.time() - start_time) * 1000)

        savings = max(0.0, round(((orig_size - converted_size) / orig_size) * 100, 2)) if orig_size > 0 else 0.0

        telemetry = {
            "originalWidth": orig_w,
            "originalHeight": orig_h,
            "convertedWidth": converted_w,
            "convertedHeight": converted_h,
            "originalSize": orig_size,
            "convertedSize": converted_size,
            "compressionPercentage": savings,
            "quality": quality,
            "metadataPreserved": preserve_metadata,
            "transparencyPreserved": transparency_preserved,
            "pageCount": 1,
            "frameCount": 1,
            "conversionTimeMs": duration_ms,
            "targetFormat": target_fmt_clean
        }

        return converted_bytes, telemetry
