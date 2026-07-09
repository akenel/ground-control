"""TIG · Tempest — app spine (GO-LIVE Phases 1–3).

Serves the game, the ops endpoints (/healthz, /version), and OIDC auth against
Keycloak (/login · /register · /auth/callback · /logout · /me · /account).
Confidential client: tokens stay on the server; the browser gets a signed session
cookie, never a token. Structure mirrors the freehold reference app.
"""
import os
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

import auth
import build_info
import deps
import media
import players
import presence
import profiles
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
    prof = await profiles.get(user["username"])
    roles = ", ".join(user.get("roles") or []) or "player"
    banner = media.url(prof.banner_key) if prof and prof.banner_key else ""
    avatar = media.url(prof.avatar_key) if prof and prof.avatar_key else ""
    banner_html = (f"<div style='height:120px;border-radius:10px;margin-bottom:-40px;"
                   f"background:#0a1526 center/cover url({banner})'></div>" if banner else "")
    avatar_html = (f"<img src='{avatar}' style='width:84px;height:84px;border-radius:50%;"
                   f"object-fit:cover;border:2px solid #22d3ee'>" if avatar
                   else "<div style='width:84px;height:84px;border-radius:50%;border:2px dashed #22314a;"
                        "display:inline-block'></div>")
    return HTMLResponse(_ACCOUNT_HTML.format(
        env=APP_ENV.upper(), username=user["username"], email=user.get("email") or "—", roles=roles,
        display_name=(prof.display_name if prof else "") or user.get("name") or user["username"],
        tagline=(prof.tagline if prof else ""), banner_html=banner_html, avatar_html=avatar_html,
    ))


