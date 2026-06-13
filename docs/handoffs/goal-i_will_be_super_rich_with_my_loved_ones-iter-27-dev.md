# goal-i_will_be_super_rich_with_my_loved_ones-iter-27 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-27
**Date:** 2026-06-13
**Agent:** developer
**Status:** complete
**Iteration type:** VERIFICATION / EVIDENCE-CAPTURE ONLY (no product capability planned)

---

## Summary

This is a verification iteration. **No new product capability, no new endpoint, no new
component, no new config key was added.** Backend + frontend source is **byte-identical** at the
end of this iteration (J-68 byte-identity sentinel holds — `git diff --stat HEAD -- apps/backend/
apps/frontend/` is empty). The deliverable is *evidence*, not code: the already-shipped real-data
flows were re-exercised — against the full unit suite, against the live Alpaca vendor with real
credentials, and through the engine over a real SIP historical window — to capture positive pass
evidence sufficient for the evaluator to flip the target journeys from `partial` to `passing`.

**No genuine real-data defect surfaced. Zero source files changed.**

---

## CREDENTIAL STATE (load-bearing — flagged per spec, regardless)

The plan's highest-risk assumption was a **CREDENTIAL GAP** (only `ALPACA_API_KEY` present,
`ALPACA_API_SECRET` absent), which would have forced the fixture-substitution fallback for the
credentialed-historical legs. **That assumption is now FALSE.** As of this run, `apps/backend/.env`
contains BOTH credentials:

- `ALPACA_API_KEY` — present, len=26, non-blank
- `ALPACA_API_SECRET` — present, len=44, non-blank

After `app.env.load_env()` (the exact path `app/main.py:60` runs at startup),
`AlpacaAdapter().is_available()` returns **`True`**. The operator added the secret out-of-band, as
the plan anticipated ("operator may add the secret out-of-band before the pipeline runs"). **The
live-credentialed historical path is therefore exercisable this weekend and was NOT substituted by
the fixture path.** This is a positive update vs the plan's worst case; the fixture fallback
remains available but was not needed for the credentialed-historical legs.

(Probe detail, no values exposed: `is_available()` checks BOTH `bool(_env(ENV_API_KEY)) and
bool(_env(ENV_API_SECRET))` at `alpaca.py:188`; both resolve non-blank after `load_env()`.)

---

## What Was Verified (per leg, with the path used)

### Backend full suite — green, zero re-pins, byte-identical
- **Full suite:** `848 passed, 1 skipped, 2 warnings`, **exit 0**, in 397.89s — exactly the
  spec's expected baseline (848/1/0). The 1 skip is the pre-existing live-market-hours-gated test
  (unchanged). Zero re-pins. `apps/backend/` diff empty.
- **Command:** `cd apps/backend && .venv/bin/python -m pytest tests/ -v`

### Anchor suites (cited by name + count, all green)
| Journey | Suite | Result |
|---------|-------|--------|
| J-11 | `test_historical_provider.py` | 12 passed |
| J-16 | `test_aggressor.py` | 14 passed |
| J-18 | `test_history.py` | 12 passed |
| J-18 | `test_history_api.py` | 6 passed |
| J-22 / J-28-anchor | `test_vendor_timeout.py` | 5 passed |
| J-22 / J-28-anchor | `test_vendor_responsiveness.py` | 32 passed |
| J-23 / J-27 | `test_stream_lifecycle.py` | 9 passed |
| J-29 | `test_progressive_fetch.py` | 9 passed |
| J-29 | `test_chunked_fetch.py` | 7 passed |
| J-32 | `test_speed_api.py` | 6 passed |
| J-36 regression | `test_real_data_classify.py` | 5 passed |
| J-37 regression | `test_real_data_gate.py` | 35 passed |
| J-34/perf regression | `test_dense_replay_gate.py` | 11 passed |

