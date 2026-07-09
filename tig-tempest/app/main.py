"""TIG · Tempest — app spine (GO-LIVE Phases 1–3).

Serves the game, the ops endpoints (/healthz, /version), and OIDC auth against
Keycloak (/login · /register · /auth/callback · /logout · /me · /account).
Confidential client: tokens stay on the server; the browser gets a signed session
cookie, never a token. Structure mirrors the freehold reference app.
"""
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

import auth
import build_info
import deps
import players
from db import db_check

GAME_DIR = os.getenv("GAME_DIR", str(Path(__file__).resolve().parent.parent / "game"))
TESTKIT_DIR = os.getenv("TESTKIT_DIR", str(Path(__file__).resolve().parent / "testkit"))
APP_ENV = os.getenv("APP_ENV", "dev")

app = FastAPI(title="TIG · Tempest", version="0.3.0-phase3")
# Signed, http-only session cookie. same_site=lax lets the OIDC redirect back in.
app.add_middleware(
    SessionMiddleware, secret_key=deps.SESSION_SECRET,
    same_site="lax", https_only=deps.SESSION_HTTPS_ONLY,
)


@app.get("/healthz")
async def healthz():
    """Liveness — app + DB round-trip."""
    ok, _ = await db_check()
    return JSONResponse({"status": "ok" if ok else "degraded", "env": APP_ENV, "db": ok})


@app.get("/version")
async def version():
    """The truthful build bar the game reads."""
    return JSONResponse({
        "version": build_info.version(), "sha": build_info.sha(),
        "date": build_info.date(), "env": APP_ENV,
    })


# ---- auth (OIDC against Keycloak) -----------------------------------------
@app.get("/login")
async def login(request: Request):
    state, nonce = auth.new_secret(), auth.new_secret()
    verifier, challenge = auth.make_pkce()
    request.session["oauth"] = {"state": state, "nonce": nonce, "cv": verifier}
    redirect_uri = f"{deps.APP_BASE_URL}/auth/callback"
    return RedirectResponse(auth.build_auth_redirect(redirect_uri, state, nonce, challenge))


@app.get("/register")
async def register(request: Request):
    """Self-serve sign-up — Keycloak's registration page. New players land back at
    /auth/callback already logged in (same code path as login)."""
    state, nonce = auth.new_secret(), auth.new_secret()
    verifier, challenge = auth.make_pkce()
    request.session["oauth"] = {"state": state, "nonce": nonce, "cv": verifier}
    redirect_uri = f"{deps.APP_BASE_URL}/auth/callback"
    return RedirectResponse(auth.build_register_redirect(redirect_uri, state, nonce, challenge))


@app.get("/auth/callback")
async def auth_callback(request: Request):
    saved = request.session.get("oauth") or {}
    code = request.query_params.get("code")
    if not code or request.query_params.get("state") != saved.get("state"):
        return HTMLResponse("Login failed: bad or missing state.", status_code=400)
    redirect_uri = f"{deps.APP_BASE_URL}/auth/callback"
    try:
        tokens = await auth.exchange_code(code, redirect_uri, saved["cv"])
        claims = auth.verify_id_token(tokens["id_token"], saved.get("nonce"))
        roles = auth.roles_from_access(tokens["access_token"])
    except Exception as exc:  # noqa: BLE001
        return HTMLResponse(f"Login failed: {exc}", status_code=400)

    request.session.pop("oauth", None)
    username = claims.get("preferred_username")
    request.session["user"] = {
        "username": username,
        "name": claims.get("name") or username,
        "email": claims.get("email"),
        "roles": roles,
    }
    request.session["id_token"] = tokens["id_token"]
    await players.upsert(username, claims.get("name") or username)   # lazy player row
    return RedirectResponse("/account", status_code=303)


@app.get("/logout")
async def logout(request: Request):
    id_token = request.session.get("id_token")
    request.session.clear()
    if id_token:
        return RedirectResponse(auth.logout_redirect(id_token, f"{deps.APP_BASE_URL}/"))
    return RedirectResponse("/")


@app.get("/me")
async def me(request: Request):
    """Who am I? The game reads this to greet the player (JSON, no token)."""
    return JSONResponse({"user": deps.current_user(request)})


@app.get("/account", response_class=HTMLResponse)
async def account(request: Request):
    user = deps.current_user(request)
    if not user:
        return RedirectResponse("/login")
    roles = ", ".join(user.get("roles") or []) or "player"
    return HTMLResponse(_ACCOUNT_HTML.format(
        name=user.get("name") or user["username"], username=user["username"],
        email=user.get("email") or "—", roles=roles, env=APP_ENV.upper(),
    ))


_ACCOUNT_HTML = """<!doctype html><meta charset=utf-8>
<title>TIG · Tempest — account</title>
<body style="margin:0;background:#000;color:#22d3ee;font:16px/1.7 'Courier New',monospace;
 display:flex;min-height:100vh;align-items:center;justify-content:center;text-align:center">
<div>
  <div style="font-size:30px;letter-spacing:5px;color:#fff;text-shadow:0 0 14px #22d3ee">TIG · TEMPEST</div>
  <p style="color:#f59e0b;letter-spacing:2px">SIGNED IN — {env}</p>
  <p>PLAYER <b style="color:#fff">{name}</b><br>
     username <b>{username}</b> · email {email}<br>
     roles <b>{roles}</b></p>
  <p style="margin-top:26px">
    <a href="/" style="color:#22d3ee">▶ PLAY</a> &nbsp;·&nbsp;
    <a href="/logout" style="color:#64748b">SIGN OUT</a>
  </p>
</div></body>"""


# ---- static: test kit, then the game (catch-all, mounted last) ------------
app.mount("/testkit", StaticFiles(directory=TESTKIT_DIR, html=True), name="testkit")
app.mount("/", StaticFiles(directory=GAME_DIR, html=True), name="game")
