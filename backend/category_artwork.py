"""Versioned, original category art. Media lives in managed object storage.

This manifest lets a fresh database recover asset associations without generating
or uploading anything again. User/story data and existing later artwork are kept.
"""
import json
from pathlib import Path


async def ensure_category_artwork(db):
    manifest = json.loads((Path(__file__).parent / "category_art_manifest.json").read_text())
    previous_prefixes = (
        "pause/category/glass-2026-09-v1/",
        "pause/category/recognizable-2026-09-v2/",
        "pause/category/colorful-3d-v3/",
        "pause/category/glossy-3d-v4/",
        "pause/category/glossy-3d-v5/",
    )
    for category_id, path in manifest["artworks"].items():
        fields = {"illustration_generated": path, "illustration_revision": manifest["version"]}
        collection = db.design_assets if category_id == "all" else db.categories
        asset_id = "category-all" if category_id == "all" else category_id
        existing = await collection.find_one({"id": asset_id}, {"_id": 0, "illustration_generated": 1})
        current_path = (existing or {}).get("illustration_generated") or ""
        # Migrate the two shipped families, but never overwrite a later custom
        # replacement. This also upgrades the all-topics banner idempotently.
        if not current_path or current_path == path or current_path.startswith(previous_prefixes):
            await collection.update_one({"id": asset_id}, {"$set": fields}, upsert=category_id == "all")