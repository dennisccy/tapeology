# Goal Iteration 13 — Live replay-speed, relative-spread/impact calibration, chunked long-window load (J-32/J-33/J-34)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich
- **Iteration:** 13
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-32, J-33, J-34
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-15, J-16, J-17, J-18, J-19, J-20, J-21, J-22, J-23, J-24, J-25, J-26, J-27, J-28, J-29, J-30, J-31, J-35
- **Anti-goal reminders:**
  - **Price impact over raw aggression.** The classifier MUST distinguish absorption from control: a tape with high one-sided aggression but no corresponding price progress MUST resolve to the matching absorption state (bid_absorption / ask_absorption), never to seller_control / buyer_control. Keying on aggression ratios alone is a defect. *(critical)*
  - **Honest uncertainty.** When evidence is weak or mixed, the spread is wide **relative to the instrument's price / typical spread**, or there is no clean price impact, the state MUST be `unclear` with low confidence. The system MUST NOT manufacture a directional call to look decisive. The "wide spread" and "clean price impact" tests MUST be judged **relative to the instrument's price level / recent volatility** (e.g. spread in basis points, impact as a return), never via a single absolute dollar constant calibrated for the simulator — so a genuine strong directional move on a real symbol with a proportionate spread reads as control, while a genuinely wide *relative* spread (or high aggression with no proportionate price progress) still reads `unclear` / absorption. *(critical)*
  - **No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code.
  - **Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine MUST produce identical features, state, and confidence; classification MUST NOT depend on wall-clock time or randomness. Each simulated scenario MUST have an automated test asserting the expected state is reached with reasonable confidence.
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. *(critical)*
  - **Bounded, honest, performant vendor calls.** Every vendor-gated Watch MUST be bounded by a **real call-level deadline** (an HTTP/SDK timeout), backend bound **shorter than** the frontend client timeout. Interactive vendor paths MUST be **fast by design, not by lengthening timeouts**: a legitimate high-volume window MUST load within budget via an optimized fetch (concurrent trades/quotes, **chunked sub-window fetch with bounded concurrency for long windows up to a full trading day**, cached/reused windows). Every optimization MUST preserve correctness — **no fabricated or dropped trades/quotes, no recomputation outside the engine**. *(critical)*

## GOAL

Let a user change the historical replay speed of a running watch and have it apply immediately; make a genuine real-data directional move classify as control (not perpetual `unclear`) by judging spread/impact relative to price level; and load a long (up to Full-RTH) historical window via chunked sub-window fetches instead of the "very high-volume" error.

## BACKGROUND

