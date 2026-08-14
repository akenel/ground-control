#!/usr/bin/env bash
# ⚠️ SUPERSEDED (2026-08-14) — REFERENCE ONLY, DO NOT RUN.
#   Tempest is live as a ROUTE inside Freehold: https://www.wolfhold.app/tempest
#   This script stands up the abandoned standalone tempest-app on
#   dev-tempest.wolfhold.app, and appends a Caddy block you'd then have to clean up.
#   See CLAUDE.md -> CURRENT SITUATION and DEPLOY-SBX.md.
#
# TIG · Tempest — one-shot SBX bring-up, run ON THE WOLFHOLD BOX.
#
#   bash tig-tempest/deploy-box-sbx.sh
#
# Idempotent and safe to re-run. It:
#   1. generates any missing secrets into tig-tempest/.env
#   2. brings up the tempest stack (app + db + minio) on freehold's network
#   3. provisions the tempest-sbx realm into the shared Keycloak (for login)
#   4. ensures freehold's Caddy has the dev-tempest block, then reloads it
#   5. verifies https://dev-tempest.wolfhold.app/healthz
# A failure in step 3 does NOT stop the game going live — login just waits.
set -uo pipefail
cd "$(dirname "$0")"                       # -> tig-tempest/
say(){ printf '\n\033[1;36m### %s\033[0m\n' "$*"; }
FREEHOLD="${FREEHOLD_DIR:-$HOME/freehold}"
COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.sbx.yml)

say "1) secrets — fill any missing value in .env"
[ -f .env ] || cp deploy/sbx.env.example .env
gen(){ openssl rand -base64 36 | tr -d '\n/+=' | cut -c1-40; }
for k in POSTGRES_PASSWORD MINIO_ROOT_PASSWORD KC_CLIENT_SECRET SESSION_SECRET; do
  if grep -q "^$k=change_me" .env || ! grep -q "^$k=" .env; then
    v="$(gen)"
    if grep -q "^$k=" .env; then sed -i "s|^$k=.*|$k=$v|" .env; else echo "$k=$v" >> .env; fi
    echo "  generated $k"
  else echo "  kept $k"; fi
done

say "2) bring up tempest stack (app + db + minio)"
"${COMPOSE[@]}" up -d --build

say "3) provision the tempest-sbx realm into the shared Keycloak"
ADMPW="$(grep -E '^(KC_BOOTSTRAP_ADMIN_PASSWORD|KEYCLOAK_ADMIN_PASSWORD)=' "$FREEHOLD/.env" 2>/dev/null | head -1 | cut -d= -f2-)"
CSECRET="$(grep -E '^KC_CLIENT_SECRET=' .env | cut -d= -f2-)"
if [ -n "$ADMPW" ]; then
  KC_ADMIN_URL=https://auth.wolfhold.app KC_ADMIN_USER="${KC_ADMIN_USER:-admin}" \
  KC_ADMIN_PASSWORD="$ADMPW" KC_CLIENT_SECRET="$CSECRET" \
    python3 ops/provision-realm.py \
    || echo "  !! realm step failed — game still serves; login works once this succeeds"
else
  echo "  !! couldn't read Keycloak admin pw from $FREEHOLD/.env — skipping realm; game serves, login later"
fi

say "4) publish + reload freehold's Caddy"
grep -q 'dev-tempest.wolfhold.app' "$FREEHOLD/Caddyfile.prod" \
  || printf '\ndev-tempest.wolfhold.app {\n\timport sec\n\treverse_proxy tempest-app:8000\n}\n' >> "$FREEHOLD/Caddyfile.prod"
docker exec freehold-caddy-1 caddy reload --config /etc/caddy/Caddyfile && echo "  Caddy reloaded"

say "5) verify (waiting a few seconds for the cert)"
sleep 8
"${COMPOSE[@]}" ps
curl -sS -o /dev/null -w '  dev-tempest -> HTTP %{http_code}\n' https://dev-tempest.wolfhold.app/healthz || true
echo
echo "Done. Open https://dev-tempest.wolfhold.app  — first load fetches the Let's Encrypt cert."
