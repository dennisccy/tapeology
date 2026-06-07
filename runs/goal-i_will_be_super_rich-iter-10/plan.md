# goal-i_will_be_super_rich-iter-10 Execution Plan

Post-connect lifecycle hardening (J-25, J-26, J-27): after a Watch is accepted and the stream
connects, the cockpit ALWAYS resolves to an honest non-idle terminal state — never a mute/blank
cockpit, never a confident `live` over an empty tape, never a silent return to idle. Closes the
"No mute cockpit / no silent return to idle" critical anti-goal.

Additive only: the sole new producer is the engine/feeder writing the EXISTING `stream_status`
(Data Contract row 6) with two new values — `waiting` and `failed`. No new endpoint, no second
status field/writer, no engine-math change, no client recomputation. Determinism is unaffected
(status is delivery/lifecycle metadata, never part of `classify(...)`).

## What to Build

- **Engine `waiting` rung** (`tape_engine.py`): add an explicit `waiting` status between
  `connecting` (pre-open) and `live` (first event arrived). The existing `connecting`→`live`
  flip on the first `process_event` stays; add a `waiting`→`live` flip so a stream that signalled
  open (status `waiting`) also promotes to `live` on its first event. `paused`/`stale`/`closed`
  semantics untouched. Status-label only — no change to features/state/confidence.
- **Feeders signal stream-open → `waiting`** (`watch_manager.py`): in `_feed`, `_feed_paced`, and
  `_feed_live`, set `stream_status = "waiting"` once the provider stream is open but BEFORE the
  first event is applied (for `_feed_live`, after the puller is started / `stream()` established,
  before the first `process_event`). A connected-but-quiet stream then reads `waiting`, not a
  frozen `connecting`.
- **Feeders surface a failure → `failed`, logged not swallowed** (`watch_manager.py`): wrap each
  feeder's stream loop so a non-`CancelledError` `Exception` is (a) logged via the stdlib
  `logging` module — a real, inspectable line naming the ticker + exception (no `print`, no
  swallow) — and (b) flips `stream_status` to `failed` before the task ends. `CancelledError`
  keeps meaning a clean stop/switch (→ `closed`, re-raise) — a cancel MUST NOT be reported as
  `failed`. Live-socket teardown stays the EXISTING bounded `aclose()` path; do NOT add a
  synchronous `unsubscribe_*`/blocking close in the failure branch (iter-4 deadlock lesson).
- **Bound `waiting`→`stale` with the already-registered `CONFIG.stale_gap_seconds`**: ensure the
  live stale watchdog flips to `stale` from `waiting` (not only from `live`), so an off-hours /
  quiet live feed that NEVER produced a first event still bounds out to `stale` instead of sitting
  on `waiting` forever. Add NO new timeout literal. (The paced/sim feeders are bounded/finite, so
  their `waiting` resolves to `live`-or-`closed` by exhaustion — no new timer needed there.)
- **Snapshot/serializer docstrings**: extend the `stream_status` value list in
  `engine/snapshot.py` and the serializer comments to include `waiting`/`failed` (documentation
  only — `serializers.py` lines 52/81/130 already pass `stream_status` through verbatim; do NOT
  add a second status field or recompute anything).
- **Cockpit `waiting` treatment** (`Cockpit.tsx` / `app/page.tsx`): when the canonical snapshot's
  `stream_status === "waiting"`, render an explicit human-readable
  "Connected to `<SYMBOL>` (`<mode>`) — waiting for the first trade…" treatment IN PLACE OF the
  blank panel grid. Read symbol/mode from existing state and the status verbatim from the snapshot
  — no client-side "is the tape empty?" guess, no recomputation of any engine value.
