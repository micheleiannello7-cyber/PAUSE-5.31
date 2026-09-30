"""One-off: generate the 3D icons for the reader's intro CTAs ("Inizia a
leggere" → open book, "Ascolta" → headphones) in the exact visual language of
the colorful-3d-v3 category icons (chunky matte clay objects on black), then
key out the black studio background so they sit on the glass buttons.

Run once:  python generate_cta_icons.py
Output:    ../frontend/assets/images/kind-book.png, kind-headphones.png (512x512 RGBA)
"""
import asyncio
import base64
import io
import json
import os
from collections import deque
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

from PIL import Image, ImageOps, ImageFilter  # noqa: E402
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent  # noqa: E402

MODEL = "gemini-3.1-flash-image-preview"
SOURCES = json.loads((ROOT / "category_art_sources_v3.json").read_text())
STYLE_REF = SOURCES["sheet_url"]
OUT_DIR = ROOT.parent / "frontend" / "assets" / "images"

STYLE = (
    "Match this reference sheet EXACTLY in art direction: a single chunky, simple, "
    "matte clay-like 3D object, bold saturated flat colours, soft studio lighting, "
    "rounded smooth shapes, minimal detail, centred on a pure black (#000000) "
    "background, no text, no floor shadow, no glow, square 1:1 composition with "
    "generous empty black margin around the object. Output ONE object only. "
)
ICONS = {
    "kind-book.png": STYLE + (
        "The object: an open book seen from a slight three-quarter front angle, "
        "glossy saturated cyan-blue hard cover, thick cream pages fanned open, "
        "one page gently lifting mid-turn, representing starting to read."
    ),
    "kind-headphones.png": STYLE + (
        "The object: a pair of over-ear headphones seen from a three-quarter front "
        "angle, saturated violet-purple headband and ear cups with soft coral-orange "
        "ear cushions, representing listening to audio."
    ),
}


def key_out_background(image: Image.Image, tol: int = 40) -> Image.Image:
    """Flood-fill transparent from the four corners over near-background pixels."""
    img = image.convert("RGBA")
    w, h = img.size
    px = img.load()
    bg = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    br, bgc, bb = (sum(c[0] for c in bg) // 4, sum(c[1] for c in bg) // 4, sum(c[2] for c in bg) // 4)
    seen = bytearray(w * h)
    q = deque([(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)])
    mask = Image.new("L", (w, h), 255)
    mpx = mask.load()
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or seen[y * w + x]:
            continue
        seen[y * w + x] = 1
        r, g, b, _ = px[x, y]
        if abs(r - br) + abs(g - bgc) + abs(b - bb) > tol * 3:
            continue
        mpx[x, y] = 0
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    mask = mask.filter(ImageFilter.GaussianBlur(1.0))
    img.putalpha(mask)
    return img


def fit_square(img: Image.Image, size: int = 512, margin: float = 0.06) -> Image.Image:
    """Crop to the object's bounding box and centre it in a square canvas."""
    bbox = img.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if bbox:
        img = img.crop(bbox)
    side = int(max(img.size) * (1 + margin * 2))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - img.width) // 2, (side - img.height) // 2), img)
    return canvas.resize((size, size), Image.Resampling.LANCZOS)


async def generate(name: str, prompt: str, ref_b64: str) -> None:
    chat = LlmChat(
        api_key=os.getenv("EMERGENT_LLM_KEY"),
        session_id=f"cta-icon-{name}",
        system_message="You are a world-class 3D icon illustrator.",
    ).with_model("gemini", MODEL).with_params(modalities=["image", "text"])
    _, images = await chat.send_message_multimodal_response(UserMessage(text=prompt, file_contents=[ImageContent(ref_b64)]))
    if not images:
        raise RuntimeError(f"no image returned for {name}")
    raw = base64.b64decode(images[0]["data"])
    image = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    (ROOT / "media_cache").mkdir(exist_ok=True)
    image.save(ROOT / "media_cache" / f"cta-{name}.raw.png")
    out = fit_square(key_out_background(image))
    out.save(OUT_DIR / name, "PNG", optimize=True)
    print("saved", OUT_DIR / name, out.size)


async def main():
    ref_b64 = base64.b64encode(requests.get(STYLE_REF, timeout=60).content).decode("utf-8")
    for name, prompt in ICONS.items():
        await generate(name, prompt, ref_b64)


if __name__ == "__main__":
    asyncio.run(main())
