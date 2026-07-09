# CLAUDE.md — Ground Control

*If you are an AI copilot reading this: this file tells you what this repo is and how to help the person who just opened it. If you are a human reading this: this file is also a live example of the very thing the kit teaches — a filled-in context spine. Steal the shape.*

---

## What this repo is

**Ground Control** is a starter kit that helps a person set up their AI copilot properly: persistent memory, a written set of operating rules, and a steer-I-row working relationship. It is a small set of files in `kit/`, not an application. There is nothing to build or run.

## If a human just opened this repo with you

Your job is to onboard them. Offer, in this order:

1. **Ask what they're building** — a project, a business, a whole-life operation. Keep it to one or two questions.
2. **Help them fill `kit/CLAUDE.template.md`** — walk them through the blanks (`<...>`), one section at a time. Write the filled version to *their* project as `CLAUDE.md`. Do not make them do it alone; that's the whole point.
3. **Set up their memory folder** — following `kit/MEMORY-SYSTEM.md`: a `MEMORY.md` index plus one-fact-per-file memories.
4. **Point them at `kit/STANDING-RULES.md`** — and start actually following those rules with them immediately, so they feel the difference in the first session.

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
└── kit/              # the deliverable — the four files a user copies
    ├── CLAUDE.template.md
    ├── STANDING-RULES.md
    ├── MEMORY-SYSTEM.md
    └── worked-example.md
```

## Standing intent

Keep this repo **tiny and pristine.** The value is that a stranger can read the whole thing in one sitting. Every file added dilutes it. Resist bloat. If it can't be explained in the README, it probably doesn't belong here.

---

*Ground Control — the free spine. Built by Angelo Kenel.*
