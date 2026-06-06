# Goal Iteration 9 — No silent dead-clicks: every Watch gives immediate, bounded, honest feedback

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich
- **Iteration:** 9
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-21, J-22, J-23, J-24
- **Required-still-passing journeys:** J-01, J-09, J-10, J-11, J-14, J-17, J-19, J-20 (and by extension all of J-01–J-20 — the Watch-flow change must not regress any existing journey)
- **Anti-goal reminders:**
  - **No silent dead-clicks.** Pressing Watch MUST always produce a visible UI change within ~1 second — a pending/"connecting" state, streaming data, an empty-state, an explicit error, or an inline validation message. The UI MUST NOT silently remain on the idle/previous screen, MUST NOT leave "Connecting…" running with no resolution, and MUST NOT swallow a failure (no empty `catch`, no unawaited promise that drops an error, no unbounded external wait). A reproducible silent no-op, an infinite connecting spinner, or a swallowed Watch error is a veto on GOAL_ACHIEVED. *(critical)*
  - **No unbounded waits.** Every outbound vendor call — market-clock check, historical fetch, and live-stream connect — runs under an explicit timeout from config (no magic numbers); no external call may block a Watch request indefinitely. The frontend also enforces a client-side request timeout as a backstop, so a slow or hung backend always resolves to a visible error rather than a frozen UI.
  - **No fabricated data.** The system MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. Every real-data failure mode MUST surface an explicit, distinct state and never a cockpit. *(critical)*
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. *(critical)*
  - **No magic numbers.** Every timeout/threshold MUST come from config — no such literal in engine/classifier code (and, here, no literal millisecond timeout buried in a fetch helper — it comes from one config constant).

## GOAL

Every Watch click — in Simulated, Live, or Historical mode — acknowledges itself within ~1 second with an explicit pending/"connecting" state, and every outcome (streaming data, empty window, provider unavailable, unknown symbol, market closed, request timeout, unreachable backend, failed initial stream, or invalid input) resolves to a distinct, visible on-screen state within a bounded time — never a silent no-op and never an infinite spinner.

## BACKGROUND

The session reached GOAL_ACHIEVED at iter-8 with J-01–J-20 all passing; a new spec commit then added four Must-have journeys (J-21–J-24) and the critical **"No silent dead-clicks"** anti-goal, so the goal is no longer closed. Code inspection of the current Watch flow confirms four concrete gaps against the new bar: (1) `app/page.tsx#handleWatch` sets `ticker` only *after* `await teardownActiveWatch()` + `await watchTicker()` resolve, so there is no pending "Connecting to <SYMBOL>…" screen between click and result (J-21); (2) `lib/api.ts#watchTicker`/`fetchInitialSnapshot` use `fetch` with **no client-side `AbortController` timeout**, and the backend's `_watch_historical`/`get_market_clock` vendor calls run via `asyncio.to_thread(...)` with **no `asyncio.wait_for` bound** — a hung vendor or backend blocks indefinitely (J-22, and the goal's "No unbounded waits" constraint); (3) `lib/useTapeStream.ts` **swallows** the initial-snapshot fetch failure with `.catch(() => {})` and reduces a WS error to `connStatus="closed"` with no surfaced banner — a failed initial connection is silent (J-23); (4) an empty/whitespace symbol makes `handleWatch` silently `return`, and the Watch button is never disabled, so an empty-input click is a no-op (J-24). This is a Watch-lifecycle hardening pass that crosses the frontend boundary and adds one backend timeout wrapper + new unit tests, and it backs a *critical* anti-goal — hence **full** depth, not lean. No new canonical engine value is introduced; the cockpit's data still comes once from the engine.

## IN SCOPE

### Backend
- [ ] Add a single config constant `vendor_call_timeout_seconds` to `app/config.py` (a `*_seconds` float with a no-magic-numbers comment, consistent with `stale_gap_seconds`/`pause_poll_seconds`). This is the bound for a single outbound vendor request, distinct from `stale_gap_seconds` (a mid-stream delivery-gap watchdog).
- [ ] In `app/main.py`, wrap the outbound vendor `asyncio.to_thread(...)` calls that gate a Watch request under `asyncio.wait_for(..., timeout=CONFIG.vendor_call_timeout_seconds)`: at minimum `adapter.fetch_historical` in `_watch_historical` and `adapter.get_market_clock` in the live-watch market-closed pre-flight (`_watch_live`). On `asyncio.TimeoutError`, raise an explicit, distinct error (e.g. a `RealDataError`/`HTTPException` with a clear `detail` and a stable `reason` such as `provider_timeout`) — NO engine is created and NO tape is fabricated.
- [ ] Keep the live-socket teardown timeout in `adapters/alpaca.py` unchanged (already bounded; out of scope to touch).

