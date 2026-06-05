# Goal Iteration 7 — Render-verify the prediction chart (J-17/J-18) + build honest Pause/Resume (J-19)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich
- **Iteration:** 7
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-17, J-18, J-19
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-15, J-16
- **Anti-goal reminders:**
  - **Honest pause.** Pause MUST freeze the displayed state without tearing the session down or fabricating data; while paused the UI MUST read as **paused**, never as live. On resume, **live** MUST rejoin current real data — the engine MUST NOT synthesize trades to "catch up" the gap. *(critical)*
  - **One focused chart, computed once.** OHLC bars and tape-state markers MUST be computed once in the engine history buffer and read identically by `…/history` and the chart; the UI MUST NOT recompute side, state, or price from raw data. An empty window MUST yield an **empty** chart, not invented candles. The chart is analysis-only — it MUST NOT add any order/execution affordance. *(critical)*
  - **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the tape. *(critical)*
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*
  - **No fabricated data.** The system MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. (For pause: no fabricated backfill on resume; while paused the status is `paused`, never a fabricated `live`.) *(critical)*
  - **No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code. (Any stale-gap / pause-related timeout MUST live in config.)
  - **Provider-agnostic engine.** The engine and API MUST depend only on the provider interface (TradeEvent / QuoteEvent / BookLevelEvent); swapping the simulator for a real feed MUST NOT require engine or API changes. Pause is a feeder/engine concern and MUST NOT leak any vendor specifics.
  - **Stay in scope.** No scanner/screener, no news/sentiment, no fundamentals, no indicator/pattern charting, no portfolio/position management. The one allowed chart adds **no** indicators, studies, or drawing tools. *(critical)*

## GOAL

Capture the missing rendered-chart browser evidence so J-17/J-18 move from `partial` to `passing`, and add an honest Pause/Resume control that freezes a watched session (cockpit + chart + counters + tape state) without teardown — reading the engine's canonical paused state — so J-19 passes.

## BACKGROUND

The iter-6 evaluator returned **CONTINUE** with an explicit two-part recommendation for iter-7 at **full** depth: (1) close the J-17/J-18 render-verification gap by running browser-qa against a **clean isolated frontend** and capturing real screenshots of the populated candlestick canvas, and (2) build J-19 (pause/resume; Data Contract rows 6 `paused` + 11 already pre-registered; the honest-pause anti-goal is load-bearing). The chart backend is already independently proven (159 tests, `/history?bar=` correct for all five sim scenarios + over the wire 404/422/empty, SSOT, isolated production build serves clean) — only the pixel-level render was never confirmed because the shared `:3650` `.next` was corrupted at QA time (the iter-3/iter-6 failure mode). J-20 (local-time picker) is deliberately deferred to its own next slice (it likely needs a blueprint touch for the timezone surface and is independent of this work). This is **full** depth because the prior evaluator mandated it, J-19 crosses backend+frontend and the watch-lifecycle data model, and the honest-pause anti-goal needs real tests beyond a browser smoke.

**Decomposer pre-checks performed for this spec (evidence the plan is grounded):**
- `apps/frontend/components/PriceChart.tsx` and the bar-size selector already exist; no chart code change is needed for J-17/J-18 — only a clean-build browser render.
- **A CDP-capable browser client IS now available in this environment**: Python `playwright` imports and drives `/usr/bin/google-chrome` (verified: it rendered text and wrote a 6.7 KB screenshot). The iter-6 "no CDP browser client" blocker no longer applies, so the render gap is closable this iteration — provided the run uses an **isolated** frontend dist, never the shared `:3650`/`.next`.
- Backend pause surface: `apps/backend/app/watch_manager.py` owns feeders as asyncio tasks in `self._tasks[ticker]`; `stop()` does `task.cancel()` + `set_stream_status("closed")` + teardown. There are three feeders — `_feed` / `_feed_paced` (sync providers: sim + historical) and `_feed_live` (async live). **Pause must be a NEW, distinct freeze that does NOT cancel the task and does NOT tear down.** The engine snapshot (`apps/backend/app/engine/snapshot.py:29`) currently has only `stream_status` with enum `connecting|live|stale|closed` and **no `paused` field** — both need additive extension (add a `paused` boolean; add `paused` to the `stream_status` value set). The watch routes live in `apps/backend/app/main.py` (not `api.py`).

