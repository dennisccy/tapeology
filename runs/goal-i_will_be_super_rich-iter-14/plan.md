# goal-i_will_be_super_rich-iter-14 Execution Plan

Closes the two real-data defects the iter-13 synthetic-only "pass" shipped: **J-36** (a real
directional move stuck on perpetual `unclear`) and **J-37** (a long/dense window times out into
"very high-volume"). Both are backend correctness/performance fixes behind already-registered UI
rows — **no UI surface, value, route, or control changes**. The authoritative gate is
**committed-real-data CI tests that run without live credentials** (anti-goal #20).

## What to Build

**J-36 — real directional move classifies as control, not perpetual `unclear`**
- **Per-mode vendor feed (in the ONE adapter).** Select the **SIP** consolidated feed for
  `fetch_historical` and keep **IEX** for `stream_live`, driven by config (`historical_feed='sip'`
  / `live_feed='iex'`), read only inside `alpaca.py`. The `ALPACA_FEED` env override must remain
  supported. No vendor `DataFeed` enum leaks outside the adapter. (Root cause: `alpaca.py` `feed`
  property + `_data_feed()` return IEX for both modes; `fetch_historical` line 242 must use the
  historical feed, `stream_live` line 476 the live feed.)
- **Spread becomes a graded confidence factor, not an absolute veto.** In `classifier.py`, add a
  config-driven **directional override**: when a move is *clearly directional* — ratio ≥ floor AND
  |relative price impact| past its cutoff AND speed ≥ floor (the existing control predicate **minus**
  the spread term) — it resolves to `buyer_control` / `seller_control` **even when the quoted spread
  is momentarily wide or quotes are absent/crossed** (e.g. around an LULD halt). In that override
  path the spread enters **only** through the confidence score (graded), never as a veto. (Root
  cause: `classifier.py:104/128/148/168` apply `spread_metric <= max_spread` as a hard AND-term that
  kills an otherwise-clear move on a 2,700-bps single-venue quote.)
- **Keep the honest-uncertainty floor intact.** A genuinely wide *relative* spread on weak/mixed
  tape, or high aggression with no proportionate price progress, still reads `unclear` / absorption
  (J-06 / J-33 behaviour). The override engages **only** for the clearly-directional-with-wide/absent-spread
  case. The absorption gates MUST remain the **exact complement** of the control impact condition
  (the iter-5/iter-13 keystone) — re-prove on a shared boundary fixture.

**J-37 — long/dense window loads progressively (first chunk replays immediately, rest streams in)**
- **Decouple time-to-first-data from total-window load.** Restructure the fetch+replay seam so the
  backend **never fetches the whole window before responding**: the **first sub-window chunk** is
  fetched within the bounded budget and replay begins on it; **remaining chunks fetch in the
  background** and are appended **in epoch order** as the replay advances. Likely shape: the adapter
  exposes a **chunk-by-chunk** fetch (a generator/iterator of `HistoricalWindow` sub-windows in
  epoch order, reusing the existing `_split_window` partition); `HistoricalProvider` / the historical
  feeder (`watch_manager._feed_paced`) consumes chunks progressively instead of materializing one
  whole `HistoricalWindow`. (Root cause: `_fetch_trades_quotes` materializes ALL chunks before
  returning; `historical.py:stream()` materializes the whole window before yielding; `main.py:292`
  awaits the entire fetch before building the engine.)
- **Correctness preserved (single source of truth + determinism).** Streamed chunks MUST NOT
  fabricate, drop, reorder (beyond canonical epoch order), or de-duplicate real prints;
  quote-before-trade ordering at equal epochs is preserved per chunk AND across the stitch boundary;
  the engine still bins on its logical timeline so progressive chunks vs. a single-shot fetch yield
  **identical** features / state / confidence. Keep single-window `fetch_historical` working for
  short windows + the cache; a re-watch stays near-instant from the window cache.
- **"Very high-volume — try a shorter range" becomes a true backstop.** The advertised **Full RTH**
  quick-pick loads for a liquid symbol without that error; the message fires only when the **first
  chunk itself** genuinely cannot load within budget. Backend bound stays < frontend
  `WATCH_REQUEST_TIMEOUT_MS`. Any new **displayed-series cap** (e.g. capping the history buffer /
  recent-trades length so a ~50k-event window does not stall) is config-owned and must not change
  tape state / features.

**Config (no magic numbers)**
- Add `historical_feed` / `live_feed`; any J-36 directional-override / graded-spread-factor boundary;
  any J-37 displayed-series cap. No literal threshold in engine/classifier/adapter code.

**Real-data fixtures + CI tests (the anti-goal #20 gate — REQUIRED, not operator-gated)**
- Extend `apps/backend/scripts/capture_alpaca_fixture.py` to support `--feed sip` (so the captured
  fixture records `feed: sip` and carries SIP quotes).
- Commit the **GME 14-05-2024 13:30–13:40 UTC** SIP window (the >10% drop into the LULD halt) and,
  if feasible, a **mirror rally** SIP window. Commit a **long/dense** liquid-symbol window large
  enough to exercise chunked progressive load (a dense representative slice if a true Full-RTH
  capture is too large to commit — document the size/coverage decision).
- Write the J-36 and J-37 CI tests (below) to **fail loudly** until the real fixtures are present —
  a synthetic stand-in is NOT acceptable (anti-goal #20).

## Agents Required

- **backend-data: yes** — all of the above (classifier override, per-mode feed, progressive
  fetch+replay seam, config constants, fixture capture-script extension, CI tests).
- **frontend-ux: no** — no UI surface, value, route, or control changes this iteration.

## Frontend Present: no

(Backend correctness + performance fixes behind already-registered rows. The Historical
replay-speed control, chart, date picker, and waiting/progress treatment are all unchanged.
UI-impact / UI-test-design / browser-QA / UX-regression steps are N/A — the authoritative gates are
the committed-real-data CI tests.)

## Files to Create/Modify

- `apps/backend/app/config.py` — add `historical_feed` / `live_feed`; J-36 directional-override /
  graded-spread boundary constant(s); any J-37 displayed-series cap. Document each (no magic numbers).
- `apps/backend/app/providers/adapters/alpaca.py` — per-mode feed selection (`fetch_historical` uses
  SIP, `stream_live` uses IEX, both config-owned; `ALPACA_FEED` override preserved); add a
  **chunk-by-chunk** historical fetch (generator of epoch-ordered sub-windows) while keeping
  single-window `fetch_historical` + cache for short windows. No vendor enum leaks outward.
- `apps/backend/app/engine/classifier.py` — config-driven directional override so a clearly-directional
  move with a wide/absent quoted spread resolves to control (spread graded, not a veto); absorption
  gates stay the exact complement; reads spread/impact/price from the canonical feature engine only.
  Document the override predicate in the docstring.
- `apps/backend/app/providers/historical.py` — consume chunks progressively (stitch in epoch order
  across the chunk boundary; quote-before-trade preserved; epoch anchor still the first real record).
- `apps/backend/app/watch_manager.py` — historical feeder consumes the progressive chunk stream;
  background chunk fetch appended in epoch order; determinism/single-source preserved.
- `apps/backend/app/main.py` — `_watch_historical` begins replay on the first chunk within budget
  instead of awaiting the entire window; "shorter range" backstop fires only when the first chunk
  cannot load. Backend bound < frontend timeout preserved.
- `apps/backend/scripts/capture_alpaca_fixture.py` — `--feed sip` support; capture quotes-by-feed.
- `apps/backend/tests/fixtures/alpaca/GME_*_sip.json` — NEW committed REAL SIP fixture (the GME drop;
  mirror rally if captured). Self-documented `source: alpaca`, `feed: sip`, `note: REAL … not synthesized`.
- `apps/backend/tests/fixtures/alpaca/<LIQUID>_long_*.json` — NEW committed REAL long/dense fixture.
- `apps/backend/tests/test_real_data_gate.py` (or a new `test_real_data_classify.py`) — J-36 CI test:
  GME SIP fixture → `HistoricalProvider` + `TapeEngine` → asserts `seller_control` at the drop with
  confidence ≥ `reasonable_confidence` and seller markers at the transition (mirror rally →
  `buyer_control` if captured). Fails loudly if the real fixture is absent.
- `apps/backend/tests/test_classifier_relative.py` — extend with the J-36 keystone (absorption =
  exact complement at the boundary) + negative guards (wide *relative* spread on weak tape → unclear;
  absolute-fallback / sim fixtures byte-identical, pinned confidence unchanged).
- `apps/backend/tests/test_chunked_fetch.py` / `test_historical_provider.py` — J-37 CI test over the
  long/dense fixture: (a) first chunk consumed before the whole window is fetched (time-to-first-data
  decoupled), (b) NO "very high-volume" error on the advertised path, (c) streamed record set ==
  single-shot set in epoch order (no fabricate/drop/reorder/dedup); + a determinism test (progressive
  chunks vs. single-shot → identical tape_state / confidence / features).
- `apps/backend/tests/test_real_data_gate.py` — per-mode feed assertion: `fetch_historical` uses SIP,
  `stream_live` uses IEX (config-owned), no vendor enum leaked outside the adapter (extend the
  existing `test_default_feed_is_iex` / `test_configured_feed_is_used` family).
- `docs/handoffs/goal-i_will_be_super_rich-iter-14-dev.md` — REQUIRED. Must state explicitly whether
  the GME SIP fixture and the long/dense fixture were captured with **real credentials**; if not,
  that the gating tests fail loudly until they are (never silently passed on a synthetic stand-in).

## Key Test Scenarios

- **J-36 gate (authoritative, no creds):** the committed **GME SIP** fixture replayed through
  `HistoricalProvider` + `TapeEngine` resolves to **`seller_control`** at the drop with confidence ≥
  `reasonable_confidence`, with seller markers at the transition (mirror rally → `buyer_control` if
  captured).
- **J-36 keystone + negative guards:** absorption gate remains the **exact complement** of the
  control impact condition at the boundary; a wide *relative* spread on weak/mixed tape still reads
  `unclear` (J-06 / J-33 preserved); the directional override does **not** force a call on weak
  evidence; the absolute-fallback / sim fixtures stay **byte-identical** (pinned confidence unchanged).
- **J-37 gate (authoritative, no creds):** the committed **long/dense** fixture begins replay within
  the configured budget — the **first chunk is consumed before the whole window is fetched** — with
  **NO** "very high-volume" error on the advertised path and the streamed record set **equal** to the
  single-shot set in epoch order (no fabricated/dropped/reordered/de-duplicated prints).
- **J-37 determinism:** the same dense window via progressive chunks vs. a single-shot fetch yields
  **identical** tape_state / confidence / features (chunk boundaries do not perturb the engine).
- **Per-mode feed:** `fetch_historical` uses the SIP feed and `stream_live` uses the IEX feed
  (config-owned), with the `ALPACA_FEED` override still honoured and no vendor enum leaking outside
  the adapter.
- **Regression floor (MUST stay green, zero regressions):** all five sim scenarios (J-01–J-09), the
  J-33 relative gates, J-11/J-16/J-17/J-18 historical+chart, J-28/J-29/J-34 vendor-responsiveness.
  Full backend suite ≥ the iter-13 floor of **259 passed / 1 credential-gated skip** plus the new
  tests, with the absolute-fallback / sim fixtures byte-identical. Error cases hold: an empty/anchorless
  window → empty chart + honest read; a window whose **first chunk** genuinely cannot load → the
  actionable "shorter range" backstop (J-28).

## Assumptions & Notes

- **Fixture capture requires real Alpaca SIP credentials.** This dev environment has none (per the
  iter-13 handoff and the recorded memory note). If the operator cannot capture the GME SIP fixture
  and the long/dense fixture with real credentials, the iteration is **incomplete**: the J-36 / J-37
  gating tests MUST be written to **fail loudly** (not be marked green on a synthetic stand-in), and
  the dev handoff must say so plainly. This is the load-bearing constraint (anti-goal #20). **Flag to
  the operator:** capturing these fixtures is the single external dependency that may block GOAL_ACHIEVED.
- **GME SIP fixture size:** the 10-minute GME drop should be a manageable committed size at the SIP
  feed; if the long/dense full-RTH capture is too large to commit, capture a dense representative
  slice (tens of thousands of events) and document the size/coverage decision in the handoff.
- **`feed` in the capture script + fixture loader:** the committed fixture's `feed` field must record
  `sip` for the GME capture; the `load_fixture_window` loader is feed-agnostic (loads epochs/prices),
  so no loader change is required beyond carrying the SIP quotes the capture writes.
- **In scope only:** these two real-data defects. Out of scope (excluded): any new UI surface / route
  / control / displayed value; changing the **live** feed (stays IEX by design); Level-2 book /
  `liquidity_pull_score`; the predictive-edge backtest harness; persistence; any re-tuning that would
  loosen honest-uncertainty / price-impact-over-aggression on mixed/weak tape (the override is
  additive only) or regress J-01–J-35.
- **Spec ↔ goal alignment:** the plan advances `docs/goal.md` Success Criteria ("Historical replay",
  "Real-data honesty", "A Historical watch … loads quickly") and Key Capabilities #1 (SIP for
  historical, IEX for live behind the vendor-agnostic adapter). No drift from the project goal.