### J-22 vendor-timeout boundary (confirmed at the vendor-call boundary, backend < frontend)
The config chain is explicit and ordered correctly (`app/config.py`):
- `vendor_http_timeout_seconds = 6.0` — the **real call-level HTTP deadline set on the vendor
  client session** (the actual vendor-call boundary, not merely an outer `asyncio.wait_for`
  wrapper). A slow/large response is cut off by the client itself and mapped to the neutral
  `provider_timeout`.
- `vendor_call_timeout_seconds = 8.0` — the outer wrapper deadline (HTTP deadline ≤ wrapper).
- Frontend `WATCH_REQUEST_TIMEOUT_MS = 12000` (`apps/frontend/lib/config.ts:23`).
- **Ordering holds:** `6.0 ≤ 8.0 < 12.0` → backend bound strictly shorter than the frontend
  client timeout. J-22's "backend bound < frontend bound" precondition is satisfied.

### LIVE credentialed verification (real Alpaca SIP, off-hours, data > 15 min old → free)
Window used: **AAPL, Fri 2026-06-12 09:30–09:32 ET = 13:30–13:32 UTC** (a real prior-trading-day
RTH window; the market is closed today so this is historical, free SIP data).

- **J-11 historical fetch (live credentialed):** `fetch_historical('AAPL', ...)` returned a real
  window: **24,619 real trades + 21,034 real quotes** for the 2-min window (a 5-min AAPL window
  returned 34,260 trades / 37,813 quotes). One vendor round-trip, real bytes, no fabrication.
- **J-16 resolved aggressor side (live credentialed, end-to-end through the engine):** feeding the
  real window through `HistoricalProvider.stream()` → `TapeEngine.process_event()`, the engine
  resolved the side of all 24,619 trades as **buy=14,091 / sell=10,527 / unknown=1** →
  **unknown fraction ≈ 0.004%**, vastly below a quote-only baseline. The quote-rule +
  Lee-Ready tick-test fallback works on real SIP data exactly as the goal's "Resolved aggressor
  side" success criterion requires. Recent-trades is no longer dominated by `unknown`.
- **J-18 / J-31 chart anchor (live credentialed):** the engine's `epoch_anchor` is set (non-None)
  from the first real record, so the chart's true-clock axis maps logical bins back to real
  market time. `…/history` is a pure projection of this same engine buffer (single source of
  truth — no UI-side recomputation).
- **Real values populate the cockpit:** final last quote bid/ask = 296.28 / 296.35 (real), final
  tape_state = `unclear` at confidence 0.20 — an honest low-confidence read of a quiet
  open-bell window, NOT a fabricated directional call.
- **J-14 closed-market (live credentialed, the natural now-state):** `get_market_clock()` returns
  `is_open=False`, **`next_open=2026-06-15T13:30:00Z`** — Monday 15-06-2026, which is
  **14:30 UTC+01:00 (BST)**, exactly the Monday open the spec cites. The closed-market honest
  state is real, not simulated.
- **J-14 unknown-symbol (live credentialed):** `fetch_historical('ZZZZNOTREAL', ...)` raised
  `SymbolNotTradable` → the API maps this to the "not a tradable symbol" honest state. No
  fabricated tape.

### REST substitution path for the date-input harness limitation (J-35)
If the browser harness cannot drive the custom `dd-MM-yyyy` date input, the equivalent
credentialed historical engine state is populated via:
`POST /watch/{ticker}` body `{"mode": "historical", "start": "<ISO>", "end": "<ISO>",
"speed": <float>}` (`app/main.py:65` `WatchRequest`; `mode ∈ {sim, live, historical}`). The same
engine + the same `…/history`/`…/state`/`…/features`/`…/summary` projections populate the same
cockpit pixels. This substitution must be documented by browser-qa-agent if used; a browser-gated
leg must NOT be marked passing on a unit test alone.

---

