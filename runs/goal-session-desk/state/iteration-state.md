# Iteration State — desk

**After iteration:** 25 · **Date:** 2026-07-30 · **Verdict:** GOAL_ACHIEVED

## Journeys

16 passing (J-01..J-16) · 0 failing/partial/unknown — 16 total. No journey carries `evidence_makeup` or `pending_infra`; no `DEFERRED-BUDGET` row this run (merged results 12/12 PASS). All 16 `spec_hash` values match the current `docs/goal.md`.

## Active blockers

- None. Every acceptance clause of every journey is met with evidence the evaluator opened; the session is at the first key of the finish and awaits the deterministic gates + second-key confirm.
- Non-blocking, wording/tooling only (one `evidence`-depth run could carry all three): (1) the film reads `RECORDED_WITH_NOTES` because in-row cell clicks are impossible — the stretched drill-in anchor (`app/desk/page.tsx:416`) intercepts them; swap those four `click` actions for `expect`-only assertions; (2) the film's narration drifts into judgement ("heavily confirmed", "might be noise", "might be more sticky", "helps you plan your exit") — language the product's own copy is forbidden to use; (3) the replay tool keeps saving the same first `/desk` view, so 7 of 11 verify frames are one image.
- Coupling to watch: `test_desk_ui_guards.py` reads `runs/goal-session-desk/journey-scripts/J-13.json` + `J-14.json` — archiving that folder breaks the backend suite.

## Last 2 verdicts

- iter 25: GOAL_ACHIEVED — the three iter-24 gaps closed with ZERO code change. J-16's film RECORDED with `opposite`+`levels` inside its own frames (evaluator opened step-02/step-05) and one-row-scoped click targets; J-06 re-verified (evaluator's own `tuple(TOOL_NAMES) == EXPECTED_TOOLS`, 17 tools); J-15 re-verified (609 / 5 / 2 / 121+badge read in ONE frame region, every value matched to the record on disk, 100/100 sum-invariant, checksum recomputes); `J-16-verify.png` now on disk; 9/9 goldens green, zero edits; ZERO store write (all 13 recorded files keep checksums + pre-run mtimes); `08e471b10130e1e2`; COHERENCE-PASS; scan CLEAN.
- iter 24: CONTINUE — J-16's layout shipped and measured (table `scrollWidth` 1214 === container 1214, was 1795/1214; rows 57 px, was ~115), but J-06 + J-15 were budget-deferred and the film was never recorded (lean depth records none).

## Do not redo

- J-16 layout is DONE and measured: `table-fixed` + 13-col `<colgroup>` summing to 1214 px, `flex-nowrap` coverage badges, `rank` cell = `.map` index + 1, class/distance chips (`apps/frontend/app/desk/page.tsx`). Do not re-tune widths.
- `band `/`opposite ` in-cell prefixes MUST stay (J-13.json/J-14.json pin the literal text via `get_by_text`); guard `test_desk_row_cells_keep_the_label_prefix_their_golden_script_asserts`. Served-order + testid-presence guards already exist in `apps/backend/tests/test_desk_ui_guards.py`.
- Never script a `click` on a cell inside a `/desk` ranked or skipped row — the stretched `absolute inset-0` anchor makes it structurally impossible (and a landed click navigates to `/structure`, destroying the frame). Use `expect`-only text assertions; per-row `tr[data-symbol=…]` scoping fixes multi-match, not this.
- Zero diff stays law: `engine/`, `config.py`, `desk_screen.py`, `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, both charts, `test_copy_discipline.py`, `test_desk_hover_tooltip_guard.py`; pin `08e471b10130e1e2`; 17 MCP tools; do not edit `docs/goal.md`.
- Evidence capture stays READ-ONLY: never trigger Run Screen / top-up / reconcile. iters 24 and 25 both proved `.data` stays byte-identical (only `bar_index`/`dataset_index` `-wal`/`-shm` move). Do not delete `.data/screen/screen-2026-07-30-bad6387963ef.json`.
- Accepted non-defects: 2 of 100 rows at 63 px (positions 24, 80 — the reused `round number` badge's 22 px height; do not restyle); `/desk` is 8 stacked sections; run tables unbounded; history rows not keyboard-reachable; `.mcp.json` points at `:8000` so live MCP proxy spot-checks fail against the `:8301` rig; goal.md's stale host-mask paragraph.
