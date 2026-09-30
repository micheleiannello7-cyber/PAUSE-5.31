"""Persist source-specific editorial exclusions; never erase a newer replacement."""
import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
from cover_review import REVIEW_DIR, image_source, review_image, write_json  # noqa: E402
from media_opt import upload_cover  # noqa: E402

DECISIONS = ROOT / "cover_editorial_decisions.json"
MANUAL_VERDICTS = {
    "why-romans-fell": "coherent", "psi-placebo": "coherent", "fear-basics": "coherent",
    "v8-why-does-the-progress-bar-never-tell-the-truth": "mismatch",
    "v8-why-do-jpeg-photos-lose-quality-every-time-you-save-them": "mismatch",
}
MANUAL_REASONS = {
    "v8-why-does-the-progress-bar-never-tell-the-truth": "Un PC da gaming non raffigura una barra di caricamento né il problema della stima del progresso.",
    "v8-why-do-jpeg-photos-lose-quality-every-time-you-save-them": "Un PC da gaming non rappresenta immagini JPEG né gli artefatti della compressione.",
}


def decisions():
    return json.loads(DECISIONS.read_text()) if DECISIONS.exists() else {}


async def apply_cover_exclusions(db):
    removed = []
    for sid, entry in decisions().items():
        doc = await db.stories.find_one({"id": sid}, {"_id": 0, "id": 1,
            "hero_image": 1, "hero_image_generated": 1})
        if doc is None or image_source(doc) != entry["source"]:
            continue
        field = "hero_image_generated" if doc.get("hero_image_generated") else "hero_image"
        values = {"hero_image": "", "cover_review_reason": entry["reason"]}
        if field == "hero_image_generated":
            values.update({"hero_image_generated": "", "hero_image_thumb": None, "hero_bytes": {}})
        result = await db.stories.update_one({"id": sid, field: entry["source"]}, {"$set": values})
        if result.modified_count:
            removed.append(sid)
    return removed


async def review_local_covers(db):
    """Review the eight already-bundled originals before restoring their links."""
    report_path = REVIEW_DIR / "local_covers.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    for path in sorted((ROOT / "covers").iterdir()):
        if path.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
            continue
        sid = path.stem
        doc = await db.stories.find_one({"id": sid}, {"_id": 0, "id": 1, "title": 1, "hook": 1, "category_name": 1})
        if doc is None:
            continue
        if sid not in report:
            report[sid] = await review_image(path.read_bytes(), [doc])
            write_json(report_path, report)
        print("Local review", sid, report[sid]["reviews"], flush=True)
        if report[sid]["reviews"][0]["verdict"] != "coherent":
            raise RuntimeError(f"Local cover needs manual review: {sid}")
    return report


async def main():
    report = json.loads((REVIEW_DIR / "existing_covers.json").read_text())
    if report["unreviewed_ids"] or report["errors"]:
        raise RuntimeError("Finish the existing-image audit before applying or generating anything")
    excluded = {}
    for group in report["groups"]:
        for review in group["reviews"]:
            sid = review["id"]
            verdict = MANUAL_VERDICTS.get(sid, review["verdict"])
            if verdict != "coherent":
                excluded[sid] = {"source": group["source"], "verdict": verdict,
                    "reason": MANUAL_REASONS.get(sid, review["reason"]), "observed_subject": group["observed_subject"]}
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    try:
        db = client[os.environ["DB_NAME"]]
        await review_local_covers(db)
        write_json(DECISIONS, excluded)
        removed = await apply_cover_exclusions(db)
        restored = []
        for path in sorted((ROOT / "covers").iterdir()):
            if path.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
                continue
            fields = await asyncio.to_thread(upload_cover, path.stem, path.read_bytes())
            await db.stories.update_one({"id": path.stem}, {"$set": fields})
            restored.append(path.stem)
        write_json(REVIEW_DIR / "cleanup.json", {"excluded": removed,
            "local_covers_restored": restored, "existing_audit_complete": True})
        print(json.dumps({"excluded": len(removed), "local_restored": len(restored)}), flush=True)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())