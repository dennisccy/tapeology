# Goal Iteration 6 — Unclear / choppy tape (J-06) + transition-taxonomy close-out (J-07)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_rich
- **Iteration:** 6
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes (browser verification required; **no frontend code change expected**)
- **Target journeys:** J-06, J-07
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-08
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the tape. *(critical)*
  - **Stay in scope.** No stock scanner/screener, no news/theme/sentiment analysis, no fundamental analysis, no chart-pattern or indicator charting, no portfolio/position management — these belong to separate projects and MUST NOT be built here. *(critical)*
  - **Price impact over raw aggression.** The classifier MUST distinguish absorption from control: a tape with high one-sided aggression but no corresponding price progress MUST resolve to the matching absorption state (bid_absorption / ask_absorption), never to seller_control / buyer_control. Keying on aggression ratios alone is a defect. *(critical)*
  - **Honest uncertainty.** When evidence is weak or mixed, the spread is wide, or there is no clean price impact, the state MUST be `unclear` with low confidence. The system MUST NOT manufacture a directional call to look decisive. *(critical)* — **THE keystone of this iteration.**
  - **No fabricated data.** On a provider gap/failure the system MUST surface an explicit stale/no-data state and MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. *(critical)*
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*
  - **No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code.
  - **Provider-agnostic engine.** The engine and API MUST depend only on the provider interface (TradeEvent / QuoteEvent / BookLevelEvent); swapping the simulator for a real feed MUST NOT require engine or API changes.
  - **Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine MUST produce identical features, state, and confidence; classification MUST NOT depend on wall-clock time or randomness. Each simulated scenario MUST have an automated test asserting the expected state is reached with reasonable confidence.
  - **No ML in v1.** The MVP classifier MUST be transparent rule/threshold logic over named features — no trained model in the first version.
  - **No trade/profit claims.** The product MUST NOT claim profitability or present output as trading advice; tape state is descriptive, not prescriptive.
  - **No secrets in source.** No API keys, tokens, or credentials committed; any future provider keys come from environment/config only.

## GOAL

Watching `SIM-CHOP` settles the cockpit honestly on **unclear** at low confidence — the engine, fed a genuinely choppy stream (mixed two-sided aggression, wide/jittery spread, no clean price impact), refuses to manufacture a directional or absorption call. And, from a cold start, a resolving scenario announces its state change in the event log ("Tape state changed to …") with observations updating live — closing out the transition taxonomy across the now-reachable states.

## BACKGROUND

This delivers the **fifth and final tape state** and the **honest-uncertainty** critical anti-goal. Four states are already built and green: `buyer_control` (J-02), `seller_control` (J-03), `bid_absorption` (J-04), `ask_absorption` (J-05). The product must now prove the inverse claim with equal rigor — that when the tape is genuinely ambiguous, the system says so rather than forcing a decisive read. The iter-5 evaluator recommended advancing to J-06 at **full** depth and folding in the J-07 transition-taxonomy verification.

**This work is net-new — confirmed by direct code inspection (not forward-carried notes; lesson iter-4).** `apps/backend/app/providers/simulated.py` registers `SIM-CHOP → "unclear_chop"` in `SIM_SCENARIOS` but `stream()` has **no branch** for it (`simulated.py:63-73`) — it emits **zero** events today, so the engine sits at a cold-start `unclear` (0.10) and never warms up. iter-5's UT-09 proved only that behavior (honest unclear *on silence*). J-06's acceptance needs an **actively choppy** driven stream that *warms up and still reads unclear by mixed signals* — a stronger, distinct demonstration than mere silence.

**Crucially, this iteration needs NO classifier and NO config change.** The `unclear` fallback already exists (`classifier.py:154-158`, returns `unclear_confidence` when warmed up but no gate fires), and all four state gates already require a one-sided `ratio >= threshold` **and** `spread <= max_stable_spread` (`classifier.py:76-151`). A balanced, wide-spread, no-refresh chop satisfies none of them, so it falls through to `unclear` through the existing logic. **If the developer finds a classifier or config change is required to make chop read unclear, that is a red flag** — it would mean an existing gate is mis-specified (a latent J-01–J-05 risk) and must be surfaced in the handoff, not silently patched. Expected backend diff: `simulated.py` + tests only.

