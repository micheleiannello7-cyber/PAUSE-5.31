"""Slice the approved new ceramic artwork and upload immutable WebP assets.

Run `python calm_category_art.py` to print a manifest. Originals stay untouched.
The same deterministic pipeline is used by restore_category_art after a fork.
"""
import hashlib
import io
import json
from pathlib import Path
from statistics import median

import requests
from dotenv import load_dotenv
from PIL import Image, ImageChops, ImageOps

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

from storage import put_object  # noqa: E402

# Lato maggiore dell'oggetto rispetto al riquadro (uguale per tutte le icone).
OBJECT_FRACTION = 0.6


def read_image(url: str) -> Image.Image:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return ImageOps.exif_transpose(Image.open(io.BytesIO(response.content))).convert("RGB")


def encode_icon(image: Image.Image) -> bytes:
    # Match the studio background to the app's constant artwork surface. This
    # removes JPEG background offsets, not the newly generated sculptural detail.
    corners = [image.getpixel((x, y)) for x in (2, image.width - 3) for y in (2, image.height - 3)]
    background = tuple(int(median(c[channel] for c in corners)) for channel in range(3))
    image = ImageChops.subtract(image, Image.new("RGB", image.size, background))
    # Azzera il rumore residuo dello sfondo (gradienti JPEG) così il riquadro
    # è uniforme anche quando l'oggetto viene ricentrato su una tela più grande.
    import numpy as np
    arr = np.asarray(image).astype(np.float32)
    lum = arr.max(axis=2, keepdims=True)
    keep = np.clip((lum - 12.0) / 22.0, 0.0, 1.0)
    arr = arr * keep
    image = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
    image = ImageChops.add(image, Image.new("RGB", image.size, (5, 7, 12)))
    # Normalizza posizione e scala: l'oggetto viene centrato e occupa sempre la
    # stessa frazione del riquadro (stessa dimensione visiva in tutte le tessere).
    mask = image.convert("L").point(lambda v: 255 if v > 70 else 0)
    bbox = mask.getbbox() or (0, 0, image.width, image.height)
    obj_w, obj_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    side = int(round(max(obj_w, obj_h) / OBJECT_FRACTION))
    cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    square = Image.new("RGB", (side, side), (5, 7, 12))
    square.paste(image, (int(round(side / 2 - cx)), int(round(side / 2 - cy))))
    square.thumbnail((512, 512), Image.Resampling.LANCZOS)
    encoded = io.BytesIO()
    square.save(encoded, "WEBP", quality=90, method=6)
    return encoded.getvalue()


def build_assets() -> tuple[str, dict[str, bytes]]:
    config = json.loads((ROOT / "category_art_sources_v3.json").read_text())
    sheet = read_image(config["sheet_url"])
    cols, rows = config["columns"], config["rows"]
    assets = {}
    for index, category_id in enumerate(config["order"]):
        col, row = index % cols, index // cols
        cell_w, cell_h = sheet.width / cols, sheet.height / rows
        inset = round(min(cell_w, cell_h) * 0.03)  # evita le linee di separazione del foglio
        bounds = (round(col * cell_w) + inset, round(row * cell_h) + inset,
                  round((col + 1) * cell_w) - inset, round((row + 1) * cell_h) - inset)
        assets[category_id] = encode_icon(sheet.crop(bounds))
    assets["all"] = encode_icon(read_image(config["all_url"]))
    for category_id, url in config.get("overrides", {}).items():
        assets[category_id] = encode_icon(read_image(url))
    # Sorgenti versionate nel repo (icone 2026: zampa Animali, stella Qualsiasi
    # argomento): sopravvivono ai fork senza dipendere da URL esterni.
    for category_id, rel_path in config.get("local_overrides", {}).items():
        assets[category_id] = encode_icon(Image.open(ROOT / rel_path).convert("RGB"))
    return config["version"], assets


def main():
    version, assets = build_assets()
    manifest = {"version": version, "artworks": {}}
    for category_id, data in assets.items():
        digest = hashlib.sha256(data).hexdigest()[:12]
        path = f"pause/category/{version}/{category_id}-{digest}.webp"
        result = put_object(path, data, "image/webp")
        manifest["artworks"][category_id] = result["path"]
        print(f"Uploaded {category_id}: {len(data)} bytes", flush=True)
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()