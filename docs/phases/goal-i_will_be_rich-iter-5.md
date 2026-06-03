# Goal Iteration 5 — Absorption pair: bid_absorption (J-04) & ask_absorption (J-05) — price impact, not aggression

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_rich
- **Iteration:** 5
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-04, J-05
- **Required-still-passing journeys:** J-01, J-02, J-03, J-08
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the tape. *(critical)*
  - **Stay in scope.** No stock scanner/screener, no news/theme/sentiment analysis, no fundamental analysis, no chart-pattern or indicator charting, no portfolio/position management — these belong to separate projects and MUST NOT be built here. *(critical)*
  - **Price impact over raw aggression.** The classifier MUST distinguish absorption from control: a tape with high one-sided aggression but no corresponding price progress MUST resolve to the matching absorption state (bid_absorption / ask_absorption), never to seller_control / buyer_control. Keying on aggression ratios alone is a defect. *(critical)* — **THE keystone of this iteration.**
  - **Honest uncertainty.** When evidence is weak or mixed, the spread is wide, or there is no clean price impact, the state MUST be `unclear` with low confidence. The system MUST NOT manufacture a directional call to look decisive. *(critical)*
  - **No fabricated data.** On a provider gap/failure the system MUST surface an explicit stale/no-data state and MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. *(critical)*
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*
  - **No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code.
  - **Provider-agnostic engine.** The engine and API MUST depend only on the provider interface (TradeEvent / QuoteEvent / BookLevelEvent); swapping the simulator for a real feed MUST NOT require engine or API changes.
  - **Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine MUST produce identical features, state, and confidence; classification MUST NOT depend on wall-clock time or randomness. Each simulated scenario MUST have an automated test asserting the expected state is reached with reasonable confidence.
  - **No ML in v1.** The MVP classifier MUST be transparent rule/threshold logic over named features — no trained model in the first version.
  - **No trade/profit claims.** The product MUST NOT claim profitability or present output as trading advice; tape state is descriptive, not prescriptive.
  - **No secrets in source.** No API keys, tokens, or credentials committed; any future provider keys come from environment/config only.

## GOAL

Watching `SIM-BIDABS` settles the cockpit on **bid_absorption** (not seller_control) and watching `SIM-ASKABS` settles on **ask_absorption** (not buyer_control) — proving the product's defining claim: when one-sided aggression is high but price makes no matching progress, the tape is *absorbing*, not *in control*. Both reads render live in amber with elevated absorption / refresh readouts and an absorption message in the event log.

## BACKGROUND

This is the **defining price-impact case** and the single most safety-critical anti-goal surface in the whole product. `buyer_control` (iter-1, J-02) and `seller_control` (iter-4, J-03) are both built, each gated on *real* price progress (positive `buy_price_impact` / negative `sell_price_impact`). That negative-impact guard is exactly the prerequisite that makes absorption testable: bid_absorption is *high aggressive sell volume with the price refusing to fall* — the same high `aggressive_sell_ratio` as seller_control, but with `sell_price_impact ≈ 0` because the bid refreshes at the same price. The iter-4 evaluator recommended advancing to J-04 at **full** depth with J-05 as its paired mirror, and folding in the thrice-deferred stream-status-dot coherence consolidation here.

**This work is net-new — confirmed by direct code inspection (not by trusting forward-carried notes; see lessons iter-4).** `classifier.py` has only `STATE_BUYER_CONTROL` / `STATE_SELLER_CONTROL` / `STATE_UNCLEAR`; `features.py` `FEATURE_NAMES` has 9 of the 14 features and explicitly defers `absorption_score` / `bid_refresh_score` / `ask_refresh_score`; `config.py` has no absorption thresholds; `simulated.py` has `SIM-BIDABS`/`SIM-ASKABS` registered but their streams emit **zero** events (the `stream()` dispatch only handles SIM-BUYER/SIM-SELLER). The frontend already maps `bid_absorption`/`ask_absorption` → "Bid/Ask Absorption" amber labels (`format.ts`), and the amber base utility classes are confirmed in the served Tailwind bundle (iter-3 latent-class guard via the `./lib/**` content glob) — but `FeaturesPanel.tsx` renders a **fixed** 9-row `FEATURE_ROWS` list, so the new absorption features will NOT appear until rows are added.

Full depth is correct: net-new backend across features + classifier + provider + config, the highest-stakes anti-goal (price-impact-not-aggression) with its keystone guard tests, plus a frontend feature-row addition and a coherence consolidation. Depth is NOT a thin verify pass.

## IN SCOPE

