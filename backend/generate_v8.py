"""
PAUSE v8 — scrive i testi (IT + EN, 6 capitoli) per gli argomenti di v8_topics.py
con GPT-5.4 via emergentintegrations e li salva in v8_content.json.

Il JSON è un checkpoint: ogni voce completata viene salvata subito, quindi il
processo si può interrompere e rilanciare (riprende dagli argomenti mancanti).
seed_pack_v8.py legge il JSON e costruisce i documenti con la stessa gerarchia
del resto del catalogo (chapters_v6, translations.en, objective per le lezioni).

Usage:
    cd /app/backend && python generate_v8.py            # scrive i mancanti
    cd /app/backend && python generate_v8.py --only <id>
"""
import argparse
import asyncio
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")
sys.path.insert(0, str(ROOT_DIR))

from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402
from generate_fill import CHAPTER_ICONS, SYSTEM, parse_json, story_prompt, lesson_prompt  # noqa: E402
from story_builder import CAT_META  # noqa: E402
from seed_data import CATEGORY_NAMES_EN  # noqa: E402
from v8_topics import all_topics  # noqa: E402

MODEL = ("openai", "gpt-5.4")
CONCURRENCY = 5
OUT = ROOT_DIR / "v8_content.json"
N_CHAPTERS = 6


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()[:56]


def topic_id(kind: str, title_en: str) -> str:
    return f"v8-{'lez-' if kind == 'lesson' else ''}{slugify(title_en)}"


def load_out() -> dict:
    if OUT.exists():
        return json.loads(OUT.read_text())
    return {}


def save_out(data: dict):
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    tmp.replace(OUT)


async def ask(session_id: str, prompt: str, retries: int = 3) -> dict:
    last_err = None
    for attempt in range(retries):
        try:
            chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=f"{session_id}-{attempt}", system_message=SYSTEM)
            chat.with_model(*MODEL)
            raw = await chat.send_message(UserMessage(text=prompt))
            return parse_json(raw)
        except Exception as e:  # noqa: BLE001
            last_err = e
            msg = str(e).lower()
            if "budget" in msg or "insufficient" in msg or "402" in msg:
                raise
            await asyncio.sleep(2 + attempt * 3)
    raise RuntimeError(f"LLM failed for {session_id}: {last_err}")


def validate(d: dict, kind: str):
    it, en = d["it"], d["en"]
    assert len(it["chapters"]) == N_CHAPTERS and len(en["chapters"]) == N_CHAPTERS, "need 6 chapters"
    for lang in (it, en):
        assert lang["title"] and lang["hook"] and lang["summary"], "missing fields"
        for ch in lang["chapters"]:
            assert ch["title"] and len(ch["body"].split()) >= 60, "chapter too short"
        if kind == "lesson":
            assert lang.get("objective"), "missing objective"


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only")
    args = parser.parse_args()

    out = load_out()
    lock = asyncio.Lock()
    sem = asyncio.Semaphore(CONCURRENCY)
    todo = []
    for cat_id, kind, title_it, title_en in all_topics():
        sid = topic_id(kind, title_en)
        if args.only and sid != args.only:
            continue
        if sid in out and not args.only:
            continue
        todo.append((sid, cat_id, kind, title_it, title_en))
    print(f"done={len(out)} todo={len(todo)}")

    async def one(sid, cat_id, kind, title_it, title_en):
        name, icon, color = CAT_META[cat_id]
        cat = {"id": cat_id, "name": name, "name_en": CATEGORY_NAMES_EN[cat_id], "icon": icon, "color": color}
        prompt = story_prompt(cat, title_it, title_en) if kind == "story" else lesson_prompt(cat, title_it, title_en)
        async with sem:
            try:
                d = await ask(f"v8-{sid}", prompt)
                validate(d, kind)
                icons = [i if i in CHAPTER_ICONS else None for i in (d.get("chapter_icons") or [])]
                entry = {"id": sid, "category_id": cat_id, "kind": kind, "it": d["it"], "en": d["en"], "icons": icons}
                async with lock:
                    out[sid] = entry
                    save_out(out)
                print(f"OK   {kind:6} {cat_id}/{sid}", flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"FAIL {kind:6} {cat_id}/{sid}: {e}", flush=True)

    await asyncio.gather(*(one(*t) for t in todo))
    print(f"[done] total={len(out)}")


if __name__ == "__main__":
    asyncio.run(main())
