import io
import time
from typing import Dict, Any, Tuple, List
from PIL import Image, ImageSequence

class AnimationConverter:
    """
    Handles animated formats (GIF, animated WEBP), extracting frames and converting sequences.
    """

    @classmethod
    def extract_frames(cls, image_bytes: bytes) -> List[Tuple[bytes, int]]:
        """Extracts individual frames with their durations."""
        img = Image.open(io.BytesIO(image_bytes))
        frames = []
        for i, frame in enumerate(ImageSequence.Iterator(img)):
            frame_img = frame.copy()
            duration = frame.info.get("duration", 100)
            buf = io.BytesIO()
            frame_img.save(buf, format="PNG")
            frames.append((buf.getvalue(), duration))
        return frames

    @classmethod
    def frames_to_animated(
        cls,
        frames_bytes: List[bytes],
        target_format: str = "WEBP", # 'GIF' or 'WEBP'
        duration_ms: int = 100,
        loop: int = 0
    ) -> Tuple[bytes, Dict[str, Any]]:
        start_time = time.time()
        fmt = target_format.upper()
        pil_frames = [Image.open(io.BytesIO(b)).convert("RGBA" if fmt == "WEBP" else "P") for b in frames_bytes]

        if not pil_frames:
            raise ValueError("No frames provided")

        out_buf = io.BytesIO()
        first_frame = pil_frames[0]

        if fmt == "GIF":
            first_frame.save(
                out_buf,
                format="GIF",
                save_all=True,
                append_images=pil_frames[1:],
                duration=duration_ms,
                loop=loop,
                optimize=True
            )
        else:
            first_frame.save(
                out_buf,
                format="WEBP",
                save_all=True,
                append_images=pil_frames[1:],
                duration=duration_ms,
                loop=loop,
                lossless=False,
                quality=80
            )

        data = out_buf.getvalue()
        telemetry = {
            "frameCount": len(pil_frames),
            "targetFormat": fmt,
            "convertedSize": len(data),
            "conversionTimeMs": int((time.time() - start_time) * 1000)
        }
        return data, telemetry
