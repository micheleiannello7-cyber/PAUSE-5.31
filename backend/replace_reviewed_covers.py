"""Explicit editorial replacements: stage first, visually review, then publish IDs.

Never clears a live image. Preserves old metadata/originals; refuses incomplete
catalogs, duplicate generation processes and unapproved publication.
"""
import argparse
import asyncio
import fcntl
import io
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
from generate_covers import STYLE, budget_error  # noqa: E402
from generate_images import MODEL, generate_image  # noqa: E402
from media_opt import HERO_MAX, encode_webp, upload_cover  # noqa: E402


def write_report(path, report):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    temporary.replace(path)


def validate(raw):
    with Image.open(io.BytesIO(raw)) as image:
        image.load()
        if min(image.size) < 768 or image.width >= image.height:
            raise ValueError(f"Expected high-resolution portrait, got {image.size}")
    return encode_webp(raw, HERO_MAX)


async def stage(db, decisions, folder, report, report_path):
    for item in decisions:
        sid = item["id"]
        if sid in report["candidates"]:
            continue
        try:
            current = db.stories.find_one({"id": sid}, {"_id": 0, "id": 1, "title": 1,
                "hero_image_generated": 1, "hero_image_thumb": 1, "hero_image": 1,
                "hero_source_digest": 1, "hero_bytes": 1})
            if current is None or not item.get("reason") or not item.get("prompt"):
                raise ValueError("Replacement requires an existing story, reason and explicit prompt")
            path = folder / f"{sid}.webp"
            if not path.exists():
                print(f"GENERATE {sid}", flush=True)
                raw, _ = await asyncio.wait_for(generate_image(
                    f"pause-review-{uuid.uuid4().hex}", item["prompt"] + STYLE), timeout=240)
                path.write_bytes(validate(raw))
            report["candidates"][sid] = {"before": current, "reason": item["reason"],
                "prompt": item["prompt"], "file": str(path), "status": "awaiting_visual_review"}
            write_report(report_path, report)
            print(f"STAGED {sid}", flush=True)
        except Exception as exc:
            report["errors"].append({"id": sid, "type": type(exc).__name__,
                                     "budget": budget_error(exc)})
            report["stop_reason"] = "budget_or_quota" if budget_error(exc) else "generation_error"
            write_report(report_path, report)
            print(f"STOP {sid}: {str(exc)[:180]}", flush=True)
            return
    report["status"] = "staged"
    write_report(report_path, report)


def publish(db, ids, folder, report, report_path):
    for sid in ids:
        item = report["candidates"][sid]
        if item["status"] == "published":
            continue
        raw = Path(item["file"]).read_bytes()
        validate(raw)
        previous = item["before"]
        fields = upload_cover(sid, raw)
        fields.update({"hero_image": "", "hero_generated_at": datetime.now(timezone.utc).isoformat()})
        result = db.stories.update_one({"id": sid,
            "hero_image_generated": previous.get("hero_image_generated"),
            "hero_image": previous.get("hero_image")}, {"$set": fields})
        if not result.matched_count:
            raise RuntimeError(f"Live cover changed while reviewing {sid}; preserve it")
        backups = folder / "previous_originals"
        backups.mkdir(exist_ok=True)
        for path in (ROOT / "covers").glob(f"{sid}.*"):
            if path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                path.replace(backups / path.name)
        destination = ROOT / "covers" / f"{sid}.webp"
        temp = destination.with_suffix(".tmp")
        temp.write_bytes(raw)
        temp.replace(destination)
        item.update({"status": "published", "after": fields,
                     "approved_at": datetime.now(timezone.utc).isoformat()})
        write_report(report_path, report)
        print(f"PUBLISHED {sid}", flush=True)


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decisions", type=Path)
    parser.add_argument("--publish", help="Comma-separated IDs explicitly visually approved")
    args = parser.parse_args()
    with (ROOT / ".cover_generation.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with MongoClient(os.environ["MONGO_URL"]) as client:
            db = client[os.environ["DB_NAME"]]
            docs = list(db.stories.find({}, {"_id": 0, "hero_image_generated": 1, "hero_image": 1}))
            if any(not (d.get("hero_image_generated") or d.get("hero_image")) for d in docs):
                raise SystemExit("Complete empty covers before replacing existing covers")
            folder = args.decisions.parent / (args.decisions.stem + "_staged")
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / "report.json"
            report = json.loads(path.read_text()) if path.exists() else {
                "model": MODEL, "quality": 84, "started_at": datetime.now(timezone.utc).isoformat(),
                "candidates": {}, "errors": [], "status": "running"}
            if args.publish:
                publish(db, args.publish.split(","), folder, report, path)
            elif report.get("stop_reason"):
                raise SystemExit("Previous run stopped; no automatic paid retry")
            else:
                await stage(db, json.loads(args.decisions.read_text()), folder, report, path)


if __name__ == "__main__":
    asyncio.run(main())