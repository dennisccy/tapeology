# Iteration State — desk

**After iteration:** 26 · **Date:** 2026-07-31 · **Verdict:** CONTINUE

## Journeys

17 passing (J-01..J-17) · 0 failing/partial/unknown · 0 `DEFERRED-BUDGET` — 17 total (merged results 17/17 PASS). Only J-17 carries `evidence_makeup: true` (film owed; behaviour proven). No `pending_infra`. All 17 `spec_hash` values match the current `docs/goal.md`.

## Active blockers

- **Stale shared frontend build — do this FIRST, dev-owned.** `apps/frontend/.next/static/chunks/app/{layout,desk/page}.js` now contain `localhost:8000` and NOT `localhost:8301` (evaluator's own grep): iter-26's scoped rig built the ONE shared `.next` against its own backend, since torn down. `:3301` renders nothing and all 16 goldens (`journey-scripts/J-01..J-16.json`) will false-FAIL until `rm -rf apps/frontend/.next` + rebuild + restart both ambient processes.
- **J-17's `[NEW]`-flagged walkthrough was never recorded** (`reports/demo/goal-desk-iter-26/` absent). The spec asked `Depth: full`; the arbiter demoted to `lean`, which records no film — the same demotion that cost iter-24 J-16's film. Needs `evidence` (or `full`) depth.
- **No golden script for J-17** — `journey-scripts/J-17.json` deliberately not written (its counts came from a throwaway rig); J-17 must ride the LLM browser-qa lane, not replay.
- Coupling to watch: `test_desk_ui_guards.py` reads `runs/goal-session-desk/journey-scripts/J-13.json` + `J-14.json` — archiving that folder breaks the backend suite.

## Last 2 verdicts

- iter 26: CONTINUE — J-17 built and proven (run record on disk matches the screenshot number for number: `0 reused · 6 fetched · 2 unchanged · 4 failed`, 2 tail / 10 full_lookback, all three window cases real; suite 1474 passed / 8 skipped, `08e471b10130e1e2`, 17 tools, every zero-diff and the append-only proof re-run by the evaluator; COHERENCE-PASS, scan CLEAN) — but its acceptance-named film does not exist.
- iter 25: GOAL_ACHIEVED — 16/16 passing with zero code change; J-16's film RECORDED with `opposite`+`levels` inside its own frames; J-06 + J-15 re-verified; all capture debt cleared.

## Do not redo

- **J-17 is BUILT and verified** — `_pair_window`'s three cases, the `unchanged` 409 outcome, the four additive per-pair fields, and `/desk`'s counts + tail-vs-lookback line + per-failed-pair `requested_window` + the shared `WINDOW_BASIS_NOT_RECORDED` fallback. Do not re-implement or re-tune; the ONLY gap is the film.
- **The single existing-test edit is RATIFIED** (`test_desk_topup_compute.py:1092`, 4-key → 8-key set equality — widened, not relaxed). Do not revert it; do not edit any other pre-existing assertion.
- J-16 layout is DONE and measured (`table-fixed` + 13-col `<colgroup>` = 1214 px, `flex-nowrap` badges). Do not re-tune widths or add a 14th column. `band `/`opposite ` in-cell prefixes MUST stay (goldens pin the literal text).
- Never script a `click` on a cell inside a `/desk` ranked or skipped row — the stretched `absolute inset-0` anchor makes it impossible and a landed click navigates away. Use `expect`-only text assertions (this is also what turns `RECORDED_WITH_NOTES` into `RECORDED`).
- Zero diff stays law and was re-verified at iter-26: `engine/`, `config.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py`, `levels.py`, `desk_topup_log.py`, `routes.py`, `meta.py`, `mcp/__init__.py`, both charts, and the 5 guard test files; pin `08e471b10130e1e2`; 17 MCP tools; do not edit `docs/goal.md`.
- Evidence capture stays READ-ONLY on the ambient store: never trigger Run Screen / top-up / reconcile there. iters 24–26 all proved `.data` byte-identical (only `bar_index` `-wal`/`-shm` move). Accepted non-defects (leave as is): 2/100 rows at 63 px, 8 stacked `/desk` sections, `.mcp.json` at `:8000`, goal.md's stale host-mask paragraph, iter-25's optional film-wording + replay-duplication notes.