### Frontend
- [ ] **Pending/connecting state (J-21):** In `app/page.tsx#handleWatch`, set an explicit pending state for the entered symbol *synchronously, before* the `await teardownActiveWatch()` / `await watchTicker()` round-trip, so the cockpit immediately leaves the idle screen and shows "Connecting to <SYMBOL>…" with the connecting status dot in every mode. Clear/replace it when the watch resolves (to the cockpit on success, or to the matching error/honest panel on failure). Reuse the existing connecting-dot affordance (`CONN_DOT.connecting`) rather than inventing a second status concept.
- [ ] **Client-side request timeout backstop (J-22):** In `lib/api.ts`, give `watchTicker` (and `fetchInitialSnapshot`) an `AbortController` whose timeout comes from ONE frontend config constant in `lib/config.ts` (e.g. `WATCH_REQUEST_TIMEOUT_MS`) — no inline literal. On abort/timeout, resolve to an explicit, distinct error result (e.g. "Market data provider timed out" / "Request timed out") so the connecting state is replaced by a visible error rather than hanging forever.
- [ ] **Surface failed initial connection / stream (J-23):** In `lib/useTapeStream.ts`, stop swallowing the initial-snapshot failure — replace `.catch(() => {})` with a path that records an explicit connect-failure status, and treat a WS `onerror`/early `onclose` (before any snapshot) as a surfaced "couldn't connect to the tape stream" condition. `app/page.tsx` must render that as the existing error banner / a failure panel within a bounded time. No empty `catch`, no dropped promise rejection anywhere in the Watch path.
- [ ] **Inline validation for empty/invalid input (J-24):** In `components/TopBar.tsx` / `app/page.tsx`, show an immediate inline message ("Enter a ticker symbol"; in Historical, "Choose a valid time window") and/or disable the Watch button until the input is valid, so an empty-symbol or missing-window click is never a silent no-op. The existing backend 422 remains the server-side backstop, but the client must give immediate feedback without a round-trip.

### New user-facing capability
The user always gets immediate, honest feedback from a Watch click: a pending acknowledgement, then exactly one of {live cockpit, honest non-cockpit panel, explicit error, inline validation} — never a frozen or silent UI.

### New information displayed
- A pending "Connecting to <SYMBOL>…" cockpit state (with the connecting dot) shown the instant Watch is clicked, before any tape data.
- A bounded, explicit timeout/connect-failure error message ("…timed out" / "couldn't connect to the tape stream" / "Backend unreachable").
- Inline input-validation messages for an empty symbol or a missing/invalid historical window.

### New user actions
No new controls. The existing **Watch** button gains immediate feedback (pending state on click, disabled/validated on invalid input). No execution/order affordance is added.

### UI surface changes
All on `/` (the single tape-cockpit screen): a transient pending/connecting cockpit treatment, the existing error banner reused for timeout/stream-failure, and inline validation text beside the Watch controls in `TopBar`.

### Product surface delta
The cockpit's Watch flow becomes trustworthy: no dead clicks, no infinite spinners, no swallowed failures. The product *feels* responsive and honest in the first second after every click, in all three modes.

### Blueprint conformance
No new surfaces and no nav-skeleton change. Everything lives on the existing **`/` — Watch (the tape cockpit) — HOME**, within the already-registered app shell and idle/connecting/error states. The blueprint's IΑ already lists the "Idle/empty state" and the connecting/stale/closed status dot; this iteration makes the pre-snapshot **connecting** affordance and the explicit error/validation states first-class. Additive blueprint edits only (see Data-contract additions); no `blueprint.reapproval-requested` written.

### Data-contract additions
- **No new engine/displayed canonical value.** The cockpit's tape state, confidence, features, quote, observations, and event log still come once from the engine (rows 1–6) — unchanged and not recomputed.
- The new **pending/connecting**, **timeout/connect-failure error**, and **inline-validation** states are transient UI presentation states, not engine-computed values. They are folded into the existing **row 6** *watch/stream status* (`connecting` is already a registered status) and **row 9** *real-data availability / failure state* (a new `provider_timeout` reason is an additive sibling of the existing `provider_unavailable`/`symbol_not_tradable`/`no_data_for_window`/`market_closed` reasons, served by the same `POST /watch` failure path — NOT a new endpoint or a second producer). The new backend `vendor_call_timeout_seconds` and the frontend `WATCH_REQUEST_TIMEOUT_MS` are config constants, not displayed values. Blueprint rows 6 and 9 are updated additively to note `provider_timeout` and the bounded-wait guarantee.

## OUT OF SCOPE

- Any change to the engine, classifier, feature math, or the five tape states (this is lifecycle/feedback hardening, not classification).
- The mid-stream `stale` watchdog (J-15) and pause/resume (J-19) — already built; `stale_gap_seconds` is a *delivery-gap* timeout and MUST NOT be conflated with the new per-call `vendor_call_timeout_seconds`.
- The live-socket teardown timeout in `adapters/alpaca.py` (already bounded).
- Any new route, page, watchlist, dashboard, chart change, or execution/order affordance.
- Re-verifying operator-gated legs against a live vendor (J-12 live socket, J-15 stale-recover, the against-live-vendor leg of J-11/J-16/J-18 remain gated as the goal designates).

