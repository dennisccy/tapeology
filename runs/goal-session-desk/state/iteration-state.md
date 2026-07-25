# Iteration State — desk

**After iteration:** 2 · **Date:** 2026-07-25 · **Verdict:** CONTINUE

## Journeys

2 passing (J-01 J-02) · 4 failing (J-03 J-04 J-05 J-06) · 1 partial (J-07) — 7 total

## Active blockers

- None human-owned; none blocking J-03. Three dev-owned carried items: (1) `record_bar_series`'s benign "identical content already
  on file" **409 is labelled `outcome: "failed"`** + CLI exit 1 (`desk_topup_compute.py:146-147`) — a next-UTC-day re-run hits ~100
  `1w` pairs; decide the vocabulary, keeping `"reused"` == zero vendor calls. (2) `latest_window_end_utc` is the REQUESTED window
  end, not the last bar (real AAPL `1w`: `2026-07-25` vs `2026-07-20`) — J-04 must not badge it "last bar". (3) Iter-1's
  `edge_report_cache._config_content_hash` move still strands the setups/tradability/edge-report caches (real `/research/setups`
  cold ~9-11 min, `/structure` Load ~21.6 s; iter-2 added no `Config` field, so it held still) — warm it, and re-point
  `journey-scripts/J-07.json` step 8 off the async `300.11` text, before J-04's browser pass.

## Last 2 verdicts

- iter 2: CONTINUE — J-02 `passing` on the evaluator's OWN in-process runs (fixture-universe truth-table vs the era-open
  `bar_index`; run-1 fetched / run-2 all-reused at 0 vendor calls; composite cancel-then-resume; 4.3 ms coverage at 0 `BarStore`
  calls), suite 1240p/8s/0f, pin `08e471b10130e1e2`, 24/24 kept routes byte-identical, COHERENCE-PASS.
- iter 1: CONTINUE — J-01 `passing` on the evaluator's own run through the real routes; suite 1210p/8s/0f; pin unchanged incl.
  under a Path-A field override; COHERENCE-PASS.

## Do not redo

- **J-01 + J-02 are DONE and independently verified.** J-02 shipped `desk_coverage.py` (`get_desk_coverage`,
  `DESK_TOPUP_TIMEFRAMES = ("1h","4h","1d","1w")`), `desk_topup_compute.py` (`DeskTopupComputeManager` + `run_topup` + CLI
  `main()`), an additive `BarIndex.coverage()`, and `GET /research/desk/coverage` + the `POST/GET/POST-cancel` topup trio. Reuse
  by name; do not re-derive the timeframe set or re-probe these clauses.
- **No `Config` field was needed in iter-2** — the pin held with zero Path-A work. Prefer that route; a new field re-moves `_config_content_hash` and re-strands the caches.
- **Coverage truth is per-`(symbol, timeframe)`** — era-open store = AAPL (all 4 tf), AMD (all 4), MSFT (`1h`/`1d` ONLY); ~100
  members have no bars, so a real screen is mostly honest `skipped: no bars` until the operator top-up runs.
- **J-07 stays `partial` BY DECISION** until nav = 3 routes (J-04) and MCP = 17 tools (J-06) — see `state/assumptions.md`. Suite
  floor is now **1240p / 8s**; the pin must not move; kept-route capture = 24 templates (audit T5: 3 more are vendor/wall-clock).
- **Next target settled: J-03 alone, `full` depth.** HARD: the screen `as_of` derives from the screen date's session close, NEVER
  `now()` (do not copy `_TOPUP_LOOKBACK_DAYS`'s wall-clock window); the bar-store-signature pin reads the durable index, never a
  JSON-store re-hash. J-06 is unbuildable until `/research/desk/screen` exists. Full carry-forwards in `iter-2/eval.md`.
