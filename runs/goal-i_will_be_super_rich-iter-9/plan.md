# goal-i_will_be_super_rich-iter-9 Execution Plan

Watch-lifecycle feedback hardening: every Watch click acknowledges itself within ~1s and every
outcome resolves to a distinct, visible, bounded state — never a silent no-op, infinite spinner,
or swallowed failure. Targets J-21–J-24; must not regress J-01–J-20. No engine/classifier change.

## What to Build
- **Pending/connecting state (J-21):** In `app/page.tsx#handleWatch`, set an explicit pending state
  for the entered symbol *synchronously, before* the `await teardownActiveWatch()` / `await watchTicker()`
  round-trip, so the cockpit leaves the idle screen immediately and shows "Connecting to <SYMBOL>…"
  with the connecting dot, in all three modes. Replace it on resolve (cockpit / honest panel / error).
  Reuse the existing `CONN_DOT.connecting` affordance — do NOT fork a second status concept.
- **Backend per-call vendor timeout (J-22 half 1):** Add config constant `vendor_call_timeout_seconds`
  (a `*_seconds` float, no-magic-numbers comment) to `app/config.py`. In `app/main.py`, wrap the
  Watch-gating outbound vendor `asyncio.to_thread(...)` calls under `asyncio.wait_for(..., timeout=
  CONFIG.vendor_call_timeout_seconds)` — at minimum `adapter.fetch_historical` in `_watch_historical`
  and `adapter.get_market_clock` in the `_watch_live` market-closed pre-flight. On `asyncio.TimeoutError`,
  raise an explicit distinct error (HTTPException/RealDataError with a stable `reason: provider_timeout`),
  create NO engine and fabricate NO tape (assert the watch is not registered after a timeout).
- **Frontend client-side request-timeout backstop (J-22 half 2):** Add ONE frontend config constant
  `WATCH_REQUEST_TIMEOUT_MS` to `lib/config.ts` (no inline literal). Give `watchTicker` and
  `fetchInitialSnapshot` in `lib/api.ts` an `AbortController` with that timeout; on abort, resolve to a
  distinct error result ("Market data provider timed out" / "Request timed out") so the connecting state
  is replaced by a visible error, never a hang.
- **Surface failed initial connection / stream (J-23):** In `lib/useTapeStream.ts`, replace the
  `.catch(() => {})` swallow of the initial-snapshot fetch with a path that records an explicit
  connect-failure status; treat a WS `onerror` / early `onclose` (before any snapshot) as a surfaced
  "couldn't connect to the tape stream" condition. `app/page.tsx` renders it via the existing error
  banner / failure panel within a bounded time. No empty `catch`, no dropped promise rejection in the
  Watch path.
- **Inline validation for empty/invalid input (J-24):** In `components/TopBar.tsx` / `app/page.tsx`,
  show an immediate inline message ("Enter a ticker symbol"; Historical: "Choose a valid time window")
  and/or disable Watch until input is valid, so an empty/whitespace symbol or missing/invalid window is
  never a silent no-op. The backend 422 remains the server-side backstop.

## Agents Required
- backend-data: yes -- add `vendor_call_timeout_seconds` config + `asyncio.wait_for` bounds on the two
  Watch-gating vendor calls with an explicit `provider_timeout` error; new backend unit test (mocked
  slow adapter → timeout, no engine created).
- frontend-ux: yes -- pending/connecting state, client-side `AbortController` timeout from one config
  constant, non-swallowed stream failure, inline input validation; new frontend tests.
- developer: yes -- implements both backend + frontend changes with TDD.

Frontend Present: yes