## DEFINITION OF DONE

- [ ] Target journeys J-21, J-22, J-23, J-24 pass via browser-qa-agent (with a real rendered screenshot of the pending state, the bounded error state, and the inline-validation state — per the standing visual-evidence lesson, a placeholder/idle screenshot is NOT evidence).
- [ ] Required-still-passing journeys J-01–J-20 remain green (especially J-01 cockpit populate, J-09 stop→idle, J-10 mode switch, J-11 historical replay, J-14 honest failure panels, J-17/J-19/J-20 visual/control surfaces).
- [ ] No anti-goal violation introduced (no fabricated data on any failure path; single source of truth preserved — the connecting/error/validation states add no recomputation of an engine value).
- [ ] Unit/integration tests pass; no regressions. New tests cover: the backend per-call timeout (mocked slow adapter → explicit timeout error, no engine created) and the frontend client-side timeout + non-swallowed stream failure.
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich-iter-9-dev.md`.
- [ ] `blueprint.md` rows 6 and 9 updated additively (already done by the decomposer); no nav-skeleton change.

## TESTING REQUIREMENTS

- **Browser:** J-21 (pending "Connecting to <SYMBOL>…" within ~1s in each of sim/live/historical, idle screen never persists after a valid click), J-22 (a slow/hung or unreachable backend resolves to an explicit bounded error, not an infinite spinner), J-23 (backend stopped right after Watch → explicit "couldn't connect to the tape stream" error within a bounded time, no swallowed failure), J-24 (empty/whitespace symbol → inline "Enter a ticker symbol" or disabled Watch; Historical missing/invalid window → inline "Choose a valid time window"). Also re-verify J-01 (sim cockpit still populates), J-09 (stop→idle), J-10 (3-mode switch), J-14 (honest market-closed/unavailable panels unchanged).
- **Unit/integration:**
  - Backend: a mocked slow `fetch_historical`/`get_market_clock` adapter proves the `asyncio.wait_for(..., vendor_call_timeout_seconds)` bound fires and yields an explicit error with NO engine instance created (assert the watch is not registered after a timeout). Assert `vendor_call_timeout_seconds` is read from config (no inline literal).
  - Frontend: `watchTicker`/`fetchInitialSnapshot` abort on the client-side timeout and return an explicit error result (a non-resolving fetch is replaced by a visible error); `useTapeStream` surfaces (does not swallow) an initial-snapshot failure and a pre-snapshot WS error. Assert the timeout value comes from the single `lib/config.ts` constant.
- **Error cases that must be handled (not swallowed):** empty/whitespace symbol; Historical with a missing or invalid (`end <= start`) window; backend unreachable at Watch time; vendor call that never returns; initial snapshot fetch that fails; WS that errors/closes before the first snapshot. Each must resolve to a distinct, visible state within a bounded time.

## NOTES

- **Apply iter-3/iter-6/iter-7/iter-8 frontend-QA lessons (load-bearing):** the shared harness `.next` on `:3650` has corrupted browser-qa three times. The browser run for this iteration MUST build into an **isolated** `NEXT_DIST_DIR` wired to an isolated backend (`NEXT_PUBLIC_API_URL`) and drive a real Chromium (Playwright is installed; browsers in `~/.cache/ms-playwright`) — never `npm run build` against the shared `.next`, and never `git checkout` a file carrying uncommitted iter edits. For these target journeys the *pixels are the evidence*: open the bytes and confirm the pending/error/validation states actually rendered — a confident PASS row over an idle/placeholder screenshot is NOT evidence.
- **J-22 has two halves, both required by the goal:** the *backend* per-call timeout (proven by the mocked-slow-adapter unit test) AND the *frontend* client-side timeout backstop (proven by a non-resolving request). Build and verify both; do not let one stand in for the other.
- **Reuse existing affordances, don't fork status concepts:** the connecting dot already exists (`CONN_DOT.connecting`) and the error banner already renders in `TopBar`; the honest non-cockpit panel already exists (`ProviderUnavailable`). Add the `provider_timeout` reason as a sibling of the existing row-9 reasons rather than a new component/endpoint — this keeps the coherence-auditor's single-producer rule satisfied (one `POST /watch` failure path, one reason enum).
- **Single-source-of-truth guard:** the pending/error/validation states are pure UI presentation; do NOT let them introduce any client-side recomputation of an engine value (state/confidence/features/spread). The cockpit, once data arrives, still reads the engine snapshot verbatim (rows 1–6).
- This iteration re-opens the GOAL after a prior GOAL_ACHIEVED because the Must-have journey set grew (J-21–J-24) — the evaluator should score the four new journeys and confirm J-01–J-20 did not regress before any GOAL_ACHIEVED is re-declared.
