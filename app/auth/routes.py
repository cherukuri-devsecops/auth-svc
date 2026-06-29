from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlencode, urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

import redis.asyncio as aioredis
from app.auth.dependencies import get_current_user, get_redis
from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    user_from_payload,
)
from app.config import get_settings
from app.schemas import GoogleUser, RefreshRequest, TokenResponse, VerifyTokenRequest, VerifyTokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# Restrict redirect destinations to known-safe in-app routes.
ALLOWED_REDIRECT_PATHS = {
    "/",
}


def _resolve_allowed_redirect_target(target: Optional[str]) -> Optional[str]:
    if not target:
        return None
    normalized = target.strip()
    if normalized in ALLOWED_REDIRECT_PATHS:
        return normalized
    return None


@router.get("/google")
async def google_login(
    redirect_after: Optional[str] = Query(None, description="URL to forward tokens to after login"),
):
    """Redirect user to Google login. Pass redirect_after to send tokens to your app."""
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",   # no offline — we don't store anything
        "state": redirect_after or "",
    }
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@router.get("/google/callback")
async def google_callback(code: str, state: Optional[str] = None):
    """
    Google redirects here after login. Fetches user info from Google,
    mints JWT tokens (no DB write), and either returns JSON or redirects
    to the caller app.
    """
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange Google auth code")

        google_tokens = token_resp.json()

        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {google_tokens['access_token']}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch Google user info")

        info = userinfo_resp.json()

    user = GoogleUser(
        google_id=info["sub"],
        email=info["email"],
        name=info.get("name", info["email"]),
        picture=info.get("picture"),
    )

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    safe_redirect_target = _resolve_allowed_redirect_target(state)
    if safe_redirect_target:
        params = urlencode({"access_token": access_token, "refresh_token": refresh_token})
        return RedirectResponse(f"{safe_redirect_target}?{params}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    redis: aioredis.Redis = Depends(get_redis),
):
    """Exchange a valid refresh token for a new token pair (no Google round-trip)."""
    blacklisted = await redis.get(f"blacklist:{body.refresh_token}")
    if blacklisted:
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    payload = decode_token(body.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = user_from_payload(payload)
    access_token = create_access_token(user)
    new_refresh_token = create_refresh_token(user)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: GoogleUser = Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Blacklist the current access token so it cannot be reused."""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if token:
        payload = decode_token(token)
        if payload:
            ttl = max(int(payload["exp"] - datetime.now(timezone.utc).timestamp()), 1)
            await redis.setex(f"blacklist:{token}", ttl, "1")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=GoogleUser)
async def get_me(current_user: GoogleUser = Depends(get_current_user)):
    """Return the user info embedded in the current JWT (no DB call)."""
    return current_user


@router.post("/verify", response_model=VerifyTokenResponse)
async def verify_token(
    body: VerifyTokenRequest,
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Service-to-service: verify a JWT and return the embedded Google user.
    Other apps call this — no API key required, the token is the credential.
    """
    payload = decode_token(body.token)
    if payload is None or payload.get("type") != "access":
        return VerifyTokenResponse(valid=False, error="Invalid or expired token")

    blacklisted = await redis.get(f"blacklist:{body.token}")
    if blacklisted:
        return VerifyTokenResponse(valid=False, error="Token has been revoked")

    return VerifyTokenResponse(valid=True, user=user_from_payload(payload))
