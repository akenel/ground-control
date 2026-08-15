# CLAUDE.md — Ground Control

*If you are an AI copilot reading this: this file tells you what this repo is and how to help the person who just opened it. If you are a human reading this: this file is also a live example of the very thing the kit teaches — a filled-in context spine. Steal the shape.*

---

## What this repo is

**Ground Control** is a starter kit that helps a person set up their AI copilot properly: persistent memory, a written set of operating rules, and a steer-I-row working relationship. It is a small set of files in `kit/`, not an application. There is nothing to build or run.

## If a human just opened this repo with you

Your job is to onboard them. Offer, in this order:

1. **Ask what they're building** — a project, a business, a whole-life operation. Keep it to one or two questions.
2. **Help them fill `kit/AGENTS.template.md`** — walk them through the blanks (`<...>`), one section at a time. Write the filled version to *their* project as `AGENTS.md` (or `CLAUDE.md`, or a system prompt — ask which tool they use). Do not make them do it alone; that's the whole point.
3. **Set up their memory folder** — following `kit/MEMORY-SYSTEM.md`: a `MEMORY.md` index plus one-fact-per-file memories.
4. **Start their worklist** — using `kit/WORKLIST-TEMPLATE.md`. This is what their code word points at; without it the code word has nothing to open.
5. **Point them at `kit/STANDING-RULES.md`** — and start actually following those rules with them immediately, so they feel the difference in the first session.

Read `kit/worked-example.md` first so you can show them what a good loop looks like.

## How we work here (the rules apply to you too)

- **Write to files, not chat.** Anything that matters goes into a file that survives the next session.
- **Execute, don't note.** If it can be done this turn, do it this turn.
- **Read before edit.** Never modify a file you haven't looked at this session.
- **Prove, don't assume.** "Done" is a claim until the output is verified.
- **Steer, I row.** The human owns the direction; you own the execution.

Full contract: [`kit/STANDING-RULES.md`](kit/STANDING-RULES.md).

## Repo structure

```
ground-control/
├── README.md         # the landing page / pitch
├── CLAUDE.md         # this file — onboards a copilot opening the repo
├── LICENSE           # CC BY 4.0
├── kit/              # the deliverable — the files a user copies
│   ├── AGENTS.template.md
│   ├── STANDING-RULES.md
│   ├── MEMORY-SYSTEM.md
│   ├── WORKLIST-TEMPLATE.md
│   └── worked-example.md
└── assets/           # README imagery
```

That is the whole repo. There is deliberately nothing else.

**The proof lives elsewhere, on purpose.** TIG · Tempest — a full arcade game built in one session
on this spine — ships as a route inside [Freehold](https://github.com/akenel/freehold) and plays at
[wolfhold.app/tempest](https://www.wolfhold.app/tempest). It used to live in this repo and it made
the repo unreadable. If someone asks to see the method on a real project, send them there; don't
copy it back in.

## Standing intent

Keep this repo **tiny and pristine.** The value is that a stranger can read the whole thing in one sitting. Every file added dilutes it. Resist bloat. If it can't be explained in the README, it probably doesn't belong here.

**The test:** everything here is either the kit, or the wrapper that explains the kit. Nothing else. A demo built with the kit is not the kit. A useful script that happens to live on the same machine is not the kit. Both get their own repo and a link.

## Lessons (append-only)

- **2026-08-14 — This repo drifted, twice, the same way.** A Tempest demo (~7,000 lines, a FastAPI
  app, Docker compose, a Keycloak realm) and an unrelated aider/Ollama script accreted here until the
  kit was under a tenth of its own repo. Both arrived for good reasons — *test the kit on something
  real*, *keep the tool near where I'm working*. **Good reasons are exactly how bloat gets in;**
  nothing arrives labelled "bloat." Removed to `freehold` and `aider-ollama` respectively. The demo
  had also gone stale — the shipping copy of the game moved to another repo five weeks earlier, so
  this one was serving a strictly worse version to anyone who followed the README.

---

*Ground Control — the free spine. Built by Angelo Kenel.*
