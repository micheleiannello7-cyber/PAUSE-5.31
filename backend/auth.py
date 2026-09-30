"""PAUSE — autenticazione account (Google via Emergent Auth, Sign in with Apple).

Collezioni:
  users          {user_id, email, name, picture, provider, apple_sub, created_at}
  user_sessions  {session_token, user_id, created_at, expires_at}

Lo `user_id` dell'account (`user_<hex>`) è lo stesso identificativo che il
frontend usa per `user_state`: dopo il login l'app adotta questo id, così
progressi/preferiti restano legati all'account e non al dispositivo.
"""
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
import jwt
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

EMERGENT_SESSION_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"
APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"
SESSION_DAYS = 7

_apple_jwks = jwt.PyJWKClient(APPLE_JWKS_URL, cache_keys=True)


def _apple_audiences() -> list[str]:
    raw = os.environ.get("APPLE_AUDIENCES", "")
    return [a.strip() for a in raw.split(",") if a.strip()]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _public_user(doc: dict) -> dict:
    return {
        "user_id": doc["user_id"],
        "email": doc.get("email"),
        "name": doc.get("name"),
        "picture": doc.get("picture"),
        "provider": doc.get("provider"),
    }


class SessionExchange(BaseModel):
    session_id: str


class AppleSignIn(BaseModel):
    identity_token: str
    full_name: Optional[str] = None
    email: Optional[str] = None


async def ensure_auth_indexes(db) -> None:
    await db.users.create_index("user_id", unique=True)
    await db.users.create_index("email", unique=True, sparse=True)
    await db.users.create_index("apple_sub", unique=True, sparse=True)
    await db.user_sessions.create_index("session_token", unique=True)
    await db.user_sessions.create_index("user_id")
    await db.user_sessions.create_index("expires_at", expireAfterSeconds=0)


def create_auth_router(db) -> APIRouter:
    router = APIRouter(prefix="/api/auth")

    async def _create_session(user_id: str) -> str:
        token = uuid.uuid4().hex + uuid.uuid4().hex
        now = _now()
        await db.user_sessions.insert_one({
            "session_token": token,
            "user_id": user_id,
            "created_at": now,
            "expires_at": now + timedelta(days=SESSION_DAYS),
        })
        return token

    async def _current_user(request: Request) -> dict:
        header = request.headers.get("authorization") or ""
        if not header.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")
        token = header[7:].strip()
        sess = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
        if not sess or _aware(sess["expires_at"]) < _now():
            raise HTTPException(status_code=401, detail="Session expired")
        user = await db.users.find_one({"user_id": sess["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user

    @router.post("/session")
    async def exchange_session(body: SessionExchange):
        """Google (Emergent Auth): scambia il session_id one-shot con una sessione nostra."""
        try:
            async with httpx.AsyncClient(timeout=15) as http:
                res = await http.get(EMERGENT_SESSION_URL, headers={"X-Session-ID": body.session_id})
        except httpx.HTTPError as exc:
            logger.warning("Emergent auth unreachable: %s", exc)
            raise HTTPException(status_code=401, detail="Invalid session")
        if res.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        data = res.json()
        email = (data.get("email") or "").strip().lower()
        if not email:
            raise HTTPException(status_code=401, detail="Invalid session")

        user = await db.users.find_one({"email": email}, {"_id": 0})
        if user:
            patch = {}
            if data.get("name") and not user.get("name"):
                patch["name"] = data["name"]
            if data.get("picture") and data["picture"] != user.get("picture"):
                patch["picture"] = data["picture"]
            if patch:
                await db.users.update_one({"user_id": user["user_id"]}, {"$set": patch})
                user.update(patch)
        else:
            user = {
                "user_id": f"user_{uuid.uuid4().hex[:12]}",
                "email": email,
                "name": data.get("name"),
                "picture": data.get("picture"),
                "provider": "google",
                "created_at": _now(),
            }
            await db.users.insert_one(dict(user))
        token = await _create_session(user["user_id"])
        return {"session_token": token, "user": _public_user(user)}

    @router.post("/apple")
    async def apple_sign_in(body: AppleSignIn):
        audiences = _apple_audiences()
        if not audiences:
            raise HTTPException(status_code=503, detail="Apple sign-in not configured")
        try:
            key = _apple_jwks.get_signing_key_from_jwt(body.identity_token).key
            claims = jwt.decode(
                body.identity_token, key, algorithms=["RS256"], audience=audiences, issuer=APPLE_ISSUER,
            )
        except jwt.PyJWTError as exc:
            logger.info("Apple token rejected: %s", exc)
            raise HTTPException(status_code=401, detail="Invalid Apple token")

        sub = claims["sub"]
        email = (body.email or claims.get("email") or "").strip().lower() or None
        user = await db.users.find_one({"apple_sub": sub}, {"_id": 0})
        if user:
            # Nome/email arrivano solo al primo accesso: non sovrascrivere mai con null.
            patch = {}
            if body.full_name and not user.get("name"):
                patch["name"] = body.full_name
            if email and not user.get("email"):
                patch["email"] = email
            if patch:
                await db.users.update_one({"user_id": user["user_id"]}, {"$set": patch})
                user.update(patch)
        else:
            # Stessa email già registrata con Google → stesso account, si collega Apple.
            user = await db.users.find_one({"email": email}, {"_id": 0}) if email else None
            if user:
                await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"apple_sub": sub}})
                user["apple_sub"] = sub
            else:
                user = {
                    "user_id": f"user_{uuid.uuid4().hex[:12]}",
                    "apple_sub": sub,
                    "email": email,
                    "name": body.full_name,
                    "picture": None,
                    "provider": "apple",
                    "created_at": _now(),
                }
                await db.users.insert_one(dict(user))
        token = await _create_session(user["user_id"])
        return {"session_token": token, "user": _public_user(user)}

    @router.get("/me")
    async def me(request: Request):
        return _public_user(await _current_user(request))

    @router.post("/logout")
    async def logout(request: Request):
        header = request.headers.get("authorization") or ""
        if header.lower().startswith("bearer "):
            await db.user_sessions.delete_one({"session_token": header[7:].strip()})
        return {"ok": True}

    return router
