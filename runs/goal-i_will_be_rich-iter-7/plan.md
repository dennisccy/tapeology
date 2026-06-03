# goal-i_will_be_rich-iter-7 Execution Plan

Closes the **ninth and final Must-have journey — J-09 (Stop watching)** and completes the
watch lifecycle (start → read → **stop** → re-start) in the UI. Net-new across the stack:
a `DELETE /watch/{ticker}` endpoint, a `WatchManager.stop()` method, and the first real
frontend control since iter-1 (a **Stop** button). Confirmed net-new by direct inspection
this iteration: `main.py` has no DELETE route, `WatchManager` has no `stop()`, `TopBar.tsx`
has no Stop button, and `api.ts` has no `stopTicker` — zero existing `stop`/`DELETE`/`stopTicker`
references in `app/`, `lib/`, or `components/`.

## What to Build

**Backend**
- **`WatchManager.stop(ticker: str) -> bool`** in `apps/backend/app/watch_manager.py`:
  - Cancel the per-ticker feeder task if present and pop it from `self._tasks`.
  - Set the engine's stream status to `"closed"` via the existing `engine.set_stream_status("closed")`
    (so any already-connected WS holding the engine reference, and any in-flight `/summary` read,
    report the truthful closed status).
  - **Remove** the engine from `self._engines` (REQUIRED — this is what makes a later `watch()`
    build a *fresh* engine, satisfying "re-watch starts a fresh read" and sidestepping the
    exhausted-engine re-watch trap where `watch()` returns the existing closed engine).
  - Return `True` if the ticker was being watched, `False` otherwise — idempotent, raises nothing
    on stop-of-not-watched.
  - May refactor `shutdown()` to reuse `stop()` per ticker **only if it stays trivial**; otherwise
    leave `shutdown()` untouched. No behavior change to `shutdown()`.
- **`DELETE /watch/{ticker}` route** in `apps/backend/app/main.py`:
  - Async route calling `manager.stop(ticker)`.
  - `True` → HTTP 200 `{"ticker": ticker, "status": "stopped"}`.
  - `False` → `HTTPException(status_code=404, …)` matching the existing `_engine_or_404` convention
    (honest "not watched", never a fabricated success).
- **No new code** for post-stop reads — confirm the existing semantics hold: after `stop()`,
  `GET /tape/{ticker}/state|features|events|summary` → **404** (engine removed) and a fresh
  `WS /tape/{ticker}/stream` connect closes **4404** (`manager.get()` is `None`). This is the
  timing-independent teardown evidence.

**Frontend**
- **`stopTicker(ticker: string)`** in `apps/frontend/lib/api.ts`: `DELETE ${API_BASE}/watch/{ticker}`,
  returning `{ ok: boolean; error?: string }` — mirror `watchTicker`'s try/catch + "Backend
  unreachable" handling. A **404 counts as effectively-stopped** (the ticker is not watched either way).
