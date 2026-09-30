"""Keep paid narration off unless explicitly enabled independently of image AI."""
import os

from dotenv import load_dotenv
from fastapi import HTTPException, Request

load_dotenv()


async def check_optional_services(request: Request) -> None:
    """An image-generation key must not implicitly enable paid audio endpoints."""
    if request.url.path.startswith("/api/tts/") and os.getenv("TTS_ENABLED", "false").lower() != "true":
        raise HTTPException(status_code=503, detail="Audio generation is currently disabled")