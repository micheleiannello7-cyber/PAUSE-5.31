"""
PAUSE — genera il 5° step per ogni mini lezione (IT + EN) con gpt-5.4.

Le mini lezioni nascevano con 4 passi; l'app le vuole con la stessa gerarchia
delle curiosità: 5 capitoli + la voce "Da ricordare" (summary, già presente).
Questo script legge le 14 lezioni da seed_lessons_a.LESSONS, chiede al modello
un 5° passo coerente con l'arco didattico (in genere "metti in pratica /
errore comune / caso reale") e scrive tutto in seed_lessons_step5.py come dict
STEP5 = { lesson_id: {"it": (title, body), "en": (title, body)} }.

Idempotente rispetto all'output: riscrive sempre il file completo.
Uso:  cd /app/backend && python generate_lesson_step5.py
"""
import asyncio
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")
sys.path.insert(0, str(ROOT_DIR))

from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402
from seed_lessons_a import LESSONS  # noqa: E402

MODEL = ("openai", "gpt-5.4")
CONCURRENCY = 4

SYSTEM = (
    "You are the senior editor of PAUSE, a premium micro-learning app. Mini lessons teach ONE concept "
    "in ordered steps. You write clean, vivid, factual prose for curious adults. "
    "You always answer with valid JSON only, no markdown fences, no commentary."
)


def parse_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()
    start, end = raw.find("{"), raw.rfind("}")
    return json.loads(raw[start:end + 1])


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
            await asyncio.sleep(2 + attempt * 3)
    raise RuntimeError(f"LLM failed for {session_id}: {last_err}")


def prompt_for(lesson: dict) -> str:
    it_ch = [{"title": c["title"], "body": c["body"]} for c in lesson["chapters"]]
    en = lesson["translations"]["en"]
    en_ch = [{"title": c["title"], "body": c["body"]} for c in en["chapters"]]
    payload = {
        "title_it": lesson["title"],
        "objective_it": lesson.get("objective", ""),
        "summary_it": lesson["summary"],
        "steps_it": it_ch,
        "title_en": en["title"],
        "objective_en": en.get("objective", ""),
        "summary_en": en["summary"],
        "steps_en": en_ch,
    }
    return (
        "This mini lesson currently has 4 ordered steps. Write ONE additional final step (step 5) that "
        "naturally CONTINUES the didactic arc — typically 'put it into practice', 'the most common mistake', "
        "or 'apply it to a real everyday case'. It must NOT repeat what earlier steps already said, and must "
        "feel like the natural closing step before the takeaway.\n\n"
        "Requirements (identical meaning in both languages):\n"
        "- step title: short, max 45 chars, same style as the existing step titles (e.g. 'Passo 5 — ...' in IT, "
        "'Step 5 — ...' in EN, matching how the existing steps are titled).\n"
        "- step body: 90-130 words, factual, concrete, warm, no bullet points, no markdown.\n\n"
        "Return JSON exactly: {\"it\": {\"title\": \"...\", \"body\": \"...\"}, \"en\": {\"title\": \"...\", \"body\": \"...\"}}\n\n"
        "LESSON DATA:\n" + json.dumps(payload, ensure_ascii=False)
    )


async def main():
    sem = asyncio.Semaphore(CONCURRENCY)
    results: dict[str, dict] = {}

    async def one(lesson):
        async with sem:
            lid = lesson["id"]
            try:
                d = await ask(f"step5-{lid}", prompt_for(lesson))
                it, en = d["it"], d["en"]
                assert it.get("title") and it.get("body") and en.get("title") and en.get("body")
                results[lid] = {
                    "it": (it["title"].strip(), it["body"].strip()),
                    "en": (en["title"].strip(), en["body"].strip()),
                }
                print(f"OK   {lid}")
            except Exception as e:  # noqa: BLE001
                print(f"FAIL {lid}: {e}")

    await asyncio.gather(*(one(l) for l in LESSONS))

    # Write the module in a stable, human-readable order (as in LESSONS).
    lines = [
        '"""PAUSE — 5° step generato per ogni mini lezione (IT + EN).',
        "Prodotto da generate_lesson_step5.py (gpt-5.4). Consumato da seed_lessons_a.py,",
        "che lo appende come capitolo 5 di ogni lezione, così le mini lezioni hanno la",
        'stessa gerarchia delle curiosità: 5 capitoli + la voce "Da ricordare"."""',
        "",
        "STEP5 = {",
    ]
    for lesson in LESSONS:
        lid = lesson["id"]
        if lid not in results:
            continue
        r = results[lid]
        lines.append(f"    {json.dumps(lid, ensure_ascii=False)}: {{")
        lines.append(f"        \"it\": ({json.dumps(r['it'][0], ensure_ascii=False)}, {json.dumps(r['it'][1], ensure_ascii=False)}),")
        lines.append(f"        \"en\": ({json.dumps(r['en'][0], ensure_ascii=False)}, {json.dumps(r['en'][1], ensure_ascii=False)}),")
        lines.append("    },")
    lines.append("}")
    lines.append("")
    out = ROOT_DIR / "seed_lessons_step5.py"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {len(results)}/{len(LESSONS)} steps -> {out}")


if __name__ == "__main__":
    asyncio.run(main())
