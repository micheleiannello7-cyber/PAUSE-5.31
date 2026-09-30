"""One-off category art import. Keeps originals intact; prints a storage manifest.

Run from backend: python import_category_art.py
Only image bytes are uploaded. It does not alter story/user records or generate AI.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image, ImageOps

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

from storage import put_object  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", default="category_art_sources.json")
    args = parser.parse_args()
    sources = json.loads((ROOT / args.sources).read_text())
    manifest = {"version": sources["version"], "artworks": {}}
    for category_id, filename in sources["sources"].items():
        response = requests.get(sources["base_url"] + filename, timeout=60)
        response.raise_for_status()
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(response.content))).convert("RGB")
        # Remove only the peripheral art-generation margin, retaining complete silhouettes.
        margin = round(min(image.size) * 0.04)
        image = image.crop((margin, margin, image.width - margin, image.height - margin))
        image.thumbnail((480, 480), Image.Resampling.LANCZOS)
        encoded = io.BytesIO()
        image.save(encoded, "WEBP", quality=88, method=6)
        data = encoded.getvalue()
        digest = hashlib.sha256(data).hexdigest()[:12]
        path = f"pause/category/{sources['version']}/{category_id}-{digest}.webp"
        result = put_object(path, data, "image/webp")
        manifest["artworks"][category_id] = result["path"]
        print(f"Uploaded {category_id}: {len(data)} bytes", flush=True)
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()