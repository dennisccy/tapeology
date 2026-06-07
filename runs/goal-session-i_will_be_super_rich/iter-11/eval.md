# Iteration 11 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** n/a (halt — goal achieved)

## Summary

The last three unbuilt Must-haves — J-28 (true call-level vendor deadline + actionable oversize
message), J-29 (fast-by-design historical load: concurrent fetch, folded pre-flight, window cache,
prompt warm-up), and J-30 (warmed/cancellable symbol search) — are all built and verified with
concrete evidence: 230 backend tests pass (independently re-run; +32 over the iter-10 floor of 198,
zero regressions) and a real browser run on a working frontend (`:3650`, credentials present)
captured the J-28 actionable timeout, the J-29 fast/cached historical load, and the crisp J-30
search against the live Alpaca IEX vendor. With J-01–J-27 still green, COHERENCE-PASS, and no
anti-goal violation, the full Must-have set J-01–J-30 is complete.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-28 | failing | passing | reports/qa/.../iter-11-evidence/UT-06-timeout-error.png (actionable "try a shorter range", no cockpit) + backend `test_vendor_responsiveness.py` (HTTP deadline at SDK boundary, config-asserted backend 6.0s ≤ 8.0s < frontend 12000ms ordering, oversize→actionable provider_timeout with NO engine) |
| J-29 | failing | passing | UT-07-cockpit-populated.png (real TSLA window populated ~2s, full features + chart), UT-08-rewatch-cache-hit.png (~131ms cache hit), UT-15-waiting-indicator.png (waiting treatment during fetch) + unit tests (concurrent fetch ≈ max not sum; one round-trip on success; cache hit replays same real records; warm-up fast-forward determinism-identical) + live run (~1.0s first / 0.013s cached) |
| J-30 | failing | passing | UT-04-aapl-fast-response.png (~60ms first search post-restart), UT-03-rapid-type-result.png (no out-of-order), UT-05 (no stuck spinner), UT-09-zzz-empty-dropdown.png (vendor-miss → empty, no error), UT-13-aapl-selected.png (real match selectable), UT-11 (free-text still works) + unit tests (startup warm, abort cancellation, vendor-error→[], min-query) |
| J-01 | passing | passing (re-verified) | UT-12: SIM-BUYER → Buyer Control conf 0.870, full panels live (reports/qa/.../iter-11-evidence/UT-11-12-sim-buyer-control.png) |
| J-02 | passing | passing (carried) | UT-12 buyer_control conf 0.870, aggressive_buy_ratio 0.925, +14800 net; engine math empty-diff this iter (coherence-confirmed); test_scenario green in 230-pass run |
| J-03–J-07 | passing | passing (carried) | engine/classifier/observation generation untouched (git diff = config/adapter/fetch only); 230-pass suite incl. test_scenario/test_classifier/test_features |
| J-08 | passing | passing (carried) | coherence.md Step 1: stream_status written once by engine/feeder, read verbatim; no client recomputation of rows 1–6; cache supplies raw input records, not computed outputs |
| J-09 | passing | passing (carried) | watch lifecycle (_feed/_feed_live/pause/stop) untouched; only _feed_paced warm-up pacing changed; UT in QA shows Stop→idle |
| J-10 | passing | passing (re-verified) | UT-14-mode-selector.png: exactly Live/Historical/Simulated; each reveals correct controls, no crash |
| J-11 | passing | passing (carried) | historical replay success path unchanged (cache miss = today); UT-07 real historical populated; test_historical_provider green |
| J-12 | passing | passing (carried) | live-socket path untouched (iter-4 deadlock lesson heeded); UT-14 Live controls + market-status render without feed; operator-gated socket leg unchanged |
| J-13 | passing | passing (re-verified) | UT-13: real AAPL match returned + selectable (search correctness; speed is the separate J-30, now also passing) |
| J-14 | passing | passing (carried) | folded fetch preserves honest states: unknown→symbol_not_tradable, empty→no_data_for_window (unit tests TC-21/TC-22); no-creds warm is no-op; off-hours closed path unchanged |
| J-15 | passing | passing (carried) | stale watchdog / mid-stream lifecycle explicitly out of scope and untouched; operator-gated |
| J-16 | passing | passing (carried) | aggressor/tick-test classifier untouched; test_historical_provider tick-test fixture green |
| J-17 | passing | passing (carried) | UT-07 chart pane renders with markers on the populated historical cockpit; PriceChart untouched |
| J-18 | passing | passing (carried) | /history projection + chart untouched; UT-07 real historical candles render; operator-gated against-live leg unchanged |
| J-19 | passing | passing (carried) | pause behavior unchanged (only _feed_paced warm-up pacing changed); 19 hermetic pause tests green in 230-pass run |
| J-20 | passing | passing (carried) | datetime/window-resolution + Historical picker untouched (no picker file changed); UT-06/UT-07 show the zone-labelled picker + quick-picks; test_window_resolution green |
| J-21 | passing | passing (carried) | page.tsx pending branch unchanged; UT-15 connecting/waiting observed within ~300ms of Watch |
| J-22 | passing | passing (carried, hardened) | client backstop (12000ms AbortController) + wrapper retained as backstop; J-28 adds the true HTTP deadline beneath it; test_vendor_timeout green |
| J-23 | passing | passing (carried) | no-swallow Watch path untouched; useTapeStream/page.tsx render-priority unchanged; UT-09/UT-05 show no stuck spinner |
| J-24 | passing | passing (carried) | TopBar validation gate untouched; UT-11 free-text still Watches without false "select a symbol" error |
| J-25 | passing | passing (carried) | watch-resolution/idle-leave logic untouched; UT-15 leaves idle within ~300ms; UT-06 resolves to explicit non-idle error |
| J-26 | passing | passing (carried) | waiting/empty treatment unchanged and exercised by J-29's fetch wait (UT-15 amber pulsing dot, no blank screen) |
| J-27 | passing | passing (carried) | stale/failed/no-data lifecycle out of scope and untouched; backend lifecycle tests green in 230-pass run |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Bounded, honest, performant vendor calls (critical) | OK | Real call-level `requests.Session` HTTP deadline at the adapter boundary (not just the wrapper); backend 6.0s ≤ 8.0s < frontend 12000ms ordering asserted from config; concurrent fetch + folded pre-flight + LRU/TTL window cache make it fast by design (not by lengthening timeouts); warmed universe + abort-cancellation + min-query for search; oversize error is actionable ("try a shorter range"), not a misleading retry; all bounds are config constants (no magic numbers) |
| No fabricated data (critical) | OK | Window cache stores/replays raw real `HistoricalWindow` records; warm-up fast-forward is delivery-pacing only (engine sees identical ordered stream; determinism unit-test-proven); oversize timeout creates NO engine (no fabricated tape); vendor-miss search → `[]` not invented symbols |
| Single source of truth (critical) | OK | coherence.md Step 1 PASS: stream_status/features/state/confidence written once by engine/feeder, read verbatim; cache supplies raw inputs, engine computes OHLC/markers/features once; no client/API recomputation |
| Provider-agnostic engine (critical) | OK | All `alpaca`/`alpaca-py` imports confined to `adapters/alpaca.py` (git-grep verified); `main.py` names neither the SDK nor `_ASSET_UNIVERSE` (warm fires through the neutral `warm_symbol_universe()` seam; `VendorTimeout` is a neutral exception in base.py) |
| No secrets in source (critical) | OK | `apps/backend/.env` not git-tracked and gitignored; `.env.example` has only empty placeholders; no hardcoded key assignment in tracked source |
| No execution path (critical) | OK | No order/broker/execution affordance added; vendor-fetch + search responsiveness only |
| No silent dead-clicks (critical) | OK | UT-15: connecting/waiting within ~300ms; UT-06 resolves to explicit actionable error; search abort resolves to no-result, never a swallowed failure |
| No mute cockpit / silent return to idle (critical) | OK | UT-15 waiting treatment fills the fetch wait (no blank/idle); UT-06 oversize resolves to explicit non-idle error panel; stream_status lifecycle untouched |
| No magic numbers | OK | New constants (HTTP deadline, cache size/TTL, warm/refresh interval, fast-forward bound, frontend debounce-ms/min-query) all in config.py / config.ts |
| Deterministic & reproducible | OK | Warm-up fast-forward determinism unit-test-proven (features/state/confidence byte-identical to synchronous reference); cache replays same records |
| One focused chart, computed once (critical) | OK | Chart/PriceChart/history path untouched; UT-07 renders real historical candles + markers from /history verbatim |

