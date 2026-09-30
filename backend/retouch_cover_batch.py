"""Bounded, no-AI cleanups for explicitly reviewed newly generated covers only."""
import argparse
import fcntl
import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image, ImageChops, ImageFilter
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
from media_opt import QUALITY, upload_cover  # noqa: E402

RETOUCHES = {
    "v8-why-do-we-feel-embarrassed-for-other-people": "remove-header-lettering",
    "v8-why-do-we-drive-on-the-right-and-the-british-on-the-left": "blend-footer-artifact",
    "v8-lez-watching-wildlife-without-disturbing-it": "crop-forest-header",
    "v8-lez-posture-and-breath-6-minutes-to-feel-better-at-your-desk": "crop-office-header",
    "v8-lez-arguing-well-6-rules-for-a-discussion-that-resolves": "crop-artificial-frame",
    "v8-lez-visiting-an-archaeological-site-and-understanding-what-y": "remove-sky-lettering",
    "v8-lez-saying-no-without-guilt-the-6-step-method": "quarantine-incomplete-portrait",
}

# A story ID alone is not approval to edit future regenerated versions.
# These coordinates/rejections were reviewed ONLY in these historical batches.
LEGACY_RETOUCH_IDS = {
    "7dbe6ded62644d7e9ccf42931de7f6d0": {
        "v8-why-do-we-feel-embarrassed-for-other-people",
        "v8-why-do-we-drive-on-the-right-and-the-british-on-the-left",
    },
    "56ba5742cf674cb7a8acbbc14cf85680": {
        "v8-lez-watching-wildlife-without-disturbing-it",
        "v8-lez-posture-and-breath-6-minutes-to-feel-better-at-your-desk",
        "v8-lez-arguing-well-6-rules-for-a-discussion-that-resolves",
        "v8-lez-visiting-an-archaeological-site-and-understanding-what-y",
        "v8-lez-saying-no-without-guilt-the-6-step-method",
    },
}