- **page.tsx routes snapshot-borne `failed`/`waiting`** (`app/page.tsx`): render the EXISTING
  `StreamFailedState` + error banner when the SNAPSHOT's `stream_status === "failed"` (a
  post-connect feeder failure, distinct from iter-9's pre-snapshot `connStatus === "failed"`),
  and the new waiting treatment when `stream_status === "waiting"`. An empty cold-start snapshot
  MUST NOT short-circuit into the full `Cockpit` grid as a settled `live` connection. No new
  client timer (iter-9's `WATCH_REQUEST_TIMEOUT_MS` covers the pre-connect phase, unchanged).
- **Status dots** (`TopBar.tsx`): add `waiting` to `STREAM_DOT` (amber + `animate-pulse`, reads as
  in-progress, consistent with stale/paused = amber); add `failed` to `STREAM_DOT` (rose) so a
  snapshot-borne `stream_status === "failed"` renders the rose failed dot. Dots read the engine
  status verbatim — the dot MUST NOT read a confident `live` over an empty tape.
- **types.ts**: extend the `stream_status` doc comment to include `waiting`/`failed` (already a
  free `string` — no shape change).

## Agents Required

- developer: yes -- backend (engine `waiting` rung + the three feeders' `waiting`/`failed`
  handling + `waiting`→`stale` bound + docstrings) AND frontend (Cockpit waiting treatment +
  page.tsx routing of snapshot-borne `waiting`/`failed` + TopBar dots + types comment), with new
  backend unit tests. Single cross-cutting change owned by one agent.

## Frontend Present
yes

## Files to Create/Modify

- `apps/backend/app/engine/tape_engine.py` -- add the `waiting` rung; `connecting`/`waiting`→`live`
  on first event; no engine-math change.
- `apps/backend/app/watch_manager.py` -- `_feed`/`_feed_paced`/`_feed_live`: set `waiting` on
  stream-open; catch non-`CancelledError` `Exception` → log (stdlib `logging`, names the ticker)
  + flip `failed`; live `waiting`→`stale` bound via `stale_gap_seconds`; keep the bounded
  `aclose()` teardown (no synchronous unsubscribe in the failure branch).
- `apps/backend/app/engine/snapshot.py` -- extend the `stream_status` value-list comment with
  `waiting`/`failed` (doc only).
- `apps/backend/app/serializers.py` -- extend the `stream_status` comments with `waiting`/`failed`
  (doc only; pass-through unchanged).
- `apps/backend/tests/test_stream_lifecycle.py` -- NEW: the unit tests below (no-event provider,
  feeder-raises, cancel-is-not-failed, rung order), covering the paced/sim AND live feeders.
- `apps/frontend/components/Cockpit.tsx` -- render the waiting treatment when
  `stream_status === "waiting"` (instead of blank panels).
- `apps/frontend/components/IdleState.tsx` -- add a `WaitingState({ symbol, mode })` treatment
  (reuse the existing connecting/failed component pattern; amber pulsing dot, DOM text
  "Connected to `<SYMBOL>` (`<mode>`) — waiting for the first trade…").
- `apps/frontend/app/page.tsx` -- route a snapshot-borne `stream_status === "waiting"` to the new
  waiting treatment and `=== "failed"` to `StreamFailedState` + banner; an empty cold-start
  snapshot must not render the full cockpit grid.
- `apps/frontend/components/TopBar.tsx` -- add `waiting` (amber, pulse) and `failed` (rose) to
  `STREAM_DOT`.
- `apps/frontend/lib/types.ts` -- extend the `stream_status` doc comment with `waiting`/`failed`.
- `docs/handoffs/goal-i_will_be_super_rich-iter-10-dev.md` -- dev handoff (required).

## UI Evolution

- **New user-facing capability:** a watched ticker that connects but has no data yet says so
  ("Connected to AAPL (live) — waiting for the first trade…") instead of showing blank panels
  under a misleading status; a later background feeder failure shows an explicit failure instead
  of freezing; an off-hours Live watch lands on an explicit closed/waiting→stale state — never
  idle, never a fake-`live` empty cockpit.
- **New information displayed:** an explicit waiting / "connected — no data yet" cockpit treatment
  labelled with symbol + mode; a `waiting` status dot (amber, in-progress) and a snapshot-borne
  `failed` status dot (rose), both driven by the canonical engine `stream_status`.
- **New user actions:** none. Honest lifecycle reporting on the existing Watch/Stop/Pause/Resume
  surface — no new buttons/forms/controls.
- **UI surface changes:** the single `/` cockpit area gains two in-place treatments (waiting,
  post-connect failure) alongside the existing idle / connecting / cockpit / honest-panel /
  pre-snapshot-failure treatments. No new page, no new route.
- **Navigation changes:** none.

## Visual Requirements

- **Component patterns:** reuse the existing `IdleState.tsx` honest-non-cockpit pattern
  (`ConnectingState` / `StreamFailedState`) for the new `WaitingState`; reuse the existing
  `StreamFailedState` + TopBar error banner for the post-connect `failed` case. No new component
  library, no raw-div soup beyond the established panel idiom.
- **Layout:** the new waiting/failed treatments occupy the same centered cockpit real estate as
  the existing idle/connecting/failed states (single-column, `min-h-[40vh]` centered block).
  Cockpit panel grid unchanged.
- **Key visual effects:** restrained per DESIGN SYSTEM. `waiting` = amber with `animate-pulse`
  (in-progress, matches `CONN_DOT.connecting`); `failed` = rose `⚠` (matches `StreamFailedState`).
  Monospaced symbol. No new effects invented.
- **States to handle:** waiting (connected, no first event — new), post-connect failure (new),
  plus the unchanged idle / connecting / cockpit / honest-panel / pre-snapshot-failure / paused
  states. The waiting treatment is itself the "empty/loading" state for a connected-but-quiet tape.

## Key Test Scenarios

Backend unit tests (`apps/backend/tests/test_stream_lifecycle.py`, using the existing
`FakeLiveProvider`/`FakeAdapter` doubles in `tests/fakes.py` — the provider seam, never the prod
path), covering BOTH the paced/sim feeder (`_feed`/`_feed_paced`) and the live feeder
(`_feed_live`):

- A connected feeder with NO first event sets `stream_status == "waiting"` (not `live`, not a
  frozen `connecting`), then flips to `stale` after a tiny `stale_gap_seconds` override — and
  fabricates NO trade during the wait (recent-trades stays empty, `event_count == 0`).
- The first real event flips `waiting`→`live` (rung order holds; J-01 behavior unchanged).
- A feeder whose provider RAISES mid-stream (or before the first event) ends with
  `stream_status == "failed"` AND emits a server-side log record naming the ticker (assert via
  `caplog`); the engine is NOT frozen at `connecting`/cold-start and is NOT fabricated to `live`.
- A clean stop/switch (cancel) still ends `closed` and re-raises `CancelledError` — a cancel is
  NOT reported as `failed` (no false-failure on normal teardown).
- Full suite green: `cd apps/backend && .venv/bin/python -m pytest tests/ -v` rises above the
  current 189 passing with zero failures; sim path J-01–J-09 behavior-identical.

Browser (browser-qa, by journey ID) — run against a CLEAN isolated frontend
(`NEXT_DIST_DIR` + `NEXT_PUBLIC_API_URL` → an isolated backend), NEVER the shared `:3650` `.next`
(iter-3/6/8 lesson); **hash the evidence dir (`md5sum *.png | uniq -c -w32`)** before trusting any
PASS table; assert on DOM text, not just pixels (iter-9 placeholder-screenshot lesson):

- **J-26** — Watch a symbol that connects but yields no first event (no-event provider behind the
  seam, or a `page.route` HTTP hold on the snapshot round-trip). Assert the cockpit shows the
  explicit "waiting for the first trade" treatment labelled with symbol/mode and the status dot
  reads `waiting` (NOT `live`). DOM-text assertion ("waiting for the first trade",
  "Connected to <SYMBOL>").
- **J-25** — In Historical AND Live (incl. an off-hours / closed-clock Live watch on the isolated
  stack), click Watch: assert the idle screen leaves within ~1s and the watch resolves to a
  non-idle terminal state (closed panel with next open, or `waiting`→`stale`, or an explicit
  error) — never idle, never a fake-`live` empty cockpit. The `market_closed` path is verifiable
  without a feed (FakeAdapter clock=closed, as in iter-3).
- **J-27** — With a connected watch whose feeder then fails (kill the isolated backend after
  connect, or a no-event/raising provider): assert the UI surfaces an explicit failed state
  (`StreamFailedState` + banner), "not stuck on Connecting", and never a blank `live` cockpit.
- **Regression smoke:** J-01 (SIM-BUYER full cockpit + Buyer Control), J-10 (3-mode controls),
  J-17 (sim chart), J-21 (synchronous connecting), J-24 (inline validation) re-verified on the
  same isolated stack — no Watch-flow regression.

## Out of Scope (excluded — do NOT build here)

- **J-28 / J-29 / J-30** (vendor-call-boundary timeout enforcement, fast concurrent historical
  fetch / cached windows, warmed/cached fast symbol search). A separate vendor-performance
  concern for a later iteration. Do NOT add concurrency, caching, request-cancellation, or a new
  HTTP-deadline mechanism. They share the words "timeout"/"vendor" with this work but mixing them
  in would bloat the iteration and make scoring ambiguous. If a J-28–J-30 defect is noticed during
  implementation, note it in the handoff and exclude it.
- Changing `vendor_call_timeout_seconds`, `WATCH_REQUEST_TIMEOUT_MS`, or the iter-9 pre-connect
  timeout behavior (J-22 is passing — do not regress).
- Any new engine math, classifier threshold, feature, or chart behavior (status labels are NOT
  part of classification — keep the engine deterministic; sim engine-math modules stay an
  effectively empty diff).
- Any new endpoint, route, page, or a SECOND `stream_status` writer/field (the coherence-auditor
  will FAIL that drift; the UI must read `waiting`/`failed` verbatim and recompute nothing).
- Auto-reconnect of a dropped live socket (a `failed` feeder surfaces `failed`; it does not
  silently retry).
- Any order/execution/broker affordance (anti-goal).

## Goal Alignment & Risk Notes

- **Advances the goal:** directly closes the load-bearing "No mute cockpit, no silent return to
  idle" critical anti-goal and the J-25–J-27 Must-have journeys re-added to `docs/goal.md`. After
  this iteration only J-28–J-30 remain unbuilt.
- **Builds on existing architecture:** serializers already pass `stream_status` verbatim;
  `FakeLiveProvider` (no-event lever) and `FakeAdapter` (`*_raises` flags) already exist;
  `StreamFailedState`/`ConnectingState` and the TopBar banner/dot maps already exist. The change
  is additive to these, not a rebuild.
- **Sharp edges (call out to dev):**
  1. **Single source of truth** — the ONLY new producer is the engine/feeder writing the existing
     `stream_status`. No second status field, no second writer, no UI recompute of any rows 1–6
     value. (coherence-auditor hard-fails drift.)
  2. **Determinism** — `waiting`/`failed` must never enter `classify(...)`/any feature/score; the
     same ordered event stream must still yield identical features/state/confidence.
  3. **iter-4 deadlock** — in the `failed` branch do NOT call the SDK's blocking
     `unsubscribe_*`/close from the generator/`finally`; set status, log, and let the existing
     bounded `aclose()` teardown run.
  4. **cancel ≠ failure** — `CancelledError` must remain `closed` + re-raise; only a real
     `Exception` becomes `failed`.
- **No spec/goal contradiction or scope creep detected.** The spec is precise, code-grounded, and
  self-enforces scope discipline (J-28–J-30 explicitly deferred). No items flagged out-of-scope
  against CORE RULES beyond those the spec already excludes.