### Backend

- [ ] **Feature engine (`app/engine/features.py`)** — add three features to `FEATURE_NAMES` and compute them in `_Window.compute()`, additively (the existing 9 features MUST remain byte-identical — additive only):
  - [ ] `bid_refresh_score` — among the aggressive-**sell** prints in the window (prints the engine tagged `Side.SELL`, i.e. hitting the bid), the fraction after which the **bid did not fall** (held/refreshed at ≥ its prior level). High (→1.0) when the bid holds under selling (SIM-BIDABS); low when the bid walks down (SIM-SELLER). A pure, deterministic function of in-window events.
  - [ ] `ask_refresh_score` — the strict mirror: among aggressive-**buy** prints (hitting the ask), the fraction after which the **ask did not rise**. High when the ask holds under buying (SIM-ASKABS); low when the ask walks up (SIM-BUYER).
  - [ ] `absorption_score` — a single summary measure of "high one-sided aggression with little/no price progress": elevated when the dominant aggressive ratio is high **and** that side's price impact is flat (near zero). Deterministic; scales/cutoffs from config.
  - [ ] To compute the refresh scores the window needs the **bid/ask price series**, which it does not currently store (it stores only `(ts, spread)`). Extend `_Window`/`FeatureEngine.add_quote(...)` and the `TapeEngine.process_event` quote branch to thread `bid` and `ask` (additively) so refresh can be computed. Do not change how `average_spread` or any existing feature is computed.
- [ ] **Config (`app/config.py`)** — add absorption thresholds/boundaries; NO literal in engine/classifier code (no-magic-numbers anti-goal):
  - [ ] Gate floors: `min_bid_refresh_score`, `min_ask_refresh_score` (and `min_absorption_score` if the gate uses it).
  - [ ] The absorption impact condition reuses the existing control cutoffs as the boundary — bid_absorption requires `sell_price_impact` **above** the negative `max_sell_price_impact` (i.e. price did NOT fall meaningfully); ask_absorption requires `buy_price_impact` **below** the positive `min_buy_price_impact` (price did NOT rise meaningfully). Add an absorption impact band / near-zero ceiling in config only if the developer's design needs one — do not inline it.
  - [ ] Any absorption-specific confidence scales/weights (the absorption confidence rewards flat impact, so it cannot reuse the directional impact component unchanged) — all in config.
- [ ] **Classifier (`app/engine/classifier.py`)** — add `STATE_BID_ABSORPTION = "bid_absorption"` and `STATE_ASK_ABSORPTION = "ask_absorption"`, and insert two gates **after** the buyer/seller control gates and **before** the final `unclear` fallback (control takes precedence whenever real price progress exists):
  - [ ] **bid_absorption gate** — `aggressive_sell_ratio >= min_aggressive_sell_ratio` AND `sell_price_impact > max_sell_price_impact` (no real drop — the complement of the seller-control impact condition) AND `bid_refresh_score >= min_bid_refresh_score` (positive absorption evidence) AND stable spread; emit only at confidence `>= reasonable_confidence`, else stay `unclear`.
  - [ ] **ask_absorption gate** — the mirror on the buy side (`aggressive_buy_ratio` high, `buy_price_impact < min_buy_price_impact`, `ask_refresh_score >= min_ask_refresh_score`, stable spread).
  - [ ] Absorption confidence function(s) + per-tick observations (e.g. for bid_absorption: "Heavy sell volume being absorbed", "Bid refreshing at <price>", "Price holding despite sell prints"). Transparent threshold logic only — no ML.
  - [ ] **Keystone precedence (the critical anti-goal):** high sell aggression **with** real negative impact ⇒ `seller_control`; high sell aggression with **flat** impact + bid refresh ⇒ `bid_absorption` (never `seller_control`, never silently `unclear`). Symmetric for buy/ask. The gates are mutually exclusive on the impact condition, so the two cannot both fire.
