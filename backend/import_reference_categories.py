"""One-off import of user-requested reference-style art. No AI at runtime.

Generated sheets contain alternate takes: coordinates select one subject each.
Only writes new versioned objects and an import report; publication is separate.
"""
import hashlib
import io
import json
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from PIL import Image

load_dotenv(Path(__file__).parent / '.env')
from storage import put_object  # noqa: E402

ROOT = Path(__file__).parent / 'category_art' / 'reference-3d-v4'
VERSION = 'reference-3d-v6'
PICKS = {
    'scienza': ('a', (34, 35, 248, 259)),
    'spazio': ('a', (281, 35, 494, 259)),
    'tecnologia': ('a', (527, 35, 740, 259)),
    'natura': ('a', (1018, 35, 1232, 259)),
    'animali': ('a', (281, 291, 494, 514)),
    'storia': ('a', (773, 291, 985, 514)),
    'psicologia': ('b', (34, 36, 248, 260)),
    'corpo-umano': ('b', (280, 36, 494, 260)),
    'cultura': ('b', (527, 36, 740, 260)),
    'economia': ('b', (34, 292, 248, 516)),
    'arte': ('b', (280, 292, 494, 516)),
    'geografia': ('b', (1018, 36, 1232, 260)),
}


def artwork(category_id):
    if category_id == 'all':
        image = Image.open(ROOT / 'all-source.jpg').convert('RGB')
    else:
        sheet, box = PICKS[category_id]
        image = Image.open(ROOT / f'sheet-{sheet}.jpg').convert('RGB').crop(box)
    image = image.resize((480, 480), Image.Resampling.LANCZOS)
    pixels = np.asarray(image, dtype=float)
    y, x = np.mgrid[:480, :480]
    distance = np.minimum.reduce([x, y, 479 - x, 479 - y])
    opacity = np.clip(distance / 32, 0, 1)
    opacity = (opacity * opacity * (3 - 2 * opacity))[..., None]
    pixels = pixels * opacity + np.array([4, 10, 20]) * (1 - opacity)
    image = Image.fromarray(pixels.astype('uint8'))
    buf = io.BytesIO()
    image.save(buf, 'WEBP', quality=94, method=6)
    return buf.getvalue()


def main():
    report_path = ROOT / 'import-report.json'
    report = json.loads(report_path.read_text()) if report_path.exists() else {
        'version': VERSION, 'artworks': {},
    }
    for category_id in [*PICKS, 'all']:
        if category_id in report['artworks']:
            continue
        content = artwork(category_id)
        digest = hashlib.sha256(content).hexdigest()[:12]
        path = f'pause/category/{VERSION}/{category_id}-{digest}.webp'
        result = put_object(path, content, 'image/webp')
        report['artworks'][category_id] = result['path']
        (ROOT / f'{category_id}.webp').write_bytes(content)
        report_path.write_text(json.dumps(report, indent=2) + '\n')
        print(f'{category_id}: {result["path"]} ({len(content)} bytes)', flush=True)


if __name__ == '__main__':
    main()