Iter-12 closed J-31 and J-35 (true-clock axis + dd-MM-yyyy dates) with COHERENCE-PASS; the iter-12 evaluator recommended a full-depth iteration targeting J-33 (highest value/risk — classifier re-tuning) and J-32, with J-34 bundled. These are the last three unbuilt Must-have journeys (J-32/J-33/J-34 status `unknown`); all of J-01–J-31 + J-35 are passing. This is full depth because J-33 touches the classifier thresholds (the engine's core), J-34 changes the vendor fetch concurrency model, and the combined diff crosses backend + frontend and the data model — it needs the full pipeline (test-plan, review, browser-QA, audit) and unit tests beyond a browser smoke. Verified facts grounding the scope: there is currently **no** `POST /watch/{ticker}/speed` endpoint and `_feed_paced` reads `speed` once as a fixed local divisor (`watch_manager.py:230`); the classifier gates use **absolute** dollar/return constants `max_stable_spread`/`min_buy_price_impact`/`max_sell_price_impact` (`config.py:28-37`, `classifier.py:74-143`); and `fetch_historical` does a single concurrent trades+quotes fetch with **no** chunking (`alpaca.py:189-228`) — an oversized window deterministically returns "that window is very high-volume — try a shorter range" (`main.py:98`).

## IN SCOPE

### Backend
- [ ] **J-32 — mutable replay speed.** Add `POST /watch/{ticker}/speed` (in `app/main.py`) that sets the replay speed of a **running** watch: validate the body speed against `CONFIG.allowed_replay_speeds` (out-of-set ⇒ **422**), not-watched ticker ⇒ **404**. Make `WatchManager` own a per-ticker mutable speed (a small holder updated by a `set_speed(ticker, speed)` method); change `_feed_paced` to read the **current** speed each loop iteration (replace the captured local `divisor = speed`) so a change applies to the in-progress replay within ~1s — no re-fetch, no engine restart, no teardown. A change while paused applies on resume (the existing `_wait_while_paused` gate is unchanged). Pacing remains **delivery-only**: the engine still processes the same ordered events with the same logical timestamps, so features/state/confidence for the window are **byte-identical** regardless of speed (determinism preserved).
- [ ] **J-33 — relative spread/impact gates.** Re-tune the directional/absorption gates in `app/engine/classifier.py` so the "wide spread" and "clean price impact" tests are judged **relative to the instrument's price level / recent volatility** (e.g. spread as basis points of last/mid price; impact as a return rather than absolute dollars), with every new boundary owned by `app/config.py` (no inline literal, no magic number). The reference failing case: a real ~$30–50 name with a proportionate spread and strong negative impact must resolve to **seller_control** (mirror: **buyer_control** for a rally), not `unclear`. A genuinely **wide relative** spread, or high aggression with **no proportionate** price progress, MUST still read `unclear` / absorption (price-impact-over-aggression and honest-uncertainty anti-goals hold). The absorption gates MUST remain the exact complement of the control impact condition (mutual exclusivity preserved). Compute the price-relative basis once in the feature engine / from the canonical snapshot — do **not** recompute price or features inside the classifier beyond the existing feature reads.
- [ ] **J-34 — chunked long-window fetch.** In the historical fetch path (`app/providers/adapters/alpaca.py` + historical provider), split a long requested window into **bounded sub-windows** fetched with **bounded concurrency** (both bounds config-owned) and **stitch them in epoch order** into one real window. It MUST NOT fabricate, drop, reorder, or de-duplicate real prints; a re-watch of the same symbol+window stays near-instant from the existing window cache. This is **fast by design** (parallelizing the SDK's sequential pagination), not a longer timeout: any timeout raise stays modest and the backend bound MUST remain **shorter than** the frontend `WATCH_REQUEST_TIMEOUT_MS`. The advertised **Full RTH** quick-pick MUST load for a liquid symbol without the "very high-volume" error; that error becomes a **true backstop** only for a window genuinely too large to load within budget (still resolves via J-28's actionable "shorter range" message).

### Frontend (if applicable)
- [ ] **J-32 — replay-speed control wiring.** Wire the existing Historical **replay-speed** control so changing it on a **running** replay issues `POST /watch/{ticker}/speed` (not a re-Watch) and the cockpit/chart continue from their current position at the new cadence. No new surface — it is the speed control already present in the Historical mode-specific controls (blueprint IA). Reject/disable out-of-set values client-side as a courtesy, but the backend 422 is authoritative.
- [ ] No new frontend work is required for J-33 (the tape-state panel already renders the canonical state/confidence verbatim) or J-34 (the Historical fetch wait already shows the row-6 `waiting`/progress treatment; the Full-RTH quick-pick already exists).

### New user-facing capability
The user can drag/select a new replay speed mid-replay and see the cadence change immediately without re-Watching; a real symbol making a clear directional move now reads as buyer/seller control instead of staying `unclear`; and the Full-RTH (or any multi-hour) historical window loads instead of being refused as "very high-volume".

### New information displayed
No new displayed value. The tape-state panel may now show **control** where it previously showed `unclear` on real directional moves (same row-1 value, recalibrated). The chart may show seller/buyer markers at those transitions (same row-10 markers).

### New user actions
Changing the **replay-speed** control during a running historical replay (applies live).

### UI surface changes
None new — the Historical replay-speed control and the Full-RTH quick-pick already exist on `/`. Only their backend behavior changes.

### Product surface delta
The cockpit becomes interactively re-paceable mid-replay, classifies real directional moves honestly as control, and stops refusing legitimate long windows — the three remaining gaps before the J-31–J-35 refinement pass is complete.

### Blueprint conformance
All work lives on the existing single `/` HOME (the tape cockpit) — no new page, no nav-skeleton change, so **no re-approval requested**. J-32 → the existing Historical replay-speed control; J-33 → the existing tape-state panel (row 1); J-34 → the existing Historical fetch path serving rows 10/4/3 and the Full-RTH quick-pick (row 12). Blueprint edited additively: an iter-13 header note + the new `POST /watch/{ticker}/speed` lifecycle endpoint registered against rows 6/12, and clarifying notes on row 1 (relative gates) and row 10 / the vendor seam (chunked fetch).

### Data-contract additions
**None.** No new displayed value. `POST /watch/{ticker}/speed` is a **lifecycle control** on the already-registered watch (speed is delivery-pacing only, never a displayed engine value); the new bounds (relative spread/impact thresholds, sub-window size, chunk concurrency) are **config constants, not displayed values**. J-33 recalibrates the computation of the **existing** row-1 tape state + confidence (one owner: `TapeStateClassifier`); the classifier MUST read the price-relative basis from the canonical snapshot/feature engine — never introduce a second computation or a second source of spread/impact/price.

## OUT OF SCOPE

- Any change to live-mode classification beyond what the engine-level relative gates already produce (J-33 is calibration, not a live-feed change); the live socket path stays untouched.
- New chart studies, indicators, drawing tools, or any order/execution affordance (anti-goal: Stay in scope; no execution path).
- Persisting the window cache to disk, or any datastore (Phase 1 stays in-memory).
- Changing the symbol-search, pause/resume, or timeout-ordering behavior (J-19/J-28/J-30) beyond keeping them green.
- Adding a second vendor adapter.

## DEFINITION OF DONE

- [ ] Target journeys J-32, J-33, J-34 pass via browser-qa-agent (J-32 control + immediate-apply browser-verifiable; J-33 gated by a **deterministic regression fixture** asserting `seller_control`, real-GME leg operator-gated; J-34 gated by **chunk-split + in-order-stitch unit tests**, full-window load operator-gated with credentials)
- [ ] Required-still-passing journeys (J-01 – J-31, J-35) remain green — **all five sim scenarios J-01 – J-09 and the existing classifier unit tests MUST stay green after the J-33 re-tuning**
- [ ] No anti-goal violation introduced (price-impact-over-aggression, honest-uncertainty, no-magic-numbers, determinism, single-source-of-truth, bounded/honest/performant vendor calls)
- [ ] Unit tests pass; no regressions — including: a backend test for `POST /watch/{ticker}/speed` (valid apply, out-of-set ⇒ 422, not-watched ⇒ 404, and determinism: same window at two speeds ⇒ identical features/state/confidence); a deterministic classifier regression fixture for J-33 (warmed, high sell ratio, strong negative relative impact, spread wide in absolute $ but normal relative to price ⇒ `seller_control`; plus a negative-guard fixture: wide *relative* spread / no proportionate progress ⇒ `unclear`/absorption); and chunk-split + in-order-stitch tests for J-34 (no fabricated/dropped/reordered/de-duplicated prints)
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich-iter-13-dev.md`

## TESTING REQUIREMENTS

- Browser: J-32 (change replay speed on a running historical replay → cadence changes within ~1s, no re-Watch, watch not torn down); regression smoke on J-17 (sim chart still renders), J-02/J-03 (sim buyer/seller still resolve), J-20 (historical window picker unchanged).
- Unit/integration:
  - `app/main.py` / `app/watch_manager.py` — `POST /watch/{ticker}/speed`: 422 out-of-set, 404 not-watched, live-apply changes the in-progress pacing; **determinism** test (replay one fixed window at 1× and 10×, assert identical final features/state/confidence).
  - `app/engine/classifier.py` / `app/config.py` — J-33 regression fixture (relative-spread/impact ⇒ `seller_control` on the ~$30–50 reference shape) **and** the negative guards (wide relative spread ⇒ `unclear`; high aggression no proportionate progress ⇒ absorption); re-run `test_scenario` (all 5 sim scenarios) and `test_classifier` — both MUST stay green.
  - `app/providers/adapters/alpaca.py` / historical provider — chunk-split (a long window splits into the expected bounded sub-windows) and in-order stitch (merged stream is epoch-ordered with **no** fabricated/dropped/reordered/de-duplicated prints); re-watch hits the window cache.
- Error cases: out-of-set replay speed ⇒ 422; speed on a not-watched ticker ⇒ 404; a window genuinely too large to load within budget ⇒ the actionable "shorter range" message (J-28 backstop), not a routine refusal of a normal long session; an empty/anchorless window still ⇒ empty chart (no fabricated prints).

## NOTES

- **Lesson (iter-5), applies to J-33:** any change to the classifier/side logic — the authoritative proof is the **in-loop deterministic fixture replay re-derived from code**, not a screenshot; re-run the suite and assert the metric. The keystone safety check: the absorption gates MUST remain the exact complement of the control impact condition so J-04/J-05 are not silently reclassified when the relative gates land.
- **Lesson (iter-12 + iter-7/iter-6), applies to the J-32 browser leg and any visual regression check:** the dedicated browser-qa-agent run and the qa-agent's own Chrome MCP run can disagree or SKIP (shared `:3650` `.next` corruption / frontend-not-served). Open the evidence **bytes** and reconcile both reports; for a fast-resolving control like the speed change, hold/observe the request (e.g. `page.route` the `POST .../speed`) and assert the DOM/cadence, not just a PASS label. If browser-qa SKIPs, render the working-tree source into an isolated `NEXT_DIST_DIR` wired to the running backend (iter-8 technique).
- **Lesson (iter-11), applies to the J-32 speed-set 422 path:** trace any config/threshold FAIL to the spec and **both** sides of any mirror before scoring a regression — `allowed_replay_speeds` is backend-authoritative; the frontend control disable is a courtesy.
- iter-12 coherence verdict was **COHERENCE-PASS** — no consolidation pass owed; this iteration adds new scope cleanly.
- When J-32/J-33/J-34 all pass with no regression and coherence holds, the J-31–J-35 refinement pass is complete and the evaluator may declare **GOAL_ACHIEVED**.
