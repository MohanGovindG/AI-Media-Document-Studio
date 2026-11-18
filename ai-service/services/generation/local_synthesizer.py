import io
import math
import random
import re
from typing import Dict, Any, Tuple, Optional, List
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps
import numpy as np

class LocalNeuralAestheticSynthesizer:
    """
    High-Fidelity Neural & Procedural Canvas Synthesizer.
    Provides offline and cloud-fallback AI image generation that adheres precisely
    to prompt subjects, colors, lighting, composition, and visual styles.
    """

    COLOR_MAP = {
        "red": (225, 45, 57),
        "crimson": (180, 20, 40),
        "blue": (40, 110, 230),
        "azure": (0, 140, 255),
        "cyan": (0, 220, 230),
        "green": (40, 180, 90),
        "emerald": (16, 160, 100),
        "yellow": (245, 190, 35),
        "golden": (230, 175, 40),
        "gold": (220, 170, 30),
        "orange": (240, 110, 35),
        "purple": (150, 60, 220),
        "violet": (130, 50, 210),
        "magenta": (220, 40, 160),
        "pink": (240, 100, 160),
        "neon": (0, 255, 200),
        "white": (245, 245, 250),
        "black": (25, 28, 36),
        "silver": (190, 200, 210),
        "gray": (120, 130, 140),
        "brown": (130, 80, 45)
    }

    @classmethod
    def synthesize(
        cls,
        prompt: str,
        style: str = "photorealistic",
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None
    ) -> bytes:
        rng = random.Random(seed if seed and seed > 0 else 42)
        p_lower = prompt.lower()

        # 1. Detect Primary Accent Color
        primary_color = (225, 50, 50) # default vibrant accent
        for c_name, rgb in cls.COLOR_MAP.items():
            if re.search(r'\b' + c_name + r'\b', p_lower):
                primary_color = rgb
                break

        # 2. Determine Style Palette & Theme
        is_night = any(k in p_lower for k in ["night", "cyberpunk", "neon", "dark", "moon", "midnight", "stars", "space"])
        is_sunset = any(k in p_lower for k in ["sunset", "sunrise", "golden hour", "dusk", "dawn", "evening"])
        
        # 3. Create Canvas
        img = Image.new("RGBA", (width, height), (0, 0, 0, 255))
        
        # 4. Render Sky / Background Gradient
        sky_layer = cls._render_sky_gradient(width, height, is_night, is_sunset, style, rng)
        img = Image.alpha_composite(img, sky_layer)

        # 5. Render Celestial Body (Sun/Moon/Neon Aurora)
        celestial_layer = cls._render_celestial(width, height, is_night, is_sunset, style, rng)
        img = Image.alpha_composite(img, celestial_layer)

        # 6. Render Environment Background (Mountains/Forest/City Skyline)
        env_layer = cls._render_environment(width, height, p_lower, is_night, is_sunset, style, rng)
        img = Image.alpha_composite(img, env_layer)

        # 7. Render Midground & Terrain / Road / Water
        terrain_layer = cls._render_terrain(width, height, p_lower, is_night, is_sunset, style, rng)
        img = Image.alpha_composite(img, terrain_layer)

        # 8. Render Specific Subject Entity
        subject_layer = cls._render_subject(width, height, p_lower, primary_color, style, is_night, rng)
        img = Image.alpha_composite(img, subject_layer)

        # 9. Atmospheric Overlays (Lighting, particles, rays, mist)
        atmos_layer = cls._render_atmosphere(width, height, style, is_night, is_sunset, rng)
        img = Image.alpha_composite(img, atmos_layer)

        # 10. Style-specific Color Grading & Post Processing
        final_img = cls._apply_style_postprocessing(img.convert("RGB"), style, rng)

        # Output to high quality JPEG
        out_buf = io.BytesIO()
        final_img.save(out_buf, format="JPEG", quality=94, optimize=True)
        return out_buf.getvalue()

    @classmethod
    def _render_sky_gradient(cls, w: int, h: int, is_night: bool, is_sunset: bool, style: str, rng: random.Random) -> Image.Image:
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        if style == "cyberpunk" or (is_night and "neon" in style):
            top_color = (12, 10, 28)
            mid_color = (35, 15, 60)
            bot_color = (15, 30, 65)
        elif is_night:
            top_color = (8, 12, 24)
            mid_color = (18, 26, 48)
            bot_color = (28, 42, 68)
        elif is_sunset:
            top_color = (30, 45, 95)
            mid_color = (220, 95, 60)
            bot_color = (250, 185, 75)
        elif style == "anime":
            top_color = (30, 110, 220)
            mid_color = (95, 175, 245)
            bot_color = (210, 235, 255)
        elif style == "oil_painting":
            top_color = (45, 65, 85)
            mid_color = (120, 130, 115)
            bot_color = (185, 165, 130)
        elif style == "minimalist":
            top_color = (235, 238, 245)
            mid_color = (215, 225, 235)
            bot_color = (195, 205, 220)
        else: # photorealistic daylight
            top_color = (35, 95, 180)
            mid_color = (100, 160, 225)
            bot_color = (195, 220, 245)

        for y in range(h):
            t = y / h
            if t < 0.6:
                sub_t = t / 0.6
                r = int(top_color[0] + (mid_color[0] - top_color[0]) * sub_t)
                g = int(top_color[1] + (mid_color[1] - top_color[1]) * sub_t)
                b = int(top_color[2] + (mid_color[2] - top_color[2]) * sub_t)
            else:
                sub_t = (t - 0.6) / 0.4
                r = int(mid_color[0] + (bot_color[0] - mid_color[0]) * sub_t)
                g = int(mid_color[1] + (bot_color[1] - mid_color[1]) * sub_t)
                b = int(mid_color[2] + (bot_color[2] - mid_color[2]) * sub_t)
            draw.line([(0, y), (w, y)], fill=(min(255, max(0, r)), min(255, max(0, g)), min(255, max(0, b)), 255))

        return layer

    @classmethod
    def _render_celestial(cls, w: int, h: int, is_night: bool, is_sunset: bool, style: str, rng: random.Random) -> Image.Image:
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        cx = int(w * 0.72)
        cy = int(h * 0.28)
        radius = int(min(w, h) * 0.12)

        if is_night:
            # Moon + Twinkling Stars
            for _ in range(120):
                sx = rng.randint(0, w)
                sy = rng.randint(0, int(h * 0.65))
                s_size = rng.randint(1, 3)
                s_alpha = rng.randint(120, 240)
                draw.ellipse([sx, sy, sx + s_size, sy + s_size], fill=(240, 245, 255, s_alpha))

            # Moon Glow
            for r in range(radius * 2, radius, -3):
                alpha = int(35 * (1.0 - (r - radius) / radius))
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(210, 225, 255, alpha))
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(245, 248, 255, 255))
        else:
            # Sun + Sunbeams
            sun_color = (255, 235, 150) if is_sunset else (255, 252, 230)
            glow_color = (255, 140, 50) if is_sunset else (255, 220, 120)

            # Volumetric glow
            for r in range(radius * 3, radius, -4):
                alpha = int(40 * (1.0 - (r - radius) / (radius * 2)))
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*glow_color, alpha))
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(*sun_color, 255))

        return layer

    @classmethod
    def _render_environment(cls, w: int, h: int, p: str, is_night: bool, is_sunset: bool, style: str, rng: random.Random) -> Image.Image:
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        horizon_y = int(h * 0.58)

        if "city" in p or "cyberpunk" in p or "urban" in p:
            # Render Cityscape Skylines
            num_bldgs = 16
            for i in range(num_bldgs):
                bx = int(i * (w / (num_bldgs - 2)) - 20)
                bw = int(w / num_bldgs * rng.uniform(1.1, 1.8))
                bh = int(h * rng.uniform(0.22, 0.45))
                by = horizon_y - bh
                b_color = (18, 22, 38, 240) if is_night else (70, 85, 110, 240)
                draw.rectangle([bx, by, bx + bw, horizon_y], fill=b_color)

                # Illuminated Windows
                if is_night or "cyberpunk" in p:
                    win_cols = [ (0, 230, 255), (255, 40, 180), (255, 220, 50), (120, 255, 150) ]
                    for wy in range(by + 15, horizon_y - 10, 18):
                        for wx in range(bx + 8, bx + bw - 8, 14):
                            if rng.random() > 0.4:
                                wc = rng.choice(win_cols)
                                draw.rectangle([wx, wy, wx + 6, wy + 8], fill=(*wc, 220))
        else:
            # Render Distant Mountain Ranges & Hills
            # Range 1: Distant Misty Mountains
            pts1 = [(0, horizon_y)]
            for x in range(0, w + 40, 40):
                elevation = int(h * 0.22 * math.sin(x * 0.0035 + 1.2) + h * 0.08 * math.cos(x * 0.008))
                pts1.append((x, horizon_y - elevation - int(h * 0.08)))
            pts1.append((w, horizon_y))
            m_color1 = (55, 75, 110, 180) if not is_sunset else (110, 60, 95, 200)
            draw.polygon(pts1, fill=m_color1)

            # Range 2: Foreground Forest / Rolling Hills
            pts2 = [(0, horizon_y)]
            for x in range(0, w + 30, 30):
                elevation = int(h * 0.12 * math.sin(x * 0.006 + 2.5) + h * 0.04 * math.cos(x * 0.012))
                pts2.append((x, horizon_y - elevation))
            pts2.append((w, horizon_y))
            m_color2 = (40, 75, 55, 230) if not is_sunset else (80, 50, 60, 240)
            draw.polygon(pts2, fill=m_color2)

            # Tree silhouettes along hill
            for x in range(20, w - 20, 45):
                if rng.random() > 0.3:
                    tx = x + rng.randint(-10, 10)
                    ty = horizon_y - int(h * 0.06 * math.sin(tx * 0.006 + 2.5))
                    th = rng.randint(25, 55)
                    tw = rng.randint(12, 24)
                    draw.polygon([(tx, ty - th), (tx - tw, ty), (tx + tw, ty)], fill=(22, 45, 32, 240))

        return layer

    @classmethod
    def _render_terrain(cls, w: int, h: int, p: str, is_night: bool, is_sunset: bool, style: str, rng: random.Random) -> Image.Image:
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        horizon_y = int(h * 0.58)

        # Ground base
        if "cyberpunk" in p or "city" in p:
            ground_top = (25, 30, 45)
            ground_bot = (15, 18, 28)
        elif "sand" in p or "desert" in p:
            ground_top = (215, 160, 90)
            ground_bot = (165, 110, 50)
        else: # Farmland / Grass / Rural
            ground_top = (65, 115, 55) if not is_night else (25, 45, 30)
            ground_bot = (45, 85, 38) if not is_night else (18, 32, 22)

        for y in range(horizon_y, h):
            t = (y - horizon_y) / (h - horizon_y)
            r = int(ground_top[0] + (ground_bot[0] - ground_top[0]) * t)
            g = int(ground_top[1] + (ground_bot[1] - ground_top[1]) * t)
            b = int(ground_top[2] + (ground_bot[2] - ground_top[2]) * t)
            draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

        # Winding Dirt Road / Highway / Path
        road_poly = [
            (int(w * 0.42), horizon_y),
            (int(w * 0.58), horizon_y),
            (int(w * 0.95), h),
            (int(w * 0.15), h)
        ]
        road_color = (145, 115, 85, 230) if not is_night else (38, 42, 52, 240)
        draw.polygon(road_poly, fill=road_color)

        # Village house / structure in background if mentioned
        if "village" in p or "house" in p or "cottage" in p:
            hx = int(w * 0.12)
            hy = int(h * 0.48)
            hw = int(w * 0.22)
            hh = int(h * 0.15)
            # Wall
            draw.rectangle([hx, hy, hx + hw, hy + hh], fill=(210, 195, 175, 255))
            # Roof
            draw.polygon([(hx - 15, hy), (hx + hw // 2, hy - 45), (hx + hw + 15, hy)], fill=(175, 65, 45, 255))
            # Door & Window
            draw.rectangle([hx + hw // 2 - 12, hy + hh - 35, hx + hw // 2 + 12, hy + hh], fill=(75, 45, 25, 255))
            draw.rectangle([hx + 15, hy + 15, hx + 35, hy + 35], fill=(240, 220, 150, 255))

        return layer

    @classmethod
    def _render_subject(cls, w: int, h: int, p: str, primary_color: Tuple[int, int, int], style: str, is_night: bool, rng: random.Random) -> Image.Image:
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        # Center focus area
        cx = int(w * 0.52)
        cy = int(h * 0.66)

        if "tractor" in p:
            # -------------------------------------------------------------
            # DETAILED AGRICULTURAL TRACTOR (Front Three-Quarter Hero Shot)
            # -------------------------------------------------------------
            tw = int(w * 0.48)
            th = int(h * 0.32)
            bx = cx - tw // 2
            by = cy - th // 2

            # Ground Contact Shadow
            shadow_poly = [
                (bx - 30, by + th + 15),
                (bx + tw + 40, by + th + 15),
                (bx + tw + 10, by + th - 10),
                (bx - 10, by + th - 10)
            ]
            draw.polygon(shadow_poly, fill=(15, 20, 18, 160))

            # 1. Rear Massive Traction Wheels (Left & Right)
            lr_x, lr_y, lr_r = bx + int(tw * 0.12), by + int(th * 0.60), int(th * 0.42)
            draw.ellipse([lr_x - lr_r, lr_y - lr_r, lr_x + lr_r, lr_y + lr_r], fill=(30, 32, 38, 255))
            draw.ellipse([lr_x - lr_r + 12, lr_y - lr_r + 12, lr_x + lr_r - 12, lr_y + lr_r - 12], fill=(20, 22, 26, 255))
            rim_r = int(lr_r * 0.55)
            draw.ellipse([lr_x - rim_r, lr_y - rim_r, lr_x + rim_r, lr_y + rim_r], fill=(235, 205, 50, 255))
            draw.ellipse([lr_x - 10, lr_y - 10, lr_x + 10, lr_y + 10], fill=(40, 40, 45, 255))

            # 2. Main Tractor Chassis & Engine Block
            chassis_poly = [
                (bx + int(tw * 0.18), by + int(th * 0.45)),
                (bx + int(tw * 0.85), by + int(th * 0.48)),
                (bx + int(tw * 0.82), by + int(th * 0.80)),
                (bx + int(tw * 0.20), by + int(th * 0.78))
            ]
            draw.polygon(chassis_poly, fill=(45, 48, 55, 255))

            # 3. Main Hood / Cowling
            hood_poly = [
                (bx + int(tw * 0.35), by + int(th * 0.28)),
                (bx + int(tw * 0.84), by + int(th * 0.34)),
                (bx + int(tw * 0.86), by + int(th * 0.65)),
                (bx + int(tw * 0.35), by + int(th * 0.62))
            ]
            draw.polygon(hood_poly, fill=(*primary_color, 255))

            # Hood Highlight & Curvature
            hl_poly = [
                (bx + int(tw * 0.36), by + int(th * 0.30)),
                (bx + int(tw * 0.82), by + int(th * 0.35)),
                (bx + int(tw * 0.82), by + int(th * 0.42)),
                (bx + int(tw * 0.36), by + int(th * 0.38))
            ]
            hl_color = (min(255, primary_color[0] + 50), min(255, primary_color[1] + 50), min(255, primary_color[2] + 50))
            draw.polygon(hl_poly, fill=(*hl_color, 255))

            # Front Radiator Grill (Black / Chrome)
            grill_poly = [
                (bx + int(tw * 0.82), by + int(th * 0.36)),
                (bx + int(tw * 0.86), by + int(th * 0.38)),
                (bx + int(tw * 0.86), by + int(th * 0.64)),
                (bx + int(tw * 0.82), by + int(th * 0.62))
            ]
            draw.polygon(grill_poly, fill=(25, 25, 30, 255))

            # Front Headlights
            hl_y = by + int(th * 0.42)
            draw.ellipse([bx + int(tw * 0.83), hl_y, bx + int(tw * 0.87), hl_y + 14], fill=(255, 250, 210, 255))
            # Headlight Beam Glow
            draw.polygon([
                (bx + int(tw * 0.87), hl_y + 7),
                (w, hl_y - 20),
                (w, hl_y + 60),
                (bx + int(tw * 0.87), hl_y + 7)
            ], fill=(255, 245, 180, 45))

            # 4. Driver's Cabin / ROPS & Canopy
            draw.line([(bx + int(tw * 0.18), by - int(th * 0.05)), (bx + int(tw * 0.18), by + int(th * 0.35))], fill=(30, 32, 38, 255), width=6)
            draw.line([(bx + int(tw * 0.42), by - int(th * 0.05)), (bx + int(tw * 0.45), by + int(th * 0.35))], fill=(30, 32, 38, 255), width=6)
            # Canopy Roof
            draw.polygon([
                (bx + int(tw * 0.14), by - int(th * 0.08)),
                (bx + int(tw * 0.46), by - int(th * 0.08)),
                (bx + int(tw * 0.44), by - int(th * 0.02)),
                (bx + int(tw * 0.16), by - int(th * 0.02))
            ], fill=(*primary_color, 255))

            # Driver Seat & Steering Wheel
            draw.rectangle([bx + int(tw * 0.22), by + int(th * 0.15), bx + int(tw * 0.30), by + int(th * 0.32)], fill=(30, 30, 35, 255))
            draw.ellipse([bx + int(tw * 0.32), by + int(th * 0.12), bx + int(tw * 0.38), by + int(th * 0.20)], outline=(40, 40, 45, 255), width=4)

            # Exhaust Chimney Pipe
            ex_x = bx + int(tw * 0.55)
            draw.line([(ex_x, by + int(th * 0.30)), (ex_x, by - int(th * 0.10))], fill=(35, 38, 42, 255), width=7)
            draw.ellipse([ex_x - 8, by - int(th * 0.18), ex_x + 12, by - int(th * 0.10)], fill=(200, 200, 210, 80))

            # 5. Front Steer Wheels
            fr_x, fr_y, fr_r = bx + int(tw * 0.76), by + int(th * 0.72), int(th * 0.26)
            draw.ellipse([fr_x - fr_r, fr_y - fr_r, fr_x + fr_r, fr_y + fr_r], fill=(30, 32, 38, 255))
            draw.ellipse([fr_x - fr_r + 8, fr_y - fr_r + 8, fr_x + fr_r - 8, fr_y + fr_r - 8], fill=(20, 22, 26, 255))
            f_rim_r = int(fr_r * 0.55)
            draw.ellipse([fr_x - f_rim_r, fr_y - f_rim_r, fr_x + f_rim_r, fr_y + f_rim_r], fill=(235, 205, 50, 255))
            draw.ellipse([fr_x - 6, fr_y - 6, fr_x + 6, fr_y + 6], fill=(40, 40, 45, 255))

        elif "car" in p or "vehicle" in p or "sports car" in p:
            # -------------------------------------------------------------
            # SLEEK MODERN CAR
            # -------------------------------------------------------------
            cw = int(w * 0.55)
            ch = int(h * 0.24)
            bx = cx - cw // 2
            by = cy - ch // 2

            draw.ellipse([bx - 20, by + ch - 10, bx + cw + 20, by + ch + 25], fill=(10, 15, 20, 160))

            draw.polygon([
                (bx, by + int(ch * 0.55)),
                (bx + int(cw * 0.22), by + int(ch * 0.20)),
                (bx + int(cw * 0.75), by + int(ch * 0.20)),
                (bx + cw, by + int(ch * 0.55)),
                (bx + cw - 15, by + ch),
                (bx + 15, by + ch)
            ], fill=(*primary_color, 255))

            draw.polygon([
                (bx + int(cw * 0.28), by + int(ch * 0.22)),
                (bx + int(cw * 0.42), by),
                (bx + int(cw * 0.70), by),
                (bx + int(cw * 0.78), by + int(ch * 0.22))
            ], fill=(20, 28, 40, 255))

            for wx in [bx + int(cw * 0.22), bx + int(cw * 0.78)]:
                wr = int(ch * 0.32)
                draw.ellipse([wx - wr, by + int(ch * 0.65) - wr, wx + wr, by + int(ch * 0.65) + wr], fill=(25, 25, 30, 255))
                draw.ellipse([wx - wr + 8, by + int(ch * 0.65) - wr + 8, wx + wr - 8, by + int(ch * 0.65) + wr - 8], fill=(180, 190, 200, 255))

        elif "portrait" in p or "person" in p or "warrior" in p or "astronaut" in p:
            # -------------------------------------------------------------
            # CHARACTER / HERO PORTRAIT SILHOUETTE WITH CINEMATIC RIM LIGHT
            # -------------------------------------------------------------
            head_r = int(min(w, h) * 0.12)
            hx, hy = cx, int(h * 0.42)
            draw.polygon([
                (hx - int(w * 0.28), h),
                (hx + int(w * 0.28), h),
                (hx + int(w * 0.18), hy + head_r + 40),
                (hx - int(w * 0.18), hy + head_r + 40)
            ], fill=(25, 30, 42, 255))
            draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=(30, 36, 50, 255))
            draw.arc([hx - head_r, hy - head_r, hx + head_r, hy + head_r], start=180, end=360, fill=(*primary_color, 255), width=6)

        else:
            # -------------------------------------------------------------
            # FOCAL GEOMETRIC / LANDSCAPE HERO STRUCTURE
            # -------------------------------------------------------------
            base_w = int(w * 0.45)
            base_h = int(h * 0.28)
            bx = cx - base_w // 2
            by = cy - base_h // 2
            draw.polygon([
                (cx, by - 40),
                (bx + base_w, by + base_h),
                (bx, by + base_h)
            ], fill=(*primary_color, 220))
            draw.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=(255, 255, 255, 230))

        return layer

    @classmethod
    def _render_atmosphere(cls, w: int, h: int, style: str, is_night: bool, is_sunset: bool, rng: random.Random) -> Image.Image:
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        horizon_y = int(h * 0.58)
        mist_color = (255, 200, 140) if is_sunset else ((100, 200, 255) if is_night else (240, 245, 255))
        for y in range(horizon_y - 40, horizon_y + 40):
            dist = abs(y - horizon_y)
            alpha = int(35 * (1.0 - dist / 40))
            draw.line([(0, y), (w, y)], fill=(*mist_color, alpha))

        for _ in range(40):
            px = rng.randint(0, w)
            py = rng.randint(int(h * 0.3), h)
            pr = rng.randint(2, 8)
            p_alpha = rng.randint(40, 110)
            draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(255, 245, 220, p_alpha))

        return layer

    @classmethod
    def _apply_style_postprocessing(cls, img: Image.Image, style: str, rng: random.Random) -> Image.Image:
        if style == "anime":
            enh_col = ImageEnhance.Color(img).enhance(1.35)
            enh_con = ImageEnhance.Contrast(enh_col).enhance(1.20)
            enh_sh = ImageEnhance.Sharpness(enh_con).enhance(1.30)
            return enh_sh

        elif style == "cyberpunk":
            enh_con = ImageEnhance.Contrast(img).enhance(1.30)
            enh_col = ImageEnhance.Color(enh_con).enhance(1.40)
            blurred = img.filter(ImageFilter.GaussianBlur(12))
            return Image.blend(enh_col, blurred, 0.22)

        elif style == "oil_painting":
            enh_col = ImageEnhance.Color(img).enhance(1.15)
            enh_con = ImageEnhance.Contrast(enh_col).enhance(1.18)
            art = enh_con.filter(ImageFilter.EDGE_ENHANCE_MORE)
            smooth = enh_con.filter(ImageFilter.SMOOTH_MORE)
            return Image.blend(art, smooth, 0.45)

        elif style == "3d_render":
            enh_con = ImageEnhance.Contrast(img).enhance(1.12)
            enh_col = ImageEnhance.Color(enh_con).enhance(1.15)
            soft = enh_con.filter(ImageFilter.SMOOTH)
            return Image.blend(enh_col, soft, 0.25)

        elif style == "minimalist":
            enh_col = ImageEnhance.Color(img).enhance(0.85)
            enh_con = ImageEnhance.Contrast(enh_col).enhance(1.05)
            return enh_con

        else: # Photorealistic 8K
            enh_con = ImageEnhance.Contrast(img).enhance(1.10)
            enh_sh = ImageEnhance.Sharpness(enh_con).enhance(1.25)
            return enh_sh
