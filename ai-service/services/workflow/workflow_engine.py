import io
import time
from typing import Dict, Any, List, Tuple
from services.conversion.conversion_engine import ConversionEngine
from services.image.image_service import ImageService
from services.enhancement.enhancement_service import EnhancementService
from services.jobs.job_manager import JobManager

class WorkflowEngine:
    """
    Visual Workflow Execution Engine:
    Sequentially processes assets through configurable step pipelines.
    Example: Upload -> Resize -> Remove Background -> Convert -> Compress -> Watermark -> ZIP
    """

    PRESETS = {
        "ecommerce": [
            {"type": "remove_background", "params": {"replacementColor": "#FFFFFF"}},
            {"type": "resize", "params": {"width": 1000, "height": 1000, "keepAspectRatio": True}},
            {"type": "convert", "params": {"targetFormat": "WEBP", "quality": 85}},
            {"type": "compress", "params": {"targetSizeKb": 300}}
        ],
        "social_media": [
            {"type": "resize", "params": {"width": 1080, "height": 1080, "keepAspectRatio": False}},
            {"type": "enhance", "params": {"mode": "auto", "intensity": 1.2}},
            {"type": "convert", "params": {"targetFormat": "JPG", "quality": 90}}
        ],
        "print_ready": [
            {"type": "upscale", "params": {"scaleFactor": 2}},
            {"type": "convert", "params": {"targetFormat": "PDF", "dpi": 300}}
        ]
    }

    @classmethod
    def execute_pipeline(
        cls,
        file_bytes: bytes,
        filename: str,
        pipeline_steps: List[Dict[str, Any]]
    ) -> Tuple[bytes, str, List[Dict[str, Any]]]:
        current_bytes = file_bytes
        current_name = filename
        step_logs = []

        for step in pipeline_steps:
            s_type = step.get("type")
            params = step.get("params", {})
            start_step = time.time()

            try:
                if s_type == "remove_background":
                    current_bytes = ImageService.remove_background(
                        current_bytes,
                        replacement_color=params.get("replacementColor")
                    )
                elif s_type == "resize":
                    out_bytes, _ = ConversionEngine.process_conversion(
                        current_bytes,
                        target_format="PNG",
                        width=params.get("width"),
                        height=params.get("height"),
                        keep_aspect_ratio=params.get("keepAspectRatio", True)
                    )
                    current_bytes = out_bytes
                elif s_type == "convert":
                    target_fmt = params.get("targetFormat", "WEBP")
                    out_bytes, _ = ConversionEngine.process_conversion(
                        current_bytes,
                        target_format=target_fmt,
                        quality=params.get("quality", 85)
                    )
                    current_bytes = out_bytes
                    base_name = current_name.rsplit(".", 1)[0]
                    current_name = f"{base_name}.{target_fmt.lower()}"
                elif s_type == "compress":
                    out_bytes, _ = ConversionEngine.process_conversion(
                        current_bytes,
                        target_format="WEBP",
                        quality=params.get("quality", 80),
                        target_size_kb=params.get("targetSizeKb")
                    )
                    current_bytes = out_bytes
                elif s_type == "watermark":
                    current_bytes = ImageService.apply_watermark(
                        current_bytes,
                        text=params.get("text", "WATERMARK"),
                        opacity=params.get("opacity", 0.4),
                        position=params.get("position", "bottom-right")
                    )
                elif s_type == "enhance":
                    out_bytes, _ = EnhancementService.enhance_image(
                        current_bytes,
                        mode=params.get("mode", "auto"),
                        intensity=params.get("intensity", 1.0)
                    )
                    current_bytes = out_bytes
                elif s_type == "upscale":
                    out_bytes, _ = EnhancementService.upscale(
                        current_bytes,
                        scale_factor=params.get("scaleFactor", 2)
                    )
                    current_bytes = out_bytes

                step_logs.append({
                    "step": s_type,
                    "status": "SUCCESS",
                    "durationMs": int((time.time() - start_step) * 1000)
                })
            except Exception as e:
                step_logs.append({
                    "step": s_type,
                    "status": "ERROR",
                    "error": str(e),
                    "durationMs": int((time.time() - start_step) * 1000)
                })

        return current_bytes, current_name, step_logs
