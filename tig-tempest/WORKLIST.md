# WORKLIST — Tig & Angel (the deck)

*Single source of truth for what's next, in order. Top item is what "ON DECK" starts on.*
*Working item lives at the top. Move done items to the bottom log. Keep it honest.*

---

## ON DECK

*The faithful build is complete — core loop, waves/zoom, superzapper, full 5-enemy bestiary, title screen, high scores, and sound are all in. From here it's polish-to-taste and whatever Angel wants next. Ideas parked below.*

1. **Tuning pass (optional)** — dial sound volumes, spawn mixes, spike danger to taste after more play.
2. **Nice-to-haves** — bonus lives at score thresholds, a real attract-mode demo, more tube shapes (open/fan tubes), enemy variety per level, pause key.
3. **Angel's parked ideas (2026-07-09):**
   - **Between-level music** during STAND BY — eerie *Twilight-Zone-ish* arpeggio (Web Audio, original composition — the real TZ theme is copyrighted, so evoke, don't copy). On-brand.
   - **Sexy `/status` page** (not raw JSON) — "all systems go · server up · build · N players online · top players" landing at `/healthz`+`/version`, with a *Play now* button. *Needs presence/leaderboard data → build it real in Phase 5, not faked earlier.*
   - Test note: c3 (`=` life) and c5 (dev bar) weren't bugs — the cheats worked; feedback was too subtle. Fixed with bright cheat toasts + a clearer dev bar (proven headless).

### BIG EPIC — GO LIVE (in progress) — full spec in [`GO-LIVE.md`](GO-LIVE.md)

Take Tempest online: accounts, leaderboard, "who's online", three envs on
`*.wolfhold.app`, SSO via the **existing shared Keycloak**. Phased build order in
`GO-LIVE.md` §13. Two decisions still open: *own Tempest realms vs shared identity*
(§1) and *seed the RNG from day one* for anti-cheat + seed-challenge (§7/§9).

Phase tracker:
- **Phase 1 — thin FastAPI serves the game** · **human-green ✓** (Angel played to lvl 6 at localhost:8080).
  App in `tig-tempest/app/` (`main.py`, `Dockerfile`, `entrypoint.sh`), `docker-compose.yml`.
  `docker compose up -d --build` → play at **http://localhost:8080**. `/healthz` + `/version` verified.
  **Build bar** on the game (freehold-style `BUILD b# · sha · date · ENV`, reads `/version`) — Angel's branding.
  **Dev cheats** (gated: localhost/dev-/stg- only, never prod/Pages): `1-9` jump level · `=` +life ·
  `0` god · `\` force over · `F/S/T/B/P` spawn enemy. **Interactive test harness** at
  **/testkit/** (`app/testkit/index.html`, TEST-TMP-P1 — banco format: pass/fail rows, autosave,
  copy-results). Convention: **one test script per phase**; new-user tests use Gmail plus-addressing
  (`angel.kenel+larry@…`). *Test harness itself is machine-verified (serves 200); awaiting Angel's run-through.*
- **Phase 2 — Postgres + models + migrations** · **machine-green ✓** (self-migrates on boot;
  tables `players`/`scores`/`presence` created; `/healthz` reports `db:true`). `app/models.py`,
  `app/db.py`, `app/alembic/` (rev `0001`), Postgres `tempest-db` in base compose.
  *Box-DB decision for Phase-2 SBX redeploy: own `tempest-db` container (current) vs reuse
  freehold's Postgres (a `tempest` DB) — decide at redeploy; overlay already keeps the app on
  both `edge` + default nets so its own DB works on the box.*
- Phase 3 — Auth: three `tempest-*` realms on the shared Keycloak, `/login`, session cookie.
- Phase 4 — Score submit + **dashboard** + presence. *(Confirmed want: player **profiles with
  avatars + banners** via MinIO, like freehold's profile — build + test it here.)*
- Phase 5 — Leaderboard.
- Phase 6 — Anti-cheat v1 (plausibility caps + game token); seed the RNG.
- **Phase 7 — Arcade Keycloak login theme (CONFIRMED WANT).** Per-env branded login so
  players know it's *Tempest*, not raw Keycloak: a nice game background + clear
  "TEMPEST · PRODUCTION / STAGING / SANDBOX" so they know which env they're in. `GO-LIVE.md` §6.
  *(Needs Phase 3 first — can't theme a login that doesn't exist yet.)*
- Phase 8 — Deploy rails (compose overlays, SOPS, backup gate) → SBX → STG → PRD.
- Phase 9 — Social login (Google + GitHub first; Facebook after review).

Parked research (Angel's question): **real-time multiplayer** — how do other games do it,
and could Tempest? Currently `GO-LIVE.md` §9 says single-driver + async seed-challenge.
Write up the options (shared-world netcode vs. the cheap seed-race) in Lego language and
decide. Not blocking launch.

---

## DONE (log — newest first)

- 2026-07-09 — Step 7: **Polish** — title/attract screen (spinning well, blinking INSERT COIN, controls, high score), **synthesized arcade sound** (fire/hit/zap/dive/hurt/start/gameover, M to mute), **high-score table** saved to localStorage (top 8, new-entry highlight). Introduced a `mode` state machine (title/play/over) — also fixed a latent first-frame auto-dive bug (game now starts clean at lvl 1). JS syntax verified, no stale refs. *Awaiting Angel's human-green.* **← faithful build complete.**
- 2026-07-09 — Step 6b: **Fuseball + Pulsar** — Fuseball (lvl 4+): crackling ball, skates lanes, flickers armored (bolt-proof) / vulnerable, 250 pts. Pulsar (lvl 5+): electrifies its whole lane (cyan bolt warning); lethal if you're on it at the peak, 300 pts. **Full 5-enemy bestiary done.** JS syntax verified. *Awaiting Angel's human-green.*
- 2026-07-09 — Step 6a: **Tanker** — amber block (lvl 3+, ~20%), climbs without flipping; shot → **splits into two flippers** at that spot. Tanker 100 pts. Three distinct enemy silhouettes now (red bowtie / green diamond / amber block). JS syntax verified. *Awaiting Angel's human-green.*
- 2026-07-09 — Step 5: **Spiker + spikes** — green diamond enemies (lvl 2+, ~30%) lay green zig-zag spikes up their lane; bolts erode spikes; a tall spike on your lane at the dive = red-flash life loss. Plus **STAND BY breather** after each wave + longer/calmer dive (Angel: "give me a second to breathe"). Spiker = 200 pts. JS syntax verified. *Awaiting Angel's human-green.*
- 2026-07-09 — Step 4: **Waves + level zoom** — finite waves (5+lvl×2 flippers), clear → tunnel-dive transition ("LEVEL n") → fresh well in a per-level hue. Per-level difficulty ramp (spawn + climb speed) and Superzapper refill. HUD shows LVL. JS syntax verified. *Awaiting Angel's human-green.*
- 2026-07-09 — Step 3: **Superzapper** — SPACE wipes all on-screen flippers, white flash, 2 per game (→ per-level once waves land), HUD "ZAP ×n". Plus difficulty rebalance to offset rapid-fire: faster spawns (65–110f) + climb (0.0040). JS syntax verified. *Awaiting Angel's human-green.*
- 2026-07-09 — Step 2: **Hold-to-fire** on a 7-frame cadence with an authentic **8-bolt on-screen cap**; single click still fires one. Angel human-green ✓ ("excellent... almost too easy" → difficulty bumped in step 3).
- 2026-07-09 — Step 1: **Flippers** — red bowtie enemies spawn deep, climb & flip lane-to-lane; bolt kills them (+150); reaching the rim costs a life; 3 lives → GAME OVER + click-to-restart. HUD (score + lives) now live. Angel human-green ✓ ("felt like the good old days").
- 2026-07-09 — Locked game feel: **classic tube/well** + **mouse control**. Recorded in `memory/project-tig-tempest.md`.
- 2026-07-09 — First playable frame: `game/index.html` — receding 16-lane well, yellow ship rides the rim following the mouse, click fires a projectile down the current lane. JS syntax verified. *Awaiting Angel's human-green.*
- 2026-07-09 — Set up the context spine: `CLAUDE.md`, this worklist, and the `memory/` folder.
