# Auth Service — Google OAuth2 + JWT

A standalone Python authentication service built with **FastAPI**. It authenticates users
via Google OAuth2, issues JWT tokens, and exposes a `/auth/verify` endpoint so other
applications can validate tokens without knowing anything about Google.

## Architecture

```
Browser / App          Auth Service            Other Apps
─────────────    ──────────────────────    ─────────────────
GET /auth/google ──▶  redirect to Google
                       Google callback ──▶  mint JWT from Google user info
                       issue JWT ──────────────────────────────▶
                                            POST /auth/verify
                                               (token check)
```

Fully stateless — no database. Google user info (id, email, name, picture) is embedded
directly in the JWT. Redis is used only to blacklist tokens on logout.

**Services (docker-compose)**

| Container  | Port | Purpose                         |
|------------|------|---------------------------------|
| auth-app   | 8000 | FastAPI auth service            |
| redis      | 6379 | Token blacklist (logout/revoke) |

---

## Quick Start

### 1. Google OAuth credentials

1. Go to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
2. Create an **OAuth 2.0 Client ID** (Web application)
3. Add `http://localhost:8000/auth/google/callback` to **Authorized redirect URIs**
4. Copy the Client ID and Client Secret

### 2. Configure environment

```bash
cp .env.example .env
# edit .env and fill in:
#   GOOGLE_CLIENT_ID
#   GOOGLE_CLIENT_SECRET
#   SECRET_KEY      (generate: python -c "import secrets; print(secrets.token_hex(32))")
#   SERVICE_API_KEY (generate: python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### 3. Start everything

```bash
docker-compose up --build
```

The API is live at **http://localhost:8000**
Interactive docs at **http://localhost:8000/docs**

---

## API Reference

### Auth endpoints (`/auth/...`)

| Method | Path                    | Auth        | Description                                   |
|--------|-------------------------|-------------|-----------------------------------------------|
| GET    | `/auth/google`          | —           | Redirect to Google login                      |
| GET    | `/auth/google/callback` | —           | Google calls this; returns tokens             |
| POST   | `/auth/refresh`         | refresh JWT | Get new access + refresh token pair           |
| POST   | `/auth/logout`          | Bearer JWT  | Blacklist current token                       |
| GET    | `/auth/me`              | Bearer JWT  | Current user profile (from JWT payload)       |
| POST   | `/auth/verify`          | —           | Verify a JWT and return user (for other apps) |

---

## How Other Apps Integrate

### Option A — Browser-based login with redirect

Send the user to:
```
http://localhost:8000/auth/google?redirect_after=http://yourapp.com/auth/callback
```
After Google login, the auth service redirects to:
```
http://yourapp.com/auth/callback?access_token=<jwt>&refresh_token=<jwt>
```

### Option B — Verify a token server-side

```python
import httpx

resp = httpx.post("http://localhost:8000/auth/verify", json={"token": user_token})
data = resp.json()   # {"valid": true, "user": {"email": "...", "name": "...", ...}}
```

See `example-client/client.py` for a full working example.

---

## Token flow

```
Access token   — short-lived (default 30 min), used for all API calls
Refresh token  — long-lived (default 7 days), used only to get a new access token
Logout         — blacklists the access token in Redis until it naturally expires
```

---

## Development

```bash
# Run locally without Docker (needs Redis already running)
pip install -r requirements.txt
uvicorn app.main:app --reload
```