- **Stop button** in `apps/frontend/components/TopBar.tsx`: rendered only when `watched` is set
  (next to the watched-ticker label), wired to a new `onStop: () => void` prop. Use a **static**
  Tailwind `className` for its colors (slate/rose ghost button) — do **NOT** build the class string
  at runtime (lessons iter-2/iter-3: runtime-built Tailwind classes are dropped from the bundle;
  `bg-rose-500`/rose tokens are already scanned into the bundle via `TopBar`'s existing dot/error styles).
- **`handleStop`** in `apps/frontend/app/page.tsx`: call `stopTicker(ticker)`, then `setTicker(null)`
  and clear any error. `setTicker(null)` returns the body to `<IdleState/>` **and** triggers
  `useTapeStream`'s effect cleanup, which **closes the WS client-side** — this is the mechanism for
  "no further updates"; it must NOT rely on the server closing the socket. Pass `onStop={handleStop}`
  to `TopBar`.

### Explicitly NOT built (red-flag guard)
- **No server-initiated WS close / connection registry.** The client-side WS close (driven by
  `setTicker(null)`) is sufficient for "no further updates"; server connection-tracking is out of scope.
- **`classifier.py`, `features.py`, `config.py`, and `providers/` stay byte-untouched.** Teardown is a
  `WatchManager` + API + frontend-control concern. A diff touching any of them is a red flag — surface it
  loudly, do not silently patch.
- **No new thresholds/config, no new Data-Contract value, no nav change.** J-09 needs none. No
  confirmation dialog, animation, or keyboard shortcut for Stop — a plain button is enough.

## Agents Required

- **developer: yes** — backend (`WatchManager.stop()` + `DELETE /watch/{ticker}` + tests) and
  frontend (`stopTicker` + Stop button + `handleStop` wiring).
- **backend-data: yes** — `WatchManager.stop()`, the DELETE route, and the backend/integration tests.
- **frontend-ux: yes** — first real frontend code change since iter-1 (net-new Stop control + handler).

## Frontend Present
Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/watch_manager.py` — add `stop(ticker) -> bool` (cancel feeder, set closed, remove engine).
- `apps/backend/app/main.py` — add `DELETE /watch/{ticker}` route (200 stopped / 404 not-watched).
- `apps/backend/tests/test_api.py` — `DELETE /watch/{ticker}` route tests (200 then 404 reads / 4404 WS; not-watched → 404); may also house the `WatchManager.stop()` + re-watch-fresh unit tests, or add a new `apps/backend/tests/test_watch_manager.py` (developer's choice — keep with existing conventions).
- `apps/frontend/lib/api.ts` — add `stopTicker(ticker)` (DELETE; `{ ok, error? }`; 404 = effectively-stopped).
- `apps/frontend/components/TopBar.tsx` — add Stop button (only when `watched`) + `onStop` prop; static rose/slate class.
- `apps/frontend/app/page.tsx` — add `handleStop` (stopTicker → `setTicker(null)` → clear error); pass `onStop`.

## UI Evolution (Frontend Present: yes)
- **New user-facing capability:** the user can deliberately stop watching the current ticker from the
  cockpit, returning to a clean idle screen, then start a fresh watch — the full watch lifecycle
  (start → read → stop → re-start) is now complete in the UI.
- **New information displayed:** *no new value.* A **Stop** control appears in the top bar while a
  ticker is watched; after Stop the existing idle/empty state ("No ticker watched") is shown — no
  stale numbers, no frozen last frame.
- **New user actions:** **Stop** button in the top bar (issues `DELETE /watch/{ticker}`).
- **UI surface changes:** `TopBar` gains a Stop button, visible only while watching. No new page,
  panel, or route — everything stays on `/`.
- **Navigation changes:** none. The Stop control and the post-Stop idle state are already named in
  `blueprint.md`'s Information Architecture; no nav-skeleton change → no re-approval required.

## Visual Requirements (Frontend Present: yes)
- **Component patterns:** plain `<button>` matching the existing hand-built TopBar Watch-button idiom
  (no component library in this project); place it next to the watched-ticker label inside the existing
  `{watched && …}` block.
- **Layout:** in the persistent top bar; Stop sits beside the "Watching <TICKER>" label.
- **Key visual effects:** restrained slate/rose **ghost** button via a **static** Tailwind class
  (e.g. rose text/border on a transparent or slate surface). Color semantics: rose = stop / sell-side,
  consistent with the design system. Static class only — never runtime-concatenated.
- **States to handle:** button only rendered when `watched` is set (absent in idle); on click → cockpit
  empties to `<IdleState/>` with no stale numbers and the status dot returns to **idle**; `stopTicker`
  failure/404 still returns the UI to idle (idle is the truthful end state either way).

## Key Test Scenarios
- **Browser (the real gate — Chrome MCP, J-09):** from a fresh cold watch of `SIM-BUYER` (status dot
  **live**, panels populated), press **Stop promptly while still live** → body shows `<IdleState/>`
  ("No ticker watched"), dot returns to **idle**, no further snapshot updates arrive; then **re-watch
  the same ticker** → cockpit repopulates from a **cold start** (connecting → live → values), i.e. a
  fresh read, not a frozen/closed leftover. Evidence screenshots: cockpit-live → post-Stop-idle →
  re-watch-fresh. *(Optional convenience: widen delivery pacing via `TAPEOLOGY_FEED_PACE=0.12` to make
  the live window easier to catch — delivery pacing only, does not affect classification determinism.
  Idle-return + re-watch-fresh hold even if the bounded stream exhausts before the click.)*
- **Deterministic teardown evidence (timing-independent):** after `DELETE /watch/{ticker}`,
  `GET /tape/{ticker}/state` → 404 and a fresh `WS …/stream` connect is rejected (4404); a re-`POST
  /watch/{ticker}` → 200 and yields a fresh cold-start snapshot.
- **Unit — `WatchManager.stop()`:** stopping a watched ticker cancels its feeder task, sets engine
  `stream_status="closed"`, and removes it from `_engines` (subsequent `get()` → `None`); `stop()` of a
  not-watched ticker → `False`, raises nothing.
- **Unit — re-watch is a fresh engine:** `watch(t)` → `stop(t)` → `watch(t)` returns a **different**
  engine instance, starting cold (no carried-over event count / state).
- **Unit — DELETE route (`test_api.py`):** watched → 200 `{"status":"stopped"}`, then `GET …/state` → 404
  and fresh `WS …/stream` → 4404; not-watched → 404.
- **Determinism guard:** `watch → stop → re-watch` on the same seeded ticker yields an **identical**
  fresh cold-start snapshot to a first-ever watch (no state leakage across the stop boundary).
- **Required-still-passing journeys:** J-01 (watch → live cockpit), J-02 (`SIM-BUYER` re-resolves to
  `buyer_control` with positive `buy_price_impact` — proves the fresh read), J-08 (UI ≡ REST). J-03–J-07
  must not regress.
- **Regression / anti-goal gates:** the existing 61 backend tests stay green (new `stop`/DELETE tests
  added); frontend build passes (`cd apps/frontend && npm run build`); idle cockpit shows no
  stale/fabricated numbers; stopped-ticker reads return explicit 404 (no synthesized snapshot); no
  recomputation added in API or frontend; `classifier.py`/`features.py`/`config.py`/`providers/` byte-untouched.
- **Dev handoff** written at `docs/handoffs/goal-i_will_be_rich-iter-7-dev.md`.

## Scope & Coherence Note
Spec is fully aligned with `docs/goal.md` (J-09 + `DELETE /watch/{ticker}` are in the Phase-1 API
surface and the ninth Must-have journey) and with `blueprint.md` (the Stop control + post-Stop idle
state are already in the Information Architecture; the iter-7 realization is already logged on the
existing **"Watched-scenario label + watch/stream status"** Data-Contract row — same owner
`WatchManager`, same endpoints, **no new contract row, no second producer, no nav-skeleton change**).
No scope creep detected. This is a genuine net-new cross-stack iteration (not a thin verify pass);
the full pipeline (ui-impact → ui-test-design → browser-qa → ux-regression → closure) and the closure
gate are warranted, per the iter-6 evaluator's recommendation.
