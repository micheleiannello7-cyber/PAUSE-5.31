"""One-off: 3D glossy PAUSE mark (ring + two bars) replicating the user's mockup.
Output: frontend/assets/images/pause-mark.png (RGBA, black keyed to alpha via
luminance so the soft glow survives on the dark navy intro background).

Run:  python generate_pause_mark.py
"""
import asyncio
import base64
import io
import os
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

from PIL import Image, ImageOps  # noqa: E402
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent  # noqa: E402

MODEL = "gemini-3.1-flash-image-preview"
REF = ROOT.parent / "memory" / "icons_2026" / "mockup_logo.jpg"
RAW = ROOT.parent / "memory" / "icons_2026" / "pause_mark.raw.png"
OUT = ROOT.parent / "frontend" / "assets" / "images" / "pause-mark.png"

PROMPT = (
    "Recreate this app logo from the low-resolution reference as a flawless, ultra-high-quality "
    "3D glossy icon, identical in shape and colours. The logo: a thick perfectly circular ring "
    "(pause symbol) with a smooth saturated neon gradient running around it: vivid magenta-violet "
    "at the bottom-left, electric blue on the right, bright cyan at the top; inside the ring two "
    "vertical rounded pill-shaped bars (pause bars) with a glossy cyan-to-blue gradient, glowing. "
    "The ring and bars have soft, elegant luminous glow and subtle specular highlights, like "
    "polished glass neon. Inside the ring, between the bars, the area is pure black. Pure black "
    "(#000000) background, perfectly centred, square 1:1, the ring fills about 70% of the frame, "
    "no text, no other elements."
)


def black_to_alpha(image: Image.Image) -> Image.Image:
    """Additive-glow keying: alpha = max(R,G,B); colours un-premultiplied."""
    rgb = np.asarray(image.convert("RGB")).astype(np.float32)
    alpha = rgb.max(axis=2)
    alpha = np.clip((alpha - 6) * (255.0 / 249.0), 0, 255)
    safe = np.where(alpha > 0, alpha, 1.0)[..., None]
    out_rgb = np.clip(rgb * 255.0 / safe, 0, 255)
    rgba = np.dstack([out_rgb, alpha]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def fit_square(img: Image.Image, size: int = 768, margin: float = 0.10) -> Image.Image:
    bbox = img.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox()
    if bbox:
        img = img.crop(bbox)
    side = int(max(img.size) * (1 + margin * 2))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - img.width) // 2, (side - img.height) // 2), img)
    return canvas.resize((size, size), Image.Resampling.LANCZOS)


async def main():
    ref_b64 = base64.b64encode(REF.read_bytes()).decode("utf-8")
    chat = LlmChat(
        api_key=os.getenv("EMERGENT_LLM_KEY"),
        session_id="pause-mark-2026",
        system_message="You are a world-class 3D icon illustrator.",
    ).with_model("gemini", MODEL).with_params(modalities=["image", "text"])
    _, images = await chat.send_message_multimodal_response(UserMessage(text=PROMPT, file_contents=[ImageContent(ref_b64)]))
    if not images:
        raise RuntimeError("no image returned")
    raw = base64.b64decode(images[0]["data"])
    image = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    image.save(RAW)
    out = fit_square(black_to_alpha(image))
    out.save(OUT, "PNG", optimize=True)
    print("saved", OUT, out.size, OUT.stat().st_size, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
