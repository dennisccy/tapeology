# Goal Iteration 7 — Stop watching a ticker (J-09): DELETE /watch + Stop control + return-to-idle

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_rich
- **Iteration:** 7
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-09
- **Required-still-passing journeys:** J-01, J-02, J-08
- **Anti-goal reminders:**
  - **No fabricated data.** On a provider gap/failure the system MUST surface an explicit stale/no-data state and MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. *(critical)* — for J-09 this means: after Stop, the idle cockpit shows NO stale/fabricated numbers, and a read of the stopped ticker returns an explicit error, never a synthesized snapshot.
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*
  - **Provider-agnostic engine.** The engine and API MUST depend only on the provider interface; swapping the simulator for a real feed MUST NOT require engine or API changes. — teardown is a `WatchManager`/API concern, not a provider concern.
  - **Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine MUST produce identical features, state, and confidence; classification MUST NOT depend on wall-clock time or randomness. — stop/re-watch must be covered by deterministic unit tests.
  - **No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config. — J-09 introduces NO new numeric threshold (none needed); do not add inline literals.

## GOAL

A user watching a ticker can press a **Stop** control that issues `DELETE /watch/{ticker}`; the live stream closes, the cockpit returns to the idle/empty state with no further updates and no stale numbers, and re-watching the same ticker starts a fresh read — completing the ninth and final Must-have journey.

## BACKGROUND

Eight of nine Must-have journeys are green; only **J-09 (Stop watching)** remains, and it was explicitly out-of-scope through iter-6 (the `apps/frontend` diff has been empty since iter-1). The iter-6 evaluator recommends advancing to J-09 at **full** depth — it is the first real frontend change since iter-1 (a net-new user-facing control) and it closes out the MVP, so the closure gate matters.

**Verified by direct code inspection this iteration (per lesson iter-4 — do not trust forward-carried "already built" notes):**
- `apps/backend/app/main.py` has **no `DELETE /watch/{ticker}` route** (only `/health`, `POST /watch`, the four `GET /tape/{ticker}/…` reads, and `WS /tape/{ticker}/stream`). It must be built.
- `apps/backend/app/watch_manager.py` `WatchManager` has **no per-ticker stop** — only `watch()` (which returns the *existing* engine when present), `get()`, `_feed()` (sets `stream_status="closed"` on natural exhaustion or `CancelledError`), and `shutdown()` (cancels *all* tasks at app exit). A `stop(ticker)` method must be added.
- `apps/frontend/components/TopBar.tsx` has the Watch form + status dot but **no Stop button**. `apps/frontend/app/page.tsx` renders `{ticker ? <Cockpit/> : <IdleState/>}`, and `apps/frontend/lib/useTapeStream.ts` closes the WS via effect cleanup when `ticker` becomes `null` — so the idle return is driven by `setTicker(null)`. `apps/frontend/lib/api.ts` has `watchTicker` but no `stopTicker`.

This is **declared IA**, not new surface: the blueprint app shell already lists a "**Stop** control (`DELETE /watch/{ticker}`)" and an "Idle/empty state — before a ticker is watched, and after Stop", and `DELETE /watch/{ticker}` is in `docs/goal.md`'s Phase-1 API surface and on the "Watched-scenario label + watch/stream status" Data-Contract row. So there is **no nav-skeleton change and no new Data-Contract value** — this iteration *realizes* the already-registered DELETE half of an existing row.

**Teardown-observation gotcha (lessons iter-5 + iter-6) — designed around up front:** the live→idle teardown is only observable on a still-live stream, but bounded sim streams exhaust quickly and `watch()` returns the *existing closed* engine on re-watch, AND the harness permission layer **blocks a backend restart** (browser-qa was denied in iter-6). This iteration's own mechanism dissolves the trap: `DELETE /watch` tears down a *live* engine directly (no restart needed), and `stop()` **removing** the engine from the registry is exactly what makes a subsequent `watch()` build a fresh engine (the "re-watch = fresh read" acceptance) instead of returning the exhausted closed one. The browser test arrangement and deterministic fallbacks are spelled out in TESTING REQUIREMENTS.

