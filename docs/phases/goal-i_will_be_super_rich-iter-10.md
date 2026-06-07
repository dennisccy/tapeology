# Goal Iteration 10 — No mute cockpit / no silent return to idle (post-connect lifecycle: J-25–J-27)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich
- **Iteration:** 10
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-25, J-26, J-27
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-15, J-16, J-17, J-18, J-19, J-20, J-21, J-22, J-23, J-24
- **Out-of-scope (future) journeys:** J-28, J-29, J-30 (vendor-call-boundary timeout enforcement / fast historical load / fast symbol search — a separate performance concern; do NOT build here)
- **Anti-goal reminders** (verbatim from `docs/goal.md`, load-bearing this iteration):
  - **No mute cockpit, no silent return to idle.** A valid Watch MUST resolve to a non-idle terminal state and MUST NOT silently return to or remain on the idle/previous screen. A watched cockpit MUST NOT present a confident **live** status over an empty tape, nor render blank panels indefinitely with no explanation. Connected-but-no-data MUST read as an explicit connecting/waiting or honest empty-state and MUST resolve, within a bounded configured time, to streaming data or an explicit honest state (**stale** / **closed** / no-data / market-closed / unavailable / error) — owned once by the engine's `stream_status`. A cold-start/empty snapshot MUST NOT be treated as a settled connection that disables the failure/empty-resolution path; a feeder failure MUST be logged and surfaced, never swallowed. A reproducible Watch that returns to idle, or an indefinitely-empty cockpit, in any mode (including off-hours), is a veto on GOAL_ACHIEVED. *(critical)*
  - **No silent dead-clicks.** Pressing Watch MUST always produce a visible UI change within ~1 second … The UI MUST NOT silently remain on the idle/previous screen, MUST NOT leave "Connecting…" running with no resolution, and MUST NOT swallow a failure (no empty `catch`, no unawaited promise that drops an error, no unbounded external wait). *(critical)*
  - **No fabricated data.** The system MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. … a provider gap/feed lull → `stale`. Falling back to simulated or invented data to mask a real-data failure is a defect. *(critical)*
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. *(critical)*
  - **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders … It only reads and classifies the tape. *(critical)*
  - **Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine MUST produce identical features, state, and confidence; classification MUST NOT depend on wall-clock time or randomness.
  - **No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config.

## GOAL

After a Watch click is accepted and the stream connects, the cockpit always resolves to an honest non-idle terminal state — it explains a connected-but-empty tape with an explicit "waiting for the first trade" state (never a confident `live` over blank panels), bounds that wait to `stale`, and surfaces a background feeder failure as an explicit error (logged, never swallowed, never frozen at cold-start) — across real modes and off-hours, with no fabricated data.

## BACKGROUND

The goal re-opened after the iter-9 GOAL_ACHIEVED: two spec commits added six new Must-have journeys — `7d33007` (J-25–J-27 + the "no mute cockpit, no silent return to idle" anti-goal) and `533b6e2` (J-28–J-30 vendor responsiveness). J-25–J-30 are absent from `journey-history.json` (so they are FAILING/unbuilt), exactly the goal-expansion pattern that re-opened the session at iter-5 (J-16–J-20) and the iter-8/9 boundary (J-21–J-24).

This iteration takes the **post-connect lifecycle cluster (J-25–J-27)** — they share one mechanism. iter-9 hardened the click *up to* acceptance (pending → cockpit | honest panel | error | inline validation). What it did NOT cover: a watch that is **accepted and connects but then has no first event** (J-26), or whose **background feeder later raises/exits** (J-27), or an **off-hours Live** watch whose clock is indeterminate so it proceeds and yields no events (J-25). Today `TapeEngine.process_event` only flips `connecting`→`live` on the **first event** (`tape_engine.py:145-146`), so before any event the status sits at `connecting` and the `Cockpit` renders a full grid of blank panels once any (even empty cold-start) snapshot exists (`Cockpit.tsx`). And the feeders (`watch_manager.py` `_feed` / `_feed_paced` / `_feed_live`) only catch `asyncio.CancelledError`; a generic feeder `Exception` propagates out of the task with **no status update**, leaving the engine frozen at cold-start with the failure swallowed in the task — a direct violation of "a feeder failure MUST be logged and surfaced, never swallowed."

