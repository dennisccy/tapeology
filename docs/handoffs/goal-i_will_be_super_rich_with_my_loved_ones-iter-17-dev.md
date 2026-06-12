# goal-i_will_be_super_rich_with_my_loved_ones-iter-17 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-17
**Date:** 2026-06-12
**Agent:** developer
**Status:** complete

## What Was Built

Capability-34 **engine performance gate** — the session's first engine touch, backend-only, no
journey flips by design (it unblocks J-60–J-62, next iteration). No user-facing change.

- **Truly incremental refresh-score maintenance** in `apps/backend/app/engine/features.py`. The
  permanent post-eviction degradation is gone: `_Window` no longer sets `_refresh_incremental =
  False` on the first eviction (the old defect, after which **every** `compute()` re-ran the
  O(window) forward-merge `_refresh_fractions()` — quadratic on any stream longer than a feature
  window). `bid_refresh_score` / `ask_refresh_score` are now maintained **incrementally across
  trade AND quote evictions** by a new per-side `_RefreshSide` structure + a forward-merge cursor.
- **BYTE-IDENTITY preserved (non-negotiable).** The incremental values exactly equal the
  `_refresh_fractions()` oracle — including its post-eviction **"in-window quotes only"** semantics
  (an early trade that loses its in-effect quote to a quote eviction STOPS contributing refresh
  evidence; it is NOT served its stale append-time quote). No feature value was re-pinned; the full
  existing engine suite stays green.
- **`_refresh_fractions()` retained** as (a) the authoritative path for the standalone
  `FeatureEngine` API (which threads no in-effect quotes — behaviour unchanged) and (b) the test
  oracle the incremental path is pinned against.
- **Committed ≈10-minute real SIP dense fixture**
  `apps/backend/tests/fixtures/alpaca/PG_20260609_170000_171000_sip.json` — PG (Procter & Gamble),
  2026-06-09 17:00:00–17:10:00 UTC, **SIP** consolidated feed, captured at dev time via the
  existing bounded/chunked vendor adapter. 3,229 real trades + 11,012 real SIP quotes, ~1.2 MB
  (well under the ~25 MB budget). Spans ~598 s so **all five feature windows evict**. This is the
  same fixture capability 32's reference study will reuse next iteration.
- **Config budget key** `dense_replay_time_budget_seconds = 60.0` in `app/config.py`, **excluded
  from `config_fingerprint`** with a documented rationale (a CI gate value never enters persisted
  computation) + a fingerprint-stability test + the counter-test (a real classifier threshold still
  moves the fingerprint) — the iter-12/iter-16 discipline.
- **New test matrix** (see below): structural no-rescan counter with eviction guard; oracle
  equivalence (real fixture + sim + millions of randomised ops); CI timing gate; pinned anchors;
  fingerprint pair; full error-case matrix.

## How The Incremental Algorithm Works (for the reviewer)

The refresh score is the fraction of **weak prefix-maxima (records)** over each side's in-effect
quote values, in arrival order (bid: `bid >= running_max`; ask: `ask <= running_min`). Two facts
make it maintainable without a per-event rescan:

- **Append** (dense-burst case): O(1) — a new print is a record iff it beats the window-wide best,
  held in a monotonic deque (`_best`).
- **Front eviction**: removing a left prefix can only LOWER later prefix-maxes, so a print's record
  status can only flip not→yes, never back. When the evicted front print was a record, the gap up
  to the next still-standing record is re-scanned for newly-exposed records, then we stop. Each
  print is promoted **at most once** over its lifetime → amortised O(1).
