# GO-LIVE — Tempest online (accounts · leaderboard · three environments)

*Handoff spec for the build terminal (Tig). Written from a detailed read of the
`freehold` reference stack — we **cherry-pick freehold's proven patterns**, we do
not reinvent them. This file is the plan; the worklist item at the bottom is the
deck. Angel steers, Tig rows.*

*Author of this plan: the ground-control (design) session, 2026-07-09.*

---

## 0. The one honest truth up front

The game today is **one static `game/index.html`** — canvas + plain JS, no server,
no memory. Everything Angel described (log in, "your last score", "your top games",
a leaderboard, "who's online now") needs three things that a static file cannot do:

1. **An auth server** — Keycloak (✅ *already running* at `auth.wolfhold.app`).
2. **A backend API** — to receive and serve scores (new, small: FastAPI).
3. **A database** — to remember them (new: Postgres, freehold's exact pattern).

So going live is not "polish the HTML." It is **wrapping the game in a thin server**
that serves it, logs the player in, and stores scores. The good news: **freehold
already solved every hard part of that**, and we reuse it almost verbatim.

> **Mental model:** Tempest is to the wolfhold box what **Open WebUI** already is —
> *a second app SSO'd into the one shared Keycloak, added as an opt-in overlay.*
> See `freehold/docs/private/OPENWEBUI-ON-FREEHOLD.md`; we copy that shape.

---

## 1. The shape (target architecture)

One shared Keycloak (already up), three Tempest environments, its own small
app+DB. Everything under `wolfhold.app`, TLS auto-issued by the existing Caddy.

| Host | Role | Realm |
|------|------|-------|
| `dev-tempest.wolfhold.app` | **SBX** — sandbox / dev, where a change lands first | `tempest-sbx` |
| `stg-tempest.wolfhold.app` | **STG** — staging / stress-test before prod | `tempest-stg` |
| `tempest.wolfhold.app` | **PRD** — live production | `tempest-prd` |
| `auth.wolfhold.app` | the **existing shared Keycloak** — we just add 3 realms | — |

> **Naming note:** the *hostname* uses a `dev-`/`stg-` prefix (Angel's choice, live in
> Porkbun DNS as of 2026-07-09, all → `167.233.125.248`), but the *internal env label
> and realm* stay `sandbox`/`staging` (`tempest-sbx`/`tempest-stg`) to match freehold's
> convention. Code targets the realm; the hostname is just what players type. Prod is
> `tempest.wolfhold.app` → realm `tempest-prd`.

```
        browser
           │  (session cookie only — no token ever in JS)
           ▼
   Caddy  ──►  tempest-app  (FastAPI: serves the game + /api/scores + /dashboard)
     │            │
     │            ├─► Postgres  (players, scores, presence)   ← tempest's own DB
     │            └─► Keycloak  (auth.wolfhold.app, realm tempest-<env>)   [shared]
     └─► /realms/* etc. proxied to the same shared Keycloak
```

**Why its own realms (not reuse freehold's `kc-*`):** Angel wants a *Tempest player
community* with a *branded arcade login screen* and a *separate username pool* ("a
real player of tempest"). Its own realms (`tempest-sbx/stg/prd`) give all three,
while still running on the **one Keycloak server you already operate** — no new auth
infra, just three realm JSONs. *(If you'd rather have one shared identity across all
wolfhold apps, the simpler alternative is to skip new realms and add a `tempest-web`
client to the existing `kc-*` realms — say the word and we flip it. Recommendation:
own realms.)*

**Admin model (answers Angel's question directly):** you are **not** a master-realm
admin for day-to-day. Master-realm admin is the *bootstrap* account that only the
`make apply` script uses. In each Tempest realm there are two **realm roles**:
`admin` (you) and `player` (everyone else). You hold the Keycloak master admin
password in your vault for break-glass; you play and moderate as a realm `admin`.

---

## 2. What changes about the game itself

Small, surgical. The game stays canvas + plain JS — it just stops being a file you
open from disk and becomes **served by the app at the domain**, so the browser has a
login session on the same origin.

1. **Served, not opened.** `tempest-app` serves `index.html` at `/`. Same code.
2. **A login gate.** A "INSERT COIN — SIGN IN" button hits `/login` → the server-side
   OIDC dance (freehold's `door.py`, copied) → back with a **signed session cookie**.
   *Tokens never touch the JS* — this is freehold's confidential-client model and it
   is exactly right for a static-JS game (no token handling in the browser at all).
3. **Submit a score.** On GAME OVER the JS does one `fetch('/api/scores', {method:
   'POST', credentials:'include', body: {level, points, waves, duration_ms}})`.
   Same-origin cookie authenticates it — no bearer token, no CORS.
4. **A dashboard.** `/dashboard` (server-rendered, freehold style): your last score,
   your personal bests, your rank, and "who's online now".
5. **Attract screen knows you.** If logged in, the title shows your handle + best.

> The polish work already on the deck (attract screen, high-score table, sound) is
> **not wasted** — the local high-score table becomes the *seed* of the leaderboard
> UI; we just point it at `/api/leaderboard` instead of `localStorage`.

---

## 3. Data model — freehold's exact style

freehold's load-bearing insight: **identity is not a table.** Keycloak owns users;
the app stores the Keycloak `preferred_username` as a plain indexed string column
and "owns" rows by string match. No `users` table to build, no FK to Keycloak. We
copy that. Two tables + one for presence:

```python
# models.py  — SQLAlchemy 2.0, mirrors freehold/app/models.py
class Player(Base):                    # mirrors freehold Profile — lazily created on first login
    __tablename__ = "players"
    id: Mapped[int]        = mapped_column(primary_key=True)
    username: Mapped[str]  = mapped_column(String(80), unique=True, index=True)  # Keycloak preferred_username
    display_name: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Score(Base):                     # mirrors freehold Ticket
    __tablename__ = "scores"
    id: Mapped[int]        = mapped_column(primary_key=True)
    player_username: Mapped[str] = mapped_column(String(80), index=True)   # owner, by string match
    points: Mapped[int]    = mapped_column(index=True)     # indexed for ORDER BY points DESC
    level: Mapped[int]     = mapped_column(default=1)      # how far they got (the "stat")
    waves: Mapped[int]     = mapped_column(default=0)
    duration_ms: Mapped[int] = mapped_column(default=0)
    verified: Mapped[bool] = mapped_column(default=False)  # see anti-cheat, §7
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Presence(Base):                  # "who's online now" — a heartbeat table
    __tablename__ = "presence"
    username: Mapped[str]  = mapped_column(String(80), primary_key=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

Everything else copies freehold verbatim:

- **`db.py`** — `create_async_engine` off one `DATABASE_URL`, `pool_pre_ping=True`,
  `async_session` maker, session-per-operation (`async with async_session() as s:`).
- **Migrations** — Alembic, hand-numbered revisions (`0001_create_players`,
  `0002_create_scores`, `0003_create_presence`), run from `entrypoint.sh`
  (`alembic upgrade head` → uvicorn) so `up -d` self-migrates.
- **Service module per entity** — `scores.py` owns all SQLAlchemy; routers stay thin.
- **Lazy player row** — no "create on signup"; upsert the `Player` on first `/dashboard` hit.

**The leaderboard queries** (freehold's `list_tickets` / `counts` patterns + a `.limit()`):

```python
# top 20 overall
select(Score).order_by(Score.points.desc()).limit(20)
# each player's personal best (the real leaderboard)
select(Score.player_username, func.max(Score.points).label("best"))\
    .group_by(Score.player_username).order_by(func.max(Score.points).desc()).limit(50)
# who's online now (heartbeat within 60s) — count + list
select(Presence.username).where(Presence.last_seen > now_minus_60s)
```
*(freehold has no pagination anywhere — for a leaderboard, top-N `.limit()` is all
you need; add offset later only if it grows.)*

---

## 4. Auth — copy freehold, add three realms

Reuse `freehold/app/auth.py` + `routers/door.py` almost unchanged (~120 lines,
PyJWT + `PyJWKClient`, PKCE + `state` + `nonce`, split-horizon public/internal URLs
with a **fixed issuer** so validation is deterministic behind the proxy).

**Realm topology** — three new realm JSONs, cloned from freehold's and edited:
`keycloak/realms/tempest-sbx-realm.json` etc. Per-realm differences to set:

- `realm` / `displayName` — "Tempest" / "Tempest Sandbox" / "Tempest Staging".
- `sslRequired` — `external` for prod, `none` for sandbox.
- `redirectUris` / `webOrigins` — the env's host (`https://tempest.wolfhold.app/*`
  etc.) plus `https://localhost:8443/*` for dev.
- **Roles** — `admin` + `player` (rename freehold's `staff` → `player`).
- **Seed users** — see §5.
- **Client** — one confidential client `tempest-web` (`publicClient:false`,
  placeholder secret; `prod-apply.py` stamps the real secret from `.env`).
- **`loginTheme: "tempest"`** — the arcade login skin, see §6.

> **Gotcha (freehold learned it the hard way):** realm JSON is imported **only on a
> fresh Keycloak DB.** Since `auth.wolfhold.app` is already running with data, you do
> **not** re-import — you **add the realms live via the admin API** (extend
> `ops/prod-apply.py`, or import the JSON once through the admin console). A plain
> restart will NOT pick up a new realm JSON. This is the single most common trap.

---

## 5. Demo user in every environment (including prod)

Angel wants a one-click **demo/guest** player in all three envs so a curious visitor
can try Tempest without signing up.

- **SBX / STG:** seed `demo`/`demo` (role `player`) directly in the realm JSON —
  same as freehold's sandbox `demo`/`sam`.
- **PRD:** freehold ships `tempest-prd` hardened with **no users + open
  self-registration**. Add **one** exception: a single `demo`/`demo` player, seeded
  via `prod-apply.py` (not the JSON, since prod isn't re-imported). Mark demo scores
  so they can be excluded from the "real" leaderboard if you want (`verified=false`
  or a `is_demo` flag on `Player`). Everyone else registers themselves and lands as
  a roleless `player`.

Real players: **self-serve registration is already open** — freehold's `/register`
shares the `/auth/callback` code path. Unique username + unique email are enforced by
Keycloak natively; nothing to build.

---

## 6. Different login screen per environment (the arcade skin)

freehold varies only the realm `displayName` between envs — all three share one
theme. Angel wants a genuinely **different, branded arcade login** per env. Two layers:

1. **Real custom theme** — `keycloak/themes/tempest/login/` with `parent=keycloak`,
   a FreeMarker `login.ftl` override + CSS for the vector/neon Tempest look (the
   "INSERT COIN" vibe). This is a real chunk of work (not a config toggle) but it is
   the thing that makes the login *feel* like the game. Start from freehold's
   extend-don't-fork theme structure.
2. **Per-env cue on top of it** — realm `displayName` ("TEMPEST • SANDBOX" in amber,
   "TEMPEST • STAGING" in cyan, "TEMPEST" in the real arcade red for prod) + a CSS
   accent driven by a realm attribute, so you always know which env you're logging
   into at a glance. Cheap, and it prevents "which env am I on" mistakes.

---

## 7. ⚠️ Score integrity — the tip Angel didn't ask for but needs most

**A public leaderboard on a client-side JS game is trivially cheatable.** Anyone can
open devtools and `fetch('/api/scores', {body:{points: 9999999}})`. If the board is
public and competitive, someone *will*. Plan for it now; it's far cheaper than
retrofitting a poisoned board later. Layered defence, cheapest first:

1. **Server-side plausibility caps.** The server knows Tempest's rules. Reject or
   flag any score where `points` exceeds the theoretical max for `level`/`waves`
   reached, where `duration_ms` is implausibly short for the level, or where level
   progression is non-monotonic. Store survivors as `verified=true`.
2. **Rate + shape limits.** One score per finished game; cap submissions/minute per
   user; require a server-issued **game token** (handed out at game start, single-use
   at submit) so a score must correspond to a game the server actually started.
3. **Two-tier board.** Show `verified` scores on the public board; keep unverified in
   a "pending/unranked" bucket you can review (freehold's `admin_or_deny` guard gives
   you the moderation page for free).
4. **Later, if it matters: deterministic replay.** Make the game **seeded** (one RNG
   seed per game, sent at start). The client submits the seed + the input timeline;
   the server re-simulates and confirms the score. This is the gold standard *and* it
   unlocks the seed-challenge feature in §9 — so seeding the RNG is worth doing early
   even before you build replay.

**Recommendation:** ship §1–§3 for launch (a day of work, stops the casual cheater),
design the RNG to be seeded from day one, add §4 only if the board gets competitive
enough to be worth gaming.

---

## 8. "Who's online now" — a heartbeat, not websockets

Don't reach for websockets. freehold's no-frills style says: the logged-in game
`fetch('/api/ping')` every ~20s; the server upserts `Presence(username, last_seen=now)`.
"Online" = `last_seen` within 60s. `/dashboard` shows the count + handles. Zero new
infrastructure, survives restarts, good enough for hundreds of players. Upgrade to a
websocket presence channel only if you later want live "X is playing level 7 right
now" spectating.

---

## 9. Two-player? — keep it single-driver, compete asynchronously

Angel's instinct is right: **Tempest was never a head-to-head game**, and real-time
2P would be a heavy rewrite for a game not built for it. The competition is **social
and asynchronous**, which is exactly what leaderboards + presence deliver:

- **Launch:** everyone plays solo; you compete on the board and see who's online.
- **Cheap, high-value next step — the SEED CHALLENGE.** Because the RNG is seeded
  (§7), two players can play the **identical** wave sequence from the same seed and
  compare scores fairly — asynchronous head-to-head without any netcode. "Beat my
  run on seed #48213." This is the competitive hook, and it's nearly free once the
  RNG is seeded.
- **Far-future:** live spectating (watch a top player's run) via the presence channel.

Real-time versus is explicitly **out of scope** unless Angel decides the seed
challenge isn't enough.

---

## 10. Environments & deploy — mirror freehold's rails exactly

Copy freehold's operating model wholesale; it is the most battle-tested part:

- **One compose base + overlays**, not forked YAML. `docker-compose.yml` (base) +
  `docker-compose.prod.yml` (real domains + Let's Encrypt) + a `tempest` overlay,
  mirroring how Open WebUI is added. Env differences are **env-vars + realm + image
  tag**, never duplicated config.
- **Per-env `.env`** cloned from `deploy/{sandbox,staging,production}.env.example`
  (freehold's exact template — Postgres parts, `APP_ENV`, `KC_REALM=tempest-<env>`,
  `SITE_DOMAIN`, `KC_CLIENT_SECRET`, `SESSION_SECRET`, `BACKUP_PASSPHRASE`).
- **Caddy** — add a hostname block per subdomain (`{$SITE_DOMAIN} → tempest-app:8000`),
  reusing freehold's `(sec)` security-headers snippet and the **inert-loopback-default
  trick** so an unset env's block stays valid-but-unpublished.
- **The promotion ladder** — same git ref walks **local → SBX → STG → PRD**:
  ```
  git commit -am "…" && git push
  git pull && python3 ops/deploy.py sandbox      # test at dev-tempest.wolfhold.app
  git pull && python3 ops/deploy.py staging      # retest at stg-tempest.wolfhold.app
  git pull && python3 ops/deploy.py production    # backup GATE runs first, then deploy
  ```
- **Build-stamp + `/version` "prove after restart"** — the deploy re-probes the served
  SHA and fails if it isn't the one it stamped. Promotion is never a leap of faith.
- **Secrets: SOPS + age** — encrypted `secrets/<env>.enc.yaml` committed to git, one
  age key in your password manager, `make secrets ENV=<env>` decrypts to `.env`.
  Client secret / social-login secrets flow SOPS → `.env` → `make apply` → Keycloak
  (never raw in git).
- **Backup gate before prod** — `ops/backup.py`: `pg_dump` → encrypt → **restore-drill
  into a throwaway DB** → off-box to B2 (write-only key, object-lock immutable).
  Prod won't deploy unless a backup is proven restorable. *"A backup you've never
  restored is a rumor."*
- **`make apply` (`prod-apply.py`)** — the idempotent reconcile that aligns the
  `tempest-web` client secret, enables social IdPs, seeds the prod demo user, and
  (extended by us) creates the three realms live. Re-runnable any time.

---

## 11. Social login (Google / GitHub / Facebook)

Already built as Keycloak identity providers; ship disabled with empty client id
(no broken buttons), enabled per-provider via `.env` + `make apply`.

- Register **one OAuth app per provider** with all three realms' broker redirect URIs:
  `https://auth.wolfhold.app/realms/tempest-<env>/broker/<google|github|facebook>/endpoint`.
- **GitHub** allows one callback per app → set it to the host `https://auth.wolfhold.app`
  (it matches sub-paths) so one app covers all three realms.
- **Google** — publish the OAuth consent screen or only test users can sign in.
- **Facebook** — needs a privacy-policy URL + app review before the `email` scope
  works for the public. Budget time for review, or launch with Google+GitHub and add
  Facebook later.

---

## 12. What you're NOT missing, and what you ARE

**You've thought of the hard stuff** — three envs, shared Keycloak, unique
usernames, social login, demo users, per-env login screens, dashboards, and
(correctly) that Tempest stays single-driver. Freehold already implements almost all
of it.

**Gaps to put on the radar (in priority order):**

1. **Score integrity (§7)** — the biggest one, and not in the original ask. A public
   competitive board *will* be cheated without server-side validation.
2. **Seeded/deterministic RNG (§7/§9)** — decide early; it unlocks both anti-cheat
   replay and the seed-challenge competition, and it's painful to retrofit.
3. **Abuse & moderation** — profanity/impersonation in usernames + display names;
   you'll want a reserved-word list and an admin "reset/rename/ban" page (the
   `admin_or_deny` guard is already there).
4. **Rate limiting / basic abuse protection** on `/api/scores` and registration.
5. **Legal-lite** — a one-page privacy note + terms (Facebook login *requires* a
   privacy URL anyway; and you're storing emails, so say what you do with them).
6. **Box capacity** — the wolfhold CX22 (2 vCPU / 4 GB) already runs Keycloak +
   Postgres + freehold + Open WebUI. Tempest's app+DB is light, but check `free -m`
   headroom and add swap like the Open WebUI doc did if needed. A busy leaderboard is
   cheap; watch it.
7. **Email is optional** — only forgot-password/account-linking use it; social-login
   players never touch it. You can launch without SMTP.
8. **GDPR-lite "delete my account"** — nice-to-have; Keycloak deletes the identity,
   you cascade-delete their `scores`/`presence` by username.

**Freehold's hard-won gotchas that will bite you too:**
- Realms import **only on a fresh KC DB** → add Tempest realms **live**, not by JSON re-import (§4).
- **No inline `# comments` on `.env` value lines** — Compose keeps them and Caddy chokes.
- The `tempest-web` client secret in Keycloak **must equal** `KC_CLIENT_SECRET` in `.env`.
- Session cookie **must** be `same_site=lax` or the OIDC redirect-back loses it.
- Access-token audience is `account` → read roles with `verify_aud=False`.
- On a shared multi-env box, deploy with `make promote` / `deploy.py`, **never
  `up --build`** (it rebuilds every env from the working tree and erases per-env divergence).

---

## 13. Suggested build order for Tig (phases, each independently shippable)

> Finish the **polish** deck item first (attract screen, local high-score table,
> sound) — it's the game's front end and it becomes the leaderboard UI's seed.

1. **Skeleton server.** `tempest-app` (FastAPI) that just *serves* today's
   `index.html` unchanged at `/`, plus `/healthz` + `/version`. Dockerfile +
   `entrypoint.sh` + compose base. Prove the game still plays, now served.
2. **Postgres + models + migrations.** `players`, `scores`, `presence`; `db.py`;
   Alembic `0001–0003`; self-migrate on boot. No auth yet — write a fake score via curl.
3. **Auth.** Copy `auth.py`/`door.py`; stand up the three `tempest-*` realms on the
   shared Keycloak (live, via admin API); `/login`, `/auth/callback`, session cookie.
   Log in as a seeded `demo` in sandbox.
4. **Score submit + dashboard.** `POST /api/scores` (guarded), `/dashboard` with your
   last score / bests / rank; wire GAME OVER → submit; presence heartbeat.
5. **Leaderboard.** `/api/leaderboard` + the board UI (reuse the local high-score
   table's look). Public read.
6. **Anti-cheat v1 (§7.1–7.3)** — plausibility caps + game token + verified flag.
   Seed the RNG now even if replay comes later.
7. **Arcade login theme (§6)** + per-env accent.
8. **Deploy rails** — clone freehold's `ops/` + compose overlays + SOPS secrets;
   walk SBX → STG → PRD; wire the backup gate.
9. **Social login** — Google + GitHub first; Facebook after review.
10. **Later:** seed-challenge competition, live spectating, GDPR delete.

---

## 14. Paste-ready kickoff for the other terminal

Copy this to Tig when you're ready to start (after polish is human-green'd):

> **ON DECK — Tempest go-live, Phase 1.** Read `GO-LIVE.md` top to bottom, then
> execute Phase 1 only (§13.1): stand up a minimal FastAPI `tempest-app` that serves
> the existing `game/index.html` unchanged at `/`, plus `/healthz` and `/version`,
> with a Dockerfile + `entrypoint.sh` + a base `docker-compose.yml`, copying
> freehold's structure (`freehold/app/{main,db}.py`, `freehold/app/Dockerfile`,
> `freehold/app/entrypoint.sh`) as the template. **Do not** add auth or DB yet —
> just prove the game still plays when served by the app. Human-green = Angel opens
> `https://localhost:8443` (or the dev port) and Tempest plays exactly as before.
> Then stop and report; we take Phase 2 next.

---

*Everything here is lifted from `freehold` (auth, deploy, data patterns) — the
judgment to assemble it for a game is the only new part. Own the box, own the login,
own the leaderboard. Insert coin.*