- [ ] **Observations / event log** — an absorption-specific message MUST reach the event log on the absorption read (J-04/J-05 acceptance), e.g. "Large sell print absorbed" / "Bid refreshing at <price>" (bid) and "Large buy print absorbed" / "Ask refreshing at <price>" (ask). Generate it **once** in the engine (single source of truth); keep the existing state-transition line ("Tape state changed to bid_absorption" / "…ask_absorption") working. No fabrication — the message must reflect real in-window evidence.
- [ ] **Simulated provider (`app/providers/simulated.py`)** — author the two absorption streams and wire them into `stream()` (currently they emit nothing). Deterministic + seedable; emit only `QuoteEvent`/`TradeEvent` with `Side.UNKNOWN` (aggressor classification stays downstream in the engine):
  - [ ] `_bid_absorption_stream()` (SIM-BIDABS) — majority aggressive **sells** print at the bid, but the **bid holds at the same price** (refreshes — does NOT drop). Result over the primary window: `aggressive_sell_ratio` high, `sell_price_impact ≈ 0` (above the −cutoff — no real drop), `bid_refresh_score` high, large prints present (absorbed). Contrast SIM-SELLER, where the bid walks down so `sell_price_impact` is strongly negative.
  - [ ] `_ask_absorption_stream()` (SIM-ASKABS) — the mirror: majority aggressive **buys** print at the ask, the **ask holds**; `aggressive_buy_ratio` high, `buy_price_impact ≈ 0`, `ask_refresh_score` high.
- [ ] **(Coherence consolidation — fold-in, thrice-deferred)** Drive the top-bar **stream-status dot** from the engine's canonical `snapshot.stream_status`, not the client `connStatus`. This is a backend-contract-enforcing frontend change (see Frontend) — listed here because it closes the Data-Contract "watch/stream status" row's single-source rule. No backend code change is required for it; `stream_status` already transitions `connecting → live → closed` (set in `watch_manager._feed`).

### Frontend

- [ ] **`components/FeaturesPanel.tsx`** — add three rows to the fixed `FEATURE_ROWS` so the absorption readouts are visible (required for J-04/J-05 "read the absorption / bid-refresh readouts"): `absorption_score`, `bid_refresh_score`, `ask_refresh_score` (sensible labels, 3 decimals, not color-by-sign). Existing rows unchanged.
- [ ] **Tape-state rendering** — `bid_absorption`/`ask_absorption` already resolve to amber via the dynamic `stateColor`/`stateBarColor`/`stateLabel` in `lib/format.ts`; verify (do not assume) the **first on-screen amber render of a RESOLVED absorption state** computes amber — measure the headline `text-amber-400` and the confidence-bar `bg-amber-500` with `getComputedStyle` **and** a base-selector stylesheet probe (`.text-amber-400{` / `.bg-amber-500{`, excluding `:hover`/variant forms), NOT a screenshot glance and NOT a `grep`-substring (lessons iter-2/iter-3).
- [ ] **Stream-status dot (`components/TopBar.tsx`, and the `page.tsx`/`Cockpit` data flow that feeds it)** — display the canonical `snapshot.stream_status` from the engine when a snapshot is present (map its values — connecting/live/stale/closed — to the dot color/label), falling back to the client `connStatus` only for the pre-snapshot idle/connecting affordance. This removes the parallel client-side source of "is the stream live" and fixes the real divergence: the WS loop in `main.py` pushes until the client disconnects, so when a bounded sim stream exhausts and the engine flips `stream_status → "closed"`, today's dot still reads client `connStatus = "live"` (a false "live"). Must NOT destabilize the live dot on J-01/J-02/J-03.

### New user-facing capability

The user can watch the two absorption scenarios and get an honest, *non-directional-when-appropriate* read: `SIM-BIDABS` shows **Bid Absorption** (heavy selling being absorbed, price holding) and `SIM-ASKABS` shows **Ask Absorption** (heavy buying being absorbed, price stalling) — each with confidence, absorption/refresh feature readouts, amber state coloring, observations, and an absorption event-log message. The top-bar stream-status dot now tells the truth about whether the engine's stream is live or closed.

### New information displayed

- Three new feature rows in the Features panel: `absorption_score`, `bid_refresh_score`, `ask_refresh_score` (per window).
- Two newly reachable tape states in the Tape-state panel rendered in amber: **Bid Absorption**, **Ask Absorption**, each with its confidence.
- Absorption observations and an absorption event-log message.

### New user actions

None. (No new controls — the Stop control / `DELETE /watch` UI remains J-09, out of scope. The ticker input + Watch already reach both new scenarios.)

### UI surface changes

No new page or route. All changes are within the existing `/` cockpit: the Features panel gains three rows; the Tape-state panel renders two already-styled amber states; the Observations and Event-log panels show absorption messages; the top-bar dot reads the canonical stream status.

### Product surface delta

The cockpit now demonstrates the product's headline differentiator end-to-end: identical high aggression resolves to *control* or *absorption* purely on whether price actually moved. Four of the five tape states are now reachable and browser-verifiable (buyer/seller control + bid/ask absorption); only `unclear`-by-active-chop (J-06) remains.

### Blueprint conformance

