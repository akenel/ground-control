---
name: project-tig-tempest
description: What we're building and the decisions already locked — open before designing or coding the game
type: project
---

Building a single-screen, vector-style 80s arcade shooter in the lineage of Atari's *Tempest* (1981): the player rides the rim of a tube/well and shoots enemies climbing toward them.

**Decisions locked so far:**
- **Tech:** HTML5 `<canvas>` + plain JavaScript. No build step, no dependencies, runs in any browser. Chosen so "done" = Angel opens `game/index.html` and plays it (human-green).
- **Home:** `ground-control/tig-tempest/` (subfolder — the kit's own files stay untouched).
- **Copilot name:** Tig (git backwards).
- **Playfield:** Classic tube/well — a receding geometric well; player rides the rim, enemies climb up from the center. (2026-07-09)
- **Controls:** Mouse — ship follows the mouse around the rim, click to fire down the current lane. (2026-07-09)

**Why:** Pure joy — Angel wants to build the feeling of the arcade cabinets he grew up on. See [[angel-who]].

**Still open (decide in worklist item 1):** exact playfield shape (classic tube/well vs. flat lane), control scheme (keys vs. mouse), enemy behavior, win/lose conditions. Update this file once those are chosen — don't re-litigate them later.
