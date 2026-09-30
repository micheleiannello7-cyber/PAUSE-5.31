"""One-off: regenerate the "ESPLORA" (all topics) 3D icon with Nano Banana from
the user's reference image (stack of glossy glass cards with a question mark on
a neon podium), then publish it as the `all` category artwork.

Run:  python generate_explore_icon.py generate   # → memory/icons_2026/explore.raw.png
      python generate_explore_icon.py publish    # → Object Storage + manifest + DB
"""
import asyncio
import base64
import hashlib
import io
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

import numpy as np  # noqa: E402
from PIL import Image, ImageOps  # noqa: E402

MODEL = "gemini-3.1-flash-image-preview"
OUT_DIR = ROOT.parent / "memory" / "icons_2026"
REF = OUT_DIR / "explore-reference.png"
RAW = OUT_DIR / "explore.raw.png"
VERSION = "reference-3d-v6"

PROMPT = (
    "Recreate the object in this reference image as a premium, ultra-high-quality 3D app icon, "
    "IDENTICAL to the reference: same composition, same shapes, same proportions, same colours, "
    "same camera angle and same lighting. The object: three translucent glossy glass cards fanned "
    "out and standing upright — the front card is blue-violet with a large bold rounded cyan-to-violet "
    "gradient question mark '?' in the middle, behind it a teal-cyan card tilted right and a warm "
    "orange-amber card tilted further right, plus a violet card edge peeking on the left. All cards sit "
    "on a rounded-square glowing dark-blue glass podium with luminous neon-blue rim edges. Smooth "
    "glass-like surfaces, saturated gradients, soft studio lighting with subtle specular highlights, "
    "crisp clean edges, no noise, no artefacts. Single object perfectly centred on a pure black "
    "(#000000) background, no text other than the question mark, no floor, no extra elements, "
    "square 1:1 composition, generous empty black margin around the object (object fills about 62% of the frame)."
)


async def generate() -> None:
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

    ref_b64 = base64.b64encode(REF.read_bytes()).decode("utf-8")
    chat = LlmChat(
        api_key=os.getenv("EMERGENT_LLM_KEY"),
        session_id="icon-2026-explore",
        system_message="You are a world-class 3D icon illustrator.",
    ).with_model("gemini", MODEL).with_params(modalities=["image", "text"])
    _, images = await chat.send_message_multimodal_response(UserMessage(text=PROMPT, file_contents=[ImageContent(ref_b64)]))
    if not images:
        raise RuntimeError("no image returned")
    raw = base64.b64decode(images[0]["data"])
    image = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    image.save(RAW)
    print("saved", RAW, image.size, flush=True)


def encode_artwork(image: Image.Image) -> bytes:
    """Same treatment as import_reference_categories.artwork: 480px, soft fade
    of the edges into the tile's dark navy so the black studio blends in."""
    image = image.resize((480, 480), Image.Resampling.LANCZOS)
    pixels = np.asarray(image, dtype=float)
    y, x = np.mgrid[:480, :480]
    distance = np.minimum.reduce([x, y, 479 - x, 479 - y])
    opacity = np.clip(distance / 32, 0, 1)
    opacity = (opacity * opacity * (3 - 2 * opacity))[..., None]
    pixels = pixels * opacity + np.array([4, 10, 20]) * (1 - opacity)
    buf = io.BytesIO()
    Image.fromarray(pixels.astype("uint8")).save(buf, "WEBP", quality=94, method=6)
    return buf.getvalue()


async def publish() -> None:
    from storage import put_object
    from motor.motor_asyncio import AsyncIOMotorClient

    content = encode_artwork(Image.open(RAW).convert("RGB"))
    digest = hashlib.sha256(content).hexdigest()[:12]
    path = f"pause/category/{VERSION}/all-{digest}.webp"
    result = put_object(path, content, "image/webp")
    path = result["path"]
    # Keep the local copies + manifest in sync so a fresh fork restores the same art.
    (ROOT / "category_art" / "all.webp").write_bytes(content)
    (ROOT / "category_art" / "reference-3d-v4" / "all.webp").write_bytes(content)
    for manifest_file in (ROOT / "category_art_manifest.json", ROOT / "category_art" / "reference-3d-v4" / "import-report.json"):
        manifest = json.loads(manifest_file.read_text())
        manifest["artworks"]["all"] = path
        manifest_file.write_text(json.dumps(manifest, indent=2) + "\n")
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    await db.design_assets.update_one(
        {"id": "category-all"},
        {"$set": {"illustration_generated": path, "illustration_revision": VERSION}},
        upsert=True,
    )
    print("published", path, len(content), "bytes", flush=True)


if __name__ == "__main__":
    asyncio.run(generate() if (sys.argv[1:] or ["generate"])[0] == "generate" else publish())
