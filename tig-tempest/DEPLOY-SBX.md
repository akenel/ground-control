# DEPLOY — Tempest Phase 1 → SBX (dev-tempest.wolfhold.app)

*Runbook you run **on the wolfhold box** (167.233.125.248), not on the laptop.
Own stack, shared Caddy: Tempest runs as its own compose and joins freehold's
network; freehold's Caddy gets **one** new site block. Real HTTPS, $0.*

**Prereqs (already true):** DNS `dev-tempest.wolfhold.app → 167.233.125.248` is
live; freehold is up on the box in prod (its Caddy owns 80/443); ports 80/443 open.

---

## 1. Get the code on the box (first time)

```bash
cd ~                      # or wherever you keep repos on the box
git clone https://github.com/akenel/ground-control.git
cd ground-control
git checkout tempest-go-live
cd tig-tempest
```
*(Later deploys: `git pull` in `ground-control`, then jump to step 4.)*

## 2. Confirm freehold's network name

```bash
docker network ls | grep freehold        # expect:  freehold_freehold
```
If it prints a different name, edit `name:` in `docker-compose.sbx.yml` to match.

## 3. (Optional) stamp the real build into /version

So the build bar shows the actual SHA instead of "dev":
```bash
printf '%s\n%s\n%s\n' "$(git rev-parse --short HEAD)" "$(date -u +%Y-%m-%d)" "$(git rev-list --count HEAD)" > app/build-sha.txt
```

## 4. Start the Tempest container (joins freehold's network)

```bash
docker compose -f docker-compose.yml -f docker-compose.sbx.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.sbx.yml ps
```
It won't publish a public port — freehold's Caddy reaches it over the shared
network as `tempest-app:8000`.

## 5. Add the Caddy block (one edit to freehold's Caddyfile)

On the box, in your **freehold** repo dir, open `Caddyfile.prod` and add:

```caddy
# ---- TIG · Tempest — SBX ----
dev-tempest.wolfhold.app {
	import sec
	reverse_proxy tempest-app:8000
}
```

Then reload Caddy (no downtime, no restart):
```bash
cd ~/…/freehold
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy \
  caddy reload --config /etc/caddy/Caddyfile
# (or: docker exec freehold-caddy-1 caddy reload --config /etc/caddy/Caddyfile)
```

> **Persist it:** commit that block to your freehold repo, or a future freehold
> redeploy that re-pulls `Caddyfile.prod` will drop it. It's the *only* freehold
> change; everything else is self-contained in this repo.

## 6. Verify

```bash
curl -s https://dev-tempest.wolfhold.app/healthz    # {"status":"ok","env":"sandbox"}
curl -s https://dev-tempest.wolfhold.app/version    # ... "env":"sandbox"
```
Then open **https://dev-tempest.wolfhold.app** — the game, green padlock, build
bar reading **BUILD … · SANDBOX**, test kit at **/testkit/**. First load may take
a few seconds while Caddy fetches the Let's Encrypt cert.

---

## Notes

- **Dev cheats are ON in SBX** (the `dev-` hostname enables them) — correct: SBX is
  the test area. They're OFF on production `tempest.wolfhold.app`.
- **No accounts yet** — Phase 1 is the game + build bar + test kit. Logins,
  leaderboard, presence arrive in Phases 2–5, redeployed onto these same rails.
- **Redeploy:** `git pull` in `ground-control`, re-run step 4. To prove the served
  build, re-stamp (step 3) before the rebuild.
- **Staging (STG) later:** same file, copy to a `stg` overlay with `APP_ENV=staging`
  + container/alias `tempest-stg`, and a `stg-tempest.wolfhold.app` Caddy block.