**Lessons applied (from `runs/goal-session-i_will_be_super_rich/state/lessons.md`):**
- **iter-6 / iter-3 (load-bearing for J-17/J-18 this iteration):** a purely-visual journey cannot be scored from backend tests + code inspection alone, and the shared harness `.next` on `:3650` has corrupted browser-qa twice. The browser-qa run for this iteration MUST rebuild or fully bypass the shared `.next` (`NEXT_DIST_DIR` set to an isolated dir + `NEXT_PUBLIC_API_URL` → an isolated backend) and capture a **real rendered screenshot of the populated chart** for each required state.
- **iter-5:** the `ui-test-results.md` can be a stale pre-build verify-only re-baseline (old test count, pre-change screenshot). Treat a "PASS_SURFACE" / "browser automation did not complete" entry as `partial`, NOT a pass; the evidence for a visual journey is the rendered screenshot, not a surface claim.
- **iter-0 (watch lifecycle):** only explicit Stop tears a watch down; a Watch / source-switch already implicitly stops the prior watch (now handled in `watch_with_provider`/`watch_with_async_provider`). **Pause is deliberately the opposite of stop** — it must NOT cancel the feeder task or close the live socket; it freezes feeding while keeping the engine, snapshot, history buffer, and (for live) the socket alive.
- **iter-4 (live-socket teardown):** do NOT call the SDK's `unsubscribe_*()` from the generator `finally` (it deadlocks on the event-loop thread). Pause must NOT introduce any such call — pausing live means stop *consuming/applying* events (and let the status read `paused`), not unsubscribing or closing the socket.

## IN SCOPE

### Backend
- [ ] Add a canonical **`paused`** boolean to the engine snapshot (`engine/snapshot.py`), owned by the engine/feeder and computed once (Data Contract **row 11**, pre-registered). Update the `stream_status` value set/docstring to include **`paused`** (Data Contract **row 6** already lists `paused`).
- [ ] `POST /watch/{ticker}/pause` and `POST /watch/{ticker}/resume` in `apps/backend/app/main.py` — freeze / continue the feeder **without** tearing the instance down. The engine, its latest snapshot, and the history buffer survive a pause; the live socket (if any) stays open. Return the updated snapshot/paused state. `404` if the ticker is not watched.
- [ ] Extend `WatchManager` with a feeder-level **pause/resume** that is distinct from `stop()`: it sets the engine paused + `stream_status="paused"` and makes the feeder stop applying events while paused (it MUST NOT `task.cancel()`, MUST NOT close the live socket, MUST NOT synthesize any catch-up trades on resume). For the paced sim/historical feeders, replay resumes from where it left off; for the live feeder, resume rejoins current real data (no fabricated backfill). On resume, restore the prior pre-pause `stream_status` (live/connecting/stale) — never fabricate `live`.
- [ ] Keep `stop()` (`DELETE /watch/{ticker}`) behavior unchanged: it still fully cancels the feeder + tears the instance down (pause is additive, not a replacement).
- [ ] All thresholds/timeouts introduced (if any) live in `app/config.py` — no inline literals (no-magic-numbers anti-goal).

### Frontend
- [ ] Add **Pause / Resume** controls to the watch-control area beside **Stop** in the app shell (the controls live in `apps/frontend/components/TopBar.tsx` / `page.tsx` — match the existing control placement and dark-surface styling). Show **Pause** when streaming and **Resume** when paused.
- [ ] Render a **PAUSED** indicator driven by the engine's canonical paused/`stream_status` value read off the snapshot / WS stream (no UI-side guess). The stream-status dot reads `paused` (amber, consistent with the existing status-dot semantics).
- [ ] When paused, the cockpit (quote / recent trades / features / tape state) and the price chart **freeze** (stop updating) — because the engine stops emitting new snapshots while paused; the frontend must NOT clear or tear down the cockpit, and must NOT fabricate a `live` reading.
- [ ] Wire the Pause/Resume buttons to `POST /watch/{ticker}/pause` and `…/resume` via `apps/frontend/lib/api.ts`; read paused state from the snapshot/stream — do not compute it client-side.

### New user-facing capability
The user can **Pause** a live/replaying watch — freezing the recent trades, chart, feature readouts, and tape state in place with a visible **PAUSED** indicator — and later **Resume** to continue without having lost the session, or **Stop** to tear it down. Separately, the already-built price-chart prediction view (candlesticks + tape-state markers) is now confirmed to actually render for the user.

