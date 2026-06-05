# Goal Iteration 8 — Local-time historical window picker (J-20) + close the real-historical chart render (J-18)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich
- **Iteration:** 8
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-20, J-18
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-15, J-16, J-17, J-19
- **Anti-goal reminders:**
  - **Timezone-correct windows.** A historical window MUST be fetched for the exact instant the user selected in their local time — no silent UTC reinterpretation that shifts the window by the local offset; all market/session times shown to the user MUST carry an explicit zone label. *(critical)*
  - **One focused chart, computed once.** OHLC bars and tape-state markers MUST be computed once in the engine history buffer and read identically by `…/history` and the chart; the UI MUST NOT recompute side, state, or price from raw data. An empty window MUST yield an **empty** chart, not invented candles. The chart is analysis-only — it MUST NOT add any order/execution affordance. *(critical)*
  - **No fabricated data.** The system MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. Every real-data failure mode MUST surface an explicit, distinct state and never a cockpit. Falling back to simulated or invented data to mask a real-data failure is a defect. *(critical)*
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*
  - **No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code. (For this iteration: the RTH session anchors 9:30 / 16:00 ET, if introduced, are display/preset constants, not engine thresholds — keep them as named constants, not scattered literals.)
  - **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. *(critical)*
  - **Provider-agnostic engine.** The engine and API MUST depend only on the provider interface; swapping the simulator for a real feed — live or historical — MUST NOT require engine or API changes. *(critical)*

## GOAL

A user selecting **Historical** picks a date/time window in their **own local timezone** (shown with an explicit zone label) — or one click of a **US-session quick-pick** (Open 9:30 ET / Close 16:00 ET / Full RTH) annotated with its local equivalent — and the window actually fetched from the vendor is the exact instant they chose (no silent UTC shift); and the real-historical candlestick chart is render-verified with a populated screenshot so J-18 is promoted from `partial` to `passing`.

## BACKGROUND

This is the final build slice toward GOAL_ACHIEVED: after iter-7, 18/20 must-have journeys pass; only **J-20** (failing/unbuilt) and **J-18** (partial — surface + backend correctness proven, but no rendered real-data screenshot) remain. The iter-7 evaluator recommended iter-8 at **full** depth because J-20 is gated by the *critical* timezone-correct-windows anti-goal, touches the historical watch path that J-11/J-16 depend on, and needs a Data Contract (row 12) blueprint touch.

The load-bearing risk is documented verbatim in the iter-2 lesson and confirmed in code this planning pass: `apps/frontend/components/TopBar.tsx:83-84` builds the watch body's `start`/`end` as a **naive** local string (`` `${date}T${startTime}` ``, no offset), and `apps/backend/app/main.py:129-132` `_parse_window_dt` treats a naive value as **UTC** — so today an operator must hand-enter UTC times (15:00 UTC = 11:00 ET) and there is no zone label and no quick-picks. The key insight for scoping: **`_parse_window_dt` already correctly honors a tz-aware instant** (it parses an offset / `Z` when present and only falls back to UTC for a naive value), so the fix is predominantly **frontend** — resolve the user's local selection (and the ET quick-picks) to an explicit tz-aware UTC instant *before* the POST. Do NOT remove the backend naive→UTC fallback in a way that breaks existing tests; the durable fix is that the frontend stops sending naive values.

J-18's render is offline-reproducible: the committed REAL Ford fixture `apps/backend/tests/fixtures/alpaca/F_20260602_150000_20260602_150200.json` (65 trades / 1772 quotes, real epochs + penny-spread prices) replays through the same engine and `…/history` endpoint with no live credentials, so a browser-qa step can watch that real historical window and screenshot the populated real-data candlestick chart. Per the iter-6/iter-7 visual-journey lessons, J-18 stays `partial` until a **real rendered screenshot of the populated chart** exists — not backend/data inference, not an idle placeholder.

## IN SCOPE