## IN SCOPE

### Backend
- [ ] Add `WatchManager.stop(ticker: str) -> bool` to `apps/backend/app/watch_manager.py`:
  - Cancel the per-ticker feeder task (if present) and remove it from `self._tasks`.
  - Set the engine's `stream_status` to `"closed"` (so any already-connected WS that captured the engine reference, and any in-flight `/summary` read, reports the truthful closed status).
  - Remove the engine from `self._engines` (REQUIRED — this is what makes a later `watch()` build a fresh engine, satisfying "re-watch starts a fresh read" and sidestepping the exhausted-engine re-watch trap).
  - Return `True` if the ticker was being watched, `False` otherwise (idempotent; no exception on stop-of-not-watched).
  - Optionally refactor `shutdown()` to reuse `stop()` for each ticker — only if it stays trivial; otherwise leave `shutdown()` as is. No behavior change to `shutdown()`.
- [ ] Add `DELETE /watch/{ticker}` route to `apps/backend/app/main.py`:
  - Async route calling `manager.stop(ticker)`.
  - On `True`: return `{"ticker": ticker, "status": "stopped"}` (HTTP 200).
  - On `False` (not currently watched): raise `HTTPException(status_code=404, …)` consistent with the existing `_engine_or_404` convention — an honest "not watched", never a fabricated success.
- [ ] Confirm post-stop read semantics hold with NO new code: after `stop()`, `GET /tape/{ticker}/state|features|events|summary` return **404** (engine removed) and a fresh `WS /tape/{ticker}/stream` connect closes with **4404** (`manager.get(ticker)` is `None`). These are the deterministic, timing-independent evidence that "the stream closed / the ticker is no longer watched".