### New information displayed
- A **PAUSED** indicator / status-dot state when a watch is frozen.
- (No new chart data — J-17/J-18 render the already-served `/history` OHLC + markers; this iteration adds the missing *visual confirmation*, not new data.)

### New user actions
- **Pause** button (freeze the current watch).
- **Resume** button (continue a paused watch).

### UI surface changes
- The watch-control cluster on `/` gains **Pause / Resume** beside **Stop**, plus a **PAUSED** state on the existing stream-status indicator. No new page, no new route.

### Product surface delta
The cockpit becomes controllable mid-watch: a user can freeze the read to inspect the chart/markers at a moment in time and then continue — without losing the session or seeing fabricated data — and the prediction chart that was shipped last iteration is now verifiably visible.

### Blueprint conformance
All surfaces live on the existing **`/` — Watch (the tape cockpit) — HOME**. The blueprint already places **Pause / Resume + the PAUSED indicator** in the persistent app-shell watch controls and assigns **J-19 → "Pause/Resume controls + PAUSED indicator"**, and assigns **J-17/J-18 → "price-chart pane above the cockpit (sim / historical)"**. No new route, no new nav section, no nav-skeleton change ⇒ **no re-approval requested**.

### Data-contract additions
**None.** This iteration *implements* values already registered in `blueprint.md`: **row 11 — Paused state (boolean)** (canonical owner: engine/feeder; served on `GET /tape/{ticker}/summary`, set via `POST /watch/{ticker}/pause|resume`; re-exposed by `WS /stream`), and the **`paused`** value of the **row 6 stream-status** (canonical owner: engine/feeder). J-17/J-18 read the already-registered **row 10 — Price history OHLC bars + markers** via `GET /tape/{ticker}/history?bar=` (no new value, no second computation). No new Data Contract row is added; no blueprint edit is required.

## OUT OF SCOPE

- **J-20 (local-time historical-window picker + US-session quick-picks).** Deferred to its own next slice — it is independent of pause/resume and likely needs a blueprint touch for the timezone surface (row 12). Do NOT build the local-time picker or quick-picks this iteration.
- Any change to the chart's data/computation (the engine history buffer, `serialize_history`, or `/history`) — the backend is already proven; this iteration only render-verifies it. Do not re-bin candles, re-infer side, or re-place markers anywhere.
- Auto-reconnect of a dropped live socket, Level 2 / `BookLevelEvent`, the predictive-edge replay harness, persistence — all explicitly *later* nice-to-haves.
- Any order/execution/broker affordance anywhere (hard anti-goal).
- Changing classifier thresholds, feature windows, or the spread gate (would risk regressing J-01–J-16).
- The advisory iter-6 coherence WARN (frontend bar-size constant mirroring backend config) — optional tidy only; do not let it expand scope.

## DEFINITION OF DONE

