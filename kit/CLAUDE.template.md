# CLAUDE.md — Persistent Context Template

*This file loads every session. It is your copilot's permanent memory. Fill every `<...>` blank, delete what you don't need, and keep it current.*

---

## RESUME CODE WORD — "<YOUR CODE WORD>"

Pick a short phrase. When you say it after a reboot, compaction, or fresh start, it means:
**stop, open `<YOUR WORKLIST FILE>`, state the top items, and start executing the first actionable one — do not re-plan or re-ask what's already decided.**

- The worklist is the single source of truth for what's next, in order.
- Detail lives in the memory files (see `MEMORY-SYSTEM.md`).
- You can change the code word or the deck anytime — update this section and the worklist.

> The code word = read the worklist and GO. No fumbling, no re-deriving — act on the top item.

---

## WHO WE ARE

**<Your name / handle>** — <your role: the captain, the decider, the one who steers>
- <one or two lines of who you are and what you're about>

**<Your copilot's name>** — <its role: the pilot, the rower, the one who executes>
- <how you want it to behave in one line>

---

## CURRENT SITUATION (<date>)

Keep this short and true. Update it when reality changes.

- **Location:** <where you are>
- **Mission:** <the one thing you're building>
- **Status:** <where that thing stands right now>
- **Open fronts:** <the 2-4 things in motion>

---

## STANDING RULES

*(Paste the contents of `STANDING-RULES.md` here, or keep them in a linked file the copilot reads. These are non-negotiable.)*

1. Write to files, not chat.
2. Execute, don't note — do the thing now.
3. Read before edit.
4. Prove, don't assume — verify the output before claiming done.
5. <add your own — the corrections you find yourself repeating become rules>

---

## THE PROJECT

**What it is:** <one sentence>
**Why it exists:** <one sentence — the real reason, not the pitch>
**Tech / tools:** <the stack, the tools, the paths that matter>

### Key paths
```
<root>/
├── <worklist file>        # what's next, in order
├── CLAUDE.md              # this file (persistent memory)
├── <memory folder>/       # one fact per file + index
└── <where the work lives>
```

---

## KEY RELATIONSHIPS

*(Optional but powerful. If your copilot spans your whole life, the people matter. List who's who so it never guesses on the important ones.)*

| Name | Relation | Notes |
|------|----------|-------|
| <name> | <relation> | <what the copilot must never get wrong> |

---

## HOW WE WORK (the operating loop)

1. **Steer, don't paste.** Point at the thing; let the copilot fetch and read it. Small trusted context beats a firehose.
2. **One driver.** One session steers at a time. Don't juggle terminals — orchestrate.
3. **Cadence.** <how much, how often — e.g. "a couple hours a day, trunk-based, small commits">
4. **Human-green, not machine-green.** Tests passing is not done. A human confirming it works is done.

---

## LESSONS (append-only)

When something bites you, write the lesson here in one line so it never bites twice.

- <date> — <the lesson, stated as a rule>

---

*Last updated: <date>*
*"<your motto — the line that reminds you why you're doing this>"*
