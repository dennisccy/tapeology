**Verdict:** COHERENCE-PASS

# Coherence Audit — goal-i_will_be_rich-iter-7

- **Session:** i_will_be_rich · **Iteration:** 7 (J-09 — Stop watching: `DELETE /watch` + Stop control + return-to-idle)
- **Audited diff:** `git diff e66fe5d4e2ea9a364b99b51a50a7be42c8857723` (uncommitted working tree)
- **Blueprint:** `runs/goal-session-i_will_be_rich/state/blueprint.md` (APPROVED, additive-only)
- **Surfaces touched:** backend `main.py`, `watch_manager.py`; frontend `page.tsx`, `TopBar.tsx`, `lib/api.ts`; tests; +5-line additive blueprint realization note.

## Part A — Data Contract (objective → FAIL): PASS

No new value is computed or served from a non-canonical source.

- **No duplicate computation.** The iteration adds teardown plumbing only — `DELETE /watch/{ticker}` (`main.py:75`) delegates to `manager.stop(ticker)` and returns a static `{"status":"stopped"}`; `WatchManager.stop()` (`watch_manager.py:60`) cancels the feeder, removes the engine, and marks closed. No new function reimplements tape state, features, spread, recent trades, observations, or scenario/stream-status. Engine-layer owners (`classifier.py`/`features.py`/`config.py`/`providers/`) are byte-untouched (confirmed by diff stat) — no recomputation leaked into the API/engine.
- **Canonical source preserved.** `stop()` is invoked on the **registered canonical owner** `WatchManager` (row "Watched-scenario label + watch/stream status"). It sets the closed status through the *pre-existing* `engine.set_stream_status("closed")` setter — the same path `_feed()` already uses on exhaustion — so there is **one producer** for stream-status, not a second. The frontend `stopTicker()` (`lib/api.ts:40`) calls the **canonical** `DELETE ${API_BASE}/watch/{ticker}`, which is explicitly the endpoint registered on that row ("+ `POST`/`DELETE /watch/{ticker}` responses"). No client-side recomputation.
- **No new/duplicate displayed value.** Stop is a control, not a readout; after Stop the already-declared idle/empty state is shown. The `{"status":"stopped"}` response is part of the already-registered DELETE-response half of an existing row — not a new value, not a synonym of an existing one.

## Part B — Information Architecture (objective → FAIL): PASS

- **Declared home, no new route.** The Stop button is rendered inside the persistent `TopBar` app shell beside the watched-ticker label (`TopBar.tsx:80`), gated on `watched` being set. The blueprint app shell already names a "**Stop** control (`DELETE /watch/{ticker}`)". Everything stays on `/` — HOME. No new page/route/panel.
- **Reachable.** The control is directly in the persistent top bar (0–1 click while watching). No undiscoverable / URL-only surface.
- **No duplicate home, no parallel shell.** `page.tsx` still renders the single `{ticker ? <Cockpit/> : <IdleState/>}` body; the post-Stop screen is the already-declared "Idle/empty state … after Stop". No second idle/results page and no alternate layout/nav introduced.

## Blueprint edit check

The only blueprint change is a 5-line additive realization note appended to the existing realization-log paragraph for the "Watched-scenario label + watch/stream status" row, stating "no new contract value, no second producer/endpoint, no nav-skeleton change." This conforms to the APPROVED/additive-only status — no contract row mutated, no IA skeleton altered.

## Part C — Advisory (non-blocking): none material

- The Stop button uses static rose/red Tailwind tokens (`border-rose-500/70`, `text-rose-400`, …) as a literal `className` string — satisfies the lessons-iter-2/3 static-class requirement (no runtime-built class). Red on a destructive control is conventional and applied to a control affordance, not a data readout, so it does not conflict with the blueprint's data color legend (red = sell-side). No action needed.

## Conclusion

No Part A or Part B violations. The iteration realizes the already-registered `DELETE /watch/{ticker}` half of an existing Data-Contract row through its one canonical owner (`WatchManager`) and its declared home (the top-bar app shell), with no new value, no recomputation, no new route, and no nav-skeleton change. **COHERENCE-PASS.**
