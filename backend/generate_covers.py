"""
PAUSE — copertine AI per TUTTO il catalogo, in ordine di anzianità (seed order),
partendo dai contenuti più vecchi ancora senza copertina.

Riusa Gemini Nano Banana + Object Storage. Salta immagini AI e foto esistenti;
produce hero e miniature WebP. Si ferma su budget/quota o errori ripetuti.

Usage:
    cd /app/backend && python generate_covers.py            # tutte le mancanti
    cd /app/backend && python generate_covers.py --limit 50
"""
import argparse
import asyncio
import fcntl
import io
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from PIL import Image

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")
sys.path.insert(0, str(ROOT_DIR))

from generate_images import MODEL, generate_image  # noqa: E402
from image_prompts import STORY_IMAGE_PROMPTS, LESSON_IMAGE_PROMPTS  # noqa: E402
from media_opt import HERO_MAX, QUALITY, THUMB_MAX, encode_webp, upload_cover  # noqa: E402

CONCURRENCY = 3
STYLE = (
    " Vertical 3:4 composition, dark cinematic editorial mood, magazine-quality photography, "
    "moody premium lighting with subtle cyan/magenta rim light, ultra-detailed, "
    "one clear subject with realistic textures and natural anatomy, uncluttered background, "
    "keep the subject within the central safe area and leave dark negative space for the app title, "
    "no text, no letters, no logos, no watermark."
)


