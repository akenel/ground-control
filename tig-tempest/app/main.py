"""TIG · Tempest — app spine (GO-LIVE Phase 1).

Wraps the existing canvas game in a thin server: it serves the game unchanged at
/, and exposes the two honest ops endpoints — /healthz (liveness) and /version
(the build bar: sha · date · build number). No auth, no database yet; those arrive
in later GO-LIVE phases. Structure mirrors the freehold reference app so the deploy
tooling and the /version stamp behave identically across both.
"""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import build_info

# Where the game lives. Baked into the image at /srv/game; overridable for local dev.
GAME_DIR = os.getenv("GAME_DIR", str(Path(__file__).resolve().parent.parent / "game"))
# Interactive test scripts (served at /testkit/), next to the app.
TESTKIT_DIR = os.getenv("TESTKIT_DIR", str(Path(__file__).resolve().parent / "testkit"))
APP_ENV = os.getenv("APP_ENV", "dev")

app = FastAPI(title="TIG · Tempest", version="0.1.0-phase1")


@app.get("/healthz")
async def healthz():
    """Liveness probe. No DB to check yet — Phase 2 adds it."""
    return JSONResponse({"status": "ok", "env": APP_ENV})


@app.get("/version")
async def version():
    """The truthful build bar the game reads: 'dev' until a deploy stamps build-sha.txt."""
    return JSONResponse({
        "version": build_info.version(),
        "sha": build_info.sha(),
        "date": build_info.date(),
        "env": APP_ENV,
    })


# Interactive test scripts (TEST-TMP-P1, …) at /testkit/. Mounted before the
# catch-all game mount so /testkit wins.
app.mount("/testkit", StaticFiles(directory=TESTKIT_DIR, html=True), name="testkit")

# The game itself, served unchanged. html=True makes "/" resolve to index.html.
# Mounted LAST so the explicit routes + /testkit above win.
app.mount("/", StaticFiles(directory=GAME_DIR, html=True), name="game")
