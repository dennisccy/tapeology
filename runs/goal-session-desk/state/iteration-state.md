# Iteration State — desk

**After iteration:** 31 · **Date:** 2026-07-31 · **Verdict:** GOAL_ACHIEVED (first key)

## Journeys

18 passing (J-01..J-18) · 0 failing/partial/unknown · 0 `DEFERRED-BUDGET` · 0 `pending_infra` · 0 `evidence_makeup` — 18 total; all 18 `spec_hash` values re-derived from `docs/goal.md` and matching.

## Active blockers

- **none.** All four recorded anti-goal items are `resolved` — iteration 30's MINOR one is CLOSED: `apps/frontend/next-env.d.ts` and `apps/frontend/tsconfig.json` are byte-identical to `48c5fc2^` (evaluator's own `git show … | diff -`, zero diff; `grep scratchpad` = 0 hits). `git status` still shows ` M` for both only because HEAD carries the polluted content — the revert ships in this iteration's commit.
- Awaiting the second key (deterministic gates + fresh-context confirm). If it REJECTs, the only named items are the four owner-optional notes below — none is a product defect.
- Coupling to watch: `test_desk_ui_guards.py` reads `journey-scripts/J-13.json` + `J-14.json` — archiving that folder breaks the backend suite.

## Last 2 verdicts

- iter 31: GOAL_ACHIEVED — the two dropped honesty fixes landed and were verified in frame (`reports/qa/goal-desk-iter-31-evidence/UT-02-result.png`: a reused run shows no amber note and no zero-counts row), both build files reverted byte-for-byte, 10/10 golden replays green, J-18 replay 4/4, walkthrough frames distinct and on-subject. Suite 1502 pass / 8 skip / 0 fail, `08e471b10130e1e2`, 17 MCP tools, `.data` provably unwritten, scan CLEAN, coherence PASS, audit PASS_WITH_GAPS.
- iter 30: ESCALATE — an `evidence` dispatch of a `lean` spec dropped three planned fixes and left two tracked build files polluted (all closed at iter-31).

## Do not redo

- **The four open notes are OWNER-OPTIONAL, not iteration work** (the hard auditor states this explicitly): B1 `failed_member: null` also covers a first-member crash; F1 the counts line is hidden on the rare `ScreenAlreadyRecorded` reuse race; T3 `journey-scripts/J-18.json`'s note 4 prose is stale (inert metadata, never read by the replay); the film's `step-02.png` scroll landed one section short. Do NOT spin any of them into a new iteration.
- **The walkthrough film is DONE** (`reports/demo/goal-desk-iter-31/`, three distinct md5s, Screen Runs section readable in `step-03.png`). The iter-30 "last time I ask" bound is satisfied — never re-plan it.
- **J-18 is BUILT and FIXED** — `desk_screen_log.py` (sole owner), the five-pin pre-check reuse short-circuit, `GET /research/desk/screen/runs`, the `/desk` "Screen Runs" section, plus iter-31's two guards (`0 < attempted < len(members)`; `run.state === "done" && !run.reused`). Do not re-implement or revert. `journey-scripts/J-18.json` is already hardened to stable substrings — do not re-pin it to ids.
- **All J-18 screenshots are DONE** (empty state iter-30; populated/reused iter-29 + iter-31 UT-02/UT-03). Never re-capture. Do NOT run a capture-only iteration, and do NOT re-verify J-01..J-17 as an iteration goal.
- J-16 layout is DONE and measured (`table-fixed` + 13-col `<colgroup>`). No 14th column, no width re-tuning; `band `/`opposite ` in-cell prefixes MUST stay. Never script a `click` inside a `/desk` ranked/skipped row — the stretched `absolute inset-0` anchor blocks it; use `expect`-only. Demo/replay scripts stay READ-ONLY over the ambient store.
- Zero diff stays law: `engine/`, `config.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py`, `levels.py`, `desk_topup_log.py`, `meta.py`, `mcp/__init__.py`, both charts, the guard test files; pin `08e471b10130e1e2`; 17 MCP tools; zero new `Config` fields. Accepted non-defect: replay-frame duplication (tooling).
