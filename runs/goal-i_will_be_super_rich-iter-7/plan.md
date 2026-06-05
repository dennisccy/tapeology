# goal-i_will_be_super_rich-iter-7 Execution Plan

Two-part slice mandated by the iter-6 evaluator (full depth):
1. **Render-verify** the already-built prediction chart so **J-17/J-18** move `partial → passing`
   (a real rendered screenshot of the populated candlestick canvas — no code change to the chart).
2. **Build honest Pause/Resume** (**J-19**) — freeze a watched session without teardown, reading the
   engine's canonical paused state.

This advances `docs/goal.md` success criteria "Tape-state prediction chart" and "Pause / resume".
It implements blueprint Data Contract **rows 6 (`paused` value), 10 (read-only), 11** — all
pre-registered; **no blueprint edit, no nav change, no re-approval** (confirmed against
`runs/goal-session-i_will_be_super_rich/state/blueprint.md`). J-20 (local-time picker) is OUT OF
SCOPE this iteration (deferred to its own slice).

## What to Build

- **Backend — canonical `paused` state.** Add a `paused: bool` field to `EngineSnapshot`
  (`engine/snapshot.py`, default `False`) and extend the `stream_status` value set/docstring to
  include `"paused"`. The engine/feeder is the single owner (reuse the existing one `stream_status`
  writer — do NOT add a second writer in the API or UI).
- **Backend — engine pause/resume primitive.** Add `pause()` / `resume()` to `TapeEngine` that set
  `paused` + flip `stream_status` to `"paused"` (pause) and restore the prior pre-pause status +
  clear `paused` (resume). Idempotent (pause-when-paused / resume-when-not-paused are no-ops, no
  crash). Must remember the pre-pause status so resume never fabricates `"live"`.
- **Backend — feeder-level freeze in `WatchManager`** (distinct from `stop()`): a `pause(ticker)` /
  `resume(ticker)` that makes the feeder **stop applying events while paused** but **does NOT**
  `task.cancel()`, **does NOT** close the live socket, and **synthesizes NO catch-up trades** on
  resume. The feeder task stays alive; the engine, its latest snapshot, and the history buffer
  survive. Paced sim/historical replay continues from where it left off; live resume rejoins current
  real data (no backfill).
- **Backend — routes** `POST /watch/{ticker}/pause` and `POST /watch/{ticker}/resume` in
  `apps/backend/app/main.py` (routes live here, not `api.py`). Return the updated snapshot/paused
  state; `404` for a not-watched ticker (reuse `_engine_or_404`, never fabricate an engine).
- **Backend — keep `stop()` (`DELETE /watch/{ticker}`) unchanged**: still fully cancels the feeder +
  tears the instance down. Pause is additive, not a replacement; stop-after-pause must still tear down.
- **Backend — config (no magic numbers):** any new timeout introduced for pause lives in
  `app/config.py`. (Likely none needed — pause is a flag flip; the existing `stale_gap_seconds`
  governs the live watchdog. If a paused-feeder poll interval is introduced, it goes in config.)
- **Frontend — Pause/Resume controls + PAUSED indicator** beside Stop in `components/TopBar.tsx`,
  wired through `lib/api.ts`, reading `paused`/`stream_status` off the snapshot (no client guess).
- **Render-verify the chart (J-17/J-18)** — no code change; the browser-QA step must capture real
  screenshots on a CLEAN isolated build (see Key Test Scenarios).

## Agents Required

- developer: yes -- backend (snapshot `paused` field + status value; engine `pause()`/`resume()`;
  `WatchManager` feeder freeze; the two `/pause`/`/resume` routes; config if any timeout) AND
  frontend (Pause/Resume buttons + PAUSED status-dot state in `TopBar.tsx`; `pauseTicker`/
  `resumeTicker` in `api.ts`; `paused` in `types.ts`). Plus pause/honest-pause unit/integration tests.
  No chart code change — J-17/J-18 are render-verification only.

## Frontend Present
yes

## Files to Create/Modify

Backend:
- `apps/backend/app/engine/snapshot.py` -- add `paused: bool = False` to `EngineSnapshot`; update the
  `stream_status` comment to `"connecting" | "live" | "stale" | "paused" | "closed"`.
- `apps/backend/app/engine/tape_engine.py` -- add `pause()` / `resume()` (set/clear `paused`, flip to
  `"paused"` / restore prior status; remember pre-pause status; idempotent); thread `paused` into
  `_build_snapshot()`.
- `apps/backend/app/watch_manager.py` -- add `pause(ticker)` / `resume(ticker)` that freeze/continue
  the feeder WITHOUT cancelling the task or closing the socket; make each feeder (`_feed`,
  `_feed_paced`, `_feed_live`) skip applying events while the engine is paused (no fabricated backfill
  on resume). Leave `stop()` semantics untouched.
- `apps/backend/app/main.py` -- add `POST /watch/{ticker}/pause` and `POST /watch/{ticker}/resume`
  (404 if not watched; return updated snapshot/paused state).
