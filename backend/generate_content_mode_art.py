"""Generate the two 3D content-mode icons (curiosità = lightbulb, mini lezioni =
books) in the exact same visual language as the category illustrations, upload
them to Object Storage and record a manifest so a fresh DB can recover them.

Run once:  python generate_content_mode_art.py
"""
import asyncio
import base64
import hashlib
import io
import json
from pathlib import Path

from dotenv import load_dotenv
import os

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

from PIL import Image, ImageOps  # noqa: E402
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent  # noqa: E402
from storage import put_object  # noqa: E402

VERSION = "content-mode-2026-06-v1"
MODEL = "gemini-3.1-flash-image-preview"

# A category illustration used as the style anchor: same dark navy studio
# background, glossy 3D render, soft coloured rim glow, single centred object.
STYLE_REF = "https://static.prod-images.emergentagent.com/jobs/52555a81-2975-4e93-b6d9-486eee38ffaf/images/86ae68768ce17fd276d9bed9c3a254e88374e0ffd799e56476d43fbed26bc2c5.jpeg"

COMMON = (
    "Match this reference image EXACTLY in art direction: a single object floating "
    "centred on a deep dark navy (#0b1220) studio background, high-end glossy 3D "
    "render, soft cinematic studio lighting, subtle coloured rim glow, gentle "
    "reflections, no text, no shadow on a floor, square 1:1 composition, plenty of "
    "empty dark margin around the object. "
)

PROMPTS = {
    "stories": COMMON + (
        "Replace the object with a single glowing glass lightbulb, warm amber-gold "
        "light radiating from the filament, transparent glossy glass envelope with "
        "cyan highlights, representing curiosity and a bright idea."
    ),
    "lessons": COMMON + (
        "Replace the object with a small neat stack of two or three closed 3D books "
        "with a glossy graduation cap resting on top, teal and violet covers with "
        "soft highlights, representing a short lesson and learning."
    ),
}


def optimise(raw: bytes) -> bytes:
    image = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    margin = round(min(image.size) * 0.04)
    image = image.crop((margin, margin, image.width - margin, image.height - margin))
    image.thumbnail((480, 480), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    image.save(out, "WEBP", quality=88, method=6)
    return out.getvalue()


async def gen_one(ref_b64: str, mode: str) -> bytes:
    chat = LlmChat(
        api_key=os.getenv("EMERGENT_LLM_KEY"),
        session_id=f"content-mode-{mode}",
        system_message="You are a world-class 3D icon illustrator.",
    ).with_model("gemini", MODEL).with_params(modalities=["image", "text"])
    msg = UserMessage(text=PROMPTS[mode], file_contents=[ImageContent(ref_b64)])
    _, images = await chat.send_message_multimodal_response(msg)
    if not images:
        raise RuntimeError(f"no image returned for {mode}")
    return base64.b64decode(images[0]["data"])


async def main():
    import requests
    ref_raw = requests.get(STYLE_REF, timeout=60).content
    ref_b64 = base64.b64encode(ref_raw).decode("utf-8")

    manifest = {"version": VERSION, "artworks": {}}
    for mode in ("stories", "lessons"):
        raw = await gen_one(ref_b64, mode)
        data = optimise(raw)
        digest = hashlib.sha1(data).hexdigest()[:12]
        path = f"pause/content-mode/{VERSION}/{mode}-{digest}.webp"
        put_object(path, data, "image/webp")
        manifest["artworks"][mode] = path
        print(f"{mode}: {len(data)} bytes -> {path}", flush=True)

    (ROOT / "content_mode_art_manifest.json").write_text(json.dumps(manifest, indent=2))
    print("manifest written", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