The fix is additive to the **single existing row-6 `stream_status`** the engine/feeder already owns (no new endpoint, no new producer): add two engine-owned post-connect statuses — **`waiting`** (connected, no first event yet) and **`failed`** (feeder raised/exited) — both already served verbatim by `serialize_summary` / `serialize_stream` (`serializers.py:81,130`), and render an explicit waiting / failure treatment in the cockpit instead of blank panels. The connected-empty→`stale` bound reuses the already-registered `stale_gap_seconds` (no new config). J-28–J-30 are a distinct performance concern and are explicitly out of scope.

**Lessons applied (from `lessons.md`):**
- **iter-4 (live-socket teardown deadlock):** the `failed`-status handling on a feeder exception MUST NOT call the SDK's `unsubscribe_*`/blocking close from the generator/`finally` on the event-loop thread (it deadlocks). Set the status, log, and let the existing bounded `aclose()` teardown run — do not add a new synchronous unsubscribe.
- **iter-3 / iter-6 / iter-8 (shared `:3650` `.next` corruption):** the harness frontend `.next` has corrupted browser-qa repeatedly. browser-qa MUST rebuild or fully bypass it — isolated `NEXT_DIST_DIR` + `NEXT_PUBLIC_API_URL` → an isolated backend — before trusting (or skipping) the visual verification. J-25/J-26 are visual states.
- **iter-9 (fast / failure-path UI states + placeholder screenshots):** these are exactly fast-resolving / failure-path UI states. Drive them with a `page.route` HTTP hold (for the snapshot/watch round-trip) and assert on **DOM text** ("waiting for the first trade", "Connected to <SYMBOL>"), not just pixels; for a feeder/connection failure, kill the isolated backend (or use a no-event provider) and assert "not stuck on Connecting" + an explicit surfaced state. **Hash the evidence dir (`md5sum *.png | uniq -c -w32`)** before trusting any PASS table — byte-identical placeholders are not evidence.

## IN SCOPE

### Backend

- [ ] **Engine: add a `waiting` post-connect status.** In `TapeEngine` (`apps/backend/app/engine/tape_engine.py`), introduce an explicit `waiting` state for "connected but no first event yet": when the feeder has signalled the stream is open but `process_event` has not yet run, the canonical `stream_status` reads `waiting` (not a bare `connecting`, and never `live`). The `connecting`→`live` flip on the first event stays; add the `waiting` rung between them (connecting = pre-open handshake / cold construction; waiting = open, awaiting first event; live = first event arrived). Keep `paused`/`stale`/`closed`/`failed` semantics intact. No engine-math change — this is a status-label change only; determinism is unaffected (status is not part of the classification).
- [ ] **Feeders: signal stream-open → `waiting`.** In `WatchManager` (`apps/backend/app/watch_manager.py`), each feeder (`_feed`, `_feed_paced`, `_feed_live`) sets the engine status to `waiting` once its provider stream is open but before the first event is applied, so a connected stream with no immediate activity reads `waiting` rather than a frozen `connecting`. (`_feed_live` already drains via the puller — set `waiting` after `stream()` is established / the puller starts, before the first `process_event`.)
- [ ] **Feeders: surface a feeder failure as `failed` (logged, not swallowed).** Wrap each feeder's stream loop so that a non-`CancelledError` `Exception` is (a) **logged server-side** (use the stdlib `logging` module — a real, inspectable log line naming the ticker + exception; no bare `print`, no swallow) and (b) flips the engine `stream_status` to **`failed`** before the task ends. `CancelledError` continues to mean a clean stop/switch (→ `closed`, re-raise) — do NOT conflate a cancel with a failure. The live socket teardown stays the existing bounded `aclose()` path (iter-4 deadlock lesson) — do NOT add a synchronous unsubscribe in the failure branch.
- [ ] **Config: bound the connected-empty wait to `stale`.** The `waiting`→`stale` transition for a connected-but-no-event stream MUST be bounded by the **already-registered** `CONFIG.stale_gap_seconds` (no new constant). For the **live** feeder this already holds (the stale watchdog flips to `stale` after `stale_gap_seconds`); ensure the flip is from `waiting` (not only from `live`) so an off-hours/quiet live feed that NEVER produced a first event still bounds out to `stale` (it must not sit on `waiting` forever). Add no new timeout literal; if any new tunable is genuinely unavoidable it MUST live in `config.py` (no magic numbers).
- [ ] **Snapshot/serializer docstrings:** extend the `stream_status` value list in `apps/backend/app/engine/snapshot.py` and the serializer comments to include `waiting` and `failed` (documentation only; the serializers already pass `stream_status` through verbatim — do NOT add a second status field or recompute anything).

### Frontend