def retouch(raw, operation):
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    if image.size != (896, 1200):
        raise ValueError("Retouch coordinates require the reviewed 896x1200 source")
    if operation == "crop-forest-header":
        image = image.crop((116, 318, 776, 1200))
    elif operation == "crop-office-header":
        # Start just above the hair: preserve the complete face and breathing pose.
        image = image.crop((140, 330, 790, 1200))
    elif operation == "crop-artificial-frame":
        # Keep the native crop resolution (no artificial upscaling).
        image = image.crop((105, 116, 790, 1048))
    elif operation == "remove-sky-lettering":
        header = image.crop((0, 0, 896, 210))
        # Include dark drop-shadows too, not only the white letter pixels.
        mask = Image.new("L", header.size, 0)
        mask.paste(255, (22, 30, 520, 198))
        mask.paste(255, (607, 30, 845, 179))
        mask = mask.filter(ImageFilter.GaussianBlur(4))
        background = header.crop((518, 0, 596, 210)).resize(header.size)
        image.paste(background.filter(ImageFilter.GaussianBlur(8)), (0, 0), mask)
    elif operation == "remove-header-lettering":
        header = image.crop((0, 0, 896, 270))
        channels = header.split()
        light = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
        mask = light.point(lambda value: 255 if value > 80 else 0)
        mask = mask.filter(ImageFilter.MaxFilter(19)).filter(ImageFilter.GaussianBlur(3))
        background = header.crop((0, 0, 95, 270)).resize((896, 270))
        background = background.filter(ImageFilter.GaussianBlur(12))
        image.paste(background, (0, 0), mask)
    elif operation == "blend-footer-artifact":
        # Existing unwanted rectangle begins at y=1080; fade the ground before it.
        mask = Image.new("L", image.size, 0)
        for y in range(970, 1200):
            t = min(1, (y - 970) / 108)
            mask.paste(round(255 * t * t * (3 - 2 * t)), (0, y, 896, y + 1))
        image.paste(Image.new("RGB", image.size, (3, 8, 11)), (0, 0), mask)
    else:
        raise ValueError(f"Unknown retouch operation: {operation}")
    output = io.BytesIO()
    image.save(output, "WEBP", quality=QUALITY, method=6)
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--only", help="Process only this explicitly reviewed new cover")
    parser.add_argument("--quarantine-reason", help="Reject only --only, preserving its paid original")
    args = parser.parse_args()
    if args.quarantine_reason and not args.only:
        parser.error("--quarantine-reason requires exactly one --only ID")
    with (ROOT / ".cover_generation.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        report = json.loads(args.report.read_text())
        if report["status"] == "running":
            raise RuntimeError("Wait for generation to finish")
        baseline = {row["id"] for row in report["existing_covers"]}
        with MongoClient(os.environ["MONGO_URL"]) as client:
            db = client[os.environ["DB_NAME"]]
            for record in list(report["generated"]):
                sid = record["id"]
                if args.only and sid != args.only:
                    continue
                legacy_ids = LEGACY_RETOUCH_IDS.get(report["id"], set())
                operation = ("quarantine-manual" if args.quarantine_reason else
                             RETOUCHES.get(sid) if sid in legacy_ids else None)
                if not operation or record.get("retouch"):
                    continue
                if sid in baseline:
                    raise RuntimeError("Pre-existing covers must never be retouched")
                source = ROOT.parent / record["source_file"]
                if operation.startswith("quarantine-"):
                    quarantine = args.report.parent / "rejected" / source.name
                    quarantine.parent.mkdir(exist_ok=True)
                    # Archive BEFORE unlinking so no paid original is ever lost.
                    quarantine.write_bytes(source.read_bytes())
                    result = db.stories.update_one(
                        {"id": sid, "hero_image_generated": record["hero_image_generated"]},
                        {"$unset": {key: "" for key in ("hero_image_generated", "hero_image_thumb",
                                    "hero_source_digest", "hero_bytes", "hero_generated_at")}})
                    if not result.modified_count:
                        raise RuntimeError(f"Concurrent cover change: {sid}")
                    source.unlink()  # Startup must not restore a rejected cover.
                    record["source_file"] = str(quarantine.relative_to(ROOT.parent))
                    record["rejection_reason"] = args.quarantine_reason or "Artificial band obscures eyes/forehead; cannot repair without new AI"
                    report.setdefault("rejected", []).append(record)
                    report["generated"].remove(record)
                    report["published"] = len(report["generated"])
                    db.cover_generation_runs.update_one({"id": report["id"]}, {
                        "$pull": {"generated_ids": sid}, "$addToSet": {"rejected_ids": sid},
                        "$set": {"published": report["published"]}})
                    temporary = args.report.with_suffix(".tmp")
                    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2))
                    temporary.replace(args.report)
                    print(f"Quarantined {sid}: original retained, no AI call", flush=True)
                    continue
                raw = retouch(source.read_bytes(), operation)
                archive = args.report.parent / "originals" / source.name
                archive.parent.mkdir(exist_ok=True)
                if not archive.exists():
                    archive.write_bytes(source.read_bytes())
                fields = upload_cover(sid, raw)
                previous = record["hero_image_generated"]
                result = db.stories.update_one(
                    {"id": sid, "hero_image_generated": previous}, {"$set": fields})
                if not result.modified_count:
                    raise RuntimeError(f"Concurrent cover change: {sid}")
                temporary = source.with_suffix(".tmp")
                temporary.write_bytes(raw)
                temporary.replace(source)
                record.update(fields)
                record["retouch"] = {"operation": operation, "previous_hero": previous,
                                     "at": datetime.now(timezone.utc).isoformat(), "ai_calls": 0}
                temporary = args.report.with_suffix(".tmp")
                temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2))
                temporary.replace(args.report)
                print(f"Retouched {sid}: no AI call, Q{QUALITY}", flush=True)


if __name__ == "__main__":
    main()