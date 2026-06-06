from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from app.config import get_settings
from app.schemas import GoogleUser

settings = get_settings()


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user: GoogleUser) -> str:
    expire = _now_utc() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user.google_id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "type": "access",
        "exp": expire,
        "iat": _now_utc(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user: GoogleUser) -> str:
    expire = _now_utc() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user.google_id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "type": "refresh",
        "exp": expire,
        "iat": _now_utc(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


def user_from_payload(payload: dict) -> GoogleUser:
    return GoogleUser(
        google_id=payload["sub"],
        email=payload["email"],
        name=payload["name"],
        picture=payload.get("picture"),
    )
