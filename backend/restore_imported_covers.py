"""Restore ONLY the user's additional PAUSE 4.96 covers. Never generates images.

python restore_imported_covers.py --report /app/memory/cover_import_4_96.json
Existing generated covers are preserved. Exact story IDs, cover-only writes.
"""
import argparse
import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
from media_opt import upload_cover  # noqa: E402
from storage import init_storage  # noqa: E402

logger = logging.getLogger("imported_covers")
COVER_FIELDS = {
    "hero_image_generated", "hero_image_thumb", "hero_source_digest",
    "hero_bytes", "hero_source_url", "hero_imported_at",
}


def download_cover(url):
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    # upload_cover decodes the image before either storage or database writes.
    return response.content


async def snapshot(db):
    """Fingerprints prove content and settings weren't changed by the import."""
    result = {}
    for collection, key in (("stories", "id"), ("categories", "id"), ("user_state", "user_id")):
        docs = await db[collection].find({}, {"_id": 0}).to_list(10000)
        result[collection] = {
            d[key]: hashlib.sha256(json.dumps(
                {k: v for k, v in d.items() if collection != "stories" or k not in COVER_FIELDS},
                sort_keys=True, default=str,
            ).encode()).hexdigest() for d in docs
        }
    return result


async def restore_imported_covers(db):
    from cover_editorial import decisions
    exclusions = decisions()
    manifest = json.loads((ROOT / "imported_cover_sources.json").read_text())
    stats = {"imported": [], "skipped": [], "unknown": [], "failed": []}
    pending = []
    for sid, filename in manifest["sources"].items():
        doc = await db.stories.find_one({"id": sid}, {"_id": 0, "id": 1, "title": 1,
            "kind": 1, "category_id": 1, "hero_image_generated": 1})
        if doc is None:
            stats["unknown"].append(sid)
        elif doc.get("hero_image_generated") or exclusions.get(sid, {}).get("source") == f"pause/hero/{sid}-{filename[:12]}.webp":
            stats["skipped"].append(sid)
        else:
            pending.append((doc, manifest["base_url"] + filename))
    if not pending:
        return stats
    await asyncio.to_thread(init_storage)
    semaphore = asyncio.Semaphore(3)
    stop = asyncio.Event()

    async def one(doc, url):
        sid = doc["id"]
        async with semaphore:
            if stop.is_set():
                stats["failed"].append({"id": sid, "error": "Import stopped"})
                return
            try:
                raw = await asyncio.to_thread(download_cover, url)
                fields = await asyncio.to_thread(upload_cover, sid, raw)
                fields.update({"hero_source_url": url,
                    "hero_imported_at": datetime.now(timezone.utc).isoformat()})
                result = await db.stories.update_one(
                    {"id": sid, "hero_image_generated": {"$in": [None, ""]}},
                    {"$set": fields},
                )
                if result.modified_count:
                    stats["imported"].append({**doc, **fields})
                    logger.info("Imported %s", sid)
                else:
                    stats["skipped"].append(sid)
            except Exception as exc:
                stats["failed"].append({"id": sid, "error": str(exc)[:200]})
                logger.error("Import failed %s: %s", sid, exc)
                status = getattr(getattr(exc, "response", None), "status_code", None)
                if status in (401, 402, 403, 429) or len(stats["failed"]) >= 3:
                    stop.set()
    await asyncio.gather(*(one(doc, url) for doc, url in pending))
    return stats


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    try:
        db = client[os.environ["DB_NAME"]]
        before = await snapshot(db) if args.report else None
        result = await restore_imported_covers(db)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps({"source": "PAUSE-4.96-main.zip",
                "before": before, "after": await snapshot(db), **result}, indent=2, ensure_ascii=False))
        print(json.dumps({k: len(v) for k, v in result.items()}), flush=True)
        if result["failed"]:
            raise SystemExit(1)
    finally:
        client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())