## Test Strategy
- **Backend unit/integration:** a mocked slow `fetch_historical` / `get_market_clock` proves the
  `asyncio.wait_for(..., vendor_call_timeout_seconds)` bound fires, yields an explicit error, and leaves
  NO engine registered for the ticker. Assert the timeout value is read from config (no inline literal).
  Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`.
- **Frontend unit:** `watchTicker` / `fetchInitialSnapshot` abort on the client-side timeout and return a
  distinct error result; `useTapeStream` surfaces (does not swallow) an initial-snapshot failure and a
  pre-snapshot WS error. Assert the timeout comes from the single `lib/config.ts` constant.
- **Browser (Chrome MCP, isolated build):** J-21 — "Connecting to <SYMBOL>…" within ~1s in sim/live/
  historical, idle never persists after a valid click; J-22 — slow/unreachable backend resolves to an
  explicit bounded error, not an infinite spinner; J-23 — backend stopped right after Watch →
  "couldn't connect to the tape stream" within a bounded time; J-24 — empty/whitespace symbol → inline
  "Enter a ticker symbol" / disabled Watch, Historical missing/invalid window → inline "Choose a valid
  time window". Re-verify J-01 (sim cockpit populates), J-09 (stop→idle), J-10 (3-mode switch),
  J-14 (honest market-closed/unavailable panels unchanged). **Pixels are the evidence** — capture real
  rendered screenshots of the pending, bounded-error, and inline-validation states; an idle/placeholder
  screenshot is NOT evidence.

## Key Test Scenarios
- A valid Watch click leaves the idle screen and shows "Connecting to <SYMBOL>…" within ~1s in every mode.
- A hung/unreachable backend resolves to a visible bounded error (both backend timeout unit test AND
  frontend non-resolving-request test pass — neither half substitutes for the other).
- Backend stopped just after Watch surfaces an explicit stream-connect error; no swallowed failure.
- Empty/whitespace symbol and missing/invalid historical window give immediate inline feedback (no no-op).
- J-01–J-20 remain green; no fabricated data on any failure path; no engine value recomputed in UI/API.

## UI Evolution
- New user-facing capability: every Watch click yields immediate honest feedback — a pending
  acknowledgement, then exactly one of {live cockpit, honest non-cockpit panel, explicit error,
  inline validation} — never a frozen or silent UI.
- New information displayed: a transient "Connecting to <SYMBOL>…" cockpit state with the connecting dot;
  bounded timeout / connect-failure error text ("…timed out" / "couldn't connect to the tape stream" /
  "Backend unreachable"); inline input-validation messages.
- New user actions: no new controls — the existing **Watch** button gains a pending state on click and is
  disabled/validated on invalid input. No execution/order affordance.
- UI surface changes: all on `/` — transient pending/connecting cockpit treatment, the reused error
  banner for timeout/stream-failure, inline validation text beside the Watch controls in `TopBar`.
- Navigation changes: none. No new route, page, or nav-skeleton change (blueprint additive only — rows 6
  and 9 already updated by the decomposer).

## Visual Requirements
- Component patterns: reuse existing hand-built panels — `Cockpit` connecting treatment, the `TopBar`
  error banner, `ProviderUnavailable` for the honest panel, and `CONN_DOT.connecting` for the status dot.
  Do not introduce a new component or endpoint for the new states.
- Layout: unchanged single-column / panel-grid tape cockpit on `/`; pending and error states occupy the
  same cockpit/banner real estate as the existing idle/error treatments.
- Key visual effects: restrained per DESIGN SYSTEM — connecting status dot, calm dark surface,
  amber/neutral for pending, the existing error styling for failures. Monospaced numerics unchanged.
- States to handle: pending/connecting (new, first-class), bounded timeout/connect-failure error,
  inline validation, plus the existing loading/empty/idle states — no regression to J-14 honest panels.

## Files to Create/Modify
- `apps/backend/app/config.py` -- add `vendor_call_timeout_seconds` (`*_seconds` float + no-magic comment).
- `apps/backend/app/main.py` -- wrap `fetch_historical` (`_watch_historical`) and `get_market_clock`
  (`_watch_live` pre-flight) in `asyncio.wait_for`; raise explicit `provider_timeout` error on timeout.
- `apps/backend/tests/` -- new test: mocked slow adapter → bounded timeout error, no engine registered;
  assert config-sourced timeout.
- `apps/frontend/lib/config.ts` -- add `WATCH_REQUEST_TIMEOUT_MS` constant.
- `apps/frontend/lib/api.ts` -- `AbortController` timeout on `watchTicker` + `fetchInitialSnapshot`,
  distinct error result on abort.
- `apps/frontend/lib/useTapeStream.ts` -- stop swallowing the initial-snapshot failure; surface
  pre-snapshot WS `onerror`/`onclose` as a connect-failure status.
- `apps/frontend/app/page.tsx` -- synchronous pending state before the watch round-trip; render
  stream/connect-failure and timeout errors; inline-validation gating.
- `apps/frontend/components/TopBar.tsx` -- inline validation message / disabled Watch for empty symbol
  and missing/invalid historical window.
- `apps/frontend/lib/` tests -- client-side timeout abort + non-swallowed stream failure.
- `docs/handoffs/goal-i_will_be_super_rich-iter-9-dev.md` -- dev handoff.

## Risks / Watch-outs
- **Shared `.next` corruption (load-bearing, iter-3/6/7/8 lesson):** the browser run MUST build into an
  **isolated** `NEXT_DIST_DIR` wired to an isolated backend (`NEXT_PUBLIC_API_URL`) and drive real
  Chromium — never `npm run build` against the shared `.next` on `:3650`, never `git checkout` a file
  carrying uncommitted iter edits.
- **J-22 has two required halves** — backend per-call timeout (mocked-slow-adapter unit test) AND the
  frontend client-side timeout (non-resolving request). Build and verify both; do not let one stand in.
- **Don't conflate timeouts:** `vendor_call_timeout_seconds` (new, per outbound call) is distinct from
  `stale_gap_seconds` (existing mid-stream delivery-gap watchdog, J-15) — do not reuse or merge them.
- **No fork of status concepts:** reuse `CONN_DOT.connecting`, the `TopBar` error banner, and
  `ProviderUnavailable`; add `provider_timeout` as a sibling row-9 reason on the one `POST /watch`
  failure path — not a new component or endpoint (keeps the single-producer / coherence rule satisfied).
- **Single-source-of-truth guard:** the pending/error/validation states are pure UI presentation — they
  MUST NOT introduce any client-side recomputation of an engine value (state/confidence/features/spread);
  the cockpit still reads the engine snapshot verbatim once data arrives.
- **No swallowed errors anywhere in the Watch path:** no empty `catch`, no unawaited promise dropping a
  rejection, no unbounded external wait — a reproducible silent no-op / infinite spinner / swallowed
  Watch error is a critical-anti-goal veto on GOAL_ACHIEVED.

## Scope check
Plan aligns with the project goal (success criterion "Every Watch action gives immediate, honest
feedback", goal.md lines 85–90) and the critical "No silent dead-clicks" / "No unbounded waits"
anti-goals. No scope creep: no engine/classifier/feature-math change, no new route/page/chart/execution
affordance, operator-gated live-vendor legs remain gated. The `stale` watchdog and pause/resume are
explicitly out of scope.
