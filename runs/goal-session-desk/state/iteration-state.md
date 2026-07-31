# Iteration State — desk

**After iteration:** 28 · **Date:** 2026-07-31 · **Verdict:** GOAL_ACHIEVED

## Journeys

17 passing (J-01..J-17) · 0 failing/partial/unknown · 0 `DEFERRED-BUDGET` · 0 `pending_infra` · 0 `evidence_makeup` — 17 total (merged results 5/5 PASS, all 17 `spec_hash` values match current `docs/goal.md`).

## Active blockers

- **none blocking the goal.** ONE disclosed, non-blocking gap, handed to the owner's OPTIONAL track and no longer tracked as journey debt: J-17's `[NEW]`-flagged demo-narrator film has never shown its subject across 3 attempts. Owner = HARNESS, not product: `scripts/automation/demo-phase.sh:316` always passes `--base-url "$FRONTEND_URL"` and `scripts/automation/lib/demo_runner.py:1292` lets that CLI value beat the script's own `base_url` (iter-28 authored `"base_url": "http://localhost:3391"` correctly and still recorded against `:3301`); and `Depth: evidence` dispatches nobody permitted to provision the scoped `:3391`/`:8391` rig, so the film's subject existed nowhere.
- Coupling to watch: `test_desk_ui_guards.py` reads `journey-scripts/J-13.json` + `J-14.json` — archiving that folder breaks the backend suite.

## Last 2 verdicts

- iter 28: GOAL_ACHIEVED — zero product diff (empty vs both `7a74e2d` and iter-27's `a9fd2e7`); 17/17 passing on evidence the evaluator opened (fresh `J-17-result.png` showing the legacy-absence disclosure for the first time + iter-27's populated frame, valid under A.6 durability); suite 1,474 pass/8 skip exit 0, `08e471b10130e1e2`, 17 MCP tools enumerated live, owner's `.data` untouched (759/1/11/1, only 4 rebuildable sidecars); COHERENCE-PASS, scan CLEAN, all 4 deterministic gates exit 0. The film gap is disclosed, not hidden, per iter-27's own written bound.
- iter 27: CONTINUE — everything proven except the J-17 film, whose 5 frames were one byte-identical image (scoped rig torn down 1 min before the narrator ran).

## Do not redo

- **J-17 is BUILT and thrice-proven** — `_pair_window`'s three cases, the `unchanged` 409 outcome, the four additive per-pair fields, `/desk`'s counts + tail-vs-lookback line + per-failed-pair `requested_window` + the legacy `"window basis not recorded in this run"` state. Do not re-implement, re-tune, or re-photograph.
- **Do NOT request a 4th capture retry of the J-17 film at `evidence` depth** — structurally unobtainable there. Fix the two harness lines above first, or plan it at `full` depth with an explicit rig-provisioning task.
- **The single existing-test edit is RATIFIED** (`test_desk_topup_compute.py:1092`, 4-key → 8-key set equality — widened, not relaxed). Do not revert it; do not edit any other pre-existing assertion.
- J-16 layout is DONE and measured (`table-fixed` + 13-col `<colgroup>`, `flex-nowrap` badges). No width re-tuning, no 14th column; `band `/`opposite ` in-cell prefixes MUST stay (goldens pin them). Never script a `click` on a cell inside a `/desk` ranked or skipped row — the stretched `absolute inset-0` anchor makes it impossible; use `expect`-only.
- **`journey-scripts/J-17.json` EXISTS** as an honest partial proxy on the ambient legacy run. Do not delete or "fix" it to chase the scoped counts — no durable store can reproduce them.
- Zero diff stays law: `engine/`, `config.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py`, `levels.py`, `desk_topup_log.py`, `routes.py`, `meta.py`, `mcp/__init__.py`, both charts, the 5 guard test files; pin `08e471b10130e1e2`; 17 MCP tools; do not edit `docs/goal.md`. Accepted non-defects: 2/100 rows at 63 px, replay-frame duplication, iter-25's optional film-wording note.
