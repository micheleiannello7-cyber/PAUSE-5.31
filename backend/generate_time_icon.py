"""One-off: 3D clock icon for the reader info card ("Tempo di lettura"), same
pipeline and art direction as the CTA icons (generate_cta_icons.py).

Run once:  python generate_time_icon.py
Output:    ../frontend/assets/images/kind-clock.png (512x512 RGBA)
"""
import asyncio
import base64

import requests

from generate_cta_icons import STYLE, STYLE_REF, generate

PROMPT = STYLE + (
    "The object: a round analog stopwatch / alarm clock seen from a slight "
    "three-quarter front angle, saturated violet-purple body with a soft "
    "cream-white clock face, thick cyan-blue minute and hour hands, small "
    "round button on top, representing reading time."
)


async def main():
    ref_b64 = base64.b64encode(requests.get(STYLE_REF, timeout=60).content).decode("utf-8")
    await generate("kind-clock.png", PROMPT, ref_b64)


if __name__ == "__main__":
    asyncio.run(main())
