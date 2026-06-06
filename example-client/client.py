"""
Example: how another app integrates with the auth service.

Usage:
    python client.py verify <access_token>
    python client.py me <access_token>
"""
import json
import sys

import httpx

AUTH_SERVICE = "http://localhost:8000"


def verify_token(token: str) -> dict:
    """Check whether a JWT issued by the auth service is still valid."""
    resp = httpx.post(f"{AUTH_SERVICE}/auth/verify", json={"token": token})
    resp.raise_for_status()
    return resp.json()


def get_me(token: str) -> dict:
    """Return the Google user embedded in the JWT."""
    resp = httpx.get(
        f"{AUTH_SERVICE}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    token = sys.argv[2] if len(sys.argv) > 2 else ""

    if cmd == "verify" and token:
        result = verify_token(token)
    elif cmd == "me" and token:
        result = get_me(token)
    else:
        print(__doc__)
        sys.exit(0)

    print(json.dumps(result, indent=2, default=str))
