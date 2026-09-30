"""Generate the ~3s "hero" clips for each category illustration (12 categories +
"Qualsiasi argomento") with fal.ai image-to-video (Kling v3), upload them to
Object Storage and record a manifest + design_assets entries so the app can
play them when a tile is tapped.

Requires FAL_KEY in backend/.env.   Run once:  python generate_category_clips.py [id ...]
"""
import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

import fal_client  # noqa: E402
import requests  # noqa: E402
from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from storage import put_object  # noqa: E402

VERSION = "clip-2026-06-v1"
MODEL = "fal-ai/kling-video/v3/standard/image-to-video"
MANIFEST = ROOT / "category_clip_manifest.json"

COMMON = (
    "Keep the exact same object, colours, glossy 3D render style, framing and dark navy studio "
    "background; camera locked, no zoom, no text, seamless subtle motion. "
)
PROMPTS = {
    "scienza": COMMON + "The glowing liquid inside the flask starts to bubble and boil, bubbles rise and burst at the neck, a few luminous drops splash out and float.",
    "spazio": COMMON + "The planet slowly rotates on its axis, its rings drift, tiny stars twinkle around it.",
    "tecnologia": COMMON + "Light pulses travel along the chip's circuit traces, the core glows brighter in a heartbeat rhythm.",
    "natura": COMMON + "A gentle breeze moves the leaves of the tree, a few leaves detach and drift down slowly.",
    "animali": COMMON + "The dog looks up at the viewer, tilts its head, wags its tail and playfully sticks out its tongue.",
    "storia": COMMON + "Dust motes drift in a soft beam of light around the ancient column, which slowly turns a few degrees.",
    "psicologia": COMMON + "The brain pulses softly with light, glowing neural sparks travel across its surface.",
    "corpo-umano": COMMON + "The DNA double helix slowly rotates on its axis, its base pairs shimmering.",
    "cultura": COMMON + "The pages of the open book flutter and one page turns over gently, a soft glow rises from the pages.",
    "economia": COMMON + "The stack of gold coins shimmers; the top coin flips in the air and lands back on the stack with a sparkle.",
    "arte": COMMON + "The paint blobs on the palette ripple and swirl, a brush stroke of colour sweeps across the air above it.",
    "geografia": COMMON + "The Earth slowly rotates, clouds drift over the oceans, a soft atmospheric glow along the edge.",
    "all": COMMON + "The crystal gem slowly rotates, light refracts through its facets in cyan and violet sparkles.",
}


async def main(only: list[str]):
    if not os.getenv("FAL_KEY"):
        raise SystemExit("FAL_KEY missing in backend/.env")
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"version": VERSION, "clips": {}}
    ids = only or list(PROMPTS)
    for cid in ids:
        if manifest["clips"].get(cid):
            print("skip (done)", cid)
            continue
        # L'illustrazione viene letta dall'API locale (usa la cache su disco,
        # anche quando l'oggetto originale non è più nel bucket).
        r = requests.get(f"http://localhost:8001/api/category-media/{cid}", timeout=60)
        if r.status_code != 200:
            print("no illustration for", cid, r.status_code)
            continue
        image, ctype = r.content, r.headers.get("Content-Type", "image/webp")
        image_url = await fal_client.upload_async(image, ctype or "image/webp")
        print("→", cid, "submitting…")
        handler = await fal_client.submit_async(MODEL, arguments={
            "start_image_url": image_url,
            "prompt": PROMPTS[cid],
            "duration": "3",
            "generate_audio": False,
            "negative_prompt": "blur, distort, low quality, text, watermark, camera movement, background change",
        })
        result = await handler.get()
        video_url = result["video"]["url"]
        data = requests.get(video_url, timeout=180).content
        digest = hashlib.sha256(data).hexdigest()[:12]
        path = f"pause/category-clip/{VERSION}/{cid}-{digest}.mp4"
        put_object(path, data, "video/mp4")
        await db.design_assets.update_one({"id": f"clip-{cid}"}, {"$set": {"clip_path": path, "clip_revision": VERSION}}, upsert=True)
        manifest["clips"][cid] = path
        MANIFEST.write_text(json.dumps(manifest, indent=2))
        print("✓", cid, len(data) // 1024, "KB")
    print("done:", len(manifest["clips"]), "clips")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
