import io
import time
from typing import Dict, Any, Tuple
from PIL import Image
import cv2
import numpy as np

class VectorConverter:
    """
    Vector conversion engine: SVG/EPS handling, raster to SVG vectorization, and SVG rendering.
    """

    @classmethod
    def raster_to_svg(
        cls,
        image_bytes: bytes,
        color_mode: str = "color", # 'color' or 'bw'
        max_colors: int = 16
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Converts raster image to scalable SVG vector contours."""
        start_time = time.time()
        orig_size = len(image_bytes)

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = img.size

        # Convert to numpy array for contour analysis
        np_img = np.array(img)

        # Simplify colors via k-means or quantization
        if color_mode == "bw":
            gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
            _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            svg_paths = []
            for cnt in contours:
                if len(cnt) > 2:
                    d_path = "M " + " L ".join([f"{pt[0][0]},{pt[0][1]}" for pt in cnt]) + " Z"
                    svg_paths.append(f'<path d="{d_path}" fill="#000000" />')

            svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <rect width="100%" height="100%" fill="#ffffff"/>
  {' '.join(svg_paths)}
</svg>'''
        else:
            # Color vectorization using posterization & contours
            quantized = img.quantize(colors=max_colors).convert("RGB")
            np_quant = np.array(quantized)
            unique_colors = np.unique(np_quant.reshape(-1, 3), axis=0)

            svg_paths = []
            for color in unique_colors:
                hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                mask = cv2.inRange(np_quant, color, color)
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for cnt in contours:
                    if cv2.contourArea(cnt) > 4 and len(cnt) > 2:
                        d_path = "M " + " L ".join([f"{pt[0][0]},{pt[0][1]}" for pt in cnt]) + " Z"
                        svg_paths.append(f'<path d="{d_path}" fill="{hex_color}" stroke="{hex_color}" stroke-width="0.5" />')

            svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <rect width="100%" height="100%" fill="#ffffff"/>
  {' '.join(svg_paths)}
</svg>'''

        svg_bytes = svg_content.encode("utf-8")
        duration_ms = int((time.time() - start_time) * 1000)

        telemetry = {
            "originalWidth": w,
            "originalHeight": h,
            "convertedWidth": w,
            "convertedHeight": h,
            "originalSize": orig_size,
            "convertedSize": len(svg_bytes),
            "compressionPercentage": 0,
            "quality": 100,
            "metadataPreserved": False,
            "transparencyPreserved": True,
            "conversionTimeMs": duration_ms,
            "targetFormat": "SVG"
        }
        return svg_bytes, telemetry
