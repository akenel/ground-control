#!/bin/sh
# TIG · Tempest — container start. Migrate, then serve (freehold pattern:
# a fresh `up -d` self-migrates). Phase 2+ has a DB; alembic upgrade is idempotent.
set -e
echo "→ TIG · Tempest — migrations: alembic upgrade head"
alembic upgrade head
echo "→ starting app"
exec uvicorn main:app --host 0.0.0.0 --port 8000
