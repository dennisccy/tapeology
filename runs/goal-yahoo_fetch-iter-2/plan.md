# goal-yahoo_fetch-iter-2 Execution Plan

Era 5 "The Library", iteration 2 — **J-02 only**: expand the keyless Yahoo adapter's
`_INTERVAL_MAP` to the full era-5 timeframe set, add the deterministic `4h`-from-`1h` resample
(the era's single named new backend computation, confined to `adapters/yahoo.py`), and make the
honest-error taxonomy explicit and distinct (unsupported-timeframe vs. out-of-retention vs.
network-timeout). No new UI (J-05 owns the `/structure` fetch control). Depth: full, per the
iteration-1 evaluator's explicit recommendation and because the `4h` resampler is a genuinely new
computation carrying its own critical anti-goal. **No drift found**: this is exactly Key
Capability 2 / Must-have journey J-02 from `docs/goal.md`, next in the natural
J-01 → J-02 → J-03 → J-04 → J-05 chain; every OUT OF SCOPE boundary in the phase spec (SQLite
index = J-03, levels/zones = J-04, UI fetch control = J-05, no 15m/8h/1mo as fetchable, no
`config.py`/`levels.py`/`backtests.py`/`strategies.py`/engine/`BarStore`/Alpaca changes) is
honored below.

## What to Build

- **Expand `_INTERVAL_MAP`** (`apps/backend/app/providers/adapters/yahoo.py`) to the **five
  directly-fetched** era-5 timeframes: `1d`→`"1d"` (byte-identical to J-01, unchanged), plus
  `1w`→`"1wk"` (yfinance's weekly spelling per the spec), `1h`→`"1h"`, `5m`→`"5m"`, `1m`→`"1m"`.
  Confirm each exact interval string against the live vendor under `pytest.mark.integration`
  before trusting it — do not assume from documentation alone.
- **Implement the deterministic `4h` resample-from-`1h`**, confined entirely inside
  `yahoo.py` (the anti-goal-mandated single home — do not add a second resample path in
  `bars.py`, `levels.py`, or a route). `4h` is NOT a `_INTERVAL_MAP` entry (yfinance has no native
  4-hour interval) — `fetch_bars` special-cases `timeframe == "4h"`: fetch real `1h` bars for the
  requested window, then aggregate into aligned 4-hour buckets: open=first, high=max, low=min,
  close=last, volume=sum. Buckets align to the session/regular-hours boundary (not naive
  wall-clock `% 4h`). The trailing partial bucket is emitted from only the `1h` bars actually
  completed within it — never padded, forward-filled, or filled from a not-yet-complete bar (the
  no-lookahead rail). Pure function of the fetched `1h` bars — no wall-clock read, no unseeded
  state — so two identical requests produce byte-identical `4h` output.
- **Make the honest-error taxonomy explicit and distinct** on `POST /research/bars` → the Yahoo
  path. Today `YahooAdapter.fetch_bars()` collapses two different situations into one empty tuple
  → the caller's generic `EmptyBarWindowError` (422 "no bars in the requested window"). J-02 must
  split this into three **observably distinct** states:
  1. **Unsupported timeframe** — `8h` / `1mo` / `15m` (all already in `CONFIG.bar_timeframes`,
     so the route's existing pre-check does NOT reject them — they reach the adapter). These are
     statically knowable with no vendor call. Recommended: `fetch_bars` checks this up front
     (timeframe not in `_INTERVAL_MAP` and not `"4h"`) and raises a neutral, explicit signal
     naming the timeframe as not served by Yahoo, confined to `yahoo.py`.
  2. **Out-of-retention / empty window** — the timeframe IS mapped/servable, but this specific
     symbol/window legitimately returns nothing from the vendor. **Recommended**: reuse the
     existing neutral `NoDataForWindow` exception (`apps/backend/app/providers/adapters/base.py`
     — already defined, already used for exactly this semantic by the analogous historical-record
     path in `research/routes.py` around line 1494, `except NoDataForWindow: raise
     HTTPException(422, "no data for that window")`) rather than inventing a new class — matches
     `docs/goal.md`'s own naming ("`NoDataForWindow` / unsupported-timeframe") and existing
     precedent.
  3. **Network failure** — already wired: `VendorTimeout` → 504. No change needed.
  The **exact exception class for case 1 is a developer decision** (the spec leaves it open) —
  either a new neutral class beside `SymbolNotTradable`/`NoDataForWindow`/`VendorTimeout` in
  `base.py`, or a distinctly-worded reuse of an existing one. The one hard requirement: cases 1
  and 2 must be observably distinct from each other (different `detail` text and/or status), and
  neither may write or fabricate a bar. `record_bar_series` (`research/routes.py`, ~line
  1590-1631) gains new `except` clause(s) mapping whichever exception(s) the adapter now raises to
  distinct HTTP responses — mirroring the existing `record_dataset` pattern. This is HTTP-mapping
  glue only; the timeframe-classification logic itself must stay confined to `yahoo.py`, never
  duplicated in `routes.py` (the coherence-auditor hard-fails a second owner).
- **Dependency discipline**: verify (do not re-add) that `yfinance` is still the only new runtime
  dependency — the J-01 pin in `requirements.txt` and allowlist entry in
  `config/install-security-policy.json` should already be sufficient; J-02 adds no new package.
- **Tests** (see Files below): interval-mapping across all six timeframes, `4h` resampler
  correctness + determinism + honest partial bucket over a committed `1h` fixture, error-taxonomy
  observable-distinctness, and a live `integration`-marked six-timeframe + "`4h` matches
  resampled-live-`1h`" + out-of-retention/unsupported check. Per `.claude/core.md` External
  Integration Testing: the mocked suite alone is not sufficient evidence — **actually run** the
  live integration test during implementation (`TAPEOLOGY_LIVE_INTEGRATION=1`) and record the
  pass/fail result explicitly in the dev handoff, the same way iter-1 did.
- Dev handoff at `docs/handoffs/goal-yahoo_fetch-iter-2-dev.md`.

**Explicitly out of scope this iteration** (do not build ahead): the SQLite index / store-first
coordinator / `?symbol=&timeframe=` filter (J-03); real levels/zones computation on the new bars
(J-04 — `research/levels.py` needs zero changes, it already computes on whatever bars exist); the
`/structure` fetch control, "Yahoo Finance" provenance badge, and `taxonomy.FEED_BASIS_LABELS`
(J-05 — **zero frontend file changes**); making `15m`/`8h`/`1mo` actually fetchable (they stay
config-valid-but-Yahoo-unsupported by product policy this era — note `15m`/`1mo` are technically
valid yfinance intervals but not in era-5's enumerated six, so they still exercise the
unsupported-timeframe path); any change to `config.py`, `research/levels.py`,
`research/backtests.py`, `research/strategies.py`, the engine, `research/bars.py`'s `BarStore`
internals, or `providers/adapters/alpaca.py` — all stay byte-identical; `config_fingerprint` stays
`4d665603569b9dbf`.

## Agents Required

- developer: yes — backend-only (new adapter logic + route error-mapping glue + tests + a
  committed `1h` fixture). Maps to the generic "backend-data: yes, frontend-ux: no" ask — this
  pipeline has one unified `developer` agent, not separately named backend/frontend agents; there
  is zero frontend/UI work this iteration.

## Frontend Present

Frontend Present: yes — set deliberately despite **zero new frontend files** this iteration (the
phase spec's own Goal Mode Metadata literally states "Frontend Present: no" and "Frontend (if
applicable): None — J-02 is a backend + provider-integration journey"). This plan sets `yes`
anyway for one mechanical, verified reason: `qa-phase.sh` / `ui-impact-phase.sh` /
`browser-qa-phase.sh` / `ux-regression-phase.sh` all gate their Chrome MCP browser lane on this
exact `plan.md` line via `detect_frontend_in_plan` (`scripts/automation/lib/common.sh:1070`) — I
read that function directly rather than assuming. The phase spec's own DEFINITION OF DONE and
NOTES require the browser-qa lane to **actually run and emit screenshot evidence** re-verifying
**J-01** (Structure page still renders real Yahoo candles) and **J-06** (foundation regression
sentinel — Cockpit/Journal/Studies/Performance/Structure unchanged, feed badge still
"Simulated") this iteration: *"This is a full-depth iteration, so the 11-step pipeline runs
browser-qa — ensure it emits evidence for the J-01/J-06 regression checks."* Setting `no` would
cause `qa-phase.sh` to print "No frontend in this phase -- skip browser checks entirely" and skip
that required regression evidence.

This is not a new judgment call — it is the **exact working pattern iter-1 already used**, and
iter-1's phase-closure-auditor explicitly pre-approved repeating it for J-02:
*"J-02/J-03 ... are also backend-heavy per `docs/goal.md`'s journey sequencing. If a future
iteration in this session repeats the `Frontend Present: yes` + zero-frontend-diff pattern for the
same 'force the regression lane' reason, that is consistent with this session's established,
working pattern — not a new anomaly to second-guess"* (`reports/phase-goal-yahoo_fetch-iter-1-closure-verdict.md`).
Downstream agents: do **not** read this flag as license to build UI — zero frontend files should
change; every UI Evolution bullet below is "none" by design, and the browser-qa pass this
iteration is regression-only (re-verifying J-01/J-06), not a new-feature click-test.

## Files to Create/Modify

- `apps/backend/app/providers/adapters/yahoo.py` -- MODIFY. Expand `_INTERVAL_MAP` to 5 entries;
  add the `4h` resample branch in `fetch_bars`; add the unsupported-timeframe vs.
  out-of-retention error distinction (confined here per the anti-goal).
- `apps/backend/app/providers/adapters/base.py` -- POSSIBLE MODIFY (developer's call). Only
  needed if the unsupported-timeframe case gets a brand-new neutral exception class alongside the
  existing `SymbolNotTradable` / `NoDataForWindow` / `VendorTimeout` trio; may stay untouched if
  the developer instead reuses/distinguishes via existing types + distinct messages.
- `apps/backend/app/research/routes.py` -- MODIFY. `record_bar_series` (~line 1590-1631) gains
  `except` clause(s) mapping the adapter's new exception(s) to distinct HTTP responses, mirroring
  the existing `except NoDataForWindow: raise HTTPException(422, "no data for that window")`
  pattern already used by `record_dataset` (~line 1494). No new computation — mapping glue only.
- `apps/backend/requirements.txt`, `config/install-security-policy.json` -- VERIFY ONLY; no new
  entries expected (yfinance already pinned + allowlisted from J-01).
- `apps/backend/tests/test_yahoo_adapter.py` -- MODIFY (extend). Add 6-timeframe interval-mapping
  coverage; add `4h` resampler tests (OHLC aggregation exact, session-boundary bucket alignment,
  honest partial trailing bucket, byte-identical across two identical calls) driven by a new
  committed `1h` fixture; add error-taxonomy tests (unsupported vs. out-of-retention observably
  distinct; zero vendor call for a statically-unsupported timeframe, mirroring this file's
  existing `assert calls == []` style). Two existing tests have a J-01-scope-boundary premise that
  J-02 legitimately outgrows — **update, don't just leave stale**:
  `test_interval_map_covers_only_the_daily_timeframe_this_iteration` (asserts
  `_INTERVAL_MAP == {"1d": "1d"}`, now wrong) and
  `test_fetch_bars_returns_empty_tuple_for_an_unmapped_timeframe_this_iteration` (uses `"1h"` as
  its unmapped example, which becomes mapped this iteration — repurpose it to use `15m`/`8h`/`1mo`
  or fold it into the new unsupported-timeframe test). This is intended evolution of a
  scope-boundary test, not the forbidden "weakening a frozen test" — J-01's actual behavioral
  guarantee ("`1d` output is byte-identical to J-01") is preserved, only the boundary marker moves.
- `apps/backend/tests/fixtures/yahoo/` -- NEW fixture file(s), e.g. a committed real `1h` capture
  (same shape as the existing `AAPL_1d_20260601_20260604.json`) to drive the `4h` resampler test
  deterministically. **MUST live under `tests/fixtures/yahoo/`, never `tests/fixtures/bars/`**
  (iter-1 lesson: the frozen `test_bars.py::test_committed_fixture_loads_through_the_real_store_path_keyless`
  runs `BarStore(FIXTURE_BAR_DIR).list()` over that whole directory and blanket-asserts
  `meta["feed"] == "sip"`).
- `apps/backend/tests/test_bars_api.py` -- MODIFY (extend only; the 12 pre-existing + 3 J-01
  assertions must keep passing unmodified). Add route-level tests: unsupported-timeframe request →
  its distinct status/detail; out-of-retention request → distinct "no data for that window";
  proven observably different from each other.
- `apps/backend/tests/test_yahoo_live_integration.py` -- MODIFY (extend; stays
  `pytest.mark.integration`, gated on `TAPEOLOGY_LIVE_INTEGRATION=1`). Add: a real fetch of each
  of the six timeframes within real retention; confirm live `4h` equals the deterministic resample
  of live `1h`; confirm a real out-of-retention `1m` window (e.g. ~2 years back) and a real
  unsupported `8h` request each surface the explicit neutral error. Run it live this session.
- `docs/handoffs/goal-yahoo_fetch-iter-2-dev.md` -- NEW. Standard dev handoff.
- **Not modified** (frozen; confirm byte-identical in the diff): `apps/backend/app/config.py`
  (`config_fingerprint` stays `4d665603569b9dbf`), `research/levels.py`, `research/backtests.py`,
  `research/strategies.py`, `research/bars.py` (the `BarStore` class itself), `providers/adapters/alpaca.py`,
  `providers/adapters/__init__.py`, `main.py`, and **all** of `apps/frontend/**` (verify via
  `git diff --stat -- apps/frontend/` — expect empty).

## UI Evolution

- New user-facing capability: none on-screen. Via `POST /research/bars` (REST) and the MCP `bars`
  proxy, an operator/agent can now fetch real Yahoo bars at all six era-5 timeframes (incl.
  derived `4h`) and gets an explicit, distinct honest error where Yahoo cannot serve — but there is
  still no on-screen control; the `/structure` "Fetch from Yahoo Finance" button is J-05.
- New information displayed: none on-screen. `GET /research/bars*` and the MCP `bars` proxy gain
  the ability to return `1w`/`1h`/`5m`/`1m`/`4h` series (previously daily-only), and new error
  responses carry distinct `detail` text — but nothing new renders in the UI this iteration.
- New user actions: none.
- UI surface changes: none — existing surfaces (`/`, `/journal`, `/journal/[id]`, `/studies`,
  `/performance`, `/structure`) must render exactly as before; the Structure page's fetch control
  does not exist yet.
- Navigation changes: none.

## Visual Requirements

N/A — no new UI this iteration (mirrors iter-1's plan for the same reason). The browser-qa lane's
only job this iteration is confirming the existing dark-mode Next.js/Tailwind pages still render
without regression after the backend interval/error-taxonomy change — see the browser-regression
bullet under Key Test Scenarios.

## Key Test Scenarios

- Interval mapping: all six era-5 timeframes resolve on a fetch (five direct via `_INTERVAL_MAP` +
  `4h` via the resample branch); `1d` output stays byte-identical to J-01; `8h`/`1mo`/`15m` do
  **not** resolve to a fetchable interval.
- `4h` resample correctness: OHLC aggregation exact (open=first/high=max/low=min/close=last/volume=sum)
  against a committed `1h` fixture, asserted candle-for-candle; buckets aligned to the
  session/regular-hours boundary (not naive wall-clock modulo); the partial trailing bucket is
  built from only the `1h` bars actually completed within it (no padding, no forward-fill, no
  future bar); two identical `4h` requests produce byte-identical output.
- Error taxonomy: unsupported-timeframe vs. out-of-retention/empty-window are observably distinct
  (different `detail`/status); network failure still surfaces the existing `VendorTimeout` → 504;
  none of the three writes or fabricates a bar (`BarStore.record` never called, or called with
  zero effect, on any of them).
- Live integration (gated, `TAPEOLOGY_LIVE_INTEGRATION=1`, actually run this session): fetch each
  of the six timeframes within its real retention window; live `4h` equals the deterministic
  resample of live `1h`; a real out-of-retention `1m` window and a real unsupported `8h` request
  each return the explicit neutral error, live.
- Regression: full backend suite green (no test deleted/weakened); the two equivalence suites
  22/22; `config_fingerprint` still `4d665603569b9dbf`; zero diff in `config.py`, `main.py`,
  `alpaca.py`, `research/levels.py`, `research/backtests.py`, `research/strategies.py`, and
  `research/bars.py`'s `BarStore` class; `yfinance` remains the **only** new runtime dependency —
  no new package added or re-pinned.
- Browser regression (must actually run and emit `ui-test-results.md` + screenshots — this is a
  **re-verification pass, not a new-feature test**): J-01 — a real `POST /research/bars` Yahoo
  fetch still renders real candles on `/structure` with `feed="yahoo"`; J-06 — Cockpit's feed badge
  still reads "Simulated" (never "yahoo"), and `/`, `/journal`, `/studies`, `/performance`,
  `/structure` all render unbroken with zero unintended "yahoo" text leakage outside the bar path.
- Coherence: the `4h` computation has exactly one owner (`adapters/yahoo.py`) — grep confirms no
  second resample path in `bars.py`, `levels.py`, or any route; no second `feed` source introduced.
- Dev handoff written at `docs/handoffs/goal-yahoo_fetch-iter-2-dev.md`, explicitly stating the
  live-integration pass/fail result (per `.claude/core.md` External Integration Testing).
