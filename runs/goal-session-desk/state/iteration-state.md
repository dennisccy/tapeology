# Iteration State — desk

**After iteration:** 3 · **Date:** 2026-07-25 · **Verdict:** CONTINUE

## Journeys

3 passing (J-01 J-02 J-03) · 3 failing (J-04 J-05 J-06) · 1 partial (J-07) — 7 total

## Active blockers

- None human-owned; J-04 (`/desk`) is unblocked, keyless, dev-owned. **Owed BEFORE its screenshots:**
  fixture-scoped backend (a real screen = ~100 honest `skipped: no bars`; `desk_screen` bypasses
  `TradabilityCache`); warm iter-1's `_config_content_hash`-stranded caches (setups ~9-11 min cold,
  `/structure` Load ~21.6 s); re-point `journey-scripts/J-07.json` step 8 off async `300.11`; T-9.
- **HUMAN call queued** (audit B10): `_select_best_band` (`desk_screen.py:206`) ranks distance BEFORE
  score → AAPL's row is `C / 2.348 bps / 57.0 (298.08-299.24)` while the same served list carries
  `C / 123.0 (300.23-302.25)`, the era's pinned wall. J-04 labels the chip "nearest same-class band"
  or the tuple is respecced (J-05's drill-in holds either way).

## Last 2 verdicts

- iter 3: CONTINUE — J-03 `passing` on the evaluator's OWN 52-check live run (bands byte-identical to
  `GET /research/tradability`, exact `distance_bps` from the basis bar's close, identical-pin re-run
  byte+mtime unchanged, 0 `BarStore` calls in the signature, cross-process determinism); suite
  1299p/8s/0f, pin unchanged, zero diff on 12 frozen owners + frontend, COHERENCE-PASS.
- iter 2: CONTINUE — J-02 `passing` (truth-table, fetch/reuse/cancel-resume top-up); suite 1240p/8s/0f.

## Do not redo

- **J-01 + J-02 + J-03 DONE, clause-verified** (`state/journey-history.json`). J-03 shipped
  `desk_screen.py` (`ScreenStore` 5-pin append-only key, `compute_screen` the SOLE walker,
  `compute_bar_store_signature`, `resolve_desk_screen_dir`, `screen_as_of`) + `desk_screen_compute.py`
  (manager + CLI) + 4 `/research/desk/screen*` routes. Re-check only suite + pin + zero-diff.
- **Settled:** zero new `Config` field all era (store dirs = env-var/sibling resolvers); `as_of =
  f"{screen_date}T23:59:59Z"`; `created_utc` = registration metadata, not a determinism input
  (`assumptions.md` iter-3); screen list META-ONLY; global single-flight (one slot, NOT per-date).
- **Hygiene when the file is already open:** scope `TAPEOLOGY_DATASET_DIR` in `route_ctx` (T3); refuse-
  rather-than-record an empty screen with no universe (B4); port `ScreenStore.record`'s corrupt-file
  guard into `UniverseStore.record` (`desk_universe.py:418` overwrites silently). J-07 stays `partial`
  until nav = 3 routes (J-04) + MCP = 17 tools (today 15); suite floor **1299p / 8s**.
