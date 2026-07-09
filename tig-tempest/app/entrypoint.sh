#!/bin/sh
# TIG · Tempest — container start.
# Phase 1 is serve-only (no DB, no migrations). Later phases add
# `alembic upgrade head` here, mirroring freehold, so `up -d` self-migrates.
set -e
echo "→ TIG · Tempest starting (Phase 1: serve-only, no DB)"
exec uvicorn main:app --host 0.0.0.0 --port 8000
