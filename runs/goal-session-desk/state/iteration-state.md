# Iteration State — desk

**After iteration:** 30 · **Date:** 2026-07-31 · **Verdict:** ESCALATE

## Journeys

18 passing (J-01..J-18) · 0 failing/partial/unknown · 0 `DEFERRED-BUDGET` · 0 `pending_infra` · 1 `evidence_makeup` (J-18, for the walkthrough frames ONLY) — 18 total; all 18 `spec_hash` values re-derived and matching `docs/goal.md`.

## Active blockers

- **MINOR anti-goal, OPEN (dev):** the scoped rig's build rewrote two TRACKED files — `apps/frontend/next-env.d.ts:3` and `apps/frontend/tsconfig.json`'s include list — with an absolute path into a scratchpad dir that teardown deleted (dangling `/// <reference>`). Fix: `git checkout --` both; make the rig restore them.
- **Spec-vs-dispatch gap (dev):** `docs/phases/goal-desk-iter-30.md` says `Depth: lean` with 3 code changes IN SCOPE, but `iter-30/depth-dispatched` reads `evidence` → no developer ran, none landed. STILL OPEN: `desk/page.tsx` `LatestScreenRunDetail` renders `desk-screen-run-latest-unreached` + zeroed `desk-screen-run-latest-counts` for a `done && reused` run (TC-2 fails); `desk_screen_compute.py:277` sets `failed_member = members[0]` when `attempted == 0` (TC-4 fails); TC-4/5/6 tests unwritten.
- **Doc drift (decomposer; COHERENCE-WARN):** `state/blueprint.md:673` asserts both fixes above shipped. They did not — correct that entry.
- **Walkthrough (demo-narrator, needs `full`):** `reports/demo/goal-desk-iter-29/` step-02/03/04 are one image. PASSENGER task only, never an iteration goal; last request — if it duplicates again it drops to owner-optional.
- Coupling to watch: `test_desk_ui_guards.py` reads `journey-scripts/J-13.json` + `J-14.json` — archiving that folder breaks the backend suite.

## Last 2 verdicts

- iter 30: ESCALATE (next run MUST be `full`) — the confirm's missing empty-state screenshot was captured on a throwaway scoped rig and the evaluator opened it (`reports/qa/goal-desk-iter-30-evidence/J-18-empty-state.png`); but the depth downgrade dropped 3 planned fixes, blueprint.md claims they shipped, and two tracked build files were left polluted. Suite 1500/8 exit 0, `08e471b10130e1e2`, 17 MCP tools, `.data` provably unwritten, scan CLEAN.
- iter 29: GOAL_ACHIEVED (first key) — REJECTed by the second key (`iter-29/eval-confirm.md`): J-18's honest empty state was never photographed.

## Do not redo

- **J-18's empty-state screenshot is DONE** (`reports/qa/goal-desk-iter-30-evidence/J-18-empty-state.png`, unique md5, scoped rig, first action). The populated + reused screenshots are DONE and were accepted by the confirm (`reports/demo/goal-desk-iter-29/step-02.png`, `reports/qa/goal-desk-iter-29-evidence/UT-01-result.png`). Never re-capture any of the three.
- **`journey-scripts/J-18.json` is already hardened** to stable `desk-screen-runs-table` substrings ("101 / 101", "no walk was performed") — iter-29 audit finding T1 is CLOSED. Do not re-pin it to ids.
- **J-18 is BUILT** — `desk_screen_log.py` (sole owner), the five-pin pre-check + reuse short-circuit in `run_screen_and_record`, `GET /research/desk/screen/runs`, the `/desk` "Screen Runs" section. Do not re-implement. The auditor's B1 one-shot `logged` latch and the optional `screen_run_store=` kwarg are ratified — do not revert or "fix".
- Do NOT run a capture-only iteration, and do NOT re-verify J-01..J-17 as an iteration goal (10 replayed green, 2 spot-checked, 5 corroborated in-frame this run).
- J-16 layout is DONE and measured (`table-fixed` + 13-col `<colgroup>`). No 14th column, no width re-tuning; `band `/`opposite ` in-cell prefixes MUST stay. Never script a `click` inside a `/desk` ranked/skipped row — the stretched `absolute inset-0` anchor blocks it; use `expect`-only. Demo scripts stay READ-ONLY over the ambient store (never click Run Screen).
- Zero diff stays law: `engine/`, `config.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py`, `levels.py`, `desk_topup_log.py`, `meta.py`, `mcp/__init__.py`, both charts, the guard test files; pin `08e471b10130e1e2`; 17 MCP tools; zero new `Config` fields. Accepted non-defect: replay/demo frame duplication (tooling).
