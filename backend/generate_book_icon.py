"""One-off: generate the 3D open-book icon for the reader's "Inizia a leggere"
button, in the same visual language as the category / content-mode icons,
then key out the studio background (flood fill from the corners) so the icon
sits on the glass button with a transparent backdrop.

Run once:  python generate_book_icon.py
Output:    ../frontend/assets/images/kind-book.png (512x512 RGBA)
"""
import asyncio
import base64
import io
import os
from collections import deque
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

from PIL import Image, ImageOps, ImageFilter  # noqa: E402
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent  # noqa: E402

MODEL = "gemini-3.1-flash-image-preview"
STYLE_REF = "https://static.prod-images.emergentagent.com/jobs/52555a81-2975-4e93-b6d9-486eee38ffaf/images/86ae68768ce17fd276d9bed9c3a254e88374e0ffd799e56476d43fbed26bc2c5.jpeg"
OUT = ROOT.parent / "frontend" / "assets" / "images" / "kind-book.png"

PROMPT = (
    "Match this reference image EXACTLY in art direction: a single object floating "
    "centred on a deep dark navy (#0b1220) studio background, high-end glossy 3D "
    "render, soft cinematic studio lighting, subtle coloured rim glow, gentle "
    "reflections, no text, no shadow on a floor, square 1:1 composition, plenty of "
    "empty dark margin around the object. "
    "Replace the object with a single open 3D book seen from a three-quarter front "
    "angle, glossy teal and violet hard cover, cream pages fanned open with one page "
    "lifting mid-turn, soft cyan glow along the page edges, representing starting to read."
)


def key_out_background(image: Image.Image, tol: int = 46) -> Image.Image:
    """Flood-fill transparent from the four corners over near-background pixels."""
    img = image.convert("RGBA")
    w, h = img.size
    px = img.load()
    bg = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    br, bgc, bb = (sum(c[0] for c in bg) // 4, sum(c[1] for c in bg) // 4, sum(c[2] for c in bg) // 4)
    seen = bytearray(w * h)
    q = deque([(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)])
    mask = Image.new("L", (w, h), 255)
    mpx = mask.load()
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or seen[y * w + x]:
            continue
        seen[y * w + x] = 1
        r, g, b, _ = px[x, y]
        if abs(r - br) + abs(g - bgc) + abs(b - bb) > tol * 3:
            continue
        mpx[x, y] = 0
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    mask = mask.filter(ImageFilter.GaussianBlur(1.2))
    img.putalpha(mask)
    return img


async def main():
    import requests
    ref_b64 = base64.b64encode(requests.get(STYLE_REF, timeout=60).content).decode("utf-8")
    chat = LlmChat(
        api_key=os.getenv("EMERGENT_LLM_KEY"),
        session_id="kind-book-icon",
        system_message="You are a world-class 3D icon illustrator.",
    ).with_model("gemini", MODEL).with_params(modalities=["image", "text"])
    _, images = await chat.send_message_multimodal_response(UserMessage(text=PROMPT, file_contents=[ImageContent(ref_b64)]))
    if not images:
        raise RuntimeError("no image returned")
    raw = base64.b64decode(images[0]["data"])
    image = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    image.thumbnail((512, 512), Image.Resampling.LANCZOS)
    out = key_out_background(image)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.save(OUT, "PNG", optimize=True)
    print("saved", OUT, out.size)


if __name__ == "__main__":
    asyncio.run(main())
