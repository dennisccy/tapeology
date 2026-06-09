**Verdict:** COHERENCE-PASS

## Coherence Audit — iter-14 (goal-i_will_be_super_rich-iter-14)

Session: `i_will_be_super_rich` · Iteration index: 14 · Snapshot SHA: `136e1740f635ed66fc524881ac0657cafaf4053d`

---

### Step 1 — Data Contract check

The iter-14 spec declares: "No new contract row. This iteration hardens the computation of already-registered rows, adding no new displayed value and no new contract row." The UI surface map confirms: "Backend-only phase (Frontend Present: no) — No UI surfaces affected."

Each registered row was checked against the diff (committed changes via `git diff 136e1740` plus all uncommitted working-tree changes via `git diff HEAD`):

**Row 1 — Tape state + confidence (`TapeStateClassifier`)**

`apps/backend/app/engine/classifier.py` is modified, but `TapeStateClassifier` remains the sole computing owner. The change recalibrates the existing buyer/seller control gates so that a wide/absent quoted spread is a graded confidence factor rather than an absolute veto for a clearly-directional move. Key observations:
- The new private helper `_graded_spread_score` lives inside `TapeStateClassifier` — it is not a second producer; it is a scoring sub-function of the existing single producer.
- No second function outside `TapeStateClassifier` computes tape state or confidence.
- New config constants (`directional_override_enabled`, `override_max_spread_multiple`, `override_spread_floor_score`) live exclusively in `config.py` — config values, not displayed values.
- No UI surface fetches tape state from a non-canonical source (no frontend changes at all).

**Row 2 — 14 core features × 5 windows (`FeatureEngine`)**

`apps/backend/app/engine/features.py` is modified to maintain incremental running aggregates in `_Window` instead of a per-tick rescan. The spec explicitly states values are "BYTE-IDENTICAL to the prior full-rescan implementation." `FeatureEngine` remains the sole computing owner; no second feature-computation path was introduced.

**Row 6 — Watched-source descriptor + watch/stream status (engine/feeder)**

`apps/backend/app/watch_manager.py` adds `watch_with_progressive_historical` and `_feed_progressive`. These methods manage delivery pacing and chunked-data stitching; they do not compute stream_status independently. The engine's `set_stream_status` calls remain the single owner. `_replay_events` is a shared pacing loop extracted from the prior inline implementation — a refactor, not a second computation.

**Rows 10 / 12 — Price history / resolved historical window**

`apps/backend/app/providers/historical.py` adds `ProgressiveHistoricalProvider`. This class implements the same Provider protocol as `HistoricalProvider` and feeds the same `TapeEngine.process_event` path; it does not bin OHLC candles, infer sides, or compute features. The engine history buffer remains the sole owner of row 10. The frontend datetime module remains the sole owner of row 12 (no frontend changes).

`apps/backend/app/providers/adapters/alpaca.py` adds `iter_historical_chunks` and `_fetch_one_subwindow`. These are fetch-path utilities inside the one vendor adapter. They do not compute any registered displayed value; they yield the same real records the single-shot `fetch_historical` would produce.

`apps/backend/app/providers/adapters/base.py`: `split_window` is moved here from `alpaca.py`. This is a pure partitioning utility refactor — it computes no displayed value.

`apps/backend/app/main.py`: `_watch_historical` branches between single-shot and progressive load paths. Both paths route into the same engine via `manager.watch_with_provider` / `manager.watch_with_progressive_historical`. No row value is recomputed here.

**Per-mode feed (J-36, `historical_feed`/`live_feed`)**

The feed selection lives exclusively inside `AlpacaAdapter._feed_name()`. The vendor `DataFeed` enum is mapped internally; no vendor type leaks outside the adapter. This is a config-owned fetch-parameter change, not a displayed value and not a second computation owner.

**No new displayed value was introduced.** No unregistered value was found. No row value was fetched from a non-canonical endpoint or recomputed in the UI.

Result: **no Step 1 violations.**

---

### Step 2 — Information Architecture check

The iteration has no frontend changes and introduces no new routes, pages, panels, or navigation elements. The UI surface map explicitly states "No UI surfaces affected." The blueprint's single `/` HOME and its persistent nav skeleton are untouched.

Result: **no Step 2 violations.**

---

### Step 3 — Advisory observations

None. The iteration is purely backend computation hardening, performance optimization, and real-data CI-test work. The observation string change in `_buyer_observations` / `_seller_observations` ("Wide quoted spread — call on price impact" when the directional override engaged) is an honest label for the existing observations panel — read from the canonical source, not a display value re-derivation.

---

### Summary

| Check | Result |
|---|---|
| Part A — Data Contract (duplicate computation / non-canonical source) | PASS — no violation |
| Part A5 — Unregistered new value | PASS — no new value introduced |
| Part B — Information Architecture (hidden feature / duplicate home / parallel shell) | PASS — no new surface |
| Part C — Advisory | PASS — no advisory issues |