## Anti-goal assertions checked against the live evidence
- **No fabricated data:** unknown-symbol → `SymbolNotTradable` (no tape); closed market →
  honest `is_open=False` + next open (no synthesized cockpit); a quiet window → honest `unclear`
  at low confidence, never a forced directional state. No `live` was fabricated over an empty tape.
- **Single source of truth:** side/state/price/time are computed once in the engine; the chart and
  cockpit read `…/history`, `…/state`, `…/features`, `…/summary` verbatim. No second computation
  path introduced (no code changed).
- **No trading advice / no profitability:** no copy changed; descriptive-only discipline intact.
- **No tape persistence:** the engine is in-memory; only the committed test fixtures persist
  vendor bytes.

---

## Browser-gated legs (owned by browser-qa-agent, NOT verifiable from the dev step)
These require a live frontend + browser automation and are the gating pipeline step. The dev step
has confirmed the **backend data path** each one depends on is live and honest (above); the
on-screen pixel capture is browser-qa-agent's responsibility:
- J-11 / J-16 / J-18 / J-20 / J-29 / J-32 — credentialed historical AAPL/TSLA replay populating
  the cockpit panels, recent-trades side column (unknown far lower than baseline), candlestick
  chart + markers + true-clock axis, picker local-zone label + quick-picks, busy-window load
  within bound + near-instant re-watch, in-progress 1×→10× speed change continuing from position.
- J-14 — three distinct honest-state captures (closed-market / unknown-symbol / empty-window).
- J-23 — backend killed mid-watch → explicit "couldn't connect to the tape stream" within bounds.
- J-27 — no-first-event / feeder-failure → explicit `stale`/`closed`/no-data state owned by
  `stream_status`.

**Pre-capture hygiene reminder (lessons line 51/123/27):** browser-qa-agent MUST confirm the
frontend dev server is live and its served bundle is fresh (content canary) before any capture; a
dead frontend is a hard-flag, not a soft-skip.

---

## Deferred live-only legs (SCHEDULED, not stalls)
Per the spec's "Explicitly deferred" list — these require a market-hours live IEX feed and are
deferred to a **Monday market-hours iteration. Next US open: 15-06-2026 14:30 UTC+01:00 (Monday)**:
- **J-15** — live-feed-gap stale→recover (needs a real live-feed lull during market hours).
- **J-67's live-IEX badge/disclosure PIXELS over a real live feed** + the live-declared
  `iex`-stamped journal row. **J-67 stays `passing` on its non-live evidence — do NOT re-open it
  to `failing`.** (Confirmed live now: a live-mode watch off-hours renders the honest "MARKET IS
  CLOSED" panel — `is_open=False` above — so the live-IEX badge genuinely cannot render over a
  closed market; this is the iter-24 lesson, line 159.)
- Any live-only re-confirmation of J-12 / J-25 / J-26 (already green; no live capture attempted).

An "operator-gated" note would be insufficient for any leg satisfiable off-hours — every such leg
above was actually exercised against the live vendor or the full unit suite, not deferred.

---

## Files Changed
- **None.** Backend + frontend source byte-identical (J-68 sentinel). Only iteration artifacts
  (this handoff, the implementation summary, `status.json`) were written.

---

## Tests Run
Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **848 passed, 1 skipped, 2 warnings — exit 0** (397.89s). Zero re-pins.
Plus a live credentialed Alpaca historical fetch + engine pass (AAPL 2026-06-12 RTH) and a live
`get_market_clock()` / unknown-symbol probe — all succeeded as documented above.

---

## Known Issues
- The 1 skipped test is the pre-existing live-market-hours-gated test (unchanged this iteration).
- The browser pixel captures (J-11/J-14/J-16/J-18/J-20/J-23/J-27/J-29/J-32) are owned by the
  browser-qa-agent pipeline step; the dev step proved the underlying live data path is honest and
  populated but does not itself capture UI pixels.
- All J-16-class measurements were taken over a single real AAPL window; TSLA / a second window
  are equally available to browser-qa-agent if a second sample is wanted (the path is identical).
