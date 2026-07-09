# Worked Example — One Loop, Start to Finish

*So you can see the method in motion before you trust it. This is a real shape of a real session, with the specifics redacted. Watch how memory, rules, and control work together.*

---

## The setup

A solo operator runs a small point-of-sale system for one real shop. It's live. The operator works in short daily sessions with one AI copilot. Everything below happens in a single sitting.

---

## 1. The fresh start

The operator opens a new session — yesterday's context is gone. They type the code word:

> **"ON DECK"**

The copilot doesn't ask "what would you like to work on?" It follows the rule attached to the code word: it opens the worklist file, reads the top items aloud, and states the first actionable one.

> *Top of the deck: (1) a checkout bug that 500s when the cashier field is empty, (2) ship the fix to production. Starting on (1).*

**No re-explaining. No re-planning.** The memory did the handoff.

## 2. The work

The copilot reads the relevant file *before* touching it (Rule 3). It finds the bug: the cashier identity isn't resolved before checkout. It makes one focused change.

Then — Rule 4, prove don't assume — it doesn't say "fixed." It runs the checkout flow with an empty cashier field and watches what actually happens. It works. *Now* it says fixed, and shows the output.

## 3. The pattern check

Rule 9 kicks in: *if one seal fails, check all the seals.* The copilot asks — where else does this same "identity resolved before action" assumption live? It finds two sibling endpoints with the same latent bug and flags them. One fix became three, because it looked for the failure mode instead of the symptom.

## 4. The ship

The operator says ship it. The copilot runs the deploy through the gate ladder — sandbox, then staging, then production — and **re-probes after each restart** (Rule 4 again: a health check greens a beat before the system truly serves). It proves the fix is live by hitting the real endpoint, not by trusting the green light.

## 5. The memory

Session's nearly done. The copilot asks the closing question:

> *What did we learn today that can't be re-derived from the code?*

Two things worth keeping:
- **A lesson:** "Identity-before-action is a repeated failure mode here — check siblings whenever one shows up." → written to a memory file, one index line added.
- **A project fact:** the sibling endpoints are now fixed too. → the roadmap memory updated (not duplicated).

Thirty seconds. Tomorrow's session will start knowing all of it.

---

## What just happened

Look back at what carried the weight:

- **The code word** turned a cold start into an instant, oriented resume.
- **The rules** stopped "fixed" from being a lie, and turned one bug into a pattern sweep.
- **The memory** made the ending of one session the beginning of the next — no context evaporated.
- **The human** never lost the wheel. They steered ("ON DECK," "ship it"); the copilot rowed.

That's the whole method. Not magic — just memory, discipline, and control, applied every single session until it's the only way that feels normal.

---

*Swap the point-of-sale story for your own work and the loop is identical. The method doesn't care what you're building.*