### Frontend
- [ ] Add `stopTicker(ticker: string)` to `apps/frontend/lib/api.ts`: `DELETE ${API_BASE}/watch/{ticker}`; return a small `{ ok: boolean; error?: string }` result (mirror `watchTicker`'s shape and its try/catch + "Backend unreachable" handling). A 404 is acceptable as effectively-stopped (the ticker is not watched either way).
- [ ] Add a **Stop** button to `apps/frontend/components/TopBar.tsx`, rendered only when `watched` is set (next to the watched-ticker label). Wire it to a new `onStop: () => void` prop. Use a **static** `className` for its colors (e.g. a slate/rose ghost button) — do NOT build the class string at runtime (lessons iter-2/iter-3: runtime-built Tailwind classes get dropped from the bundle; the static class is scanned, and `bg-rose-500`/rose tokens are already in the bundle).
- [ ] Add a `handleStop` handler in `apps/frontend/app/page.tsx`: call `stopTicker(ticker)`, then `setTicker(null)` and clear any error. `setTicker(null)` returns the body to `<IdleState/>` AND triggers `useTapeStream`'s effect cleanup, which **closes the WS client-side** — this is the mechanism for "no further updates" and must NOT rely on the server closing the socket (the WS handler holds a captured engine reference and will keep pushing closed-status frames until the client disconnects). Pass `onStop={handleStop}` to `TopBar`.

### New user-facing capability
The user can stop watching the current ticker from the cockpit and return to a clean idle screen, then start a fresh watch — the full watch lifecycle (start → read → stop → re-start) is now complete in the UI.

### New information displayed
No new *value*. A new **Stop** control appears in the top bar while a ticker is watched; after Stop the existing idle/empty state ("No ticker watched") is shown (no stale numbers).

### New user actions
- **Stop** button in the top bar (issues `DELETE /watch/{ticker}`).

### UI surface changes
`TopBar` gains a Stop button (visible only while watching). No new page, panel, or route — everything stays on `/`.

### Product surface delta
The cockpit gains lifecycle completeness: a watch can be ended deliberately and cleanly, and the screen honestly empties instead of showing a frozen last frame — reinforcing the "no fabricated/stale data" principle at the UI level.

### Blueprint conformance
All work lives on the existing **`/` — Watch (the tape cockpit) — HOME** under the already-declared persistent **app shell** (the Stop control and the post-Stop idle state are already named in `blueprint.md`'s Information Architecture). **No nav-skeleton change → no re-approval required.** J-09's canonical home (Stop control + idle state) is already mapped in the blueprint's "Canonical home per journey" line.

### Data-contract additions
**None — no new displayed value.** This iteration realizes the already-registered `DELETE /watch/{ticker}` response on the existing **"Watched-scenario label + watch/stream status"** row (canonical owner `WatchManager`; canonical serving endpoint `GET /tape/{ticker}/summary` (+ `POST`/`DELETE /watch/{ticker}` responses)). An additive one-line realization note is added to the blueprint's realization log (same row, same owner — no new row, no second producer/endpoint).

## OUT OF SCOPE

- **Server-initiated WS closing / connection tracking.** Do NOT build a registry of live WebSocket connections to push a close on DELETE. The client-side WS close (driven by `setTicker(null)`) is sufficient for "no further updates"; server connection-tracking is extra complexity beyond J-09.
- **Multi-ticker / watchlist teardown UI.** Single-ticker only (anti-goal: no watchlist grid). Stop acts on the one watched ticker.
- **New thresholds/config.** J-09 needs none; introduce no config values.
- **Any classifier / feature / provider change.** `classifier.py`, `features.py`, `config.py`, and `providers/` must stay byte-untouched (teardown is purely a `WatchManager` + API + frontend-control concern). A diff touching them is a red flag.
- **Confirmation dialogs, animations, keyboard shortcuts** for Stop — a plain button is enough.

## DEFINITION OF DONE

- [ ] **J-09 passes via browser-qa-agent**: from a fresh watch of a sim ticker, pressing **Stop** returns the cockpit to the idle/empty state ("No ticker watched") with no further updates; and re-watching the same ticker starts a fresh read (cockpit repopulates from cold). Evidence screenshots: cockpit-live → post-Stop-idle → re-watch-fresh.
- [ ] **Deterministic teardown evidence captured** (timing-independent, not dependent on catching the live window): after `DELETE /watch/{ticker}`, `GET /tape/{ticker}/state` returns 404 and a fresh `WS …/stream` connect is rejected (4404); a re-`POST /watch/{ticker}` succeeds and yields a fresh (cold-start) snapshot.
- [ ] **Required-still-passing journeys remain green:** J-01 (watch → live cockpit renders), J-02 (re-watched `SIM-BUYER` re-resolves to `buyer_control` with positive `buy_price_impact` — proves the fresh read), J-08 (UI ≡ REST on the active read). The other currently-green journeys (J-03, J-04, J-05, J-06, J-07) must not regress.
- [ ] **No anti-goal violation introduced** — in particular: idle cockpit shows no stale/fabricated numbers; stopped-ticker reads return explicit 404 (no synthesized snapshot); no recomputation added in the API or frontend; `classifier.py`/`features.py`/`config.py`/`providers/` byte-untouched.
- [ ] **Unit tests pass; no regressions** — the existing 61 backend tests stay green and new `stop`/DELETE tests are added (see TESTING REQUIREMENTS).
- [ ] **Frontend build passes** (`cd apps/frontend && npm run build`).
- [ ] **Dev handoff written** at `docs/handoffs/goal-i_will_be_rich-iter-7-dev.md`.

## TESTING REQUIREMENTS

- **Browser (browser-qa-agent) — J-09, with the teardown arrangement built in up front:**
  1. Watch a **fresh** sim ticker from cold (`SIM-BUYER` recommended) so the stream is live and panels populate; confirm the status dot reads **live** and the cockpit is populated.
  2. Press **Stop** **promptly, while the stream is still live**, to demonstrate the live→idle teardown driven by the action (not by natural exhaustion). Assert: body shows `<IdleState/>` ("No ticker watched"), the dot returns to **idle**, and no further snapshot updates arrive. *(If the bounded stream happens to exhaust before the click, the idle-return + re-watch-fresh assertions still hold — the Stop handler drives idle regardless of server stream state — but prefer catching it live.)*
  3. **Re-watch the same ticker**: assert the cockpit repopulates from a cold start (connecting → live → values), i.e. a fresh read, not a frozen/closed leftover.
  4. To make the "still live" window reliably catchable, the harness MAY widen delivery pacing for this run via `TAPEOLOGY_FEED_PACE` (e.g. `0.12`) — this is **delivery pacing only and does not change classification determinism** (the engine computes from logical timestamps; see `watch_manager.py`). This is an optional convenience, not required for the journey to pass.
  5. Color note: the Stop button must use a **static** Tailwind class; verify its color via the served bundle if asserted (lessons iter-2/iter-3) — but color is not load-bearing for J-09 acceptance.
- **Unit/integration (pytest, `apps/backend/tests/`):**
  - `WatchManager.stop()`: stopping a watched ticker cancels its feeder task, sets the engine `stream_status` to `"closed"`, and **removes** it from `_engines` (a subsequent `get()` returns `None`); `stop()` of a not-watched ticker returns `False` and raises nothing (idempotent).
  - **Re-watch is a fresh engine:** `watch(t)` → `stop(t)` → `watch(t)` returns a **different** engine instance than the first (the registry was cleared), and the fresh engine starts cold (no carried-over event count / state).
  - `DELETE /watch/{ticker}` route (in `test_api.py`): a watched ticker → 200 `{"status":"stopped"}` and afterwards `GET …/state` → 404 and a fresh `WS …/stream` connect is rejected (4404); a not-watched ticker → 404.
  - Determinism guard: `watch → stop → re-watch` on the same seeded ticker yields an identical fresh cold-start snapshot to a first-ever watch of that ticker (no state leakage across the stop boundary).
- **Error cases:** `DELETE /watch/{ticker}` on a ticker that is not currently watched → 404 (honest, no fabricated success). Reads of a stopped ticker → 404 (no synthesized snapshot). `stopTicker` on the frontend treats a 404 as effectively-stopped (still returns the UI to idle).

## NOTES

- **Lesson iter-4 applied:** the `DELETE /watch/{ticker}` endpoint and `WatchManager.stop` were confirmed **absent** by reading `main.py` and `watch_manager.py` directly — they are net-new this iteration; do not size this as a thin verify pass.
- **Lessons iter-5 + iter-6 applied (teardown observability):** the live→idle transition needs a still-live stream; bounded streams exhaust fast and a backend restart is permission-blocked. This spec dissolves that by (a) using the new `DELETE /watch` to tear down a *live* engine (no restart) and (b) having `stop()` *remove* the engine so re-watch is genuinely fresh — and it backstops the timing-sensitive browser observation with deterministic REST/WS 404/4404 + unit assertions so the journey does not hinge on catching the live window.
- **Lessons iter-2 + iter-3 applied (Tailwind):** the Stop button uses a static color class so it is never dropped from the bundle; no runtime-built class strings.
- **Why full depth:** first net-new frontend control since iter-1 + net-new backend endpoint and manager method, crossing backend↔frontend, and it closes the nine-journey MVP — so the full pipeline (ui-impact → ui-test-design → browser-qa → ux-regression → closure) and the closure gate are warranted. The iter-6 evaluator explicitly recommended full.
- **After this iteration:** all nine Must-have journeys should be green and the MVP taxonomy + watch lifecycle complete — the next evaluation is expected to assess **GOAL_ACHIEVED**, subject to coherence remaining PASS and no regression.