- `apps/backend/app/serializers.py` -- include `paused` in the snapshot projections that the UI reads
  (at least `serialize_summary` + `serialize_stream`; keep them pure projections, no recompute).
- `apps/backend/app/config.py` -- only if a pause-related timeout/poll interval is introduced (avoid
  if possible).
- `apps/backend/tests/test_pause.py` -- NEW: engine + feeder pause/resume unit/integration tests
  (alive-not-cancelled, snapshot survives, honest no-backfill, stop-after-pause, idempotency).
- `apps/backend/tests/test_pause_api.py` -- NEW (or fold into an existing API test file): the
  `/pause` + `/resume` routes incl. the 404 not-watched path.

Frontend:
- `apps/frontend/components/TopBar.tsx` -- add Pause/Resume button beside Stop (Pause when streaming,
  Resume when `paused`); add a `"paused"` entry (amber dot) to `STREAM_DOT`; accept `onPause`/`onResume`
  props.
- `apps/frontend/app/page.tsx` -- add `handlePause`/`handleResume` calling the new api fns; pass them to
  `<TopBar>`. (No teardown — pause must NOT call `stopTicker` and must NOT `setTicker(null)`.)
- `apps/frontend/lib/api.ts` -- add `pauseTicker(ticker)` / `resumeTicker(ticker)` (POST; 404 handled).
- `apps/frontend/lib/types.ts` -- add `paused?: boolean` to `TapeSnapshot` (and surface `"paused"` as a
  valid `stream_status` string — it is already a free `string`, so just document it).

## UI Evolution

- New user-facing capability: the user can **Pause** a live/replaying watch — freezing the recent
  trades, chart, feature readouts, and tape state in place — and later **Resume** without losing the
  session, or **Stop** to tear it down. Separately, the prediction chart shipped in iter-6 is now
  confirmed to actually render.
- New information displayed: a **PAUSED** state on the existing stream-status dot/label (amber). No new
  chart data — J-17/J-18 render the already-served `/history` OHLC + markers (visual confirmation, not
  new data).
- New user actions: **Pause** button (freeze the current watch); **Resume** button (continue a paused
  watch). Both sit in the watch-control cluster beside the existing **Stop**.
- UI surface changes: the watch-control cluster on `/` (in `TopBar.tsx`, currently the
  Watching/Stop/scenario row + the status dot) gains Pause/Resume and a `paused` status state. No new
  page, no new route, no new panel.
- Navigation changes: none (single `/` HOME unchanged; blueprint IA already places Pause/Resume +
  PAUSED in the persistent app-shell watch controls).

## Visual Requirements

- Component patterns: hand-built panels only (DESIGN SYSTEM: component library = none). The
  Pause/Resume control is a plain `<button>` matching the existing **Stop** button's
  `rounded border … px-2.5 py-1 text-xs font-semibold` style in `TopBar.tsx`. The PAUSED state reuses
  the existing status-dot pattern (a colored dot + `capitalize` label) — add one `STREAM_DOT` entry.
- Layout: unchanged — the persistent top bar (`<header>`); the Pause/Resume button goes inside the
  existing `{watched && (...)}` Watching/Stop cluster (lines ~159-172). No layout reflow.
- Key visual effects (DESIGN SYSTEM color semantics, load-bearing): **amber** for paused (consistent
  with `stale`/absorption/unclear = amber, e.g. `bg-amber-400` dot, `text-amber-400` control). Buy =
  emerald, sell = rose, absorption/unclear/stale/paused = amber. Monospaced numerics unchanged.
  Buttons get hover/focus/active states matching the existing Stop button.
- States to handle: **Pause shown** when `stream_status` ∈ {connecting, live, stale} and not paused;
  **Resume shown** when `paused` is true (status reads `paused`); neither relevant when `closed`/idle.
  While paused the cockpit + chart simply stop updating (the engine stops emitting new snapshots and
  accrues no new candles) — the UI MUST NOT clear/tear down the cockpit and MUST NOT fabricate a
  `live` reading. The status dot/label must read **paused**, never live.

## Key Test Scenarios

Browser (MUST be real rendered screenshots on a CLEAN isolated build — set `NEXT_DIST_DIR` to an
isolated dir + `NEXT_PUBLIC_API_URL` → an isolated backend; **never** the shared `:3650`/`.next`,
which corrupted browser-QA in iter-3 and iter-6). Playwright + `/usr/bin/google-chrome` is available
in this environment (verified by the decomposer), so the render gap is closable — it MUST actually use
the isolated dist.

- **J-17 (no creds):** Watch `SIM-BUYER` → candlesticks render with an **emerald** buyer_control marker
  and rising candles; `SIM-SELLER` → **rose** marker / falling candles; `SIM-BIDABS` and `SIM-ASKABS` →
  **amber** absorption markers with price held; toggle bar size **10 → 30 → 60 s** → candles re-render;
  select **Live** mode → the chart is **hidden**.
