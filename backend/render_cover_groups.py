"""Render numbered groups from the immutable review snapshot as individual JPEG sheets."""
import argparse
import io
import json
import textwrap
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
from storage import get_object  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=131)
    parser.add_argument("--end", type=int, default=169)
    args = parser.parse_args()
    folder = ROOT.parent / "cover_audit"
    catalog = json.loads((folder / "catalog.json").read_text())
    groups = [g for g in catalog["groups"] if args.start <= g["group"] <= args.end]

    def read(group):
        raw, _ = get_object(group["source"])
        return Image.open(io.BytesIO(raw)).convert("RGB")

    with ThreadPoolExecutor(max_workers=5) as pool:
        images = list(pool.map(read, groups))
    for start in range(0, len(groups), 10):
        batch = groups[start:start + 10]
        page = Image.new("RGB", (1800, ((len(batch) + 1) // 2) * 600), "white")
        draw = ImageDraw.Draw(page)
        font = ImageFont.load_default(size=25)
        for i, group in enumerate(batch):
            x, y = i % 2 * 900 + 20, i // 2 * 600 + 10
            draw.text((x, y), f"GROUP {group['group']}", font=font, fill="black")
            image = ImageOps.contain(images[start + i], (840, 370))
            page.paste(image, (x + (840 - image.width) // 2, y + 35))
            story = group["stories"][0]
            draw.text((x, y + 416), story["id"], font=font, fill="blue")
            for row, line in enumerate(textwrap.wrap(story["title"], width=58)):
                draw.text((x, y + 452 + row * 30), line, font=font, fill="black")
        target = folder / f"groups-{batch[0]['group']}-{batch[-1]['group']}.jpg"
        page.save(target, quality=88)
        print(target, flush=True)


if __name__ == "__main__":
    main()