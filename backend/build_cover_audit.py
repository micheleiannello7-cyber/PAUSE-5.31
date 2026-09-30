"""Create contact-sheet PDFs covering every currently visible cover and its story titles."""
import io
import json
import os
import textwrap
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pymongo import MongoClient

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
from storage import get_object  # noqa: E402

OUT = Path("/app/cover_audit")
OUT.mkdir(exist_ok=True)


def fetch(entry):
    source, _ = entry
    try:
        if source.startswith("https://"):
            response = requests.get(source, timeout=30)
            response.raise_for_status()
            raw = response.content
        else:
            raw, _ = get_object(source)
        image = Image.open(io.BytesIO(raw)).convert("RGB")
        return image, None
    except Exception as exc:
        return None, type(exc).__name__


def main():
    if (OUT / "decisions.json").exists():
        raise SystemExit("Reviewed catalog is immutable: use render_cover_groups.py to inspect its existing groups.")
    with MongoClient(os.environ["MONGO_URL"]) as client:
        docs = list(client[os.environ["DB_NAME"]].stories.find({}, {"_id": 0, "id": 1, "title": 1, "hook": 1,
            "hero_image": 1, "hero_image_generated": 1, "hero_variants": 1}))
    groups = defaultdict(list)
    for doc in docs:
        source = (doc.get("hero_variants") or {}).get("thumb") or doc.get("hero_image_generated") or doc.get("hero_image")
        if source:
            groups[source].append(doc)
    entries = sorted(groups.items(), key=lambda item: (not item[0].startswith("https://"), item[0]))
    with ThreadPoolExecutor(max_workers=8) as pool:
        images = list(pool.map(fetch, entries))
    index = []
    panels = []
    for group, ((source, stories), (image, error)) in enumerate(zip(entries, images), 1):
        index.append({"group": group, "source": source, "stories": stories, "error": error})
        for start in range(0, len(stories), 3):
            panels.append((group, stories[start:start + 3], image, error))
    font = ImageFont.load_default(size=21)
    small = ImageFont.load_default(size=19)
    pages = []
    for page_start in range(0, len(panels), 6):
        page = Image.new("RGB", (1800, 2160), "white")
        draw = ImageDraw.Draw(page)
        for slot, (group, stories, image, error) in enumerate(panels[page_start:page_start + 6]):
            x, y = (slot % 2) * 900 + 20, (slot // 2) * 720 + 15
            draw.text((x, y), f"GROUP {group}", fill="black", font=font)
            if image:
                thumb = ImageOps.contain(image, (840, 355))
                page.paste(thumb, (x + (840 - thumb.width) // 2, y + 32))
            else:
                draw.text((x, y + 100), f"IMAGE UNAVAILABLE: {error}", fill="red", font=font)
            offset = y + 397
            for story in stories:
                draw.text((x, offset), story["id"], fill="blue", font=small)
                offset += 25
                for line in textwrap.wrap(story["title"], width=66):
                    draw.text((x, offset), line, fill="black", font=font)
                    offset += 26
                offset += 10
        pages.append(page)
    for start in range(0, len(pages), 6):
        path = OUT / f"catalog-{start // 6 + 1}.pdf"
        pages[start].save(path, save_all=True, append_images=pages[start + 1:start + 6], resolution=140)
        print(path, flush=True)
    report = {"total_stories": len(docs), "covered_stories": sum(len(v) for v in groups.values()),
        "missing_story_ids": [d["id"] for d in docs if not (d.get("hero_image_generated") or d.get("hero_image"))],
        "groups": index}
    (OUT / "catalog.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"{len(entries)} unique images, {len(panels)} panels, {len(pages)} pages", flush=True)


if __name__ == "__main__":
    main()