### Backend
- [ ] No new engine, classifier, provider, or endpoint logic is required for J-20 — `_parse_window_dt` (`apps/backend/app/main.py`) already resolves a tz-aware ISO instant correctly. Add (or extend) a backend unit test asserting that a window submitted as an **offset-bearing** instant (e.g. `…T09:30:00-04:00`) is fetched for that exact UTC instant, and that the previously-accepted naive value is unchanged — proving the contract the frontend now relies on. (Source-of-truth verification, not a behavior change.)
- [ ] If, and only if, a reviewer finds the naive→UTC fallback is itself unsafe for the corrected flow, tightening it is permitted — but it MUST NOT regress the existing historical tests (`test_history_api.py`, `test_historical_provider.py`, `test_watch_manager.py`); prefer leaving the backend fallback intact and fixing the source at the frontend.

### Frontend (if applicable)
- [ ] Add a **historical-window resolution module** (the row-12 owner) in `apps/frontend/lib/datetime.ts` (extending the existing display-only file): a pure function that takes the user's selected local date + start/end times and returns explicit **tz-aware ISO-8601 UTC instants** (with offset or `Z`) for the watch body — resolved **once**, before the POST. This replaces the naive `` `${date}T${startTime}` `` construction in `TopBar.tsx:83-84`.
- [ ] Surface the **user's local timezone label** on the Historical picker (e.g. derived from `Intl.DateTimeFormat().resolvedOptions().timeZone` / the local offset) so the user can see which zone their entry is interpreted in — satisfying "all market/session times shown carry an explicit zone label."
- [ ] Add **US-session quick-picks** beside the Historical date/time controls: **Open 9:30 ET**, **Close 16:00 ET**, **Full RTH (9:30–16:00 ET)**. Each is annotated with its **local equivalent** for the selected date, and clicking one fills a valid regular-hours start/end (which then resolves through the same row-12 function to tz-aware UTC). The 9:30 / 16:00 ET anchors are named constants (not scattered literals); compute the ET→local/UTC mapping via the IANA `America/New_York` zone so it is DST-correct (do not hardcode a fixed −4/−5 offset).
- [ ] Keep the watched-source label honest: the Historical descriptor shown in the UI should reflect the actual resolved window; do not display a window different from the one fetched.

### New user-facing capability
A Historical user can pick a date/time window in their own local timezone (clearly labeled), or one-click a US-session preset (Open / Close / Full RTH) shown in both ET and their local time, and trust that the data fetched matches exactly the local window they selected — no mental UTC conversion, no silent shift.

### New information displayed
- An explicit **local timezone label** on the Historical date/time picker.
- **US-session quick-pick** controls (Open 9:30 ET / Close 16:00 ET / Full RTH), each annotated with the local-time equivalent for the chosen date.
- (J-18 render) the populated **real-historical candlestick chart** — real replayed Ford prices as candles with tape-state markers — made visible/verified, not new UI but newly evidenced.

### New user actions
- Click a **US-session quick-pick** button to fill the start/end window.
- (Unchanged) enter date/start/end/speed and Watch — now resolved to a tz-aware instant.

### UI surface changes
- The existing Historical controls in `TopBar.tsx` gain a zone label and a quick-pick row. No new page, no new route, no new nav section — all still on `/`, inline with the existing Historical mode reveal.

### Product surface delta
Historical selection becomes trustworthy and ergonomic: what you pick locally is what gets fetched, and the common RTH boundaries are one click away — closing the last correctness gap (timezone) and the last evidence gap (real-historical chart render) for the product.

### Blueprint conformance
All work lives under the existing **`/` — Watch (the tape cockpit) — HOME**, in the persistent app-shell **Historical** mode-specific controls already described in the Information Architecture ("date + time-window picker (local time, zone label, US-session quick-picks)"). J-20's canonical home is already registered as "Historical date/time picker (local-zone label + quick-picks)"; J-18's canonical home is the "price-chart pane above the cockpit (historical)". **No nav-skeleton change** — additive Data Contract edit only (see below), so **no re-approval is requested**.

