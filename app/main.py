import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router
from app.config import get_settings
from app.schemas import HealthResponse

logging.basicConfig(level=logging.INFO)

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Stateless Google OAuth2 auth service. "
        "No database — Google user info is embedded in JWT tokens. "
        "Other apps call /auth/verify to validate tokens."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health():
    return HealthResponse(status="ok", service=settings.APP_NAME)
