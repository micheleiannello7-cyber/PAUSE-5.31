"""
PAUSE v9 — produzione "storia + copertina subito": per ogni argomento di v9_topics.py scrive il
testo (IT + EN, 6 capitoli, ≤5 min — generate_v9.py), lo inserisce nel catalogo e genera SUBITO
la copertina AI (stesso modello/stile/prompt di generate_covers.py), così nessun contenuto resta
mai senza immagine. Ordine: prima le categorie con meno contenuti (riallineamento a 40).

Checkpoint: v9_content.json (testi, letto anche dal seed al riavvio) + copertina in covers/<id>.webp
(caricata dal seed al riavvio se l'upload fosse mancato). Si ferma su budget/quota esaurita.

Usage:
    cd /app/backend && python produce_v9.py            # tutti i mancanti (testo e/o copertina)
    cd /app/backend && python produce_v9.py --limit 5
    cd /app/backend && python produce_v9.py --only <id>
"""
import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")
sys.path.insert(0, str(ROOT_DIR))

from generate_covers import budget_error, prompt_for, save_original  # noqa: E402
from generate_fill import CHAPTER_ICONS  # noqa: E402
from generate_images import generate_image  # noqa: E402
from generate_v9 import ask, build_prompt, load_out, narration_chars, save_out, topic_id  # noqa: E402
from media_opt import upload_cover  # noqa: E402
from seed_data import CATEGORY_NAMES_EN  # noqa: E402
from seed_pack_v8 import build_pack  # noqa: E402
from server import _estimate_from_translation, _estimated_audio_minutes  # noqa: E402
from story_builder import CAT_META  # noqa: E402
from v9_topics import all_topics  # noqa: E402

LOG = ROOT_DIR.parent / "memory" / "v9_production.log"


def log(msg: str):
    line = f"{datetime.now(timezone.utc).strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with LOG.open("a") as f:
        f.write(line + "\n")


def build_doc(entry: dict) -> dict:
    stories, lessons = build_pack({entry["id"]: entry})
    doc = (stories or lessons)[0]
    doc["kind"] = entry["kind"]
    doc["created_at"] = datetime.now(timezone.utc)
    doc["audio_minutes_est"] = {"it": _estimated_audio_minutes(doc), "en": _estimate_from_translation(doc, "en")}
    return doc


async def write_text(out: dict, sid: str, cat_id: str, kind: str, title_it: str, title_en: str) -> dict:
    name, icon, color = CAT_META[cat_id]
    cat = {"id": cat_id, "name": name, "name_en": CATEGORY_NAMES_EN[cat_id], "icon": icon, "color": color}
    d = await ask(f"v9-{sid}", build_prompt(cat, kind, title_it, title_en), kind)
    icons = [i if i in CHAPTER_ICONS else None for i in (d.get("chapter_icons") or [])]
    entry = {"id": sid, "category_id": cat_id, "kind": kind, "it": d["it"], "en": d["en"], "icons": icons}
    out[sid] = entry
    save_out(out)
    log(f"TEXT  {cat_id}/{sid} ({narration_chars(d['it'])} it / {narration_chars(d['en'])} en chars)")
    return entry


async def make_cover(db, doc: dict):
    sid = doc["id"]
    existing = [p for p in (ROOT_DIR / "covers").glob(f"{sid}.*") if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
    if existing:
        raw = existing[0].read_bytes()
        log(f"COVER {sid}: riuso file locale {existing[0].name}")
    else:
        raw, _ = await asyncio.wait_for(generate_image(f"pause-cover-v9-{sid}", prompt_for(doc)), timeout=240)
        raw = save_original(sid, raw).read_bytes()
    fields = await asyncio.to_thread(upload_cover, sid, raw)
    fields["hero_generated_at"] = datetime.now(timezone.utc).isoformat()
    await db.stories.update_one({"id": sid}, {"$set": fields})
    log(f"COVER {sid}: ok ({fields['hero_image_generated']})")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--only")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    out = load_out()

    counts = {}
    async for d in db.stories.aggregate([{"$group": {"_id": "$category_id", "n": {"$sum": 1}}}]):
        counts[d["_id"]] = d["n"]
    covered = {d["id"] for d in await db.stories.find({"hero_image_generated": {"$nin": [None, ""]}}, {"_id": 0, "id": 1}).to_list(5000)}

    pending = []
    for cat_id, kind, title_it, title_en in all_topics():
        sid = topic_id(kind, title_en)
        has_text = sid in out
        has_cover = sid in covered
        if args.list:
            print(f"{'text' if has_text else '----'} {'cover' if has_cover else '-----'} {kind:6} {cat_id:12} {sid}")
            continue
        if args.only and sid != args.only:
            continue
        if has_text and has_cover and not args.only:
            continue
        pending.append((sid, cat_id, kind, title_it, title_en))
    if args.list:
        print(counts)
        return

    # Sempre l'argomento della categoria attualmente più indietro.
    todo = []
    while pending:
        pending.sort(key=lambda t: counts.get(t[1], 0))
        item = pending.pop(0)
        counts[item[1]] = counts.get(item[1], 0) + 1
        todo.append(item)
    if args.limit:
        todo = todo[: args.limit]
    log(f"[start] todo={len(todo)} testi_presenti={len(out)}")

    ok = fail = 0
    for i, (sid, cat_id, kind, title_it, title_en) in enumerate(todo, 1):
        try:
            entry = out.get(sid) or await write_text(out, sid, cat_id, kind, title_it, title_en)
            doc = build_doc(entry)
            current = await db.stories.find_one({"id": sid}, {"_id": 0, "hero_image_generated": 1, "created_at": 1})
            if current is None:
                await db.stories.insert_one(doc)
                log(f"DB    {sid}: inserito ({doc['audio_minutes_est']})")
            if not (current or {}).get("hero_image_generated"):
                try:
                    await make_cover(db, doc)
                except Exception:
                    # Regola: nessuna storia senza copertina. Il testo resta nel JSON e verrà
                    # ripubblicato (con copertina) alla prossima esecuzione.
                    if current is None:
                        await db.stories.delete_one({"id": sid, "hero_image_generated": {"$in": [None, ""]}})
                        log(f"DB    {sid}: rimosso in attesa della copertina")
                    raise
            ok += 1
            log(f"[{i}/{len(todo)}] DONE {cat_id}/{sid}")
        except Exception as e:  # noqa: BLE001
            fail += 1
            log(f"[{i}/{len(todo)}] FAIL {cat_id}/{sid}: {str(e)[:200]}")
            if budget_error(e):
                log("!! budget/quota esaurita: mi fermo (riprendere con lo stesso comando)")
                break
            if fail >= 3 and ok == 0:
                log("!! errori ripetuti: mi fermo")
                break
    log(f"[done] ok={ok} fail={fail}")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
