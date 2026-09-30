"""Versioned 3D content-mode icons (curiosità = lightbulb, mini lezioni = books).

Media lives in managed object storage; this manifest lets a fresh database
recover the asset associations without generating anything again.
"""
import json
from pathlib import Path


async def ensure_content_mode_artwork(db):
    manifest_file = Path(__file__).parent / "content_mode_art_manifest.json"
    if not manifest_file.exists():
        return
    manifest = json.loads(manifest_file.read_text())
    for mode, path in manifest["artworks"].items():
        await db.design_assets.update_one(
            {"id": f"mode-{mode}"},
            {"$set": {"illustration_generated": path, "illustration_revision": manifest["version"]}},
            upsert=True,
        )
