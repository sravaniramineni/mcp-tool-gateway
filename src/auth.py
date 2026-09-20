"""Scoped token auth for the tool gateway (HMAC-based starter)."""
import hashlib
import hmac
import os
import time

SECRET = os.environ.get("GATEWAY_SECRET", "dev-secret-change-me")
TOKEN_TTL = 3600

def issue_token(subject: str, scopes: list[str]) -> str:
    expiry = int(time.time()) + TOKEN_TTL
    payload = f"{subject}:{'|'.join(sorted(scopes))}:{expiry}"
    sig = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"

def verify_token(token: str) -> dict | None:
    try:
        *rest, sig = token.split(":")
        payload = ":".join(rest)
        expected = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        subject, scopes, expiry = payload.split(":", 2)
        if int(expiry) < time.time():
            return None
        return {"subject": subject, "scopes": scopes.split("|")}
    except Exception:
        return None
