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
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

import auth
import build_info
import deps
import players
import presence
import scores
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
    return RedirectResponse("/dashboard", status_code=303)


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


# ---- scores · presence · leaderboard · dashboard --------------------------
class ScoreIn(BaseModel):
    points: int
    level: int = 1
    waves: int = 0
    duration_ms: int = 0


@app.post("/api/scores")
async def api_submit_score(body: ScoreIn, request: Request):
    """The game POSTs a finished run here (same-origin, session cookie). Basic
    sanity clamps only — real anti-cheat (plausibility + game token) is Phase 6."""
    user = deps.current_user(request)
    if not user:
        return JSONResponse({"error": "not signed in"}, status_code=401)
    pts = max(0, min(body.points, 10_000_000))
    lvl = max(1, min(body.level, 999))
    await scores.submit(user["username"], pts, lvl, max(0, body.waves), max(0, body.duration_ms))
    return JSONResponse({
        "ok": True,
        "best": await scores.personal_best(user["username"]),
        "rank": await scores.rank(user["username"]),
    })


@app.post("/api/ping")
async def api_ping(request: Request):
    """Presence heartbeat. Returns who's online now."""
    user = deps.current_user(request)
    if not user:
        return JSONResponse({"online": [], "count": 0})
    await presence.ping(user["username"])
    names = await presence.online()
    return JSONResponse({"online": names, "count": len(names)})


@app.get("/api/leaderboard")
async def api_leaderboard():
    """Public: each player's personal best, ranked (the Phase 5 page reads this)."""
    board = await scores.leaderboard(20)
    return JSONResponse({"leaderboard": [
        {"rank": i + 1, "username": u, "best": b, "level": lvl}
        for i, (u, b, lvl) in enumerate(board)
    ]})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = deps.current_user(request)
    if not user:
        return RedirectResponse("/login")
    un = user["username"]
    best = await scores.personal_best(un)
    rk = await scores.rank(un)
    last = await scores.last_score(un)
    recent = await scores.recent(un, 5)
    online = await presence.online()

    last_html = (
        f"{last.points:06d} · LVL {last.level}" if last else "— no runs yet — go play"
    )
    recent_html = "".join(
        f"<tr><td>{r.points:06d}</td><td>LVL {r.level}</td>"
        f"<td>{r.created_at:%Y-%m-%d %H:%M}</td></tr>" for r in recent
    ) or "<tr><td colspan=3 style='color:#64748b'>no runs yet</td></tr>"
    online_html = " · ".join(f"<b>{n}</b>" for n in online) or "<span style='color:#64748b'>just you, so far</span>"

    return HTMLResponse(_DASH_HTML.format(
        name=user.get("name") or un, env=APP_ENV.upper(),
        best=f"{best:06d}", rank=(f"#{rk}" if rk else "—"),
        last=last_html, recent=recent_html, online=online_html,
        admin=(" · <a href='/console' style='color:#f59e0b'>ADMIN</a>" if "admin" in (user.get("roles") or []) else ""),
    ))


_DASH_HTML = """<!doctype html><meta charset=utf-8>
<title>TIG · Tempest — dashboard</title>
<body style="margin:0;background:#000;color:#22d3ee;font:15px/1.7 'Courier New',monospace">
<div style="max-width:640px;margin:0 auto;padding:32px 18px">
  <div style="text-align:center">
    <div style="font-size:30px;letter-spacing:5px;color:#fff;text-shadow:0 0 14px #22d3ee">TIG · TEMPEST</div>
    <div style="color:#f59e0b;letter-spacing:2px">DASHBOARD — {env}</div>
    <p>PLAYER <b style="color:#fff">{name}</b></p>
  </div>
  <div style="display:flex;gap:14px;justify-content:center;margin:18px 0">
    <div style="border:1px solid #22314a;border-radius:10px;padding:14px 22px;text-align:center">
      <div style="color:#64748b;font-size:12px">PERSONAL BEST</div>
      <div style="font-size:26px;color:#fff">{best}</div></div>
    <div style="border:1px solid #22314a;border-radius:10px;padding:14px 22px;text-align:center">
      <div style="color:#64748b;font-size:12px">RANK</div>
      <div style="font-size:26px;color:#f59e0b">{rank}</div></div>
  </div>
  <p>LAST RUN &nbsp; <b style="color:#fff">{last}</b></p>
  <p style="color:#64748b;margin-bottom:4px">RECENT RUNS</p>
  <table style="width:100%;border-collapse:collapse">{recent}</table>
  <p style="margin-top:22px">🟢 ONLINE NOW &nbsp; {online}</p>
  <p style="margin-top:26px;text-align:center">
    <a href="/" style="color:#22d3ee">▶ PLAY</a> &nbsp;·&nbsp;
    <a href="/account" style="color:#64748b">ACCOUNT</a> &nbsp;·&nbsp;
    <a href="/logout" style="color:#64748b">SIGN OUT</a>{admin}
  </p>
</div>
<style>td{{padding:4px 8px;border-bottom:1px solid #12203a}}</style>
</body>"""


# ---- static: test kit, then the game (catch-all, mounted last) ------------
app.mount("/testkit", StaticFiles(directory=TESTKIT_DIR, html=True), name="testkit")
app.mount("/", StaticFiles(directory=GAME_DIR, html=True), name="game")