- [ ] **Cockpit: render an explicit waiting treatment.** In `apps/frontend/components/Cockpit.tsx` (and/or `app/page.tsx`), when the canonical snapshot's `stream_status === "waiting"` (connected, no first event), render an explicit, human-readable **"Connected to `<SYMBOL>` (`<mode>`) — waiting for the first trade…"** treatment **in place of** the blank panel grid. Read the symbol/mode from existing state and the status verbatim from the snapshot — NO client-side guess, NO recomputation of any engine value. The status dot MUST NOT read a confident `live` over an empty tape (it reads `waiting`).
- [ ] **TopBar status dot: add `waiting` and confirm `failed`.** In `apps/frontend/components/TopBar.tsx`, add `waiting` to the `STREAM_DOT` map (amber, consistent with stale/paused = amber, e.g. `bg-amber-400 animate-pulse` to read as in-progress) so the canonical engine `waiting` status renders an honest dot. `failed` already exists in `CONN_DOT`; ensure a snapshot-borne `stream_status === "failed"` also renders the rose failed dot via `STREAM_DOT` (add the entry if missing). The dot reads the engine status verbatim.
- [ ] **page.tsx: route a snapshot-borne `failed`/`waiting` to the right treatment.** Ensure `app/page.tsx` renders the existing `StreamFailedState` + error banner when the **snapshot's** `stream_status === "failed"` (a *post-connect* feeder failure, distinct from iter-9's pre-snapshot `connStatus === "failed"`), and the new waiting treatment when `stream_status === "waiting"`. An empty cold-start snapshot MUST NOT be treated as a settled `live` connection — the waiting/failed resolution stays armed until streaming data or an explicit honest state appears. No new client-side timer is required (the bound is the engine's; the iter-9 `WATCH_REQUEST_TIMEOUT_MS` client backstop covers the pre-connect phase and is unchanged).
- [ ] **types.ts:** extend the `stream_status` doc comment to include `waiting`/`failed` (the type is already a free `string` — no shape change).

### New user-facing capability

A watched ticker that connects but has no data yet now says so ("Connected to AAPL (live) — waiting for the first trade…") instead of showing blank panels under a misleading status; if the background feed later fails, the cockpit shows an explicit failure instead of freezing; an off-hours Live watch lands on an explicit closed/waiting/stale state — never idle, never a fake-live empty cockpit.

### New information displayed

- An explicit **waiting / "connected — no data yet"** cockpit treatment labelled with the symbol + mode.
- The **`waiting`** status dot (amber, in-progress) and the **`failed`** status dot (rose) driven by the canonical engine `stream_status`.

### New user actions

None. (No new buttons/forms/controls — this is honest lifecycle reporting on the existing Watch/Stop/Pause/Resume surface.)

### UI surface changes

The single `/` cockpit area gains two in-place treatments (waiting, post-connect failure) alongside the existing idle / connecting / cockpit / honest-panel / pre-snapshot-failure treatments. No new page, no new route, no nav change.

### Product surface delta

The product stops ever showing a mute or misleading cockpit after a successful Watch: every connected watch resolves to streaming data or an explicit, honest, bounded state — closing the "no mute cockpit / no silent return to idle" anti-goal on real feeds and off-hours.

### Blueprint conformance

All three journeys live on the existing `/` HOME (the tape cockpit), ≤1 click after Watch — matching the Information Architecture in `blueprint.md`. The new treatments are in-place cockpit-area states (the existing "Honest non-cockpit states" pattern), not new routes. The blueprint was updated additively this iteration (iter-10 header note; row 6 extended with `waiting`/`failed`; the IA app-shell status list and a new singularity rule). No top-level nav section was added/renamed/moved ⇒ **no re-approval requested** (no `blueprint.reapproval-requested` written).

### Data-contract additions

No new endpoint and no new producer. The work extends the **existing Data Contract row 6** (`stream_status`, owned once by the engine/feeder) with two engine-owned values — **`waiting`** and **`failed`** — both served verbatim by the already-registered `GET /tape/{ticker}/summary` + `WS /stream` path. The UI reads them read-only (no recomputation). The connected-empty→`stale` bound reuses the already-registered `CONFIG.stale_gap_seconds`. Never introduce a second `stream_status` writer or a second status field — the coherence-auditor will FAIL that drift.

## OUT OF SCOPE

- **J-28 (true vendor-call-boundary timeout enforcement at the HTTP/SDK level, backend<frontend ordering, actionable oversize message), J-29 (fast concurrent historical fetch / cached windows / prompt warm-up), J-30 (warmed/cached symbol universe, cancelled stale searches, min-query).** These are a separate vendor-performance concern — a later iteration. Do NOT add concurrency, caching, request-cancellation, or a new HTTP-deadline mechanism here.
- Changing `vendor_call_timeout_seconds`, `WATCH_REQUEST_TIMEOUT_MS`, or the iter-9 pre-connect timeout behavior (J-22 is already passing — do not regress it).
- Any new engine math, classifier threshold, feature, or chart behavior. Status labels are NOT part of classification — keep the engine deterministic.
- Any new endpoint, route, page, or a second `stream_status` writer/field.
- Auto-reconnect of a dropped live socket (an explicitly-later nice-to-have) — a failed feeder surfaces `failed`; it does not silently retry.
- Any order/execution/broker affordance (anti-goal).

## DEFINITION OF DONE

- [ ] **J-26** passes: a watch that connects but yields no first event shows an explicit "Connected to `<SYMBOL>` (`<mode>`) — waiting for the first trade…" treatment (not blank panels), the status reads `waiting` (never a confident `live` over an empty tape), and once `stale_gap_seconds` is exceeded it bounds to `stale`. Verified by browser-qa (or evaluator isolated-stack render) using a no-event provider + DOM-text assertion, AND by a backend unit test.
- [ ] **J-27** passes: (a) a connected stream with no first event resolves within `stale_gap_seconds` to an explicit `stale`/no-data state owned by `stream_status`; and (b) a background feeder that raises/exits is **logged server-side** and flips `stream_status` to `failed`, surfaced in the UI (StreamFailedState + banner) — never swallowed, never frozen at cold-start, never a fabricated `live`. Both halves proven by backend unit tests (a no-event provider; a feeder that raises); the UI failure treatment shown by a rendered screenshot.
- [ ] **J-25** passes: in Historical and Live (including **off-hours**), a valid Watch leaves the idle screen within ~1s and resolves to a non-idle terminal state — streaming data, an explicit `waiting`/connecting state, an explicit honest state (`market_closed` with next open / `provider_unavailable` / `no_data_for_window` / `stale` / `closed` / `failed`), or an explicit error. The idle screen never reappears/persists after a valid Watch, and an off-hours Live watch shows the explicit closed (or `waiting`→`stale`) state, never idle and never a fake-`live` empty cockpit. The market-closed / unavailable paths are browser-verifiable without a feed; the real-mode legs are verified with credentials or by the evaluator's isolated stack.
- [ ] Required-still-passing journeys J-01–J-24 remain green (engine math, classifier, features, history, pause, the iter-9 Watch-flow, and J-22's bound are not regressed). Sim path J-01–J-09 must be behavior-identical (the engine-math modules stay an empty diff aside from the additive status label).
- [ ] No anti-goal violation introduced (no fabricated data; single source of truth preserved — the UI recomputes no rows 1–6 value; no execution path; deterministic engine; no magic numbers — the bound reuses `stale_gap_seconds`).
- [ ] Unit tests pass; no regressions. Run `cd apps/backend && .venv/bin/python -m pytest tests/ -v` (currently 189 passing) and confirm the new tests are added and the count rises with zero failures.
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich-iter-10-dev.md`.

## TESTING REQUIREMENTS

- **Browser (named journeys this iteration must verify, by ID):**
  - **J-26** — Watch a symbol that connects but yields no first event (e.g. the `FakeLiveProvider`/no-event provider behind the seam on the isolated stack, or a held live stream); assert the cockpit shows the explicit "waiting for the first trade" treatment labelled with the symbol/mode and the status dot reads `waiting` (NOT `live`). Use a DOM-text assertion, not just a pixel check.
  - **J-25** — In Historical and Live, including a **Live watch off-hours** (or with an indeterminate/closed clock on the isolated stack), click Watch and assert the idle screen leaves within ~1s and the watch resolves to a non-idle terminal state (closed panel with next open, or `waiting`→`stale`, or an explicit error) — never idle, never a fake-`live` empty cockpit. The `market_closed` path is verifiable without a feed (FakeAdapter clock=closed, as in iter-3).
  - **J-27** — With a connected watch whose feeder then fails (kill the isolated backend after connect, or a no-event/raising provider), assert the UI surfaces an explicit failed state (StreamFailedState + banner), "not stuck on Connecting", and never a blank `live` cockpit.
  - **Regression smoke:** J-01 (SIM-BUYER full cockpit + Buyer Control), J-10 (3-mode controls), J-17 (sim chart), J-21 (synchronous connecting), J-24 (inline validation) — re-verify on the same isolated stack to confirm no Watch-flow regression.
  - browser-qa MUST run against a CLEAN isolated frontend (`NEXT_DIST_DIR` + `NEXT_PUBLIC_API_URL` → an isolated backend) — never the shared corrupted `:3650` `.next` (iter-3/6/8 lesson). **Hash the evidence dir** (`md5sum *.png | uniq -c -w32`) before trusting any PASS table.
- **Unit/integration (code paths that MUST have tests):**
  - A new backend test (e.g. `apps/backend/tests/test_stream_lifecycle.py`) using the existing `FakeLiveProvider`/`FakeAdapter` doubles in `tests/fakes.py` that asserts:
    - A connected feeder with **no first event** sets `stream_status == "waiting"` (not `live`, not a frozen `connecting`), then flips to `stale` after `stale_gap_seconds` (use a tiny `stale_gap_seconds` override, as the existing live tests do) — and that **no trade/quote is fabricated** during the wait (recent-trades stays empty, `event_count == 0`).
    - The first real event flips `waiting`→`live` (the rung order holds; J-01 behavior unchanged).
    - A feeder whose provider **raises** mid-stream (or before the first event) ends with `stream_status == "failed"` AND emits a server-side log record naming the ticker (assert via `caplog`), and the engine is **not** frozen at `connecting`/cold-start and is **not** fabricated to `live`.
    - A clean stop/switch (cancel) still ends `closed` and re-raises `CancelledError` — a cancel is NOT reported as `failed` (no false-failure on normal teardown).
  - Cover both the paced/sim feeder (`_feed` / `_feed_paced`) and the live feeder (`_feed_live`) for the `failed`/`waiting` behavior, since all three are status owners.
- **Error cases (invalid inputs / failure paths that MUST be exercised):**
  - Feeder exception → `failed` + logged (not swallowed, not re-raised as an uncaught task exception).
  - Connected, no event, past `stale_gap_seconds` → `stale` (bounded), no fabricated data.
  - Off-hours Live with an authoritative closed clock → existing `market_closed` 409 (unchanged, must not regress); with an indeterminate clock that proceeds → `waiting`→`stale` (no fake `live`).
  - Cancel/stop during `waiting` → `closed` (clean teardown, socket closed, no `failed`).

## NOTES

- **Why full depth:** this crosses backend (engine status model + feeder exception handling across all three feeders + the live waiting→stale bound) and frontend (cockpit waiting/failed rendering + status dot), and requires new unit tests beyond a browser smoke (a no-event provider; a feeder that raises; a `caplog` assertion that the failure is logged). It touches the lifecycle owner (`WatchManager`) and the canonical engine status — risk of regressing J-01–J-24 if the status rungs are wrong — so the full 11-step pipeline (including ux-regression + coherence + closure) is warranted. The prior evaluator recommended `lean` for follow-ups, but that assumed a small Watch-flow tweak; this is a structural lifecycle change.
- **Single-source-of-truth is the sharp edge:** the *only* new producer is the engine/feeder writing the existing `stream_status`. The UI MUST read `waiting`/`failed` verbatim and recompute nothing (no client-side "is the tape empty?" guess that could disagree with the engine). The coherence-auditor will FAIL a second `stream_status` writer, a second status field, or any UI recomputation of a rows 1–6 value.
- **Determinism guard:** `stream_status` is delivery/lifecycle metadata, NOT part of classification. Adding `waiting`/`failed` must not enter `classify(...)` or any feature/score, so the same ordered event stream still yields identical features/state/confidence (determinism anti-goal; the sim engine-math modules should remain an effectively empty diff).
- **Evaluator/visual-evidence reminder:** J-25/J-26 are visual lifecycle states that have repeatedly tripped the shared-`.next` corruption and placeholder-screenshot traps (iter-3/6/8/9). The authoritative evidence is a real rendered DOM on a clean isolated stack with text assertions + a hashed evidence dir — a "PASS_SURFACE" qa row or a plausible filename is not evidence.
- **Scope discipline:** do NOT pull J-28–J-30 forward. They share the word "timeout"/"vendor" with this work but are a separate performance concern; mixing them in would bloat the iteration and make the evaluator's scoring ambiguous. If during implementation a J-28–J-30 defect is noticed, note it in the handoff and exclude it.
- After this iteration, the remaining unbuilt Must-haves are J-28, J-29, J-30 (one more iteration, likely full given real-vendor concurrency/caching + a real call-level deadline). The evaluator decides GOAL_ACHIEVED only when every Must-have has positive evidence.