No new Information-Architecture surface. Everything lives on the existing `/` cockpit home (the only route). The absorption feature readouts live in the existing Features panel; the absorption states in the existing Tape-state panel; absorption messages in the existing Observations/Event-log panels — all the canonical homes already registered in `blueprint.md`. The stream-status-dot consolidation brings the implementation into conformance with the blueprint's existing app-shell description (the dot reflects the engine's canonical stream status).

### Data-contract additions

**None (rides existing contract rows — like iter-4's seller_control).**
- `absorption_score` / `bid_refresh_score` / `ask_refresh_score` complete the already-registered **"14 core features × 5 windows"** row through its one canonical producer `FeatureEngine` and one canonical endpoint `GET /tape/{ticker}/features` (re-exposed read-only by `/summary`'s headline subset + `WS /stream`). No second producer, no new endpoint.
- `bid_absorption` / `ask_absorption` are **already-enumerated values** of the existing **"Tape state + confidence"** row, produced once by `TapeStateClassifier` and served by `GET /tape/{ticker}/state`.
- The stream-status dot now **reads** the canonical `snapshot.stream_status` (the existing "watch/stream status" row) instead of a parallel client value — enforcing, not adding to, the contract.
- `blueprint.md` has been kept current with a purely additive realization note (no new row, no nav change, no reapproval required).

## OUT OF SCOPE

- **J-06** (active SIM-CHOP stream that resolves to `unclear` by mixed signals/wide spread) — next after this pair; a silent provider already yields honest `unclear`, but J-06 needs an *actively choppy* stream.
- **J-07** (full cold-start cross-state transition taxonomy) — the absorption transition/observation messages built here advance it, but verifying the full taxonomy is its own iteration.
- **J-09** (Stop / `DELETE /watch` UI control + return-to-idle) — no new control this iteration; the stream-status-dot consolidation that J-09 depends on lands here as groundwork.
- The remaining un-built features `spread_change`, `liquidity_imbalance` (and later `liquidity_pull_score`) — not needed for absorption; defer to their owning iterations.
- Level-2 book ingestion (`BookLevelEvent`), persistence, replay/backtest, any extended states — all explicitly later/nice-to-have in `docs/goal.md`.
- Anything touching execution/orders, scanning, news, charting, portfolio (permanent anti-goals).

## DEFINITION OF DONE

- [ ] **J-04** passes via browser-qa-agent: watching `SIM-BIDABS`, the tape state settles on **bid_absorption** (NOT seller_control) at confidence ≥ `reasonable_confidence`; `aggressive_sell_ratio` reads high while the last price does **not** move meaningfully lower; `absorption_score` / `bid_refresh_score` read elevated; the event log shows an absorption message (e.g. "Large sell print absorbed" / "Bid refreshing at <price>"); rendered live in amber over WebSocket without reload.
- [ ] **J-05** passes via browser-qa-agent: watching `SIM-ASKABS`, the tape state settles on **ask_absorption** (NOT buyer_control) at confidence ≥ threshold; `aggressive_buy_ratio` high while the last price does **not** move meaningfully higher; `absorption_score` / `ask_refresh_score` elevated; the event log shows an absorption message (e.g. "Large buy print absorbed" / "Ask refreshing at <price>"); live amber render.
- [ ] **Required-still-passing journeys remain green:** J-01 (six panels live on SIM-BUYER), J-02 (SIM-BUYER still `buyer_control`, green, NOT misrouted to ask_absorption), J-03 (SIM-SELLER still `seller_control`, rose, NOT misrouted to bid_absorption), J-08 (UI ≡ REST — including at least one absorption feature, e.g. `bid_refresh_score` UI value == `/features` value, and the tape state/confidence UI == `/state`).
- [ ] The first on-screen amber render of a resolved absorption state is confirmed by computed-style + base-selector probe (not eyeballed, not grep-substring).
- [ ] The top-bar stream-status dot reflects the canonical `snapshot.stream_status` (matches `GET /tape/{ticker}/summary`'s `stream_status`); the live dot on the directional scenarios is unaffected.
- [ ] No anti-goal violation introduced (price-impact-not-aggression positively demonstrated by the SIM-BIDABS→bid_absorption / SIM-ASKABS→ask_absorption guard tests; no fabricated data; single source of truth; determinism; no magic numbers).
- [ ] Unit tests pass (the 31-test baseline plus the new absorption tests below); no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_rich-iter-5-dev.md`.

## TESTING REQUIREMENTS

- **Browser (the real gate):**
  - J-04 — `SIM-BIDABS` → **bid_absorption** (NOT seller_control), high sell ratio + flat last price + elevated absorption/bid-refresh readouts + absorption event-log message, amber render measured by probe, live over WS.
  - J-05 — `SIM-ASKABS` → **ask_absorption** (NOT buyer_control), mirror assertions.
  - Re-verify J-01, J-02, J-03, J-08 unchanged (regression guards).
  - If browser-qa SKIPS because the frontend returns HTTP 500 (corrupted `.next` cache), treat it as a verification-closure signal, not a pass: `rm -rf apps/frontend/.next`, restart the dev server with `NEXT_PUBLIC_API_URL` set, and re-run — a backend PASS does NOT substitute for browser verification of J-04/J-05 (lesson iter-1).
- **Unit/integration (`apps/backend/tests/`):**
  - **Classifier guard tests (the keystone — `test_classifier.py`):**
    - High `aggressive_sell_ratio` + `sell_price_impact ≈ 0`/above the −cutoff + high `bid_refresh_score` + stable spread ⇒ **bid_absorption** (assert NOT seller_control AND NOT unclear).
    - High `aggressive_sell_ratio` + real **negative** `sell_price_impact` ⇒ **seller_control** (assert NOT bid_absorption — control precedence).
    - Mirror pair for ask/buy: flat ⇒ ask_absorption (not buyer_control/unclear); real positive impact ⇒ buyer_control (not ask_absorption).
    - Wide spread blocks absorption (stays unclear).
  - **Feature tests (`test_features.py`):** `bid_refresh_score` high when the bid holds under sell prints / low when it walks down; `ask_refresh_score` mirror; `absorption_score` high on high-ratio-flat-impact and low on real-impact; the existing 9 feature values are unchanged by the `add_quote` bid/ask threading.
  - **Scenario tests (`test_scenario.py`):** `SIM-BIDABS` deterministically reaches `bid_absorption` at confidence ≥ `reasonable_confidence` within warm-up; `SIM-ASKABS` reaches `ask_absorption`; **SIM-BUYER still buyer_control and SIM-SELLER still seller_control** (no misroute/regression); a determinism test per new scenario (same seed ⇒ identical state/confidence).
  - **API tests (`test_api.py`):** `/state`, `/features`, `/summary`, `WS /stream` for a watched absorption ticker agree on tape_state/confidence and the absorption feature values (single-source-of-truth projection).
- **Error cases:**
  - Unknown ticker still ⇒ 400; not-watched read still ⇒ 404; no fabricated absorption — a silent/cold provider (no refresh evidence) stays honest `unclear`, since the absorption gate requires real `*_refresh_score` evidence, not mere absence of impact.

## NOTES

- **Lessons applied (from the inlined `lessons.md`):**
  - *iter-4:* sized this iteration from **direct code inspection**, not forward-carried notes — confirmed absorption is entirely net-new (classifier states, the 3 features, the config cutoffs, and both sim streams are all absent). Do not trust "already built" claims for engine/provider/config paths.
  - *iter-3 / iter-2:* the absorption states render amber via **dynamically-built** Tailwind classes (`stateColor`/`stateBarColor` return strings). The base utilities are in the bundle (iter-3 `./lib/**` glob fix), but the first on-screen render of a resolved absorption state must still be confirmed with the **base-selector** probe (`.text-amber-400{` / `.bg-amber-500{`) + `getComputedStyle`, explicitly excluding `:hover`/variant forms — never a `grep`-substring or a screenshot glance.
  - *iter-1:* an all-SKIPPED browser run (frontend HTTP 500) is a hard signal to do verification-closure, not to advance — backend PASS + clean build is NOT browser verification of J-04/J-05.
- **Why this is the hardest/most important iteration:** it is the product's reason to exist (price impact, not aggression) and its most safety-critical anti-goal. The simulators must make the distinction *earned*: SIM-BIDABS's bid genuinely holds (cumulative `sell_price_impact` stays near zero) while SIM-SELLER's bid genuinely walks down (strongly negative) — the classifier keys on that real difference, never on the ratio alone.
- **Symmetry discipline:** mirror the buyer/seller precedent — shared side-neutral config where it already exists (`max_stable_spread`, `min_trade_speed`, the ratio floors), absorption-specific cutoffs added only where the semantics genuinely differ (refresh scores, flat-impact band). Keep the amber absorption labels/observations consistent with the green/rose directional language.
- **Coherence:** expect COHERENCE-PASS — additive values on existing contract rows, one producer / one endpoint each, no new route or parallel shell; the stream-status-dot change removes a parallel source rather than adding one.
