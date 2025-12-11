"""Generate a simple architecture PNG using Pillow.

This script creates `docs/architecture.png` as a raster version of the
diagram previously stored as SVG. It is intentionally dependency-light
and uses the default font (Pillow must be installed in the active
environment).

Usage (from repo root):
    .\.venv\Scripts\Activate.ps1; python scripts\generate_architecture_png.py
"""

from PIL import Image, ImageDraw, ImageFont
import os


def draw():
    w, h = 900, 420
    bg = (255, 255, 255)
    stroke = (43, 108, 176)
    text_color = (11, 43, 74)

    img = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arial.ttf", 16)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        font_title = ImageFont.load_default()
        font_small = ImageFont.load_default()

    def rect(x, y, ww, hh):
        d.rectangle([x, y, x + ww, y + hh], outline=stroke, width=2, fill=bg)

    # Client
    rect(40, 40, 160, 60)
    d.text((120, 55), "Client", fill=text_color, anchor="mm", font=font_title)
    d.text((120, 74), "(browser, curl, tests)", fill=text_color, anchor="mm", font=font_small)

    # API
    rect(320, 30, 240, 80)
    d.text((440, 45), "API", fill=text_color, anchor="mm", font=font_title)
    d.text((440, 66), "FastAPI + Uvicorn", fill=text_color, anchor="mm", font=font_small)
    d.text((440, 86), "JWT auth (env JWT_SECRET)", fill=text_color, anchor="mm", font=font_small)

    # Mongo
    rect(640, 20, 220, 120)
    d.text((750, 35), "MongoDB", fill=text_color, anchor="mm", font=font_title)
    d.text((750, 56), "master_db + per-tenant collections", fill=text_color, anchor="mm", font=font_small)

    # master_db details
    rect(660, 110, 180, 110)
    d.text((750, 130), "master_db", fill=text_color, anchor="mm", font=font_small)
    d.text((750, 150), "• organizations (metadata)", fill=text_color, anchor="mm", font=font_small)
    d.text((750, 170), "• admins (hashed pw)", fill=text_color, anchor="mm", font=font_small)

    # per-org collections
    rect(640, 250, 220, 100)
    d.text((750, 275), "org_acme", fill=text_color, anchor="mm", font=font_small)
    d.text((750, 295), "org_otherorg", fill=text_color, anchor="mm", font=font_small)
    d.text((750, 315), "(per-tenant collections)", fill=text_color, anchor="mm", font=font_small)

    # arrows
    def arrow(x1, y1, x2, y2):
        d.line((x1, y1, x2, y2), fill=stroke, width=3)
        # arrowhead
        ax = x2
        ay = y2
        # simple arrowhead triangle
        triangle = [(ax, ay), (ax - 8, ay - 5), (ax - 8, ay + 5)]
        d.polygon(triangle, fill=stroke)

    arrow(200, 70, 320, 70)
    arrow(560, 70, 640, 70)
    arrow(560, 110, 660, 110)
    arrow(560, 280, 640, 280)

    # label
    d.text((380, 20), "Runtime data flow", fill=text_color, font=font_small)

    out_dir = os.path.join("docs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "architecture.png")
    img.save(out_path)
    print("Wrote", out_path)


if __name__ == "__main__":
    draw()
