"""Local contact sheets for visual review of a generated batch; no AI/network calls."""
import argparse
import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent


def review_font(size):
    """Use a Unicode font so Italian accents are not shown as missing glyphs."""
    for filename in ("/usr/share/fonts/truetype/freefont/FreeSans.ttf",
                     "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if Path(filename).exists():
            return ImageFont.truetype(filename, size=size)
    return ImageFont.load_default(size=size)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("/tmp/pause-cover-review"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    records = [item for path in args.reports
               for item in json.loads(path.read_text())["generated"]]
    font = review_font(17)
    for start in range(0, len(records), 12):
        batch = records[start:start + 12]
        sheet = Image.new("RGB", (1200, ((len(batch) + 3) // 4) * 450), "#101621")
        draw = ImageDraw.Draw(sheet)
        for offset, record in enumerate(batch):
            x, y = (offset % 4) * 300, (offset // 4) * 450
            with Image.open(ROOT / record["source_file"]) as source:
                image = ImageOps.contain(source.convert("RGB"), (284, 364))
                sheet.paste(image, (x + (300 - image.width) // 2, y))
            label = f'{start + offset + 1}. {record["title"]}'
            draw.multiline_text((x + 8, y + 370), "\n".join(textwrap.wrap(label, 29)),
                                font=font, fill="white", spacing=3)
        target = args.output / f"covers-{start + 1:02d}-{start + len(batch):02d}.jpg"
        sheet.save(target, quality=90)
        print(target)


if __name__ == "__main__":
    main()