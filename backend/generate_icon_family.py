"""Candidates: the other 11 category icons re-rendered in the glossy blue→violet
glass family (same language as the new paw / star). Review only — nothing is
integrated until approved.

Run:  python generate_icon_family.py [ids...]
Raw   → memory/icons_2026/family/<id>.raw.png
Keyed → backend/category_art/candidates/<id>.png (RGBA, black → alpha)
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
from generate_pause_mark import black_to_alpha, fit_square  # noqa: E402

MODEL = "gemini-3.1-flash-image-preview"
RAW_DIR = ROOT.parent / "memory" / "icons_2026" / "family"
OUT_DIR = ROOT / "category_art" / "candidates"
STYLE_REFS = [ROOT / "category_art" / "animali.webp", ROOT / "category_art" / "all.webp"]

STYLE = (
    "Create a premium 3D app icon in EXACTLY the same visual family as the two reference icons "
    "(a glossy paw and a glossy four-point star): a single smooth object with glossy glass-like "
    "surfaces, saturated gradient from bright cyan-blue to deep violet, soft studio lighting with "
    "subtle specular highlights, clean sharp edges, inflated rounded 3D forms. Perfectly centred on a "
    "pure black (#000000) background, no text, no floor, no ground shadow, no extra elements, square "
    "1:1, generous black margin (object fills about 60% of the frame). "
)
SUBJECTS = {
    "scienza": "The object: a laboratory Erlenmeyer flask with a little liquid and two small bubbles.",
    "spazio": "The object: a planet with a tilted ring (like Saturn), seen slightly from above.",
    "tecnologia": "The object: a square microchip with short pins on all four sides and a smaller square core.",
    "natura": "The object: a sprig with three rounded leaves on a short stem.",
    "storia": "The object: a classical Greek column with a simple capital and base.",
    "psicologia": "The object: a human head in profile with a smooth stylised brain inside.",
    "corpo-umano": "The object: a stylised anatomical heart with two short vessels on top.",
    "cultura": "The object: an open book with softly curved pages, seen from a three-quarter front angle.",
    "economia": "The object: a stack of three thick coins with a simple embossed circle on top.",
    "arte": "The object: a painter's palette with a thumb hole and four small round paint dabs.",
    "geografia": "The object: a desk globe on a small curved stand, showing simplified continents.",
}


async def generate(cid: str, refs: list[ImageContent]) -> None:
    chat = LlmChat(
        api_key=os.getenv("EMERGENT_LLM_KEY"),
        session_id=f"icon-family-{cid}",
        system_message="You are a world-class 3D icon illustrator.",
    ).with_model("gemini", MODEL).with_params(modalities=["image", "text"])
    _, images = await chat.send_message_multimodal_response(UserMessage(text=STYLE + SUBJECTS[cid], file_contents=refs))
    if not images:
        raise RuntimeError(f"no image returned for {cid}")
    raw = base64.b64decode(images[0]["data"])
    image = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    image.save(RAW_DIR / f"{cid}.raw.png")
    fit_square(black_to_alpha(image), size=512, margin=0.06).save(OUT_DIR / f"{cid}.png", "PNG", optimize=True)
    print("saved", cid, image.size, flush=True)


async def main():
    refs = [ImageContent(base64.b64encode(p.read_bytes()).decode("utf-8")) for p in STYLE_REFS]
    for cid in (sys.argv[1:] or list(SUBJECTS)):
        try:
            await generate(cid, refs)
        except Exception as exc:  # noqa: BLE001 — keep going, report at the end
            print("FAILED", cid, exc, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
