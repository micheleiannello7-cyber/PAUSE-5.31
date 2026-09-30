"""Explicit editorial reassignment of the former catch-all category.

No story IDs/content/progress are deleted. Original records are archived before
updates. Safe to resume after an interrupted run; unknown content fails closed.
"""
from datetime import datetime, timezone

MIGRATION_ID = "retire-curiosita-v1"
REASSIGNMENTS = {
    "why-yawn-cat": "animali",
    "why-lefties": "corpo-umano",
    "colors-cant-see": "scienza",
    "time-zones": "geografia",
    "why-mirror-flip": "scienza",
    "cur-why-yawn-contagious-fun": "scienza",  # Cotton candy, despite its legacy ID.
    "cur-why-popcorn-pops": "scienza",
    "cur-why-mirrors-reverse": "scienza",
    "cur-why-onions-cry": "natura",
    "cur-why-time-flies": "psicologia",
    "v4-carta-sette-volte": "scienza",
    "v4-pop-corn": "scienza",
    "v4-strisce-zebra": "animali",
    "v4-lez-stimare": "scienza",
    "v4-lez-perche-cielo-notte": "spazio",
    "v4-lez-coincidenze": "psicologia",
    "v5-sacchetto-patatine": "scienza",
    "v5-miele-non-scade": "scienza",
    "v5-cavi-annodano": "scienza",
    "v5-banane-radioattive": "scienza",
    "v5-qwerty": "tecnologia",
    "v5-lez-regressione-media": "scienza",
    "v5-lez-grafici-ingannevoli": "scienza",
    "v5-lez-effetto-doppler": "scienza",
    "v5-lez-hotel-hilbert": "scienza",
    "v5-lez-numeri-primi": "tecnologia",
    "lez-ghiaccio-galleggia": "scienza",
    "lez-eco": "scienza",
}
DESTINATIONS = tuple(dict.fromkeys(REASSIGNMENTS.values()))


def normalize_category_ids(ids):
    if "all" in ids:
        return ["all"]
    expanded = []
    for category_id in ids:
        expanded.extend(DESTINATIONS if category_id == "curiosita" else [category_id])
    return list(dict.fromkeys(expanded))


def category_fields(category):
    return {
        "category_id": category["id"], "category_name": category["name"],
        "category_icon": category["icon"], "category_color": category["color"],
    }


def reclassify_story(story, category):
    story.update(category_fields(category))
    for lang, translation in (story.get("translations") or {}).items():
        if not isinstance(translation, dict):
            continue
        translation["category_name"] = category.get("name_en", category["name"]) if lang == "en" else category["name"]
        for field in ("category_id", "category_icon", "category_color"):
            if field in translation:
                translation[field] = story[field]


def apply_seed_taxonomy(categories, stories):
    categories[:] = [category for category in categories if category["id"] != "curiosita"]
    by_id = {category["id"]: category for category in categories}
    for story in stories:
        if story.get("category_id") == "curiosita":
            if story["id"] not in REASSIGNMENTS:
                raise ValueError(f"Unclassified legacy story: {story['id']}")
            reclassify_story(story, by_id[REASSIGNMENTS[story["id"]]])


async def _archive(db, kind, identifier, document):
    await db.taxonomy_backups.update_one(
        {"migration": MIGRATION_ID, "kind": kind, "entity_id": identifier},
        {"$setOnInsert": {"document": document, "saved_at": datetime.now(timezone.utc)}},
        upsert=True,
    )


async def migrate_curiosita(db, categories):
    by_id = {category["id"]: category for category in categories}
    stories = await db.stories.find({"category_id": "curiosita"}, {"_id": 0}).to_list(None)
    unknown = [story["id"] for story in stories if story["id"] not in REASSIGNMENTS]
    if unknown:
        raise ValueError(f"Migration needs editorial decisions for: {unknown}")
    # Validate every destination before making any mutation.
    if not set(DESTINATIONS).issubset(by_id):
        raise ValueError("A destination category is missing")
    for story in stories:
        await _archive(db, "story", story["id"], story)
        target = by_id[REASSIGNMENTS[story["id"]]]
        fields = category_fields(target)
        for lang, translation in (story.get("translations") or {}).items():
            if not isinstance(translation, dict):
                continue
            fields[f"translations.{lang}.category_name"] = target.get("name_en", target["name"]) if lang == "en" else target["name"]
            for field in ("category_id", "category_icon", "category_color"):
                if field in translation:
                    fields[f"translations.{lang}.{field}"] = fields[field]
        await db.stories.update_one({"id": story["id"], "category_id": "curiosita"}, {"$set": fields})

    users = db.user_state.find({"$or": [{"interests": "curiosita"}, {"unlocked_categories": "curiosita"}]}, {"_id": 0})
    async for user in users:
        await _archive(db, "user_state", user["user_id"], user)
        fields = {key: normalize_category_ids(user[key]) for key in ("interests", "unlocked_categories") if "curiosita" in (user.get(key) or [])}
        # Optimistic condition preserves a concurrent preference update.
        condition = {"user_id": user["user_id"], **{key: user[key] for key in fields}}
        await db.user_state.update_one(condition, {"$set": fields})
    category = await db.categories.find_one({"id": "curiosita"}, {"_id": 0})
    if category:
        await _archive(db, "category", "curiosita", category)
        await db.categories.delete_one({"id": "curiosita"})
    return len(stories)