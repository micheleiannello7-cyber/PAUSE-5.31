"""One-off: regenerate three icons in high quality from the user's reference
screenshots (glossy blue/violet 3D family): paw (Animali), four-point star
(Qualsiasi argomento), stack of three books (Mini lezioni).

Run:  python generate_icons_2026.py [paw|star|books ...]
Raw output → memory/icons_2026/<name>.raw.png (kept for review, no processing).
"""
import asyncio
import base64
import io
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

from PIL import Image, ImageOps  # noqa: E402
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent  # noqa: E402

MODEL = "gemini-3.1-flash-image-preview"
REF_DIR = ROOT.parent / "memory" / "icons_2026"

STYLE = (
    "Recreate the object in this low-resolution reference screenshot as a premium, "
    "ultra-high-quality 3D app icon. Keep the SAME shape, proportions, colours and "
    "camera angle as the reference, but render it crisp and flawless: smooth glossy "
    "glass-like surfaces, saturated gradient from bright cyan-blue to deep violet, "
    "soft studio lighting with subtle specular highlights, clean sharp edges. "
    "Single object, perfectly centred on a pure black (#000000) background, no text, "
    "no floor, no shadow on the ground, no extra elements, square 1:1 composition, "
    "generous empty black margin around the object (object fills about 60% of the frame). "
)
ICONS = {
    "paw": (
        "crop_paw.jpg",
        STYLE + "The object: a dog paw print made of five smooth rounded pads (one large "
        "heart-shaped palm pad below, four oval toe pads above), inflated glossy 3D, "
        "blue on top fading to violet at the bottom. No dog, no text.",
    ),
    "star": (
        "crop_star.jpg",
        STYLE + "The object: a slender four-pointed star (sparkle) with a taller vertical "
        "axis, faceted crystal-like surfaces with a crease along both axes, translucent "
        "glowing cyan-blue on the left fading to violet-magenta on the right, subtle soft "
        "luminous glow around it. No text.",
    ),
    "books": (
        "crop_books.jpg",
        STYLE + "The object: a neat stack of three closed hardcover books seen from a "
        "three-quarter top angle: top book blue-violet with a tiny embossed square emblem "
        "on the cover, middle book bright cyan-teal, bottom book deep indigo-blue; visible "
        "light cream page edges, glossy covers. No text on the books.",
    ),
}


async def generate(name: str) -> None:
    ref_file, prompt = ICONS[name]
    ref_b64 = base64.b64encode((REF_DIR / ref_file).read_bytes()).decode("utf-8")
    chat = LlmChat(
        api_key=os.getenv("EMERGENT_LLM_KEY"),
        session_id=f"icon-2026-{name}",
        system_message="You are a world-class 3D icon illustrator.",
    ).with_model("gemini", MODEL).with_params(modalities=["image", "text"])
    _, images = await chat.send_message_multimodal_response(UserMessage(text=prompt, file_contents=[ImageContent(ref_b64)]))
    if not images:
        raise RuntimeError(f"no image returned for {name}")
    raw = base64.b64decode(images[0]["data"])
    image = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    out = REF_DIR / f"{name}.raw.png"
    image.save(out)
    print("saved", out, image.size, flush=True)


async def main():
    names = sys.argv[1:] or list(ICONS)
    for name in names:
        await generate(name)


if __name__ == "__main__":
    asyncio.run(main())
