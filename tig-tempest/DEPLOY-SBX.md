# DEPLOY — Tempest → SBX (dev-tempest.wolfhold.app)

*Runbook you run **on the wolfhold box** (167.233.125.248), not the laptop. Own
stack (app + Postgres + MinIO), shared front door (freehold's Caddy) and shared
Keycloak (`auth.wolfhold.app`). Real HTTPS, $0. Gets Phases 1–5 live: the game +
accounts + leaderboard.*

**Prereqs (already true):** DNS `dev-tempest.wolfhold.app → 167.233.125.248` is live;
freehold is up on the box in prod (its Caddy owns 80/443, its Keycloak serves
`auth.wolfhold.app`); ports 80/443 open.

---

## 1. Code + secrets on the box

```bash
cd ~                        # wherever you keep repos on the box
git clone https://github.com/akenel/ground-control.git   # first time
cd ground-control && git checkout tempest-go-live && git pull
cd tig-tempest

cp deploy/sbx.env.example .env
#   edit .env: set POSTGRES_PASSWORD, MINIO_ROOT_PASSWORD, KC_CLIENT_SECRET,
#   SESSION_SECRET — every change_me. Generate: openssl rand -base64 36
```

## 2. Provision the `tempest-sbx` realm into the shared Keycloak

The shared Keycloak is already running, so the realm is added **live** (it won't
re-import). This creates the realm, the `tempest-web` client, roles, and the
demo/cap users, and sets the client secret to match your `.env`.

```bash
# KC_ADMIN_PASSWORD = your Keycloak bootstrap admin pw (freehold's
#   KC_BOOTSTRAP_ADMIN_PASSWORD, in freehold's .env). KC_CLIENT_SECRET must equal
#   the one you put in tig-tempest/.env above.
KC_ADMIN_URL=https://auth.wolfhold.app \
KC_ADMIN_USER=admin \
KC_ADMIN_PASSWORD='<keycloak-admin-password>' \
KC_CLIENT_SECRET='<same-as-.env>' \
  python3 ops/provision-realm.py
```
Expect: `✓ created realm 'tempest-sbx' … ✓ 'tempest-web' client secret aligned`.
Idempotent — safe to re-run (e.g. after rotating the secret).

## 3. Confirm freehold's network name, then start the stack

```bash
docker network ls | grep freehold        # expect: freehold_freehold
#   (if different, edit `name:` in docker-compose.sbx.yml)

# optional: stamp the real build into /version (else it reads "dev")
printf '%s\n%s\n%s\n' "$(git rev-parse --short HEAD)" "$(date -u +%Y-%m-%d)" "$(git rev-list --count HEAD)" > app/build-sha.txt

docker compose -f docker-compose.yml -f docker-compose.sbx.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.sbx.yml ps
```
This runs `tempest-app` + `tempest-db` + `tempest-minio`. The app joins freehold's
network so its Caddy can reach it and it can reach freehold's Keycloak internally.

## 4. Publish the hostname in freehold's Caddy

**First, clear any stale `dev-tempest` entry.** The box symptom — TLS
`internal error` / ACME challenge timeout — is a hostname block resolving to an
inert loopback default (unset var → `localhost:20xx`), so no cert is ever issued.
Find and remove it before adding the real one:

```bash
grep -rn 'dev-tempest' ~/path/to/freehold/Caddyfile.prod
#   if a templated/inert line exists (e.g. reverse_proxy {$TEMPEST_UPSTREAM:localhost:20xx}),
#   delete that whole block — the hard-coded one below replaces it.
```

Then in your **freehold** repo on the box, open `Caddyfile.prod` and add:

```caddy
# ---- TIG · Tempest — SBX ----
dev-tempest.wolfhold.app {
	import sec
	reverse_proxy tempest-app:8000
}
```
Reload Caddy (no downtime):
```bash
docker exec freehold-caddy-1 caddy reload --config /etc/caddy/Caddyfile
```
> **Persist it:** commit that block to your freehold repo, or a future freehold
> redeploy will drop it. It's the only freehold change.

## 5. Verify

```bash
# TLS first — the handshake should now succeed (was: tlsv1 internal error).
# First hit triggers cert issuance; give it a few seconds, then it's cached.
curl -sS -o /dev/null -w 'TLS %{http_code} (ssl_verify=%{ssl_verify_result})\n' https://dev-tempest.wolfhold.app/healthz
curl -s https://dev-tempest.wolfhold.app/healthz     # {"status":"ok","env":"sandbox","db":true}
curl -s https://dev-tempest.wolfhold.app/version     # "env":"sandbox"
```
Then in a browser:
- **https://dev-tempest.wolfhold.app** — the game, green padlock, build bar `· SANDBOX`.
- Click **▶ SIGN IN** → Keycloak login (realm tempest-sbx) → sign in `demo`/`demo`
  (or `cap`/`cap` for admin) → lands on **/dashboard**.
- Play a round → your score records → **/leaderboard** shows you.
- **/account** → set a display name + upload an avatar.

First load of each hostname takes a few seconds while Caddy fetches its cert.

---

## Notes

- **Dev cheats are ON in SBX** (the `dev-` hostname enables them) — correct, it's the
  test area. OFF on production `tempest.wolfhold.app`.
- **Register real players**: `/register` → Keycloak sign-up. Test with Gmail
  plus-addressing: `angel.kenel+larry@gmail.com`, `+john`, … (unique to Keycloak,
  one inbox for you).
- **Box footprint**: tempest adds `tempest-app` (~150 MB), `tempest-db` (~30 MB),
  `tempest-minio` (~100 MB) to the CX22. Check `free -m`; add swap like the Open
  WebUI doc if tight.
- **Redeploy**: `git pull`, re-stamp (optional), re-run the step 3 `up` command.
  Re-run step 2 only if the realm/secret changed.
- **Prod (PRD) later**: same shape with `docker-compose.prd.yml` (APP_ENV=production,
  realm tempest-prd, host tempest.wolfhold.app, sslRequired external, real secrets,
  no demo cheats), provisioned the same way.
