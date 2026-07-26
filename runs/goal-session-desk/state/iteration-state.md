# Iteration State — desk

**After iteration:** 6 · **Date:** 2026-07-26 · **Verdict:** CONTINUE

## Journeys

5 passing (J-01 J-02 J-03 J-04 J-05) · 1 failing (J-06) · 1 partial (J-07 — only its "MCP = 17 tools" clause unmet, at 15) — 7 total

## Active blockers

- **Dev:** J-06 is the LAST unbuilt journey (`app/mcp/__init__.py` `_STATIC_PATHS` → 15 tools) and the only thing keeping J-07 partial. Both target endpoints already have empty + populated browser evidence.
- **Dev (honesty gap, iter-6 audit F2):** the new whole-row drill-in `<Link className="absolute inset-0">` (`apps/frontend/app/desk/page.tsx:198-213` / `:288-300`) hit-tests above every cell, so the `title` hover text carrying the full unrounded distance (`0.33523150389608725` behind `0.34 bps`) and the "window last requested" dates is unreachable — it silently undoes iter-4's own audit honesty fix. Decide the row interaction contract + add a hit-test assertion.
- **Dev (J-07 evidence):** no fresh screenshots since iter-4 for the sim cockpit, Case Studies drill-in, Edge Report honest state. Needed before J-07 can pass.
- **HUMAN (owner) call, now 3 iterations old:** `docs/goal.md` still lists `bars.py` + `StructureChart.tsx` as untouched this era; both changed in iter-4 under a developer-written spec amendment. Ratify in `docs/goal.md` or revert. Blocks nothing.
- **Test debt (audit T1):** `journey-scripts/J-05.json` has never been replayed and picks its history row by position, not by `data-screen-date`.

## Last 2 verdicts

- iter 6: CONTINUE — J-05 `failing → passing`: four acceptance screenshots opened, and the rendered past screen matched `.data/screen/screen-2026-06-22-3ecd45c062c7.json` field-for-field; suite 1333p/8s/0f (1341 collected), pin `08e471b10130e1e2`, ambient `.data/` unchanged, COHERENCE-PASS. Era cannot close while MCP = 15 tools.
- iter 5: CONTINUE — J-04 `partial → passing`: the never-existing "Run Screen running + second click refused" screenshot finally captured on a fixture-scoped backend.

## Do not redo

- **J-05 is DONE and browser-proven** — history click-and-swap, "Latest" control, ranked + skipped row drill-in, `/structure` `?symbol=&asof=` prefill + auto-load, `tests/test_desk_ui_guards.py` (5 tests incl. seeded counter-tests). Do not rebuild; only F2's hover contract is open.
- **No new backend route for desk history** — `GET /research/desk/screen?date=` already serves it verbatim (`desk_routes.py:248-266`); iter-6 added ZERO backend product code.
- **`journey-scripts/J-04.json` is write-free** (steps 5–6 are read-only `expect`s); no golden clicks a write control now. Never re-add a Run Screen click.
- **J-01–J-04 DONE, clause-verified** (`state/journey-history.json`), all re-verified passing in iter-6. Re-check only suite + pin + zero-diff on their owners.
- **Fixture-scoped browser rigs are the settled recipe** (fresh temp root + all `TAPEOLOGY_*_DIR/DB` vars + seeded real screen/bar copies); ambient `.data/` came out unchanged again.
- **Settled:** zero new `Config` field all era; suite floor now **1333p / 8s (1341 collected)**, pin `08e471b10130e1e2`, `UI_ROUTES` = 3; both ranked AND skipped rows drill in; chip copy "nearest same-class band" with `_select_best_band` byte-unchanged; hygiene items only when those files open (guard `run_screen_and_record`; `_has_finite_prices` on the per-series read; re-tighten `test_structure_chart_viewport.py:194`).
