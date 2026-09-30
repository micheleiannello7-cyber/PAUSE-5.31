"""Offline: align neutral states, then archive the existing Gemini artwork.

No image generation or runtime AI. Bundled copies keep first paint offline.
Run from backend: python publish_action_icons.py
"""
import hashlib
import json
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

from storage import get_object, put_object  # noqa: E402


def main():
    assets = ROOT.parent / "frontend" / "assets" / "images"
    # Identical geometry/alpha in both states prevents a shape jump on toggle.
    for kind in ("heart", "bookmark"):
        active = Image.open(assets / f"act-{kind}-active.png").convert("RGBA")
        neutral = ImageOps.colorize(ImageOps.grayscale(active), "#504A68", "#D9D5E7")
        neutral.putalpha(active.getchannel("A"))
        neutral.save(assets / f"act-{kind}-base.png", optimize=True)
    manifest = {"model": "gemini-3.1-flash-image-preview", "assets": {}}
    for file in sorted(assets.glob("act-*.png")):
        data = file.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        path = f"pause/action-icons/{digest[:16]}/{file.name}"
        result = put_object(path, data, "image/png")
        stored_path = result["path"]
        downloaded, _ = get_object(stored_path)
        if hashlib.sha256(downloaded).hexdigest() != digest:
            raise RuntimeError(f"Storage verification failed: {file.name}")
        manifest["assets"][file.name] = {"path": stored_path, "sha256": digest}
        print(f"Verified {file.name}", flush=True)
    (ROOT / "action_icons_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()