"""One-off: generate 3D glossy action icons (like/save/share) matching the
existing app icon style (kind-*.png). Output PNGs with transparent background.
Run: python gen_action_icons.py"""
import asyncio
import os
import base64
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

load_dotenv()

API_KEY = os.getenv("EMERGENT_LLM_KEY")
REF = os.path.join(os.path.dirname(__file__), "..", "frontend", "assets", "images", "kind-headphones.png")
OUT = os.path.join(os.path.dirname(__file__), "gen_out")
os.makedirs(OUT, exist_ok=True)

STYLE = (
    "Match EXACTLY the 3D render style of the reference image: a single glossy "
    "rounded 3D icon object, soft studio lighting, smooth matte-glossy plastic "
    "material with soft highlights and gentle soft shadow, clean, centered, "
    "fully isolated on a transparent background (alpha), no ground plane, no "
    "text, no extra elements. Same proportions and polish as the reference."
)

JOBS = [
    ("heart-base", "A single 3D heart icon in soft muted lavender-grey purple, "
        "looking inactive/empty/unselected, subtle and desaturated. " + STYLE),
    ("heart-active", "A single vibrant glossy 3D heart icon in warm coral red "
        "(#FF6B5E), fully filled, looking lit/selected and lively. " + STYLE),
    ("bookmark-base", "A single 3D bookmark ribbon icon (vertical ribbon with a "
        "notched bottom) in soft muted lavender-grey purple, looking "
        "inactive/empty/unselected, subtle and desaturated. " + STYLE),
    ("bookmark-active", "A single vibrant glossy 3D bookmark ribbon icon "
        "(vertical ribbon with a notched bottom) in bright cyan-teal (#22C7E0), "
        "fully filled, looking lit/selected. " + STYLE),
    ("share", "A single 3D share icon: three rounded spheres connected by two "
        "rounded bars forming the classic share/network symbol, in glossy "
        "purple with one cyan accent sphere. " + STYLE),
]


async def gen(ref_b64: str, name: str, prompt: str):
    chat = LlmChat(api_key=API_KEY, session_id=f"icon-{name}", system_message="You generate 3D icon assets.")
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
    msg = UserMessage(text=prompt, file_contents=[ImageContent(ref_b64)])
    _, images = await chat.send_message_multimodal_response(msg)
    if not images:
        print(f"[{name}] NO IMAGE returned")
        return
    data = base64.b64decode(images[0]["data"])
    path = os.path.join(OUT, f"{name}.png")
    with open(path, "wb") as f:
        f.write(data)
    print(f"[{name}] saved {len(data)} bytes -> {path}")


async def main():
    with open(REF, "rb") as f:
        ref_b64 = base64.b64encode(f.read()).decode("utf-8")
    for name, prompt in JOBS:
        try:
            await gen(ref_b64, name, prompt)
        except Exception as e:
            print(f"[{name}] ERROR {e}")


if __name__ == "__main__":
    asyncio.run(main())
