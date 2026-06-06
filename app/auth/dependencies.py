import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import decode_token, user_from_payload
from app.config import get_settings
from app.schemas import GoogleUser

settings = get_settings()

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    redis: aioredis.Redis = Depends(get_redis),
) -> GoogleUser:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise exc

    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise exc

    blacklisted = await redis.get(f"blacklist:{credentials.credentials}")
    if blacklisted:
        raise exc

    return user_from_payload(payload)


async def require_service_api_key(api_key: str = Security(api_key_header)) -> str:
    if api_key != settings.SERVICE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid service API key",
        )
    return api_key
