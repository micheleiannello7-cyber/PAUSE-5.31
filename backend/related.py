"""Thematic links between stories ("Questa storia si collega a…").

Pure heuristic, no LLM: each story becomes a weighted bag of stemmed keywords
(title ×3, highlight words ×3, hook/summary ×1). Similarity is a cosine over
those bags. Results favour a *path* across categories: at most two of the
three suggestions may share the current story's category, so a physics story
can lead to geography and then to space (Newton → maree → Luna).
"""
from __future__ import annotations

import math
import re
from typing import Dict, List

_STOP = set("""
a ad agli ai al alla alle allo anche ancora avere aveva bene che chi ci come con cosa
cosi così cui da dal dalla dalle dallo degli dei del della delle dello di dove e è ed
era erano essere fa fare fino fra gia già gli ha hai hanno ho i il in io la le lei li lo
loro lui ma me mi mia mie miei mio molto ne nei nel nella nelle nello noi non nostro o
ogni oppure ora per perche perché piu più poco poi puo può quale quando quanto quasi
quel quella quelle quelli quello questa queste questi questo qui quindi sa se sei sempre
senza si sia siamo sono sotto sta stai stato su sua sue sui sul sulla sulle sullo suo
suoi tra tu tua tue tuo tuoi tutti tutto un una uno vi voi vostro
the and for with that this from what when where which while your you are was were been
have has had not but into over under about after before their they them then than
there these those into just like more most other some such only own same very can will
would should could our its it's how why does did doing each few him his her she hers
""".split())

_WORD = re.compile(r"[a-zàèéìíòóùú]{4,}")


def _stem(w: str) -> str:
    # Crude prefix stemming works well enough for IT/EN plural & inflection
    # ("scienza"/"scienziato", "planet"/"planets").
    return w[:6]


def _bag(doc: dict) -> Dict[str, float]:
    bag: Dict[str, float] = {}

    def add(text: str | None, weight: float):
        for w in _WORD.findall((text or "").lower()):
            if w in _STOP:
                continue
            s = _stem(w)
            bag[s] = bag.get(s, 0.0) + weight

    add(doc.get("title"), 3.0)
    add(" ".join(doc.get("highlight_words") or []), 3.0)
    add(doc.get("hook"), 1.0)
    add(doc.get("summary"), 1.0)
    tr = (doc.get("translations") or {}).get("en") or {}
    add(tr.get("title"), 1.5)
    add(tr.get("hook"), 0.5)
    return bag


def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(v * b[k] for k, v in a.items() if k in b)
    if dot == 0:
        return 0.0
    return dot / (math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values())))


class RelatedIndex:
    """In-memory index rebuilt whenever the story count changes."""

    def __init__(self):
        self._bags: Dict[str, Dict[str, float]] = {}
        self._cats: Dict[str, str] = {}
        self._size = -1

    def build(self, docs: List[dict]):
        self._bags = {d["id"]: _bag(d) for d in docs}
        self._cats = {d["id"]: d.get("category_id", "") for d in docs}
        self._size = len(docs)

    @property
    def size(self) -> int:
        return self._size

    def affinity(self, story_id: str, liked_ids: List[str]) -> float:
        """How close a story is to the ones the user hearted (best cosine, 0..1)."""
        base = self._bags.get(story_id)
        if not base:
            return 0.0
        best = 0.0
        for lid in liked_ids:
            if lid == story_id:
                continue
            bag = self._bags.get(lid)
            if bag:
                best = max(best, _cosine(base, bag))
        return best

    def related(self, story_id: str, limit: int = 3, exclude: List[str] | None = None) -> List[str]:
        base = self._bags.get(story_id)
        if base is None:
            return []
        skip = set(exclude or [])
        skip.add(story_id)
        scored = [
            (sid, _cosine(base, bag))
            for sid, bag in self._bags.items()
            if sid not in skip
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        own_cat = self._cats.get(story_id)
        picked: List[str] = []
        same_cat = 0
        for sid, score in scored:
            if score <= 0:
                break
            if self._cats.get(sid) == own_cat:
                if same_cat >= 2:
                    continue
                same_cat += 1
            picked.append(sid)
            if len(picked) >= limit:
                return picked
        # Fallback: pad with same-category stories so the path is never empty.
        for sid, _ in scored:
            if sid in picked:
                continue
            if self._cats.get(sid) == own_cat:
                picked.append(sid)
                if len(picked) >= limit:
                    break
        return picked


INDEX = RelatedIndex()