- [ ] **J-17 passes** via browser-qa with **real rendered screenshots** captured against a CLEAN isolated frontend build (`NEXT_DIST_DIR` isolated dir + `NEXT_PUBLIC_API_URL` → an isolated backend; never the shared `:3650`/`.next`): SIM-BUYER candlesticks render with an **emerald** buyer_control marker and rising candles; SIM-SELLER shows a **rose** marker / falling candles; SIM-BIDABS and SIM-ASKABS show **amber** absorption markers with price held; the **10 → 30 → 60 s** bar-size selector re-renders the candles; the chart is **hidden in Live** mode.
- [ ] **J-18 surface passes**: candlesticks reflect real replayed prices and the bars match the engine-served `…/history` at each bar size (real-fetch correctness already stands on the backend test + the evaluator's live `/history` proof; with credentials present the real-historical render is captured, otherwise the surface/bar-match is confirmed and the credentialed half noted).
- [ ] **J-19 passes** via browser-qa on SIM-BUYER: after Watch + populate, clicking **Pause** freezes the recent trades, chart, features, and tape state, shows a **PAUSED** indicator, and does **not** clear/tear down the session; clicking **Resume** continues the stream from where it left off; clicking **Stop** still closes the stream and returns the cockpit to idle.
- [ ] Required-still-passing journeys **J-01–J-16** remain green (engine/classifier/feature/aggressor/chart-data paths unchanged; pause is additive and must not alter the unpaused stream).
- [ ] **No anti-goal violation** introduced — especially **honest pause** (paused reads `paused`, never `live`; no fabricated backfill on resume; live resume rejoins current real data), **one focused chart computed once** (no UI recompute of price/side/state; chart still reads `/history` verbatim), **no execution path**, and **single source of truth** (paused state owned once by the engine/feeder; UI reads it).
- [ ] Unit/integration tests pass with **no regressions** (current floor: 159 passed / 1 skipped).
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich-iter-7-dev.md`.

## TESTING REQUIREMENTS

- **Browser (must be captured as real rendered screenshots on a clean isolated build — not surface claims):**
  - **J-17** — Watch SIM-BUYER → candlesticks visible + **emerald** buyer_control marker + rising candles; Watch SIM-SELLER → **rose** marker / falling candles; Watch SIM-BIDABS and SIM-ASKABS → **amber** markers with price held; toggle bar size **10 → 30 → 60 s** → candles re-render; select **Live** mode → chart hidden.
  - **J-18** — Historical replay of a real symbol → candlesticks reflect replayed prices and the on-screen bars match `…/history` at each bar size (credentialed render if keys present; otherwise confirm the surface + bar-match and note the credentialed half).
  - **J-19** — Watch SIM-BUYER, let it populate; **Pause** → cockpit + chart + feature counters + tape state freeze, **PAUSED** indicator shows, session NOT cleared; **Resume** → stream continues; **Stop** → cockpit returns to idle, stream closed.
  - Prerequisite: the browser run MUST rebuild or fully bypass the shared `:3650` `.next` first (it has corrupted browser-qa twice — iter-3 and iter-6). If, despite Playwright + system Chrome being available, the populated chart still cannot be captured, that is a blocker to record explicitly — NOT a silent skip and NOT a surface "pass".
- **Unit/integration (assert exact values + a failure path):**
  - Pause sets the engine `paused=true` and `stream_status="paused"`; the feeder task is **still alive** (NOT cancelled) and the engine instance + history buffer **survive** (snapshot still readable, `…/state` not 404). Resume restores the prior `stream_status` and clears `paused`.
  - **Honest pause (load-bearing):** while paused, no new trades are applied and the snapshot never reads `live`; on resume the recent-trades/feature counts do **not** jump by a fabricated backfill (sim/historical resume continues the stream; live resume rejoins current data with no synthesized catch-up). Prefer a deterministic hermetic test asserting exact pre/post-pause counts and statuses (the standard already accepted for J-14/J-15).
  - `stop()` after a pause still fully tears down (feeder cancelled, `…/state` → 404) — pause did not break teardown.
  - Error path: `POST /watch/{unknown}/pause` and `…/resume` on a not-watched ticker → **404** (no engine fabricated).
  - Confirm `/history` and the chart-data path are byte-identical to iter-6 (no regression to row 10).
- **Error cases that must be rejected/handled:** pause/resume on an unknown or not-watched ticker → 404; resume of a not-paused watch and pause of an already-paused watch handled idempotently/explicitly (no crash, no duplicate feeder, no second status owner).

## NOTES

- **Honest-pause is the load-bearing anti-goal of this iteration** (it is marked *critical* in `docs/goal.md`). The single failure that would sink J-19 is a pause that fabricates a `live` reading or a resume that synthesizes catch-up trades — the test plan above targets exactly that.
- **Single owner:** there is already exactly one `stream_status` writer (the feeder, per the iter-4/iter-5 SSOT work). Pause MUST reuse that single owner — do not introduce a second status/paused writer in the API or UI (that is precisely the drift the coherence-auditor fails).
- **Why the render gap is closable now (not in iter-6):** iter-6 recorded "no CDP-capable browser client"; this decomposer verified Playwright drives `/usr/bin/google-chrome` and screenshots successfully. The remaining risk is purely the shared-`.next` corruption, which the dev's `NEXT_DIST_DIR` guard already exists to bypass — the browser run must actually use it.
- **Evaluator guidance:** do not mark GOAL_ACHIEVED on this iteration unless J-17/J-18 have real rendered-chart screenshots AND J-19 passes; J-20 remains to-build and is excluded here, so the goal is not yet complete after this iteration. A `browser-qa SKIPPED` / "PASS_SURFACE" for a visual journey is `partial`, not a pass (iter-3/iter-5/iter-6 lesson).
- Blueprint is already current for this work (rows 6 `paused`, 10, 11 pre-registered; Pause/Resume + PAUSED + chart pane already in the IA). No `blueprint.md` edit and no `blueprint.reapproval-requested` file are needed this iteration.
