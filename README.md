# Ground Control

**Mission control for your AI copilot — memory, discipline, and control from your first session.**

![A cold copilot session resuming instantly from memory: the user types the code word "ON DECK" and the copilot reopens the worklist, fixes the bug, checks its siblings, re-probes after deploy, and writes the lesson to memory.](assets/session.svg)

<sub><i>A fresh session with nothing in context — one code word, and the copilot picks up exactly where you left off. No re-explaining.</i></sub>

---

You started using an AI copilot. It's brilliant for ten minutes, then every new session it's a stranger again. You re-explain the same context every single day. It says "fixed" when it isn't. It wanders. You spend more time herding it than working.

Ground Control fixes that. It's a tiny starter kit — a handful of files you copy once — that turns a clever-but-forgetful assistant into a **reliable partner** that:

- **Remembers** — a file-based memory that survives every reboot, compaction, and fresh start
- **Holds the standard** — a written contract of operating rules it must follow, every time
- **Stays under your control** — you steer, it rows; you never hand over the wheel

No app. No subscription. No account. No vendor. Five files and a habit.

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

1. **Copy `kit/AGENTS.template.md`** into your own project as `AGENTS.md` — or `CLAUDE.md`, or whatever file your tool reads ([see below](#it-isnt-just-for-one-tool--the-file-has-many-names)).
2. **Fill the blanks** — who you are, what you're building, the paths that matter. ~30 minutes, once.
3. **Paste in the rules** — drop `kit/STANDING-RULES.md` into that same spine file. These are the non-negotiables.
4. **Set up your memory folder** — follow `kit/MEMORY-SYSTEM.md`. One fact per file, one index line each.
5. **Work.** When something's decided, write it to memory. When context changes, update the file. Never re-explain the same thing twice.

Not sure where to start? **Open this repo in your AI copilot and ask it to help you set up.** This repo is built to onboard you (see `CLAUDE.md`) — it's a working example of the method it teaches.

## What's in the box

| File | What it does |
|------|--------------|
| [`kit/AGENTS.template.md`](kit/AGENTS.template.md) | The persistent-memory spine. Fill the blanks and your copilot loads your whole context every session. Save it as `AGENTS.md`, `CLAUDE.md`, or a system prompt. |
| [`kit/STANDING-RULES.md`](kit/STANDING-RULES.md) | The operating contract — the rules that turn a clever assistant into a reliable partner. |
| [`kit/MEMORY-SYSTEM.md`](kit/MEMORY-SYSTEM.md) | How to keep a growing file-based memory that doesn't rot — structure, index, hygiene. |
| [`kit/WORKLIST-TEMPLATE.md`](kit/WORKLIST-TEMPLATE.md) | The handoff document — how to write a worklist your copilot can execute without guessing. |
| [`kit/worked-example.md`](kit/worked-example.md) | One real loop, start to finish, so you can see the method before you trust it. |

## How the pieces fit

```
README ──────────► the pitch + quick start (you are here)
   │
   ├─► AGENTS.template ──► the spine you fill in (30 min, once)
   │        │
   │        └─► STANDING-RULES ──► the discipline you paste in
   │
   ├─► WORKLIST-TEMPLATE ► what the code word points at — the deck
   │
   ├─► MEMORY-SYSTEM ────► how memory grows without rotting
   │
   └─► worked-example ───► proof it works, before you trust it
```

## It isn't just for one tool — the file has many names

Every serious AI coding agent now reads a project context file. They just disagree on what to call it:

| Where you work | What the file is called |
|---|---|
| Claude Code | `CLAUDE.md` |
| Codex, Gemini CLI, opencode, goose, Cursor, Zed, Copilot, Devin, Windsurf, Junie… | **`AGENTS.md`** — [an open format](https://agents.md/), used by 60k+ projects |
| Aider | `CONVENTIONS.md` — *and* `AGENTS.md` |
| Open-WebUI, LM Studio, any chat UI | the model's **system prompt** field |

Same job in all of them: *load who you are and how you work, before the conversation starts.*

**The filename is the easy part. Knowing what to put in it is the whole problem** — and that's what this kit is. `kit/AGENTS.template.md` is a template for that file whatever your tool calls it. Save it as `AGENTS.md`, paste it into a system prompt box, keep both — it's the same content doing the same work.

> **Tested, not assumed.** The same spine has been run three ways: as `CLAUDE.md` in Claude Code, as an Open-WebUI system prompt against a hosted model, and as `CONVENTIONS.md` driving [Aider](https://aider.chat) with Qwen on Ollama. Three tools, three vendors, one file. In the terminal test it went from silently writing pointless code to *"I need to push back on this request"* — same model, same settings, **only the spine changed.**

If you switch tools next year, you rewrite one filename. That's the point of owning your context instead of renting it.

## ▶ Built with this method — play it

This repo eats its own cooking. **TIG · Tempest** is a complete arcade game — a faithful tribute to the 1981 classic — built in a **single session** using nothing but the spine in this kit: a human steering, an AI copilot rowing, every step written to files.

**[▶ Play it live → wolfhold.app/tempest](https://www.wolfhold.app/tempest)** — running on my own domain, deployed the *same day* it was built, and still serving.

It doesn't live in this repo, and that's the point. Tempest ships as a route inside [**Freehold**](https://github.com/akenel/freehold), the real system it belongs to — spine, worklist, memory files and all. Ground Control stays the kit; the proof lives where it runs.

*A kit you can read in one sitting is worth more than a kit padded with the things it built.*

## The one rule that makes it all work

> **Write to files, not chat.** Chat is water — it evaporates at the next compaction. Files are stone. Anything that matters goes into a file your copilot reads next session, or it never happened.

Everything else here is downstream of that one habit.

---

## Contributing

Found this useful? Confused by something? [Open an issue](../../issues) or start a [discussion](../../discussions). The confusion of the first stranger is the roadmap for the next version.

## License

[CC BY 4.0](LICENSE) — use it, adapt it, build on it, ship it in your own work. Just keep the credit.

*Ground Control is the free, open spine of a larger method for running your whole operation through one AI copilot. Built by Angelo Kenel.*