## Coherence

iter-11 coherence.md = **COHERENCE-PASS** (no Data-Contract or Information-Architecture drift; one
advisory WARN on `SYMBOL_SEARCH_MIN_QUERY` alignment, which resolves in the implementation's favor —
see below). No structural veto.

## Browser-QA FAIL reconciliation (UT-02, UT-10 are mis-specified, not defects)

The browser-qa verdict is FAIL on 2/16 tests (UT-02, UT-10), both asserting a symbol-search
min-query of **≥ 2**. Verified directly:
- backend `apps/backend/app/config.py:123` → `symbol_search_min_query: int = 1`
- frontend `apps/frontend/lib/config.ts:34` → `SYMBOL_SEARCH_MIN_QUERY = 1`

These **match exactly**, which is precisely what the spec mandated (the frontend constant
"MIRRORING the backend `symbol_search_min_query`"). The J-30 acceptance requires only "a sensible
minimum query length"; neither the journey, the data contract, nor any anti-goal specifies 2. The
two failing tests encode the test author's own assumption of 2, contradicted by the as-built,
single-source-mirrored config. This is the exact coherence-auditor advisory WARN, resolved in the
implementation's favor. No journey regresses and no anti-goal is violated. Evidence is otherwise
real and deduplicated (`md5sum *.png` shows distinct hashes; populated cockpit shots ~160KB vs idle
~55KB — not placeholder-identical), and all J-28/J-29/J-30 target assertions pass.

## Next-Step Recommendation

Halt — goal achieved. The full Must-have set J-01–J-30 is complete with concrete passing evidence,
COHERENCE-PASS, and zero anti-goal violations. Optional (non-blocking) cleanup for any future
touch-up session: if a ≥2 min-query is ever desired for UX, bump both `symbol_search_min_query`
(backend) and `SYMBOL_SEARCH_MIN_QUERY` (frontend) together and update UT-02/UT-10 — but the current
aligned value of 1 is spec-conformant and is not a defect.

## Halt Justification

GOAL_ACHIEVED conditions are all met:
1. **Every Must-have journey J-01–J-30 has status `passing`** with positive evidence — J-28/J-29/J-30
   newly passing this iteration (real browser renders + 230-pass backend suite incl. 32 new vendor-
   responsiveness tests, independently re-run); J-01–J-27 carried/re-verified green (engine, classifier,
   history, pause, and the full Watch lifecycle untouched or provably additive — git diff is confined to
   config / adapter / fetch / search files).
2. **No unresolved anti-goal violation** — all critical anti-goals re-checked against the actual diff
   (SDK confined, provider-agnostic main.py, no committed secrets, no fabricated data, single source of
   truth, no execution path); `anti_goal_violations` remains empty.
3. **coherence.md is COHERENCE-PASS** — no structural veto.
4. **The browser-QA FAIL is a mis-specified test (min-query 2 vs the spec-conformant aligned 1)**, not a
   product defect or a journey regression.
