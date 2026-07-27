# Iteration State — desk

**After iteration:** 7 · **Date:** 2026-07-27 · **Verdict:** STALLED

## Journeys

6 passing (J-01 J-02 J-03 J-04 J-05 J-06) · 1 partial (J-07 — 3 clauses unmet, all owner-gated) — 7 total

## Active blockers

- **HUMAN (owner), 4 iterations old — NOW THE ONLY BLOCKER ON THE ERA.** iter-4 changed three files `docs/goal.md` protects: `apps/backend/app/research/bars.py`, `apps/frontend/components/StructureChart.tsx`, `apps/backend/tests/test_structure_chart_viewport.py:191-198` (guard assertion relaxed literal→regex). `docs/goal.md` is byte-unchanged since era open (`047c38e`), so J-07's own clauses "every guard test byte-unmodified" and "zero out-of-inventory changes" are literally FALSE. Unblock = ratify in `docs/goal.md`, or revert (measured cost: price-less rows return, AAPL map as-of 2026-07-25 goes empty, `/structure` crashes), or narrow J-07's wording. No agent can close this.
- **Evidence debt (dev, does not need the owner):** no era-open baseline of kept-route bodies was EVER captured, so J-07's byte-identity clause has never been checkable. Capture it from a `047c38e` worktree against a throw-away copy of `.data/`, then diff and explain every difference.
- **Test-asset debt (audit T1):** `runs/goal-session-desk/journey-scripts/J-07.json` step 10's target was changed (`tradable-map-chart-caption` → `tradable-map-table`) out of scope on a rationale the audit disproved; restore + prove with one `--mode verify --journeys J-07` results file.
- **Picture debt:** cockpit Historical mode on a REAL symbol (candles + timeframe switch + band overlay) never photographed; SIM-BUYER honestly has neither bars nor a map.

## Last 2 verdicts

- iter 7: STALLED — J-06 `failing → passing` (evaluator's own live proof: 17 tools, `desk_universe`/`desk_screen` byte-identical to curl in empty AND populated states, `?date=` verbatim, `{"screen":null}` honest); J-07's four missing pictures finally exist and were opened; halted because every remaining path to a passing J-07 is a human-owned decision. Suite 1349/0f/8s, pin `08e471b10130e1e2`, COHERENCE-PASS.
- iter 6: CONTINUE — J-05 `failing → passing`: rendered past screen matched `.data/screen/screen-2026-06-22-3ecd45c062c7.json` field-for-field.

## Do not redo

- **J-06 is DONE and live-proven** — two GET-proxy tools in `app/mcp/__init__.py` `_STATIC_PATHS` + 5 contract tests in `tests/test_mcp_server.py`. Never add a `?date=` tool (that stays `get_endpoint`-only) and never a write tool.
- **F2 hover fix is DONE** — composite `title` on the existing `desk-row-drill-in`/`desk-skip-row-drill-in` anchors (`app/desk/page.tsx:181-193`, applied :231/:319) + `tests/test_desk_hover_tooltip_guard.py`. Anchor `href`/`absolute inset-0`/`data-testid` are byte-unchanged — never reshuffle row click geometry.
- **J-01–J-05 DONE, clause-verified** (`state/journey-history.json`), all re-verified passing in iter-7. Re-check only suite + pin + zero-diff on their owners; `journey-scripts/J-05.json` step 2 now selects by `data-screen-date` — keep it that way, and keep every golden write-free.
- **J-07's met clauses need no rework** — suite+pin, 3 routes, 17 tools, and the sim-cockpit / Structure-wall / Case-Studies / Edge-Report pictures (`reports/qa/goal-desk-iter-7-evidence/UT-08..UT-12`, `TC-15`, `TC-16`).
- **Settled:** zero new `Config` field all era; suite floor now **1341 passing / 8 skipped (1349 collected)**; pin `08e471b10130e1e2`; `UI_ROUTES` = 3; fixture-scoped browser rigs are the recipe; hygiene items only when those files open (guard `run_screen_and_record`; `_has_finite_prices` on the per-series read; the new date-lookup test should seed its own screen; delete the untrue comment at `app/desk/page.tsx:207`).
