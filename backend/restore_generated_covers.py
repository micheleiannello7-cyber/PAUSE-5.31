"""Import approved AI covers, retaining source URLs for future recovery.

python restore_generated_covers.py             # only unlinked covers
python restore_generated_covers.py --reupload  # recover this set in a fresh bucket
"""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

from media_opt import upload_cover  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reupload", action="store_true")
    parser.add_argument("--replace-id", help="Explicitly replace only this story with its approved manifest image")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "generated_cover_sources.json").read_text())
    stats = {"uploaded": 0, "skipped": 0, "unknown": 0}
    with MongoClient(os.environ["MONGO_URL"]) as client:
        db = client[os.environ["DB_NAME"]]
        for sid, filename in manifest["sources"].items():
            doc = db.stories.find_one({"id": sid}, {"_id": 0, "id": 1, "hero_image_generated": 1, "hero_source_url": 1})
            if doc is None:
                stats["unknown"] += 1
                continue
            url = manifest["base_url"] + filename
            replace = args.replace_id == sid or (args.reupload and doc.get("hero_source_url") == url)
            if doc.get("hero_image_generated") and not replace:
                stats["skipped"] += 1
                continue
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            fields = upload_cover(sid, response.content)
            fields.update({"hero_source_url": url, "hero_generated_at": datetime.now(timezone.utc).isoformat()})
            db.stories.update_one({"id": sid}, {"$set": fields})
            stats["uploaded"] += 1
            print(f"uploaded {sid}: {fields['hero_bytes']}", flush=True)
    print(stats, flush=True)


if __name__ == "__main__":
    main()