### Data-contract additions
No NEW value is added — **Data Contract row 12 ("Resolved historical window")** is already registered. This iteration makes additive clarifications to row 12 in `blueprint.md`:
- Name the concrete computing owner: the resolution function in `apps/frontend/lib/datetime.ts` resolves the user's local selection (and the ET quick-picks) → tz-aware UTC instants **once**, before the `POST /watch/{ticker}` body is built; mark it built this iteration.
- Note that the **ET session anchors (9:30 / 16:00) and the displayed zone label** are display/preset values derived once by the same frontend datetime owner — there is no second timezone conversion and no backend recomputation of the window (the backend fetches exactly the resolved instants). This conforms to the existing "no second tz conversion, no silent UTC reinterpretation" guardrail.

The chart values (row 10) and the historical watch body (row 12) are read/produced exactly once; J-18 does **not** introduce any new value — it reads row-10 OHLC/markers verbatim.

## OUT OF SCOPE

- Any change to the engine, classifier, feature windows, aggressor/tick-test logic, or the `…/history` projection (J-17's chart pipeline is proven and untouched — J-18 is render-verification only).
- Removing or reworking the backend `_parse_window_dt` naive→UTC fallback (leave it intact; fix the source at the frontend) unless a reviewer proves it unsafe AND no historical test regresses.
- A general timezone picker / arbitrary-zone selection — only the user's **local** zone (with label) plus the **ET** session quick-picks are required.
- Live-mode changes (the chart is hidden in Live; J-12/J-15 are unaffected).
- Any new page, route, watchlist, dashboard, or execution/order affordance.
- The `(later)` predictive-edge measurement harness, Level-2 / `BookLevelEvent`, and persistence — all explicitly out of the current goal.

## DEFINITION OF DONE

- [ ] **J-20 passes via browser-qa-agent:** the Historical picker defaults to the user's local time with an explicit zone label; the quick-picks (Open 9:30 ET / Close 16:00 ET / Full RTH) are present, each annotated with its local equivalent, and clicking one fills a valid regular-hours start/end. (The local-time labels + presets are browser-verifiable without a feed.)
- [ ] **J-20 timezone-correct fetch verified:** with the corrected frontend, the window sent to the backend is a tz-aware instant matching the selected local window (no UTC shift). Verified by (a) the backend unit test on offset-bearing instants, AND (b) an end-to-end check that a chosen local window resolves to the expected UTC instant in the request body (browser/network inspection or an equivalent integration assertion). *(The correct-window fetch against the live vendor is operator-gated like J-12/J-15; the resolution correctness itself is verifiable offline.)*
- [ ] **J-18 promoted to passing:** a real rendered screenshot captures the **populated** real-historical candlestick chart (real replayed Ford prices as candles, with tape-state markers), produced by watching the committed Ford fixture window in Historical mode against a clean isolated frontend — not an idle placeholder, not a sim chart. Bar-size selector (10/30/60 s) re-renders against the same `…/history` data.
- [ ] Required-still-passing journeys (J-01–J-17, J-19) remain green — especially **J-11 / J-16** (historical replay + resolved side) since this iteration touches the historical watch path, and **J-17** (the sim chart render must not regress).
- [ ] No anti-goal violation introduced — in particular the timezone-correct-windows, one-focused-chart, no-fabricated-data, and single-source-of-truth criticals.
- [ ] Unit tests pass; no regressions (full backend suite green, including `test_history_api.py`, `test_historical_provider.py`, `test_watch_manager.py`).
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich-iter-8-dev.md`.

## TESTING REQUIREMENTS

- **Browser (named journeys):**
  - **J-20** — In Historical mode: assert the explicit local zone label is shown on the picker; assert the three quick-picks (Open 9:30 ET / Close 16:00 ET / Full RTH) render with local-equivalent annotations; click a quick-pick (e.g. Open) and assert it fills a valid RTH start/end; screenshot each. Then verify (network/request inspection or equivalent) that submitting the window sends a **tz-aware** `start`/`end` (with offset/`Z`) equal to the selected local instant — not a naive string and not UTC-shifted.
  - **J-18** — In Historical mode, watch the committed Ford fixture window (e.g. `F`, 2026-06-02 15:00–15:02 captured window) against a clean isolated frontend; screenshot the **populated** candlestick chart with real replayed prices and tape-state markers; switch bar size 10→30→60 s and screenshot the re-render. (No live creds required — the fixture replays offline.)
  - Run browser-qa against a **clean isolated `.next`** (use `NEXT_DIST_DIR` + `NEXT_PUBLIC_API_URL` → an isolated backend port); do **not** build against the shared harness `:3650 .next`, and do **not** `git checkout` any file carrying uncommitted iter edits (see iter-3/iter-6 lessons). A `browser-qa SKIPPED` for a visual journey is NOT a pass — a real rendered screenshot is required.
  - Re-verify **J-17** (sim chart still renders), **J-11** (historical AAPL/Ford replay still populates the cockpit), and **J-19** (pause/resume) did not regress.
- **Unit/integration:**
  - Frontend resolution: the new `lib/datetime.ts` resolution function — assert a selected local date+time resolves to the correct tz-aware UTC instant (cover at least one DST-affected date), and that the ET quick-picks (9:30/16:00 ET) map to the correct UTC instants for the chosen date via `America/New_York` (DST-correct, not a fixed offset).
  - Backend: a unit test asserting `_parse_window_dt` / the historical watch path fetches the exact UTC instant for an **offset-bearing** input (e.g. `…-04:00`), and that a naive input remains treated as UTC (no regression of existing behavior).
- **Error cases:**
  - End time ≤ start time is rejected (existing 422 — keep it).
  - An out-of-set replay speed is rejected (existing 422 — keep it).
  - A quick-pick on a date must produce a **valid regular-hours** start/end (start < end); the resolver must not emit a malformed or empty window.
  - An empty historical window MUST still yield the honest `no_data_for_window` state and an **empty** chart — never fabricated candles (no regression of J-14 / the one-focused-chart anti-goal).

## NOTES

- **Lesson applied (iter-2 — naive-UTC gotcha, the load-bearing risk for J-20):** the picker currently sends naive datetimes the backend treats as UTC (confirmed at `TopBar.tsx:83-84` + `main.py:129-132`). The durable fix is to resolve the local selection to a tz-aware instant in the frontend **before** the fetch; the backend already honors an offset instant, so prefer fixing the source over changing the backend. Use a penny-spread name (Ford, from the committed fixture) for any clean-state historical walkthrough — the free IEX top-of-book is wide for high-priced names (AAPL reads `unclear`), which is correct and out of scope to change.
- **Lesson applied (iter-6 / iter-7 — visual journeys need pixels):** J-18 is a fundamentally visual journey. Do not score it `passing` from backend/data inference or a confident PASS row — require a real rendered screenshot of the **populated** real-historical chart, and open the actual bytes (a screenshot showing the idle "No ticker watched" placeholder is NO evidence). Prefer the browser-qa-agent's `ui-test-results.md` UT evidence over a qa-report claim if they disagree.
- **Lesson applied (iter-3 / iter-6 — shared `.next` corruption):** the shared harness `:3650 .next` has corrupted browser-qa twice (`Cannot find module './833.js'` 500). The browser run MUST rebuild or fully bypass it via an isolated dist dir + isolated backend before trusting (or skipping) the visual verification.
- **Coherence:** iter-7 was COHERENCE-PASS, so no consolidation is owed. This iteration's only blueprint change is an additive clarification of the already-registered row 12 (name the `lib/datetime.ts` resolution owner; mark built) — no nav-skeleton change, so no re-approval is requested.
- **Path to GOAL_ACHIEVED:** once J-20 passes with a timezone-correct fetch and J-18 has a populated real-historical chart screenshot, all 20 must-have journeys (J-01–J-20) are passing — the goal becomes a GOAL_ACHIEVED candidate for the evaluator (the evaluator, not this spec, makes that call). J-18's against-the-live-vendor leg remains operator-gated (like J-12/J-15); the offline fixture render satisfies the in-loop visual-evidence bar.
