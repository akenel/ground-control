# Worklist Template — The Handoff Document

*The worklist is the single source of truth for what's next. The copilot reads it on the code word and executes the top item — no re-planning, no re-asking. This file teaches you how to write one that a copilot can follow without guessing.*

---

## The format

One file (`WORKLIST.md`). Ordered checklist. Top item = next action. Cross off when done.

```markdown
# WORKLIST — [Project Name]
<!-- Ordered by priority. Top = next. Cross off when done. -->

- [ ] 1. Read [specific files] to understand [what patterns to follow]
- [ ] 2. Create [path/filename] — [one sentence: what it does]
- [ ] 3. Create [path/filename] — [one sentence: what it does]
- [ ] 4. Wire [thing] into [file] following the existing pattern
- [ ] 5. Create [template/test/config] — [one sentence: what it does]
- [ ] 6. Write tests in [path] covering [specific cases]
- [ ] 7. Run the full test suite and report the actual output
- [ ] 8. Git commit with a meaningful message
```

---

## Why each part matters

**One item = one concrete action.**
"Add health checking" is a feature, not a task. "Create `models.py` HealthCheck class with fields: service, status, checked_at, detail" is a task. The copilot follows instructions — vague input produces vague output. Concrete input produces code that fits.

**Reference files by path.**
"Add a router" could go anywhere. "Create `routers/health.py`" goes exactly where it should. The copilot can read existing files to learn patterns (Rule 3: read before edit) — but only if you name the files worth reading.

**Order by dependency.**
Model before router. Router before template. Code before tests. Tests before commit. If you put tests before the model exists, the copilot either hallucinates or stalls. Dependencies first, always.

**Always end with verification + commit.**
```markdown
- [ ] N. Run the full test suite and report the actual output
- [ ] N+1. Git commit with a meaningful message
```
This enforces Rule 4 (prove, don't assume) and Rule 5 (human-green beats machine-green). The copilot runs the tests, reports what happened, then commits — in that order, every time.

**Keep it to 5-10 items.**
More than 10 and the thread gets lost. If the work needs 15 items, split it into two worklists. Finish batch 1, verify, then write batch 2. Sequential, not parallel — Rule 7: one driver, one session at a time.

---

## The CLAUDE.md side

The worklist says **what to do**. `CLAUDE.md` says **how to do it** — the patterns, the stack, the project identity. The copilot reads both on the code word. A worklist without `CLAUDE.md` produces code that doesn't match your project. `CLAUDE.md` without a worklist produces chat, not work.

The key section in `CLAUDE.md` that makes the worklist sing:

```markdown
## KEY PATTERNS (follow these exactly)
- Models: <your ORM style, your base class, your conventions>
- Routers: <your framework, your file layout, your registration pattern>
- Templates: <your templating engine, your response pattern>
- DB: <your session/query pattern>
- Tests: <your test runner, your file layout>
```

When the copilot reads this before executing the worklist, it writes code that looks like yours — not generic boilerplate.

---

## The two-terminal pattern (when planning and coding are separate sessions)

If you plan in one session and execute in another (e.g., one chat for architecture, one for coding), the worklist is the **handoff document** — it's how the planner talks to the coder without being in the same room.

```
1. Planning session:  Read the repo, understand the problem, write CLAUDE.md + WORKLIST.md
2. Coding session:    Type the code word → copilot reads CLAUDE.md → reads WORKLIST.md → executes
3. Planning session:  Verify what was produced, catch issues, plan the next worklist
4. Repeat
```

The worklist is the contract. The planner writes it. The coder executes it. The human verifies it. Sequential, never parallel — one driver at a time.

---

## A real example

This worklist was executed by a self-hosted copilot (Qwen3.5:397b via OpenWebUI) on a real FastAPI codebase. Every item was completed, all 154 tests passed, and the result was committed to git:

```markdown
# WORKLIST — Freehold Health Dashboard

- [ ] 1. Read deps.py, models.py, main.py, audit.py, build_info.py to understand Freehold's patterns
- [ ] 2. Create a HealthCheck model in models.py (service, status, checked_at, detail)
- [ ] 3. Create routers/health.py with a /status page that checks Postgres, Keycloak, MinIO, and app build SHA
- [ ] 4. Register the health router in main.py
- [ ] 5. Create a templates/status.html page showing service health with green/red indicators
- [ ] 6. Write tests for the health endpoint in tests/test_health.py
- [ ] 7. Run the full test suite to prove nothing broke
- [ ] 8. Git commit with a meaningful message
```

The copilot read the existing files (item 1), wrote code that matched the project's SQLAlchemy 2.0 + FastAPI patterns (items 2-5), wrote 6 real tests (item 6), ran the suite and reported 154 passing (item 7), and committed with a descriptive message (item 8). The worklist did its job: it told the copilot exactly what to do, in what order, and how to prove it was done.

---

*The worklist is where direction meets execution. Write it well and the copilot doesn't guess — it rows.*