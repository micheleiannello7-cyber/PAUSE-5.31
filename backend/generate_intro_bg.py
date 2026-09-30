"""One-off: generate the darker, cinematic night-blue background for the
PAUSE presentation screen (visual restyle only). Output is reviewed manually.

Run:  python generate_intro_bg.py
"""
import asyncio
import base64
import io
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

from PIL import Image, ImageOps  # noqa: E402
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent  # noqa: E402

MODEL = "gemini-3.1-flash-image-preview"
OUT = ROOT.parent / "memory" / "icons_2026"
REF = ROOT.parent / "memory" / "icons_2026" / "mockup_intro.jpg"

PROMPT = (
    "Vertical portrait 9:16 cinematic illustration for a premium dark mobile app splash screen. "
    "Match the mood, palette and composition of the reference: a very dark navy, almost black "
    "night-blue scene. A calm alpine lake with layered mountains across the middle of the frame; "
    "on the right a lone person silhouette sits on a dark rocky outcrop looking at the horizon. "
    "The horizon has a faint, soft dusk glow in muted blue, cyan and a hint of violet-pink; a few "
    "subtle stars and a faint large moon or planet in the upper right. Deep dark blue / cyan tones "
    "with small purple accents. RAZOR-SHARP, crisp, highly detailed 4K rendering: sharp mountain ridges, crisp rocks and silhouette edges, clear water reflections, NO blur, NO haze, NO fog, NO soft focus, NO mist. "
    "The top 30% of the image must be dark, quiet sky (space for a logo) and the bottom 35% must "
    "fade to near-black dark navy (space for text). No text, no logos, no UI, no bright areas, "
    "elegant and restrained, not saturated."
)


async def main():
    ref_b64 = base64.b64encode(REF.read_bytes()).decode("utf-8")
    chat = LlmChat(
        api_key=os.getenv("EMERGENT_LLM_KEY"),
        session_id="intro-bg-2026",
        system_message="You are a world-class cinematic concept artist.",
    ).with_model("gemini", MODEL).with_params(modalities=["image", "text"])
    _, images = await chat.send_message_multimodal_response(UserMessage(text=PROMPT, file_contents=[ImageContent(ref_b64)]))
    if not images:
        raise RuntimeError("no image returned")
    raw = base64.b64decode(images[0]["data"])
    image = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    out = OUT / "intro_bg_v2.raw.png"
    image.save(out)
    print("saved", out, image.size, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
