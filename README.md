# Ground Control

**Mission control for your AI copilot — memory, discipline, and control from your first session.**

---

You started using an AI copilot. It's brilliant for ten minutes, then every new session it's a stranger again. You re-explain the same context every single day. It says "fixed" when it isn't. It wanders. You spend more time herding it than working.

Ground Control fixes that. It's a tiny starter kit — a handful of files you copy once — that turns a clever-but-forgetful assistant into a **reliable partner** that:

- **Remembers** — a file-based memory that survives every reboot, compaction, and fresh start
- **Holds the standard** — a written contract of operating rules it must follow, every time
- **Stays under your control** — you steer, it rows; you never hand over the wheel

No app. No subscription. No account. Five files and a habit.

## Who it's for

- **Solo operators** doing the work of a team, who need leverage without hiring
- **Second-career founders** building something real, with no time to waste on false starts
- **Anyone** who has thought *"why am I re-explaining this to the AI again?"*

If that's you, you're ten minutes from a better setup.

## Quick start (15 minutes to first value)

**Fastest path** — make your own copy from this template:

```bash
gh repo create my-project --template akenel/ground-control --private --clone
```

Or just click **"Use this template"** at the top of this page. Then:

1. **Copy `kit/CLAUDE.template.md`** into your own project as `CLAUDE.md` (or your copilot's memory file).
2. **Fill the blanks** — who you are, what you're building, the paths that matter. ~30 minutes, once.
3. **Paste in the rules** — drop `kit/STANDING-RULES.md` into your `CLAUDE.md`. These are the non-negotiables.
4. **Set up your memory folder** — follow `kit/MEMORY-SYSTEM.md`. One fact per file, one index line each.
5. **Work.** When something's decided, write it to memory. When context changes, update the file. Never re-explain the same thing twice.

Not sure where to start? **Open this repo in your AI copilot and ask it to help you set up.** This repo is built to onboard you (see `CLAUDE.md`) — it's a working example of the method it teaches.

## What's in the box

| File | What it does |
|------|--------------|
| [`kit/CLAUDE.template.md`](kit/CLAUDE.template.md) | The persistent-memory spine. Fill the blanks and your copilot loads your whole context every session. |
| [`kit/STANDING-RULES.md`](kit/STANDING-RULES.md) | The operating contract — the rules that turn a clever assistant into a reliable partner. |
| [`kit/MEMORY-SYSTEM.md`](kit/MEMORY-SYSTEM.md) | How to keep a growing file-based memory that doesn't rot — structure, index, hygiene. |
| [`kit/worked-example.md`](kit/worked-example.md) | One real loop, start to finish, so you can see the method before you trust it. |

## How the pieces fit

```
README ──────────► the pitch + quick start (you are here)
   │
   ├─► CLAUDE.template ──► the spine you fill in (30 min, once)
   │        │
   │        └─► STANDING-RULES ──► the discipline you paste in
   │
   ├─► MEMORY-SYSTEM ────► how memory grows without rotting
   │
   └─► worked-example ───► proof it works, before you trust it
```

## The one rule that makes it all work

> **Write to files, not chat.** Chat is water — it evaporates at the next compaction. Files are stone. Anything that matters goes into a file your copilot reads next session, or it never happened.

Everything else here is downstream of that one habit.

---

## Contributing

Found this useful? Confused by something? [Open an issue](../../issues) or start a [discussion](../../discussions). The confusion of the first stranger is the roadmap for the next version.

## License

[CC BY 4.0](LICENSE) — use it, adapt it, build on it, ship it in your own work. Just keep the credit.

*Ground Control is the free, open spine of a larger method for running your whole operation through one AI copilot. Built by Angelo Kenel.*
