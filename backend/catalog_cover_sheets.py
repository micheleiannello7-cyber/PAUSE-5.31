"""Read-only catalog snapshot and visual-review sheets; never calls image AI."""
import hashlib
import io
import json
import os
import sys
import textwrap
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import dotenv_values, load_dotenv
from PIL import Image, ImageDraw, ImageOps
from pymongo import MongoClient

from render_cover_batch import review_font

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "memory" / "cover_review_final"
load_dotenv(ROOT / ".env")
BASE = dotenv_values(ROOT.parent / "frontend" / ".env")["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")


def snapshot(allow_missing=False):
    with MongoClient(os.environ["MONGO_URL"]) as client:
        docs = list(client[os.environ["DB_NAME"]].stories.find({}, {
            "_id": 0, "id": 1, "title": 1, "hook": 1, "category_id": 1,
            "hero_image_generated": 1, "hero_image_thumb": 1, "hero_image": 1,
        }))
    missing = [d["id"] for d in docs if not (d.get("hero_image_generated") or d.get("hero_image"))]
    if missing and not allow_missing:
        raise SystemExit(f"Finish missing covers BEFORE catalog review: {len(missing)}")
    docs = [d for d in docs if d.get("hero_image_generated") or d.get("hero_image")]
    return sorted(docs, key=lambda d: (d.get("category_id", ""), d["title"])), missing


def fetch(item):
    index, doc = item
    entry = {"number": index, **doc}
    source = doc.get("hero_image_generated") or doc["hero_image"]
    target = OUT / "images" / f"{index:03d}-{doc['id']}.jpg"
    try:
        url = f"{BASE}/api/media/{doc['id']}" if doc.get("hero_image_generated") else source
        response = requests.get(url, timeout=75)
        response.raise_for_status()
        raw = response.content
        with Image.open(io.BytesIO(raw)) as original:
            original.load()
            entry.update({"dimensions": list(original.size), "format": original.format})
            image = ImageOps.exif_transpose(original).convert("RGB")
        image.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        image.save(target, quality=94)
        tiny = list(image.convert("L").resize((9, 8)).getdata())
        bits = [tiny[y * 9 + x] > tiny[y * 9 + x + 1] for y in range(8) for x in range(8)]
        entry.update({"sha256": hashlib.sha256(raw).hexdigest(),
                      "dhash": sum(int(bit) << i for i, bit in enumerate(bits)),
                      "file": str(target.relative_to(ROOT.parent)), "error": None})
    except Exception as exc:
        entry["error"] = f"{type(exc).__name__}: {str(exc)[:180]}"
    return entry


PER_SHEET = 12
CELL_W, CELL_H, IMG_H = 400, 660, 520


def render(entries):
    """One JPG contact sheet per 12 covers (4x3) with number, category and title."""
    font = review_font(19)
    for start in range(0, len(entries), PER_SHEET):
        batch = entries[start:start + PER_SHEET]
        rows = (len(batch) + 3) // 4
        page = Image.new("RGB", (CELL_W * 4, CELL_H * rows), "#111827")
        draw = ImageDraw.Draw(page)
        for slot, entry in enumerate(batch):
            x, y = slot % 4 * CELL_W + 6, slot // 4 * CELL_H + 4
            if not entry["error"]:
                with Image.open(ROOT.parent / entry["file"]) as image:
                    thumb = ImageOps.contain(image, (CELL_W - 12, IMG_H))
                    page.paste(thumb, (x + (CELL_W - 12 - thumb.width) // 2, y))
            else:
                draw.text((x, y + 200), "IMAGE UNAVAILABLE", font=font, fill="orange")
            offset = y + IMG_H + 6
            draw.text((x, offset), f"#{entry['number']:03d} {entry.get('category_id', '')}", font=font, fill="#facc15")
            offset += 24
            for line in textwrap.wrap(entry["title"], 38)[:4]:
                draw.text((x, offset), line, font=font, fill="white")
                offset += 23
        target = OUT / f"sheet-{start + 1:03d}-{start + len(batch):03d}.jpg"
        page.save(target, quality=82)
        print(target, flush=True)


def main():
    allow_missing = "--allow-missing" in sys.argv
    docs, missing = snapshot(allow_missing)
    if (OUT / "catalog.json").exists():
        raise SystemExit("Snapshot already exists; preserve its review numbering.")
    (OUT / "images").mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=6) as pool:
        entries = list(pool.map(fetch, enumerate(docs, 1)))
    pairs = []
    for i, a in enumerate(entries):
        for b in entries[i + 1:]:
            if a["error"] or b["error"]:
                continue
            distance = (a["dhash"] ^ b["dhash"]).bit_count()
            if a["sha256"] == b["sha256"] or distance <= 5:
                pairs.append({"numbers": [a["number"], b["number"]],
                              "ids": [a["id"], b["id"]], "distance": distance,
                              "identical": a["sha256"] == b["sha256"]})
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "total": len(entries),
              "missing_ids": missing, "entries": entries, "similarity_candidates": pairs}
    (OUT / "catalog.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    render(entries)
    print(json.dumps({"total": len(entries), "errors": sum(bool(e["error"]) for e in entries),
                      "similar_pairs": len(pairs)}), flush=True)


if __name__ == "__main__":
    main()