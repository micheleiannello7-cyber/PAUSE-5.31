"""Offline Gemini artwork requested for PAUSE's navigation and share action.

Existing bookmark is reused, never regenerated. Raw results are cached so
rerunning does not incur another generation. Process, archive, verify, bundle.
"""
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

from emergentintegrations.llm.chat import ImageContent, LlmChat, UserMessage  # noqa: E402
from storage import get_object, put_object  # noqa: E402

MODEL = "gemini-3.1-flash-image-preview"
ASSETS = ROOT.parent / "frontend" / "assets" / "images"
RAW = ROOT / "gen_out" / "navigation-v1"
STYLE = (
    "Use the attached icons ONLY as a material and lighting reference. Match their "
    "rounded glossy 3D molded plastic, soft studio highlights and polished simple "
    "geometry. Create ONE new standalone app icon, straight-on with very slight "
    "3D depth, readable at 28 pixels. Thick clean shapes, not thin outlines. "
    "Cyan-teal main material with a subtle violet accent. Centered square composition, "
    "15% empty margin. SOLID PURE BLACK RGB(0,0,0) BACKGROUND for chroma removal. "
    "NO black material on the object, NO ground plane, NO shadow outside object, "
    "NO glow, NO tile behind it, NO text or letters, NO checkerboard. "
)
JOBS = {
    "nav-home-active": "A familiar HOME pictogram: one simple house with a peaked triangular roof, cyan walls, violet roof and a clearly defined centered doorway. No landscape, no extra props.",
    "nav-topics-active": "A familiar TOPICS/CATEGORIES pictogram: exactly FOUR chunky rounded square blocks arranged in a clean symmetrical 2 by 2 grid, equal gaps. Three cyan blocks and one violet block. Recognizable app-category grid, no dots or extra items.",
    "nav-profile-active": "A familiar USER PROFILE pictogram: a simple cyan round head sphere above a rounded cyan shoulder-and-torso bust silhouette. Minimal anonymous account avatar, no facial features, no hair, no clothes, no enclosing circle.",
    "act-share-v2": "The standard iOS SHARE symbol, unmistakable: a thick cyan U-shaped open-top square container/frame and a thick straight cyan arrow pointing VERTICALLY UP out of its center. The arrow has a large triangular arrowhead extending above the square; its vertical shaft crosses the open top. Single united extruded glossy 3D pictogram, almost front-facing. NOT connected spheres, NOT a network graph, NOT a paper plane, NOT a diagonal arrow, NOT a gift box or package.",
}


async def generate(name, prompt, references, semaphore):
    file = RAW / f"{name}.png"
    if file.exists():
        print(f"Reusing {name}", flush=True)
        return
    async with semaphore:
        chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"],
                       session_id=f"pause-navigation-{name}",
                       system_message="Create consistent, immediately recognizable 3D app icons.")
        chat.with_model("gemini", MODEL).with_params(modalities=["image", "text"])
        _, images = await chat.send_message_multimodal_response(
            UserMessage(text=STYLE + prompt, file_contents=[ImageContent(ref) for ref in references]))
        if not images:
            raise RuntimeError(f"No image returned for {name}")
        file.write_bytes(base64.b64decode(images[0]["data"]))
        print(f"Generated {name}", flush=True)


def prepare(name):
    image = Image.open(RAW / f"{name}.png").convert("RGB")
    rgb = np.asarray(image).astype(np.float32)
    # The image model occasionally outputs white despite a black-background
    # request. Detect the actual studio background instead of retaining a tile.
    corners = np.array([rgb[0, 0], rgb[0, -1], rgb[-1, 0], rgb[-1, -1]])
    white = float(corners.mean()) > 180
    distance = 255 - rgb.min(axis=2) if white else rgb.max(axis=2)
    alpha = np.clip((distance - 12) / 28, 0, 1)
    background = 255 if white else 0
    unmatte = (rgb - background * (1 - alpha[..., None])) / np.maximum(alpha[..., None], 0.01)
    rgba = np.dstack([np.clip(unmatte, 0, 255), alpha * 255]).astype(np.uint8)
    cut = Image.fromarray(rgba)
    box = cut.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox()
    if box is None:
        raise RuntimeError(f"Empty icon: {name}")
    cut = cut.crop(box)
    cut.thumbnail((460, 460), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (512, 512))
    canvas.paste(cut, ((512 - cut.width) // 2, (512 - cut.height) // 2))
    canvas.save(ASSETS / f"{name}.png", optimize=True)
    files = [ASSETS / f"{name}.png"]
    if name.startswith("nav-"):
        neutral = ImageOps.colorize(ImageOps.grayscale(canvas), "#504A68", "#D9D5E7")
        neutral.putalpha(canvas.getchannel("A"))
        base = ASSETS / f"{name.replace('-active', '-base')}.png"
        neutral.save(base, optimize=True)
        files.append(base)
    return files


async def main():
    RAW.mkdir(parents=True, exist_ok=True)
    refs = [base64.b64encode((ASSETS / f).read_bytes()).decode()
            for f in ["act-bookmark-active.png", "kind-headphones.png"]]
    semaphore = asyncio.Semaphore(2)
    await asyncio.gather(*(generate(name, prompt, refs, semaphore) for name, prompt in JOBS.items()))
    manifest = {"model": MODEL, "reused_saved": "act-bookmark-base.png / act-bookmark-active.png", "assets": {}}
    for name in JOBS:
        for file in prepare(name):
            data = file.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            result = await asyncio.to_thread(put_object, f"pause/navigation-icons/{digest[:16]}/{file.name}", data, "image/png")
            stored, _ = await asyncio.to_thread(get_object, result["path"])
            if hashlib.sha256(stored).hexdigest() != digest:
                raise RuntimeError(f"Storage verification failed: {file.name}")
            manifest["assets"][file.name] = {"path": result["path"], "sha256": digest}
            print(f"Published and verified {file.name}", flush=True)
    (ROOT / "navigation_icons_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    asyncio.run(main())