_ACCOUNT_HTML = """<!doctype html><meta charset=utf-8>
<title>TIG · Tempest — account</title>
<body style="margin:0;background:#000;color:#22d3ee;font:15px/1.7 'Courier New',monospace">
<div style="max-width:560px;margin:0 auto;padding:28px 18px">
  <div style="text-align:center;font-size:26px;letter-spacing:5px;color:#fff;text-shadow:0 0 14px #22d3ee">TIG · TEMPEST</div>
  <p style="text-align:center;color:#f59e0b;letter-spacing:2px">YOUR PROFILE — {env}</p>
  {banner_html}
  <div style="text-align:center">{avatar_html}
    <div style="margin-top:6px;font-size:20px;color:#fff">{display_name}</div>
    <div style="color:#64748b">@{username} · {email} · {roles}</div>
    <div style="color:#22d3ee">{tagline}</div>
  </div>
  <hr style="border:0;border-top:1px solid #12203a;margin:22px 0">
  <form method="post" action="/api/profile">
    <label style="color:#64748b;font-size:12px">DISPLAY NAME</label><br>
    <input name="display_name" value="{display_name}" maxlength=120
      style="width:100%;background:#0a1526;border:1px solid #22314a;border-radius:6px;color:#e5eef7;padding:8px;font:14px monospace"><br>
    <label style="color:#64748b;font-size:12px">TAGLINE</label><br>
    <input name="tagline" value="{tagline}" maxlength=160 placeholder="one line of glory"
      style="width:100%;background:#0a1526;border:1px solid #22314a;border-radius:6px;color:#e5eef7;padding:8px;font:14px monospace"><br>
    <button style="margin-top:10px;background:#22d3ee;border:0;border-radius:6px;color:#04141a;padding:8px 16px;font-weight:700;cursor:pointer">SAVE</button>
  </form>
  <div style="display:flex;gap:16px;margin-top:16px;flex-wrap:wrap">
    <form method="post" action="/api/profile/avatar" enctype="multipart/form-data">
      <div style="color:#64748b;font-size:12px">AVATAR (≤3&nbsp;MB)</div>
      <input type="file" name="file" accept="image/*" style="color:#8aa0b8;max-width:200px">
      <button style="background:#0a1526;border:1px solid #22314a;border-radius:6px;color:#22d3ee;padding:6px 12px;cursor:pointer">UPLOAD</button>
    </form>
    <form method="post" action="/api/profile/banner" enctype="multipart/form-data">
      <div style="color:#64748b;font-size:12px">BANNER (≤5&nbsp;MB)</div>
      <input type="file" name="file" accept="image/*" style="color:#8aa0b8;max-width:200px">
      <button style="background:#0a1526;border:1px solid #22314a;border-radius:6px;color:#22d3ee;padding:6px 12px;cursor:pointer">UPLOAD</button>
    </form>
  </div>
  <p style="margin-top:26px;text-align:center">
    <a href="/dashboard" style="color:#22d3ee">DASHBOARD</a> &nbsp;·&nbsp;
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
    avatars = await profiles.avatars_for([u for (u, _, _) in board])
    return JSONResponse({"leaderboard": [
        {"rank": i + 1, "username": u, "best": b, "level": lvl, "avatar": media.url(avatars.get(u))}
        for i, (u, b, lvl) in enumerate(board)
    ]})


# ---- profile: text + image uploads (avatars/banners in MinIO) -------------
@app.post("/api/profile")
async def api_profile(request: Request, display_name: str = Form(""), tagline: str = Form("")):
    user = deps.current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    await profiles.update_text(user["username"], display_name, tagline)
    return RedirectResponse("/account", status_code=303)


async def _save_upload(request: Request, file: UploadFile, field: str, prefix: str, cap: int):
    user = deps.current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if not media.is_image(file.content_type):
        return HTMLResponse("Please upload an image (jpg/png/webp/gif).", status_code=400)
    data = await file.read()
    if len(data) > cap:
        return HTMLResponse("Image too large.", status_code=400)
    key = media.save_image(data, file.content_type, f"{prefix}/{user['username']}")
    await profiles.set_image(user["username"], field, key)
    return RedirectResponse("/account", status_code=303)


@app.post("/api/profile/avatar")
async def api_avatar(request: Request, file: UploadFile = File(...)):
    return await _save_upload(request, file, "avatar_key", "avatars", 3_000_000)


@app.post("/api/profile/banner")
async def api_banner(request: Request, file: UploadFile = File(...)):
    return await _save_upload(request, file, "banner_key", "banners", 5_000_000)


@app.get("/media/{key:path}")
async def media_get(key: str):
    try:
        it, content_type = media.stream(key)
    except Exception:  # noqa: BLE001
        return JSONResponse({"error": "not found"}, status_code=404)
    return StreamingResponse(it, media_type=content_type)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = deps.current_user(request)
    if not user:
        return RedirectResponse("/login")
    un = user["username"]
    prof = await profiles.get(un)
    best = await scores.personal_best(un)
    rk = await scores.rank(un)
    last = await scores.last_score(un)
    recent = await scores.recent(un, 5)
    online = await presence.online()

    avatar = media.url(prof.avatar_key) if prof and prof.avatar_key else ""
    avatar_html = (f"<img src='{avatar}' style='width:64px;height:64px;border-radius:50%;"
                   f"object-fit:cover;border:2px solid #22d3ee;vertical-align:middle'> " if avatar else "")

    last_html = (
        f"{last.points:06d} · LVL {last.level}" if last else "— no runs yet — go play"
    )
    recent_html = "".join(
        f"<tr><td>{r.points:06d}</td><td>LVL {r.level}</td>"
        f"<td>{r.created_at:%Y-%m-%d %H:%M}</td></tr>" for r in recent
    ) or "<tr><td colspan=3 style='color:#64748b'>no runs yet</td></tr>"
    online_html = " · ".join(f"<b>{n}</b>" for n in online) or "<span style='color:#64748b'>just you, so far</span>"

    return HTMLResponse(_DASH_HTML.format(
        name=(prof.display_name if prof and prof.display_name else user.get("name") or un),
        avatar=avatar_html, env=APP_ENV.upper(),
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
    <p>{avatar}PLAYER <b style="color:#fff">{name}</b></p>
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
