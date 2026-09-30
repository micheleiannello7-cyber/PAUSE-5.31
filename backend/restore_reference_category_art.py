"""Ripristina le icone 3D delle categorie (famiglia `reference-3d-v6`) nell'Object
Storage dopo un fork / nuovo ambiente con bucket vuoto. Nessuna generazione AI:
riusa i byte già approvati in category_art/reference-3d-v4/<id>.webp, agli
stessi percorsi registrati in import-report.json (idempotente).

    python restore_reference_category_art.py
"""
import hashlib
import json
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

from storage import get_object_optional, put_object  # noqa: E402

ART = ROOT / "category_art" / "reference-3d-v4"


def main():
    report = json.loads((ART / "import-report.json").read_text())
    for category_id, path in report["artworks"].items():
        data = (ART / f"{category_id}.webp").read_bytes()
        if hashlib.sha256(data).hexdigest()[:12] not in path:
            print(f"skip     {category_id}: i byte locali non corrispondono al percorso {path}")
            continue
        if get_object_optional(path):
            print(f"ok       {category_id}")
            continue
        put_object(path, data, "image/webp")
        print(f"restored {category_id}: {len(data)} bytes -> {path}", flush=True)


if __name__ == "__main__":
    main()
