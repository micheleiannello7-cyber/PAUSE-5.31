"""Recover already-paid originals after interrupted uploads; never calls image AI."""
import asyncio
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

from media_opt import source_digest, upload_cover  # noqa: E402


async def main():
    folder = ROOT.parent / "memory" / "cover_batches"
    reports = [(p, json.loads(p.read_text())) for p in folder.glob("*.json")]
    baseline = min((r for _, r in reports), key=lambda r: len(r["existing_covers"]))
    original_ids = {d["id"] for d in baseline["existing_covers"]}
    tracked = {d["id"] for _, r in reports for d in r["generated"]}
    path, report = max(reports, key=lambda pair: pair[1]["total"])
    if report["status"] == "running":
        raise RuntimeError("Wait for the active batch to stop before recovery")
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    try:
        sources = list((ROOT / "covers").iterdir()) + list(folder.iterdir())
        for source in sources:
            sid = source.stem
            if source.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
                continue
            if sid in original_ids or sid in tracked:
                continue
            doc = await db.stories.find_one({"id": sid}, {"_id": 0})
            if doc is None:
                continue
            raw = source.read_bytes()
            digest = source_digest(raw)
            if doc.get("hero_image_generated"):
                if doc.get("hero_source_digest") != digest:
                    continue  # A newer cover wins; never replace it.
                fields = {k: doc[k] for k in ("hero_image_generated", "hero_image_thumb",
                          "hero_source_digest", "hero_bytes")}
            else:
                if doc.get("hero_image"):
                    continue
                fields = await asyncio.to_thread(upload_cover, sid, raw)
                result = await db.stories.update_one({"id": sid,
                    "hero_image_generated": {"$in": [None, ""]},
                    "hero_image": {"$in": [None, ""]}}, {"$set": fields})
                if not result.modified_count:
                    continue
            destination = ROOT / "covers" / source.name
            if source != destination:
                shutil.move(str(source), str(destination))
            record = {"id": sid, "title": doc.get("title"), "recovered": True,
                      "source_file": str(destination.relative_to(ROOT.parent)), **fields}
            report["generated"].append(record)
            report.setdefault("recovered_ids", []).append(sid)
            report["reconciled_at"] = datetime.now(timezone.utc).isoformat()
            temp = path.with_suffix(".tmp")
            temp.write_text(json.dumps(report, ensure_ascii=False, indent=2))
            temp.replace(path)
            await db.cover_generation_runs.update_one({"id": report["id"]}, {
                "$addToSet": {"generated_ids": sid, "recovered_ids": sid}})
            tracked.add(sid)
            print(f"RECOVERED {sid} (no AI call)", flush=True)
        print(f"Linked covers across batches: {len(tracked)}", flush=True)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())