Full depth is correct despite the small surface: (1) net-new provider code on a **critical** anti-goal, and (2) with **four** active gates now, the false-fire surface is large — the choppy stream must be proven NOT to transiently satisfy *any* of the four gates across *all five* rolling windows (10/30/60/180/300s) at *any* tick. The full pipeline (test-plan → ui-impact → ux-regression → closure) is warranted for the state that completes the MVP taxonomy.

## IN SCOPE

### Backend

- [ ] **Simulated provider (`app/providers/simulated.py`)** — author `_chop_stream()` (SIM-CHOP) and wire it into `stream()` (it currently emits nothing). Deterministic + seedable; emit only `QuoteEvent`/`TradeEvent` with `Side.UNKNOWN` (aggressor classification stays downstream in the engine). The choppy *shape* must, over **every** rolling window, deny all four gates by **defense in depth** (multiple independent gate conditions fail at once, so no single window's noise can trip a gate):
  - [ ] **Mixed two-sided aggression (the load-bearing guarantee).** Roughly balanced buy/sell prints — interleaved tightly (not in one-sided streaks) so that **both** `aggressive_buy_ratio` and `aggressive_sell_ratio` stay **below** their gate floors (`min_aggressive_buy_ratio` / `min_aggressive_sell_ratio`, both 0.60) in **every** window including the short, noise-prone **10s** window. Since all four gates require a one-sided ratio at/above its floor, keeping both ratios sub-floor everywhere makes every gate impossible regardless of impact/refresh/spread.
  - [ ] **Wide / jittery spread.** The quote spread oscillates and averages **above** `max_stable_spread` (0.06) in every window — independently defeating the `spread <= max_stable_spread` condition of all four gates.
  - [ ] **No clean price impact and no refresh evidence.** The mid-price jitters up and down with **no sustained directional progress**, so `buy_price_impact` and `sell_price_impact` stay near zero (past neither control cutoff); and the quote does **not** hold at a single level (it jitters), so `bid_refresh_score` and `ask_refresh_score` stay **below** their floors (0.55) — no fabricated absorption evidence. Include some mid-spread prints (price strictly between bid and ask ⇒ `Side.UNKNOWN`) to further dilute both ratios and reflect "no clean aggressor."
  - [ ] **Warms up yet stays unclear.** The stream must deliver enough trades to pass `warmup_min_events` (40) so the read is the **warmed-up** `unclear` (`unclear_confidence` = 0.20), not the cold-start 0.10 — proving the engine processed real choppy data and *still* honestly declined to call a side (distinct from iter-5's silence case).
  - [ ] **Chop shape constants are scenario DATA, not engine thresholds.** Any spread width, jitter magnitude, or balance probability lives in `simulated.py` alongside the existing `_START_BID` / `_P_MINORITY` shape constants — NOT in `app/config.py` and NOT inline in engine/classifier code (no-magic-numbers anti-goal applies to engine/classifier, and these are simulator data).
- [ ] **No change to `app/engine/classifier.py` or `app/config.py` is expected** (see BACKGROUND). The existing `unclear` fallback and the four gate conditions already produce the correct result for a genuinely choppy stream. Touch them only if a real defect is found, and document it loudly in the handoff.

### Frontend

- [ ] **None.** No frontend code change is expected. The `unclear` state already renders amber via the dynamic `stateColor`/`stateBarColor`/`stateLabel` in `lib/format.ts` (proven on the silent SIM-CHOP in iter-5 UT-09: amber "Unclear" headline + bar); the amber base utilities are confirmed in the served Tailwind bundle (iter-3 `./lib/**` content glob; iter-5 absorption amber); the scenario indicator already shows the `unclear_chop` label (SIM-CHOP is already in `SIM_SCENARIOS`); and transition lines / observations already render in the Event-log and Observations panels. This iteration **verifies** the UI for the now-active chop and the cold-start transitions — it does not modify it.

### New user-facing capability

The user can watch `SIM-CHOP` and get an honest non-call: a genuinely choppy tape reads **Unclear** at low confidence, with the UI explicitly NOT asserting buyer or seller control or absorption — the system's honesty surface. And, watching any resolving scenario from a cold start, the user sees the state-change announced live in the event log with observations reflecting current evidence.

### New information displayed

None new in kind. The already-built `unclear` tape state + its low confidence are now shown against a *driven* choppy stream (previously only cold-start silence); the already-built "Tape state changed to …" transition lines and observations are verified appearing live from a cold start.

### New user actions

None. (No new controls. The ticker input + Watch already reach SIM-CHOP and every resolving scenario. The Stop control / `DELETE /watch` UI remains **J-09**, out of scope.)

### UI surface changes

None. All verification happens on the existing `/` cockpit: the Tape-state panel renders the already-styled amber `unclear` state; the Event-log and Observations panels show the cold-start transition + evidence. No new page, route, panel, or control.

### Product surface delta

The cockpit now demonstrates the **complete five-state MVP taxonomy** end-to-end and browser-verifiable: `buyer_control` / `seller_control` / `bid_absorption` / `ask_absorption` / **`unclear`**. The product's two complementary promises are both proven on screen — it makes a decisive, price-impact-keyed call when the evidence is clean, and it honestly declines (Unclear, low confidence) when the tape is choppy.

### Blueprint conformance

No new Information-Architecture surface. Everything lives on the existing `/` cockpit home (the only route). The `unclear` state renders in the existing Tape-state panel; transitions/observations in the existing Event-log/Observations panels; the `unclear_chop` scenario label in the existing top-bar scenario indicator — all canonical homes already registered in `blueprint.md`.

### Data-contract additions

**None (rides existing contract rows).**
- `unclear` is an **already-enumerated value** of the registered **"Tape state + confidence"** row, produced once by `TapeStateClassifier` and served by `GET /tape/{ticker}/state` (re-exposed read-only by `/summary` + `WS /stream`).
- The transition / observation messages ("Tape state changed to …", "Mixed or weak evidence — no clear side in control") ride the existing **"Observations + event-log messages"** row (one producer: the engine emitter / classifier).
- The `unclear_chop` scenario label rides the existing **"Watched-scenario label + watch/stream status"** row (`SIM-CHOP` already in `SIM_SCENARIOS`).
- No new feature is introduced (chop uses the existing features). `blueprint.md` is kept current with a purely additive realization note (no new row, no nav change, no reapproval).

## OUT OF SCOPE

- **J-09** (Stop / `DELETE /watch` UI control + return-to-idle / re-watch) — the next and final journey; needs a net-new UI control and a fresh-backend teardown verification (iter-5 bounded-stream gotcha). Its stream-status-dot groundwork already landed in iter-5. Not this iteration.
- Any change to the classifier gates, confidence math, or `config.py` thresholds — the chop must read unclear through the **existing** logic (a needed change is a defect to flag, not in-scope work).
- The remaining un-built features `spread_change`, `liquidity_imbalance` (and later `liquidity_pull_score`) — not needed for chop; defer to their owning iterations.
- Level-2 book ingestion (`BookLevelEvent`), persistence, replay/backtest, any extended states — all explicitly later/nice-to-have in `docs/goal.md`.
- Anything touching execution/orders, scanning, news, charting, portfolio (permanent anti-goals).

## DEFINITION OF DONE

- [ ] **J-06** passes via browser-qa-agent: watching `SIM-CHOP`, the tape state reads **unclear** at low confidence (below `reasonable_confidence`); the UI does **not** assert buyer/seller control or absorption; the amber "Unclear" render is confirmed by **computed-style + base-selector probe** (`.text-amber-400{` / `.bg-amber-500{`, excluding `:hover`/variant forms), not eyeballed and not grep-substring; values stream live over WebSocket without reload. No fabricated prices/state when evidence is mixed.
- [ ] **J-07** passes via browser-qa-agent: watching a **resolving** scenario (e.g. `SIM-BUYER`) from a **cold start** (first watch on a fresh backend), the event log records a **"Tape state changed to <state>"** message at the transition and the observations list reflects current evidence (e.g. "Buyer aggression increasing"), appended **live** over the WebSocket. Demonstrate the cross-state taxonomy by capturing the cold-start transition on **≥2 distinct states** (e.g. `SIM-BUYER` → `buyer_control` and `SIM-SELLER` → `seller_control`, and/or an absorption scenario → its "Tape state changed to bid_absorption/ask_absorption" line). Note that `SIM-CHOP` itself produces **no** transition line (cold-start unclear → warmed unclear is not a state change) — and the absence of a spurious transition is itself correct honest behavior.
- [ ] **Required-still-passing journeys remain green:** J-01 (six panels live on SIM-BUYER), J-02 (SIM-BUYER still `buyer_control`, green), J-03 (SIM-SELLER still `seller_control`, rose), J-04 (`SIM-BIDABS` still `bid_absorption`, amber), J-05 (`SIM-ASKABS` still `ask_absorption`, amber), J-08 (UI ≡ REST — spot-checked on `SIM-CHOP` too: UI `unclear` + confidence == `GET /tape/SIM-CHOP/state`; UI feature readouts == `/features`).
- [ ] No anti-goal violation introduced (honest-uncertainty positively demonstrated against a *driven* choppy stream; no fabricated data; single source of truth holds on the unclear read; determinism; no magic numbers; the four control/absorption states unperturbed).
- [ ] Unit tests pass (the 53-test baseline plus the new chop tests below); no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_rich-iter-6-dev.md`, explicitly stating whether any classifier/config change was needed (expected: none).

## TESTING REQUIREMENTS

- **Browser (the real gate):**
  - **J-06** — `SIM-CHOP` → **unclear** at low confidence; UI asserts no side and no absorption; amber "Unclear" headline + confidence bar measured by base-selector probe + `getComputedStyle`; live over WS. Confirm Quote/feature panels show real choppy values (no fabricated decisive numbers).
  - **J-07** — cold-start → resolved transition captured on ≥2 distinct resolving scenarios: the "Tape state changed to <state>" line appears in the event log and observations update live. **Capture each on the FIRST watch of that ticker on a fresh backend** — per the iter-5 bounded-stream gotcha, a re-watch of an exhausted sim ticker returns the already-resolved (possibly closed) engine, so the *live append* is only observable on the cold first watch. (The transition message persists in the event log thereafter, so its *presence* is robust either way.)
  - Re-verify J-01, J-02, J-03, J-04, J-05, J-08 unchanged (regression guards).
  - If browser-qa SKIPS because the frontend returns HTTP 500 (corrupted `.next` cache), treat it as a verification-closure signal, not a pass: `rm -rf apps/frontend/.next`, restart the dev server with `NEXT_PUBLIC_API_URL` set, and re-run — a backend PASS does NOT substitute for browser verification of J-06/J-07 (lesson iter-1).
- **Unit/integration (`apps/backend/tests/`):**
  - **Scenario tests (`test_scenario.py`):**
    - `test_sim_chop_settles_on_unclear` — run `SIM-CHOP` through the real engine; assert `snap.tape_state == STATE_UNCLEAR`, `snap.warm is True` (and `snap.event_count >= CONFIG.warmup_min_events` — it genuinely warmed up), and `snap.confidence == CONFIG.unclear_confidence` (the warmed-up unclear value, strictly `< CONFIG.reasonable_confidence`) — i.e. unclear by *mixed signals*, not by cold-start silence.
    - **No-false-fire — step-through state guard (the critical guard):** process the `SIM-CHOP` stream event-by-event and assert the tape state is **never** `buyer_control` / `seller_control` / `bid_absorption` / `ask_absorption` at **any** tick (always `unclear`, whether cold-start or warmed). Proves the classified state never transiently misfires across the whole stream.
    - **No-false-fire — all-windows feature guard:** on the warmed-up end-state snapshot, for **every** window label in `snap.features` (10s/30s/60s/180s/300s) assert **both** `aggressive_buy_ratio < CONFIG.min_aggressive_buy_ratio` **and** `aggressive_sell_ratio < CONFIG.min_aggressive_sell_ratio` (so no gate is even reachable in any window), plus `average_spread > CONFIG.max_stable_spread` and both refresh scores `< CONFIG.min_bid_refresh_score` / `< CONFIG.min_ask_refresh_score` (defense-in-depth evidence of *why* it is unclear). Give the short **10s** window explicit attention — it is the most noise-prone.
    - `test_sim_chop_is_deterministic` — same seed ⇒ identical snapshot (`a == b`), like the other scenarios.
    - **Update `test_reserved_ticker_known_but_unresolved`:** `SIM-CHOP` is no longer the "reserved-but-unresolved" example (it is now driven). Keep the known-vs-unknown contract assertion (`build_provider("SIM-CHOP") is not None`, `build_provider("NOPE123") is None`); adjust the test's intent/comment so it no longer implies SIM-CHOP emits zero events. (All five reserved sim tickers are now driven.)
  - **Classifier test (`test_classifier.py`):** a unit mirror of the chop case — a synthetic "chop" feature dict (both ratios ≈ 0.50, wide `average_spread` e.g. 0.20, near-zero `buy/sell_price_impact`, `bid/ask_refresh_score` 0.0), warmed up (`trade_count=60`), classifies as `STATE_UNCLEAR` (and explicitly NOT any of the four resolved states). Optionally also a "balanced ratios with a *narrow* spread still ⇒ unclear" case to pin that mixed two-sided aggression alone (the load-bearing lever) denies every gate.
  - **API tests (`test_api.py`):** for a watched `SIM-CHOP`, `/state` reads `unclear` + low confidence and `/state` / `/features` / `/summary` / `WS /stream` agree (single-source-of-truth projection across the unclear state — extends J-08 coverage to the fifth state).
- **Error cases:**
  - Unknown ticker still ⇒ 400; not-watched read still ⇒ 404 (unchanged).
  - **No fabricated decisiveness:** the choppy stream must never produce a directional/absorption state or synthesized clean numbers — the honest-uncertainty + no-fabrication anti-goals. The step-through guard above is the primary defense.

## NOTES

- **Lessons applied (from the inlined `lessons.md`):**
  - *iter-4:* sized this iteration from **direct code inspection** — confirmed `SIM-CHOP` is genuinely net-new (`stream()` has no SIM-CHOP branch; it emits zero events) and that the `unclear` fallback + four gates already exist, so **no classifier/config change is needed**. Do not trust "already built" claims either way without reading the actual files.
  - *iter-2 / iter-3:* the `unclear` state renders amber via **dynamically-built** Tailwind classes; verify the amber "Unclear" render with the **base-selector** probe (`.text-amber-400{` / `.bg-amber-500{`, excluding `:hover`/variant forms) + `getComputedStyle`, never a `grep`-substring or screenshot glance. (The base utilities are already in the bundle, but confirm the on-screen computed style.)
  - *iter-5:* bounded sim streams run to exhaustion and `WatchManager.watch()` returns the **existing** engine rather than restarting — so observe the J-07 cold-start → resolved *live* transition on the **first** watch of each ticker on a fresh backend; a re-watch sees the already-resolved (possibly closed) engine. The transition message persists in the event log, so its presence is robust, but the live append is only visible cold.
  - *iter-1:* an all-SKIPPED browser run (frontend HTTP 500) is a hard signal to do verification-closure, not to advance — a backend PASS is not browser verification of J-06/J-07.
- **Why honest uncertainty is the keystone here:** the four resolved states each *earn* their call from real evidence (price impact + refresh). `unclear` must be equally earned — by genuinely mixed, wide-spread, impact-free chop — not produced by accident or by a silent provider. The simulator must make the *ambiguity* real (balanced ratios, jittery wide spread, no progress, no refresh), and the engine must decline to call a side because the evidence honestly does not support one. The step-through "never leaves unclear across the whole stream" guard is what proves the enlarged four-gate false-fire surface stays closed.
- **Coherence:** expect COHERENCE-PASS — no new displayed value, no new route/panel/control; `unclear` is an already-enumerated value of the Tape-state row with one producer / one endpoint; the chop adds only provider data + tests. `blueprint.md` updated with a purely additive realization note (no row/nav change, no reapproval).
