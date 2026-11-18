import io
from typing import Dict, Any, Tuple, Optional
from PIL import Image

class CompressionEngine:
    """
    Intelligent image compression engine with target-size search, quality optimization,
    and telemetry calculation.
    """

    @classmethod
    def compress_image(
        cls,
        image_bytes: bytes,
        quality: int = 80,
        target_size_kb: Optional[int] = None,
        lossless: bool = False,
        target_format: str = "WEBP"
    ) -> Tuple[bytes, Dict[str, Any]]:
        fmt = target_format.upper()
        if fmt == "JPG":
            fmt = "JPEG"

        orig_size = len(image_bytes)
        img = Image.open(io.BytesIO(image_bytes))

        # Handle RGBA for JPEG
        if fmt == "JPEG" and img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                bg.paste(img, mask=img.split()[3])
            else:
                bg.paste(img.convert("RGB"))
            img = bg
        elif img.mode not in ("RGB", "RGBA", "L"):
            img = img.convert("RGBA" if "A" in img.mode else "RGB")

        # If target_size_kb is specified, binary search quality
        if target_size_kb and target_size_kb > 0 and fmt in ("JPEG", "WEBP", "AVIF"):
            target_bytes = target_size_kb * 1024
            low, high = 10, 95
            best_bytes = None
            best_quality = quality

            for _ in range(7):  # Binary search steps
                mid = (low + high) // 2
                buf = io.BytesIO()
                save_kwargs = {"quality": mid, "optimize": True}
                if fmt == "WEBP":
                    save_kwargs["lossless"] = lossless
                img.save(buf, format=fmt, **save_kwargs)
                data = buf.getvalue()

                if len(data) <= target_bytes:
                    best_bytes = data
                    best_quality = mid
                    low = mid + 1
                else:
                    high = mid - 1

            if best_bytes is not None:
                output_bytes = best_bytes
                actual_quality = best_quality
            else:
                buf = io.BytesIO()
                img.save(buf, format=fmt, quality=15, optimize=True)
                output_bytes = buf.getvalue()
                actual_quality = 15
        else:
            buf = io.BytesIO()
            save_kwargs = {"optimize": True}
            if fmt in ("JPEG", "WEBP"):
                save_kwargs["quality"] = quality
            if fmt == "WEBP":
                save_kwargs["lossless"] = lossless
            elif fmt == "PNG":
                save_kwargs["compress_level"] = 9 if lossless else 6

            img.save(buf, format=fmt, **save_kwargs)
            output_bytes = buf.getvalue()
            actual_quality = quality

        compressed_size = len(output_bytes)
        savings = max(0.0, round(((orig_size - compressed_size) / orig_size) * 100, 2)) if orig_size > 0 else 0.0

        telemetry = {
            "originalSize": orig_size,
            "convertedSize": compressed_size,
            "compressedSize": compressed_size,
            "compressionPercentage": savings,
            "quality": actual_quality,
            "width": img.width,
            "height": img.height,
            "format": fmt
        }
        return output_bytes, telemetry
