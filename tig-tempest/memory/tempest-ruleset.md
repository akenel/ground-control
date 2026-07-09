---
name: tempest-ruleset
description: How the original Tempest (1981) plays — the design reference we build toward; open when adding gameplay
type: reference
---

Design reference for how the arcade original works, so [[project-tig-tempest]] stays faithful. (Factual game mechanics, from general knowledge of the 1981 Atari game.)

**Field:** Geometric well in perspective. Player rides the rim in a claw "Blaster." Enemies emerge at the deep (far) end and climb lanes toward the rim. Player shoots *down* lanes.

**Enemies:**
- **Flipper** — basic; climbs and flips lane-to-lane; kills player on contact if it reaches the rim.
- **Tanker** — climbs, splits into two enemies (Flippers early; Fuseballs/Pulsars later) when shot or on reaching the top.
- **Spiker** — spins out a growing **spike** trail in its lane; the spike is lethal during the end-of-level zoom.
- **Fuseball** — bounces up/down lanes and skates the rim; only vulnerable at moments; deadly on the rim.
- **Pulsar** — periodically electrifies its whole lane; player on that lane dies during the pulse.

**Player tools:**
- **Fire** down a lane. Authentic constraint: a **cap on shots on screen at once** (a handful) — no infinite spray.
- **Superzapper** — screen-wipe smart bomb; ~one full + one weak use per level. Precious.

**Level flow:** Clear the wave → **zoom down the tube** to the next level. Spikes left in lanes kill you during the zoom unless shot off first. Each level: new tube shape/color, faster. Lose a life when an enemy reaches you on the rim, a Pulsar zaps your lane, or you touch a Fuseball.

**Scoring:** per enemy type, with bonuses. Flippers cheap; Fuseballs/Pulsars worth more.

**Our build order toward this** lives in `../WORKLIST.md`.
