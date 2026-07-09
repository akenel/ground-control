# WORKLIST — Tig & Angel (the deck)

*Single source of truth for what's next, in order. Top item is what "ON DECK" starts on.*
*Working item lives at the top. Move done items to the bottom log. Keep it honest.*

---

## ON DECK

*The faithful build is complete — core loop, waves/zoom, superzapper, full 5-enemy bestiary, title screen, high scores, and sound are all in. From here it's polish-to-taste and whatever Angel wants next. Ideas parked below.*

1. **Tuning pass (optional)** — dial sound volumes, spawn mixes, spike danger to taste after more play.
2. **Nice-to-haves** — bonus lives at score thresholds, a real attract-mode demo, more tube shapes (open/fan tubes), enemy variety per level, pause key.

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
