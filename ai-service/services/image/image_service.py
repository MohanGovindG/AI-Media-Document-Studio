import io
import math
from typing import Dict, Any, Tuple, Optional
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont
import numpy as np
try:
    import cv2
except ImportError:
    cv2 = None

class ImageService:
    """
    Image operations: filters, background removal, watermark overlay, transformations, and presets.
    """

    @classmethod
    def apply_filters(
        cls,
        image_bytes: bytes,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        sharpness: float = 1.0,
        blur_radius: float = 0.0,
        filter_preset: Optional[str] = None
    ) -> bytes:
        img = Image.open(io.BytesIO(image_bytes))

        # Color adjustments
        if brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(brightness)
        if contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(contrast)
        if saturation != 1.0:
            img = ImageEnhance.Color(img).enhance(saturation)
        if sharpness != 1.0:
            img = ImageEnhance.Sharpness(img).enhance(sharpness)
        if blur_radius > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

        # Filter presets
        if filter_preset == "grayscale":
            img = img.convert("L").convert("RGB")
        elif filter_preset == "sepia":
            # Apply sepia matrix
            img_rgb = img.convert("RGB")
            np_img = np.array(img_rgb, dtype=np.float32)
            sepia_matrix = np.array([
                [0.393, 0.769, 0.189],
                [0.349, 0.686, 0.168],
                [0.272, 0.534, 0.131]
            ])
            sepia_img = np.dot(np_img, sepia_matrix.T)
            sepia_img = np.clip(sepia_img, 0, 255).astype(np.uint8)
            img = Image.fromarray(sepia_img)
        elif filter_preset == "vintage":
            img = ImageEnhance.Contrast(img).enhance(0.9)
            img = ImageEnhance.Color(img).enhance(0.8)
        elif filter_preset == "vivid":
            img = ImageEnhance.Contrast(img).enhance(1.2)
            img = ImageEnhance.Color(img).enhance(1.4)
            img = ImageEnhance.Sharpness(img).enhance(1.3)

        out_buf = io.BytesIO()
        img.save(out_buf, format="PNG")
        return out_buf.getvalue()

    @classmethod
    def remove_background(
        cls,
        image_bytes: bytes,
        replacement_color: Optional[str] = None # None = transparent PNG, or hex like "#FFFFFF"
    ) -> bytes:
        """
        AI & Computer Vision background removal using saliency detection & GrabCut alpha matting.
        """
        # Load image with OpenCV
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Invalid image for background removal")

        h, w = img.shape[:2]

        # GrabCut initialization
        mask = np.zeros(img.shape[:2], np.uint8)
        bgdModel = np.zeros((1, 65), np.float64)
        fgdModel = np.zeros((1, 65), np.float64)

        # Margin rect for foreground
        margin_x = int(w * 0.05)
        margin_y = int(h * 0.05)
        rect = (margin_x, margin_y, w - 2 * margin_x, h - 2 * margin_y)

        try:
            cv2.grabCut(img, mask, rect, bgdModel, fgdModel, 4, cv2.GC_INIT_WITH_RECT)
            mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
        except Exception:
            # Fallback luminance / color thresholding
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, mask2 = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
            mask2 = (mask2 / 255).astype('uint8')

        # Smooth alpha mask
        alpha_mask = cv2.GaussianBlur(mask2.astype(np.float32) * 255, (7, 7), 0)
        alpha_mask = np.clip(alpha_mask, 0, 255).astype(np.uint8)

        # Convert to RGBA
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        rgba = cv2.merge([img_rgb[:, :, 0], img_rgb[:, :, 1], img_rgb[:, :, 2], alpha_mask])

        pil_img = Image.fromarray(rgba, mode="RGBA")

        if replacement_color:
            hex_col = replacement_color.lstrip("#")
            bg_rgb = tuple(int(hex_col[i:i+2], 16) for i in (0, 2, 4)) if len(hex_col) == 6 else (255, 255, 255)
            bg_layer = Image.new("RGBA", pil_img.size, (*bg_rgb, 255))
            bg_layer.paste(pil_img, mask=pil_img.split()[3])
            pil_img = bg_layer.convert("RGB")

        out_buf = io.BytesIO()
        pil_img.save(out_buf, format="PNG")
        return out_buf.getvalue()

    @classmethod
    def apply_watermark(
        cls,
        image_bytes: bytes,
        text: Optional[str] = None,
        watermark_image_bytes: Optional[bytes] = None,
        opacity: float = 0.5,
        position: str = "bottom-right", # 'center', 'top-left', 'top-right', 'bottom-left', 'bottom-right', 'tiled'
        font_size: int = 36,
        color_hex: str = "#FFFFFF",
        rotation_deg: float = 0
    ) -> bytes:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))

        if text:
            draw = ImageDraw.Draw(overlay)
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None

            hex_col = color_hex.lstrip("#")
            rgb = tuple(int(hex_col[i:i+2], 16) for i in (0, 2, 4)) if len(hex_col) == 6 else (255, 255, 255)
            fill_color = (*rgb, int(opacity * 255))

            if position == "tiled":
                step_x = 250
                step_y = 150
                for x in range(0, img.width, step_x):
                    for y in range(0, img.height, step_y):
                        draw.text((x, y), text, fill=fill_color, font=font)
            else:
                # Calculate coordinates
                bbox = draw.textbbox((0, 0), text, font=font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                pad = 20

                if position == "center":
                    x, y = (img.width - tw) // 2, (img.height - th) // 2
                elif position == "top-left":
                    x, y = pad, pad
                elif position == "top-right":
                    x, y = img.width - tw - pad, pad
                elif position == "bottom-left":
                    x, y = pad, img.height - th - pad
                else: # bottom-right
                    x, y = img.width - tw - pad, img.height - th - pad

                draw.text((x, y), text, fill=fill_color, font=font)

        elif watermark_image_bytes:
            wm_img = Image.open(io.BytesIO(watermark_image_bytes)).convert("RGBA")
            # Apply opacity to alpha channel
            r, g, b, a = wm_img.split()
            a = a.point(lambda p: int(p * opacity))
            wm_img = Image.merge("RGBA", (r, g, b, a))

            if position == "center":
                x, y = (img.width - wm_img.width) // 2, (img.height - wm_img.height) // 2
            elif position == "top-left":
                x, y = 20, 20
            elif position == "top-right":
                x, y = img.width - wm_img.width - 20, 20
            elif position == "bottom-left":
                x, y = 20, img.height - wm_img.height - 20
            else:
                x, y = img.width - wm_img.width - 20, img.height - wm_img.height - 20

            overlay.paste(wm_img, (max(0, x), max(0, y)), mask=wm_img)

        result = Image.alpha_composite(img, overlay)
        out_buf = io.BytesIO()
        result.save(out_buf, format="PNG")
        return out_buf.getvalue()
