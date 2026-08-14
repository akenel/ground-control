"""Shared config + session helpers (freehold's deps.py, trimmed for Tempest)."""
import os

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse

APP_ENV = os.getenv("APP_ENV", "dev")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8080").rstrip("/")
SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-session-secret-change-me")
SESSION_HTTPS_ONLY = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"


def current_user(request: Request):
    """The logged-in player, or None. {username, name, email, roles}."""
    return request.session.get("user")


def require_admin(request: Request):
    user = current_user(request)
    return user if user and "admin" in user.get("roles", []) else None


def admin_or_deny(request: Request):
    """(user, None) for admins; (None, redirect) when logged out; (None, 403) otherwise."""
    user = current_user(request)
    if not user:
        return None, RedirectResponse("/login")
    if "admin" not in user.get("roles", []):
        return None, HTMLResponse("Forbidden — admins only.", status_code=403)
    return user, None
