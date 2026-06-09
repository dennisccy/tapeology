# goal-i_will_be_super_rich-iter-14 Dev Handoff

**Phase:** goal-i_will_be_super_rich-iter-14
**Date:** 2026-06-09
**Agent:** developer
**Status:** complete

## What Was Built

Closes the two real-data defects the iter-13 synthetic-only "pass" shipped — both now proven by
**committed-real-data CI tests that run without live credentials** (anti-goal #20).

- **J-36 — a real directional move classifies as control, not perpetual `unclear`.**
  - **Per-mode vendor feed (in the one adapter):** historical replay now reads the **SIP**
    consolidated feed (realistic spreads), live streaming stays on **IEX**. Config-owned
    (`historical_feed='sip'` / `live_feed='iex'`); the feed-override env var still pins both modes.
    No vendor enum leaks outside `alpaca.py`.
  - **Spread is a graded confidence factor, not an absolute veto:** a *clearly directional* move
    (ratio + relative price impact + speed all pass — the control predicate minus the spread term)
    resolves to control even when the quoted spread is wide, **as long as the spread is within the
    override band** (≤ `override_max_spread_multiple` × the stable cap). Beyond the band a wide
    *relative* spread still vetoes control (honest uncertainty for genuinely illiquid/mixed tape).
    Inside the band the spread decays the confidence (graded), never asserting false certainty. The
    absorption gates are unchanged, so they stay the **exact complement** of the control impact
    condition (the keystone).
- **J-37 — a long/dense window loads progressively (first chunk replays immediately, the rest streams in).**
  - **Adapter chunk iterator:** `AlpacaAdapter.iter_historical_chunks` lazily yields epoch-ordered
    `HistoricalWindow` sub-windows (each fetched only when the consumer advances). The neutral
    datetime partition helper moved to `providers/adapters/base.py` as `split_window`.
  - **Progressive provider + feeder:** `ProgressiveHistoricalProvider` stitches chunks in epoch order
    on one logical timeline; `WatchManager.watch_with_progressive_historical` + `_feed_progressive`
    replay the first chunk immediately while background-fetching the rest off the event loop.
  - **Route:** `_watch_historical` fetches **only the first chunk** under the vendor budget for a long
    window, then defers the remaining chunks to the background feeder — so the advertised Full-RTH
    path is accepted (no "very high-volume" refusal up front; the backstop fires only if the *first
    chunk itself* cannot load).
  - **Engine density:** the rolling-window feature computation was made **incremental** (O(1)
    amortised per event) so a dense real window (the GME drop carries ~17k prints in 7s) processes
    in ~1s instead of stalling for minutes. The produced feature values are **byte-identical** to the
    prior full-rescan implementation (verified by the existing pinned-value feature/scenario/Ford-
    fixture tests and a progressive-vs-single-shot determinism test).

## Real fixtures captured (with REAL credentials — present in this environment)

- `apps/backend/tests/fixtures/alpaca/GME_20240514_133013_133020_sip.json` — **REAL** captured GME
  SIP window (13:30:13–13:30:20 UTC, the first ~7s of the >5% open-drop cascade into the LULD halt).
  17,342 trades / 1,946 quotes, `feed: sip`, `source: alpaca`, `note: REAL … not synthesized`.
  **This is a dense representative slice** of the GME drop: a true full 10-minute / Full-RTH SIP
  capture is ~5.6 MB / ~94k events (too large to commit and too dense to replay in CI within budget),
  so the committed slice covers the directional move (price 64.83 → 60.99, −5.7%) that the J-36 gate
  asserts. Real credentials WERE available at dev time, so the gating tests pass on real data (not a
  synthetic stand-in).
- **J-37 long/dense coverage:** rather than commit a second multi-MB liquid-symbol multi-chunk
  capture (a 30-min TSLA SIP window is ~12 MB / ~97k events — too large), J-37's progressive
  stitch + determinism is proven over the **same committed REAL GME records** split into multiple
  in-test epoch chunks (real records, real stitch), and its laziness/decoupling is proven with a
  hermetic counting fake SDK driving the real adapter code path. See "Known Issues" for the rationale.

## Files Changed

- `apps/backend/app/config.py` — added `historical_feed`/`live_feed`, the J-36 directional-override
  boundaries (`directional_override_enabled`, `override_max_spread_multiple`,
  `override_spread_floor_score`), and documented the J-37 displayed-series caps (reuse the existing
  history/recent-trades caps). No magic numbers.
- `apps/backend/app/engine/classifier.py` — directional override (spread = graded factor within the
  band, not an absolute veto); absorption gates stay the exact complement; documented the predicate.
- `apps/backend/app/engine/features.py` — incremental rolling-window aggregates (sums, impact via
  per-trade boundary delta, refresh via an O(1) append path with an exact forward-merge fallback on
  eviction / the standalone API). Byte-identical values, no longer O(n²).
- `apps/backend/app/engine/tape_engine.py` — passes the in-effect quote to the feature engine for the
  incremental refresh path (the same in-effect quote the merge would find; value unchanged).
- `apps/backend/app/providers/adapters/alpaca.py` — per-mode feed selection (SIP historical / IEX
  live, override-aware); `iter_historical_chunks` (lazy epoch-ordered chunk generator) +
  `_fetch_one_subwindow`; `_split_window` re-exported from the neutral base.
- `apps/backend/app/providers/adapters/base.py` — neutral `split_window` partition helper.
- `apps/backend/app/providers/historical.py` — `ProgressiveHistoricalProvider` (stitches chunks on one
  logical timeline) + a shared `_ordered_items` helper.
- `apps/backend/app/watch_manager.py` — `watch_with_progressive_historical` + `_feed_progressive`
  (first-chunk-now + background-stitch) and a shared `_replay_events` pacing loop.
- `apps/backend/app/main.py` — `_watch_historical` splits a long window and fetches only the first
  chunk synchronously, deferring the rest; short windows keep the single-shot + cache path.
- `apps/backend/scripts/capture_alpaca_fixture.py` — `--feed sip` support; records the historical feed.
- `apps/backend/tests/test_real_data_classify.py` — NEW: J-36 real-data gate (GME SIP →
  `seller_control` with markers, deterministic, no creds in fixture; fails loudly if the fixture is absent).
- `apps/backend/tests/test_progressive_fetch.py` — NEW: J-37 gate (laziness, no fabricate/drop/reorder/
  dedup, progressive==single-shot determinism over REAL GME records, end-to-end feeder stitch + route).
- `apps/backend/tests/test_classifier_relative.py` — extended with the J-36 override band tests,
  graded-confidence monotonicity, the override-disabled byte-identical keystone switch, and the
  absorption keystone under a wide in-band spread.
- `apps/backend/tests/test_real_data_gate.py` — extended with the per-mode feed assertions
  (SIP historical / IEX live, override-aware, config-sourced).
- `apps/backend/tests/test_window_resolution.py` — updated the long-window assertion for progressive
  loading (first chunk fetched at the exact UTC instant; partition spans the whole window — no tz shift).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **283 passed, 1 skipped** (the iter-13 floor was 259 passed / 1 skipped; +24 new tests, zero
regressions). The 1 skip is the pre-existing credential-gated live-integration test. Runtime ~103s
(the real GME fixture replays add time but stay within budget).

Live smoke test (real credentials): `fetch_historical('AAPL', …)` returns SIP data with a penny
spread (187.01/187.02), confirming the per-mode SIP feed is wired live. Backend boots cleanly
(`bash scripts/start-backend.sh` → `GET /health` 200).

## Known Issues

- **J-37 long/dense fixture is the GME slice + in-test chunking, not a separate committed multi-chunk
  capture.** A genuinely long *real* multi-chunk window for a liquid symbol is multi-MB (30 min of
  TSLA SIP ≈ 12 MB / 97k events) — too large to commit and too dense to replay in CI within budget.
  J-37's correctness (progressive == single-shot, no fabricate/drop/reorder/dedup, determinism) is
  therefore proven over the **same committed REAL GME records** partitioned into multiple in-test
  epoch chunks (real data, real stitch), and its *laziness/first-data-decoupling* is proven with a
  hermetic counting fake SDK that drives the real adapter chunk-iterator code path (you cannot observe
  "before the whole window is fetched" with a pre-materialised fixture). If the reviewer requires a
  separately-committed real multi-chunk fixture, capture e.g. a 30–45 min window of a *mid-liquidity*
  symbol and add it — the test seam (`_split_real_into_chunks`, `iter_historical_chunks`) already
  supports it.
- **GME fixture size:** the committed real SIP fixture is ~1.2 MB. It is real market data only (no
  keys — asserted by a test). If repo size is a concern, a shorter sub-window (e.g. 13:30:13–13:30:18,
  ~14.5k trades / ~1 MB) still resolves to `seller_control`; the 7s window was chosen for a cleaner
  sustained `seller_control` read through the end of the window.
- **Incremental refresh fast path vs. eviction fallback:** the O(1) refresh path is used while the
  window is append-only with in-effect quotes (the dense-burst case J-37 targets); on any
  trade/quote eviction it falls back to the exact forward-merge (correct, just O(window) for that
  tick). For windows that slide continuously through an extended dense reopen burst the fallback is
  active — still correct and far faster than the old multi-pass rescan, but not O(1) there. The GME
  drop slice fits inside the window, so the fast path is active throughout its replay.
- **No frontend changes** (`Frontend Present: no`). All changes are backend correctness/performance
  behind already-registered UI rows (tape state + chart markers; the Historical fetch wait). The
  authoritative gates are the committed-real-data CI tests, not browser checks.