- **J-18 (surface; credentialed half noted if no keys):** historical replay of a real symbol →
  candlesticks reflect real replayed prices and the on-screen bars match the engine-served `…/history`
  at each bar size. With no creds, confirm the surface + bar-match and note the credentialed render
  half (backend `…/history`-agrees-with-engine already proven in iter-6).
- **J-19 (no creds):** Watch `SIM-BUYER`, let it populate → click **Pause**: recent trades, chart,
  feature counters, and tape state **freeze**, a **PAUSED** indicator shows, the session is **NOT**
  cleared (`…/state` still 200, cockpit still visible) → click **Resume**: the stream continues from
  where it left off (no fabricated jump in counts) → click **Stop**: the stream closes and the cockpit
  returns to idle.
- A `browser-qa SKIPPED` / "PASS_SURFACE" / blank screenshot for these visual journeys is `partial`,
  NOT a pass (iter-3/5/6 lesson). If, despite Playwright + Chrome, the populated chart still cannot be
  captured, that is a blocker to record explicitly — never a silent skip.

Unit/integration (assert exact values + a failure path; floor = 159 passed / 1 skipped, must rise):
- Pause sets engine `paused=true` and `stream_status="paused"`; the feeder task is **still alive**
  (NOT cancelled) and the engine + history buffer **survive** (snapshot readable, `…/state` not 404).
- Resume restores the prior `stream_status` (live/connecting/stale — never fabricated `live`) and clears
  `paused`.
- **Honest pause (load-bearing):** while paused, no new trades are applied and the snapshot never reads
  `live`; on resume the recent-trades/feature counts do **not** jump by a fabricated backfill. Prefer a
  deterministic hermetic test asserting exact pre/post-pause counts + statuses (the J-14/J-15 standard).
- `stop()` after a pause still fully tears down (feeder cancelled, `…/state` → 404).
- Error path: `POST /watch/{unknown}/pause` and `…/resume` on a not-watched ticker → **404** (no engine
  fabricated). Idempotency: resume-when-not-paused / pause-when-already-paused handled (no crash, no
  duplicate feeder, no second status owner).
- Regression guard: `/history` and the chart-data path are byte-identical to iter-6 (row 10 untouched);
  J-01–J-16 paths unchanged (pause is additive and must not alter the unpaused stream).

## Anti-Goal Guardrails (must not be violated)

- **Honest pause (critical, the load-bearing anti-goal):** paused reads `paused`, never `live`; no
  fabricated backfill on resume; live resume rejoins current real data (no synthesized catch-up).
- **Single source of truth:** `paused` + `stream_status` owned **once** by the engine/feeder (reuse the
  existing single `stream_status` writer); the API and UI **read** it — do NOT add a second status/paused
  writer. The UI must not guess paused client-side.
- **One focused chart, computed once:** the chart still reads `/history` verbatim; **no** chart code
  change, no UI recompute of price/side/state, no order/execution affordance added.
- **No execution path / no broker integration; no magic numbers** (any pause timeout in config).
- **Provider-agnostic:** pause is a feeder/engine concern; do NOT leak vendor specifics, and do NOT call
  the SDK's `unsubscribe_*()` from a generator `finally` (iter-4 deadlock lesson) — pausing live means
  stop *consuming/applying* events while the socket stays open, not unsubscribing/closing it.

## Out of Scope (flagged — exclude)

- **J-20** (local-time historical-window picker + US-session quick-picks) — deferred to its own slice;
  likely needs a blueprint touch (row 12). Do NOT build it here.
- Any change to the chart's data/computation (history buffer, `serialize_history`, `/history`) — already
  proven; render-verify only.
- Auto-reconnect of a dropped live socket, Level 2 / `BookLevelEvent`, the predictive-edge replay
  harness, persistence.
- Changing classifier thresholds / feature windows / the spread gate (would risk regressing J-01–J-16).
- The advisory iter-6 coherence WARN (frontend bar-size constant mirroring backend config) — optional
  tidy only; do not let it expand scope.

## Notes / Assumptions (documented, not blocking)

- The WS stream loop (`main.py` `stream()`) re-sends `engine.snapshot()` every `WS_PUSH_INTERVAL`
  regardless of feeder activity, so while paused it keeps pushing the frozen snapshot now carrying
  `stream_status="paused"` + `paused=true` — the UI dot flips to paused with **no client guess**, and
  the cockpit/chart freeze because the engine accrues no new trades/candles. This is the honest-pause
  mechanism; no client-side freeze hack is needed.
- The chart (`PriceChart`) polls `/history` on a 1 s cadence; while paused the engine appends no new
  candles, so the chart freezes naturally (it must continue to read `/history` verbatim, never invent
  candles).
- Assumption: the simplest correct feeder freeze is a per-engine paused flag the feeder checks before
  `process_event` (skip-and-wait while paused), not a task cancel/recreate — this preserves the alive
  task, the open live socket, and replay position, and avoids any catch-up fabrication.
