"""
One-off image generation script for PAUSE.

Reads all stories from MongoDB, and for each story that doesn't already have a
`hero_image_generated` value, generates an image via Gemini Nano Banana, uploads
it to Emergent Object Storage, and writes the storage path back to the story.

Idempotent: run multiple times safely — already-generated stories are skipped.

Usage:
    cd /app/backend && python generate_images.py           # process missing
    cd /app/backend && python generate_images.py --force   # regenerate all
    cd /app/backend && python generate_images.py --only sky-blue-sunset-orange
"""
import asyncio
import argparse
import base64
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

sys.path.insert(0, str(ROOT_DIR))

from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402
from image_prompts import STORY_IMAGE_PROMPTS, CATEGORY_IMAGE_PROMPTS, LESSON_IMAGE_PROMPTS  # noqa: E402
from storage import put_object, APP_NAME  # noqa: E402


MODEL = "gemini-3.1-flash-image-preview"
CONCURRENCY = 4


async def generate_image(session_id: str, prompt: str) -> tuple[bytes, str]:
    api_key = os.environ["EMERGENT_LLM_KEY"]
    chat = LlmChat(
        api_key=api_key,
        session_id=session_id,
        system_message="You are an editorial image generator producing dark, magazine-quality photography for a premium learning app called PAUSE.",
    )
    chat.with_model("gemini", MODEL).with_params(modalities=["image", "text"])

    msg = UserMessage(text=prompt)
    _text, images = await chat.send_message_multimodal_response(msg)
    if not images:
        raise RuntimeError(f"No image returned for {session_id}")
    image_bytes = base64.b64decode(images[0]["data"])
    mime = images[0].get("mime_type") or "image/png"
    return image_bytes, mime


async def generate_and_upload(session_id: str, prompt: str, storage_path: str) -> str:
    image_bytes, mime = await generate_image(session_id, prompt)
    await asyncio.to_thread(put_object, storage_path, image_bytes, mime)
    return storage_path


async def process_stories(db, args):
    query: dict = {"kind": {"$ne": "lesson"}}
    if args.only:
        query = {"id": args.only}
    stories = await db.stories.find(query, {"_id": 0, "id": 1, "hero_image_generated": 1, "image_prompt": 1, "title": 1, "hook": 1, "category_name": 1}).to_list(2000)
    total = len(stories)
    print(f"Found {total} stories to consider")
    sem = asyncio.Semaphore(CONCURRENCY)

    async def one(i, s):
        sid = s["id"]
        if not args.force and s.get("hero_image_generated"):
            print(f"[{i}/{total}] SKIP {sid} (already generated)")
            return
        prompt = STORY_IMAGE_PROMPTS.get(sid) or s.get("image_prompt") or (
            f"Dark, cinematic, photorealistic editorial cover image for an article titled '{s.get('title','')}' "
            f"({s.get('category_name','')}): {s.get('hook','')}. Vertical 3:4, moody premium lighting, "
            "no text, no letters, no watermark."
        )
        async with sem:
            try:
                print(f"[{i}/{total}] GEN   {sid} ...", flush=True)
                path = await generate_and_upload(
                    f"pause-img-{sid}", prompt, f"{APP_NAME}/hero/{sid}.png"
                )
                await db.stories.update_one({"id": sid}, {"$set": {"hero_image_generated": path}})
                print(f"[{i}/{total}] OK    {sid} -> {path}")
            except Exception as e:
                print(f"[{i}/{total}] FAIL  {sid}: {e}")

    await asyncio.gather(*(one(i, s) for i, s in enumerate(stories, 1)))


async def process_categories(db, args):
    query: dict = {}
    if args.only:
        query["id"] = args.only
    cats = await db.categories.find(query, {"_id": 0, "id": 1, "illustration_generated": 1}).to_list(200)
    total = len(cats)
    print(f"Found {total} categories to consider")
    for i, c in enumerate(cats, 1):
        cid = c["id"]
        if not args.force and c.get("illustration_generated"):
            print(f"[{i}/{total}] SKIP {cid} (already generated)")
            continue
        prompt = CATEGORY_IMAGE_PROMPTS.get(cid)
        if not prompt:
            print(f"[{i}/{total}] MISS  {cid} (no prompt defined)")
            continue
        try:
            print(f"[{i}/{total}] GEN cat {cid} ...", flush=True)
            path = await generate_and_upload(
                f"pause-cat-{cid}", prompt, f"{APP_NAME}/category/{cid}.png"
            )
            await db.categories.update_one({"id": cid}, {"$set": {"illustration_generated": path}})
            print(f"[{i}/{total}] OK  cat {cid} -> {path}")
        except Exception as e:
            print(f"[{i}/{total}] FAIL cat {cid}: {e}")


async def process_lessons(db, args):
    query: dict = {"kind": "lesson"}
    if args.only:
        query = {"id": args.only, "kind": "lesson"}
    lessons = await db.stories.find(query, {"_id": 0, "id": 1, "hero_image_generated": 1, "title": 1, "hook": 1, "category_name": 1}).to_list(2000)
    total = len(lessons)
    print(f"Found {total} lessons to consider")
    sem = asyncio.Semaphore(CONCURRENCY)

    async def one(i, s):
        sid = s["id"]
        if not args.force and s.get("hero_image_generated"):
            print(f"[{i}/{total}] SKIP {sid} (already generated)")
            return
        prompt = LESSON_IMAGE_PROMPTS.get(sid) or (
            f"Dark, cinematic, conceptual editorial cover illustration for a mini-lesson titled '{s.get('title','')}' "
            f"({s.get('category_name','')}): {s.get('hook','')}. Vertical 3:4, moody premium lighting, "
            "no text, no letters, no close-up faces, no watermark."
        )
        async with sem:
            try:
                print(f"[{i}/{total}] GEN les {sid} ...", flush=True)
                path = await generate_and_upload(
                    f"pause-les-{sid}", prompt, f"{APP_NAME}/hero/{sid}.png"
                )
                await db.stories.update_one({"id": sid}, {"$set": {"hero_image_generated": path}})
                print(f"[{i}/{total}] OK  les {sid} -> {path}")
            except Exception as e:
                print(f"[{i}/{total}] FAIL les {sid}: {e}")

    await asyncio.gather(*(one(i, s) for i, s in enumerate(lessons, 1)))


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--only", help="Only process this id (story or category)")
    parser.add_argument("--kind", choices=["stories", "lessons", "categories", "all"], default="all")
    args = parser.parse_args()

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    if args.kind in ("stories", "all"):
        await process_stories(db, args)
    if args.kind in ("lessons", "all"):
        await process_lessons(db, args)
    if args.kind in ("categories", "all"):
        await process_categories(db, args)

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
