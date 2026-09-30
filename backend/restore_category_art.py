"""Re-upload the approved category illustrations to Object Storage at the exact
paths recorded in category_art_manifest.json (idempotent, no AI generation).

Use after a fork / new environment whose Object Storage bucket is empty:
    python restore_category_art.py
"""
import argparse
import io
import json
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image, ImageOps

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

from storage import put_object, get_object_optional  # noqa: E402

SOURCE_FILES = {
    "glass-2026-09-v1": "category_art_sources.json",
    "recognizable-2026-09-v2": "category_art_sources_v2.json",
}


def optimise(raw: bytes) -> bytes:
    image = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    margin = round(min(image.size) * 0.04)
    image = image.crop((margin, margin, image.width - margin, image.height - margin))
    image.thumbnail((480, 480), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    image.save(out, "WEBP", quality=88, method=6)
    return out.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reupload", action="store_true", help="Restore a fresh bucket without probing missing objects")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "category_art_manifest.json").read_text())
    if manifest["version"] in ("colorful-3d-v3", "glossy-3d-v4", "glossy-3d-v5"):
        # Recreate the approved bytes from managed source images; never request
        # another AI generation or probe an empty fork bucket for every object.
        from calm_category_art import build_assets
        _, assets = build_assets()
        for category_id, path in manifest["artworks"].items():
            data = assets[category_id]
            put_object(path, data, "image/webp")
            print(f"restored {category_id}: {len(data)} bytes -> {path}", flush=True)
        return
    sources = {v: json.loads((ROOT / f).read_text()) for v, f in SOURCE_FILES.items()}
    for category_id, path in manifest["artworks"].items():
        version = path.split("/")[2]
        if not args.reupload and get_object_optional(path):
            print(f"ok       {category_id} ({path})")
            continue
        src = sources[version]
        raw = requests.get(src["base_url"] + src["sources"][category_id], timeout=60)
        raw.raise_for_status()
        data = optimise(raw.content)
        put_object(path, data, "image/webp")
        print(f"restored {category_id}: {len(data)} bytes -> {path}", flush=True)


if __name__ == "__main__":
    main()