- **Quote re-mapping** (the only window re-walk): when a quote eviction removes the in-effect quote
  an already-folded FRONT trade depended on, that trade re-maps (to the next surviving quote ≤ its
  ts, or to NONE — the oracle's quirk). Because source-quote indices are non-decreasing along the
  fold FIFO, only the front contributor can be affected; when it is, the trackers are rebuilt once
  from the surviving window. This fires only on such a remap (NOT per event on dense data) and is
  pinned by the structural no-rescan test.

The merge fallback `_refresh_fractions()` is invoked ZERO times on the engine path after evictions
begin (pinned). The standalone `FeatureEngine` API still uses it (no in-effect quotes threaded).

## Files Changed

- `apps/backend/app/engine/features.py` — replaced the permanent post-eviction merge fallback in
  `_Window` with incremental `_RefreshSide`-based maintenance byte-identical to `_refresh_fractions`;
  added the new `_RefreshSide` class and the fold cursor/eviction/remap helpers; retained
  `_refresh_fractions` for the standalone API + as oracle.
- `apps/backend/app/config.py` — added `dense_replay_time_budget_seconds` (documented research/CI
  default) and added it to the `config_fingerprint` exclusion set (+ docstring).
- `apps/backend/tests/fixtures/alpaca/PG_20260609_170000_171000_sip.json` — NEW committed ≈10-min
  real SIP dense fixture (provenance in the file + `test_dense_replay_gate.py` docstring).
- `apps/backend/tests/test_dense_replay_gate.py` — NEW: fixture sanity (real SIP, dense, no creds,
  size budget); structural no-rescan (zero post-eviction merge calls + evictions-actually-occurred
  guard + every-window-evicts guard); byte-identity-at-every-compute over the real fixture (covers
  thousands of post-eviction ticks); CI timing gate; pinned final-value anchors; determinism; the
  fingerprint stability + counter pair.
- `apps/backend/tests/test_refresh_increment.py` — NEW: the `_RefreshSide` randomised differential
  test (millions of append/evict ops vs a brute oracle); a real-`_Window` equivalence test over
  production-faithful random streams with heavy eviction; oracle equivalence over a seeded SIM
  scenario through the real engine; the full error-case matrix; the standalone-API-uses-oracle pin.
- `runs/goal-session-i_will_be_super_rich_with_my_loved_ones/state/blueprint.md` — the additive
  iter-17 build-out note (registering the fixture + budget key as test/CI assets) is present (added
  during planning); no skeleton change, no reapproval needed.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/`
Result: **629 passed, 1 skipped** in ~305 s (full suite green; exit code 0). The 1 skip is the
pre-existing `test_live_integration.py` (gated on `TAPEOLOGY_LIVE_INTEGRATION=1` + open market +
credentials — always skipped in CI; unrelated to this iteration). All new tests run and pass.

Targeted confirmations:
- `test_dense_replay_gate.py` — 11 passed (incl. CI timing gate within budget; no-rescan; anchors).
- `test_refresh_increment.py` — 10 passed (incl. the millions-of-ops differential test + error cases).
- `test_features.py`, `test_observer_equivalence.py` (7/7), `test_real_data_classify.py` (5 pinned),
  `test_real_data_gate.py` (35), `test_scenario.py`, `test_progressive_fetch.py`
  (progressive-vs-single-shot determinism) — all pass unchanged (byte-identity preserved).

### Live engine sanity (post-dev server)
Started the backend via `scripts/start-backend.sh` (port :8650), `GET /health` → `{"status":"ok"}`.
`POST /watch/SIM-BUYER` then `GET /tape/SIM-BUYER/state` resolved to **`buyer_control` at
confidence ~0.8615** (the expected J-02/J-68 read) — the cockpit's classification is unchanged
end-to-end through the live API after the engine change. Server stopped afterward (`pkill -f
uvicorn`), no orphaned processes.

### Real external integration (live SIP fetch)
The fixture was fetched **live** with real Alpaca credentials via
`scripts/capture_alpaca_fixture.py --symbol PG --start 2026-06-09T17:00:00Z --end
2026-06-09T17:10:00Z --feed sip` (adapter reported `available: True`, `historical_feed: sip`). The
committed file is real captured SIP data; CI replays it without credentials.

### Performance evidence
On the dev machine, the unpaced full-`TapeEngine` replay of the committed fixture:
- OLD (permanently-degraded post-eviction merge): **~184 s**.
- NEW (incremental maintenance): **~10 s** (≈18× faster), final read identical (`unclear`, conf 0.20).
The CI budget is `dense_replay_time_budget_seconds = 60.0` (≈6× the measured incremental time —
generous headroom against CI-box variance, far below the minutes the O(n²) path costs).

## Diff Scope (reviewer-verifiable)

Code/test/fixture changes are confined to: `app/engine/features.py`, `app/config.py`, the new PG
SIP fixture, and the two new test files. **NO** `app/research/store.py` / schema (stays v7), **NO**
`classifier.py` / thresholds / window lengths, **NO** sim scenarios, providers, history buffer,
observer seam, or snapshot shape, and **NO** frontend file is touched.

## Known Issues

- **The quote-remap rebuild is the one window re-walk on the engine path.** It is bounded by remap
  events (NOT per event on dense data — pinned structurally), and on the committed real fixture it
  fires a few hundred times across a ~3,200-trade window, contributing most of the residual ~10 s.
  This is well inside the byte-identity + CI-budget requirements; it is not a per-event full rescan
  and does not reintroduce the quadratic defect. A fully rebuild-free remap path was considered but
  rejected for this iteration: byte-identity is mandatory and the bounded rebuild is provably exact,
  whereas an incremental remap of an arbitrary front prefix is materially more error-prone. The
  structural test (`_refresh_oracle_calls == 0` post-eviction) + the byte-identity tests pin the
  invariant that matters.
- **No user-facing change by design.** The browser scope is the J-68 no-thesis SIM-BUYER regression
  sentinel + a J-08 REST==UI spot check (run by browser QA against a post-dev server); nothing
  visible changes. This is the intended negative assertion, not a stall.
- **`test_dense_replay_gate.py` runtime ~46 s** (it does several full unpaced replays + the
  per-compute oracle comparison). Acceptable for CI; the per-compute equivalence check samples the
  long windows every 50th event (with the primary window checked every event) to keep the oracle
  re-walk bounded while still provably covering thousands of post-eviction ticks.
