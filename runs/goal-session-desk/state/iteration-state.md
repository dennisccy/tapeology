# Iteration State — desk

**After iteration:** 4 · **Date:** 2026-07-26 · **Verdict:** CONTINUE

## Journeys

3 passing (J-01 J-02 J-03) · 2 failing (J-05 J-06) · 2 partial (J-04 J-07) — 7 total

## Active blockers

- **EVIDENCE LANE, dev-owned — the only reason J-04 is not `passing`:** `browser-qa-agent` never ran in iter-4 (per `trace/trace.jsonl`), `...-iter-4-ui-test-results.md` was never written, `...-closure-verdict.md` = **CLOSURE-FAIL**. Missing state: **Run Screen in progress + a second click refused**. Run it FIXTURE-SCOPED (temp universe/bar/screen dirs, 103-member fixture + AAPL/MSFT bars).
- `reports/qa/goal-desk-iter-4-qa.md` is discredited (audit T1: TC-02 `started=true` false; TC-04 retired label; TC-20 1305 vs 1328; `TC-01-empty-state.png` shows a POPULATED page; both `TC-12-*.png` blank + identical). Regenerate, never cite. No `/desk` golden yet (`journey-scripts/` = `J-07.json` only).
- **HUMAN call queued:** `docs/goal.md` lists `bars.py` (BarStore) + `components/StructureChart.tsx` as untouched this era; both changed under a developer-written spec amendment. Owner ratifies in `docs/goal.md` or the two files revert (minor/unresolved in `journey-history.json`).

## Last 2 verdicts

- iter 4: CONTINUE — `/desk` ships and works (evaluator opened the empty-state + populated-briefing shots; verified `/meta/ui-routes` = 3 routes, suite 1328p/8s/0f, pin `08e471b10130e1e2`, pinned AAPL 300.11–302.2 unchanged, J-07 replay PASS 1/1) — but the browser lane never ran and one required screenshot does not exist ⇒ J-04 `partial`. COHERENCE-WARN.
- iter 3: CONTINUE — J-03 `passing` on the evaluator's own 52-check live run; suite 1299p/8s/0f.

## Do not redo

- **J-01 + J-02 + J-03 DONE, clause-verified** (`state/journey-history.json`); re-check only suite + pin + zero-diff on their owners.
- **J-04's PRODUCT is built — do not rebuild the page.** `app/desk/page.tsx`, 7 `lib/api.ts` fns, 10 `lib/types.ts` types, `UI_ROUTES` 3rd row, `reused`/`screen_id`, no-universe 422, `UniverseStore` corrupt-file guard, `route_ctx` dataset scoping — shipped and verified. iter-5 owes EVIDENCE only.
- **Settled:** zero new `Config` field all era; chip copy "nearest same-class band" (`_select_best_band` byte-unchanged); `bar_store_signature` labelled "Bar-store signature" (a digest), "window last requested" only on coverage tooltips; Run Screen submits the client's today; price-less rows are excluded-and-reported on the merged read, never deleted (60 files stay put).
- **Hygiene when those files are open:** guard `run_screen_and_record` like the POST route (B1); apply `_has_finite_prices` to the per-series read (B2); re-tighten `test_structure_chart_viewport.py:194`. Suite floor **1328p / 8s**; J-07 `partial` until MCP = 17 tools (today 15).