def save_original(sid: str, raw: bytes) -> Path:
    """Keep a recoverable Q84 master without adding heavy PNGs to the project."""
    with Image.open(io.BytesIO(raw)) as image:
        image.load()
        extension = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}.get(image.format)
        if not extension or min(image.size) < 768 or image.width >= image.height:
            raise ValueError(f"Cover must be a high-resolution portrait: {image.size}")
    master = encode_webp(raw, HERO_MAX)
    path = ROOT_DIR / "covers" / f"{sid}.webp"
    path.parent.mkdir(exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(master)
    temporary.replace(path)
    return path


def budget_error(e: Exception) -> bool:
    m = str(e).lower()
    return any(k in m for k in ("budget", "insufficient", "402", "quota", "credit"))


def prompt_for(doc: dict) -> str:
    sid = doc["id"]
    overrides_path = ROOT_DIR / "cover_prompt_overrides.json"
    overrides = json.loads(overrides_path.read_text()) if overrides_path.exists() else {}
    if sid in overrides:
        return overrides[sid] + STYLE
    if doc.get("kind") == "lesson":
        base = LESSON_IMAGE_PROMPTS.get(sid)
        if base:
            return base.replace("16:9", "vertical 3:4") + STYLE
        return (
            f"Conceptual editorial cover photograph for a mini-lesson titled '{doc.get('title', '')}' "
            f"(topic: {doc.get('category_name', '')}). Visual idea: {doc.get('hook', '')} "
            "Show a single concrete, recognisable subject related to the lesson, no close-up faces." + STYLE
        )
    base = STORY_IMAGE_PROMPTS.get(sid)
    if base:
        return base.replace("16:9", "vertical 3:4") + STYLE
    return (
        f"Photorealistic editorial cover photograph for an article titled '{doc.get('title', '')}' "
        f"(topic: {doc.get('category_name', '')}). Visual idea: {doc.get('hook', '')} "
        "Show the concrete subject of the title, clearly recognisable." + STYLE
    )


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--concurrency", type=int, choices=range(1, 5), default=CONCURRENCY)
    parser.add_argument("--only", help="Comma-separated IDs of confirmed missing/broken covers")
    args = parser.parse_args()

    lock = (ROOT_DIR / ".cover_generation.lock").open("a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("A cover batch is already running; no duplicate generation.", flush=True)
        return

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    # Seed order = anzianità del catalogo (stessa lista di server.ALL_STORIES).
    from seed_data import STORIES  # noqa: E402
    from seed_lessons_a import LESSONS as LESSONS_A  # noqa: E402
    from seed_lessons_b import LESSONS_B  # noqa: E402
    order = [s["id"] for s in list(STORIES) + list(LESSONS_A) + list(LESSONS_B)]
    docs = await db.stories.find(
        {}, {"_id": 0, "id": 1, "kind": 1, "title": 1, "hook": 1, "category_name": 1, "hero_image_generated": 1, "hero_image": 1}
    ).to_list(3000)
    by_id = {d["id"]: d for d in docs}
    only = set(args.only.split(",")) if args.only else None

    def missing(doc):
        if doc.get("hero_image_generated"):
            return False
        return doc["id"] in only if only is not None else not doc.get("hero_image")

    todo = [by_id[i] for i in dict.fromkeys(order) if i in by_id and missing(by_id[i])]
    todo += [d for d in docs if d["id"] not in order and missing(d)]
    if args.limit:
        todo = todo[: args.limit]
    total = len(todo)
    print(f"missing covers: {total}", flush=True)
    if args.dry_run or not total:
        client.close()
        lock.close()
        return

    sem = asyncio.Semaphore(args.concurrency)
    stop = asyncio.Event()
    stats = {"ok": 0, "fail": 0, "skipped": 0, "consecutive_failures": 0, "stop_reason": None}
    run_id = uuid.uuid4().hex
    report_dir = ROOT_DIR.parent / "memory" / "cover_batches"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{run_id}.json"
    report = {"id": run_id, "model": MODEL, "total": total, "status": "running",
              "started_at": datetime.now(timezone.utc).isoformat(),
              "encoding": {"format": "webp", "quality": QUALITY,
                           "hero_max": HERO_MAX, "thumb_max": THUMB_MAX},
              "existing_covers": [d for d in docs if d.get("hero_image_generated") or d.get("hero_image")],
              "generated": [], "errors": []}

    def checkpoint():
        report.update(stats)
        temporary = report_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2))
        temporary.replace(report_path)

    checkpoint()
    await db.cover_generation_runs.insert_one({
        "id": run_id, "total": total, "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "ok": 0, "fail": 0, "generated_ids": [], "model": MODEL,
    })

    async def one(i, doc):
        if stop.is_set():
            return
        sid = doc["id"]
        async with sem:
            if stop.is_set():
                return
            try:
                current = await db.stories.find_one({"id": sid}, {"_id": 0,
                    "hero_image_generated": 1, "hero_image": 1})
                if current is None or current.get("hero_image_generated") or (
                    only is None and current.get("hero_image")
                ):
                    stats["skipped"] += 1
                    checkpoint()
                    return
                # Retry uploads from saved originals without paying to generate again.
                originals = [p for p in (ROOT_DIR / "covers").glob(f"{sid}.*")
                             if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
                prompt = prompt_for(doc)
                if originals:
                    raw = originals[0].read_bytes()
                    source = originals[0]
                    print(f"[{i}/{total}] RECOVER {sid}", flush=True)
                else:
                    print(f"[{i}/{total}] GEN  {sid}", flush=True)
                    raw, _ = await asyncio.wait_for(
                        generate_image(f"pause-cover-{run_id}-{sid}", prompt), timeout=240,
                    )
                    source = save_original(sid, raw)
                    raw = source.read_bytes()
                fields = await asyncio.to_thread(upload_cover, sid, raw)
                fields["hero_generated_at"] = datetime.now(timezone.utc).isoformat()
                # Compare-and-set also protects covers changed while the AI was working.
                result = await db.stories.update_one(
                    {"id": sid, "hero_image_generated": {"$in": [None, ""]},
                     "hero_image": current.get("hero_image")}, {"$set": fields},
                )
                if not result.modified_count:
                    # A concurrently supplied cover wins, including at the next startup.
                    if not originals:
                        source.replace(report_dir / source.name)
                    stats["skipped"] += 1
                    checkpoint()
                    return
                stats["ok"] += 1
                stats["consecutive_failures"] = 0
                report["generated"].append({"id": sid, "title": doc.get("title"),
                    "prompt": prompt, "source_file": str(source.relative_to(ROOT_DIR.parent)), **fields})
                checkpoint()
                await db.cover_generation_runs.update_one({"id": run_id}, {
                    "$inc": {"ok": 1}, "$push": {"generated_ids": sid},
                })
                print(f"[{i}/{total}] OK   {sid}", flush=True)
            except Exception as e:  # noqa: BLE001
                stats["fail"] += 1
                stats["consecutive_failures"] += 1
                report["errors"].append({"id": sid, "type": type(e).__name__})
                await db.cover_generation_runs.update_one({"id": run_id}, {"$inc": {"fail": 1}})
                print(f"[{i}/{total}] FAIL {sid}: {str(e)[:160]}", flush=True)
                if budget_error(e):
                    stats["stop_reason"] = "budget_or_quota"
                    print("!! budget/quota: mi fermo", flush=True)
                    stop.set()
                elif "429" in str(e) or "rate limit" in str(e).lower():
                    stats["stop_reason"] = "rate_limit"
                    stop.set()
                elif stats["consecutive_failures"] >= 3:
                    stats["stop_reason"] = "repeated_errors"
                    stop.set()
                checkpoint()

    await asyncio.gather(*(one(i, d) for i, d in enumerate(todo, 1)))
    print(f"[done] ok={stats['ok']} fail={stats['fail']} stopped={stop.is_set()}", flush=True)
    report["status"] = "stopped" if stop.is_set() else "completed"
    checkpoint()
    await db.cover_generation_runs.update_one({"id": run_id}, {"$set": {
        "status": "stopped" if stop.is_set() else "completed",
        "finished_at": datetime.now(timezone.utc).isoformat(), **stats,
    }})
    client.close()
    lock.close()


if __name__ == "__main__":
    asyncio.run(main())
