# Goal Iteration 5 — Resolved aggressor side: quote rule + Lee-Ready tick-test fallback (J-16)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich
- **Iteration:** 5
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-16
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-15
- **Anti-goal reminders** (verbatim from `docs/goal.md`):
  - **Honest side inference, not fabrication.** The aggressor side is a documented classification (quote rule, then a Lee-Ready **tick test** against the prior trade). This inference is legitimate and MUST be applied, but the engine MUST NOT force a guess when there is no quote **and** no prior trade — such a print stays `unknown`. Inferred side MUST NOT invent quotes or trades. *(critical)*
  - **No fabricated data.** The system MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. Every real-data failure mode MUST surface an explicit, distinct state and never a cockpit. *(critical)*
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*
  - **Price impact over raw aggression.** The classifier MUST distinguish absorption from control: a tape with high one-sided aggression but no corresponding price progress MUST resolve to the matching absorption state (bid_absorption / ask_absorption), never to seller_control / buyer_control. *(critical)*
  - **Honest uncertainty.** When evidence is weak or mixed, the spread is wide, or there is no clean price impact, the state MUST be `unclear` with low confidence. The system MUST NOT manufacture a directional call to look decisive. *(critical)*
  - **No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code.
  - **Provider-agnostic engine.** The engine and API MUST depend only on the provider interface (TradeEvent / QuoteEvent / BookLevelEvent); swapping the simulator for a real feed MUST NOT require engine or API changes. A concrete vendor SDK MUST appear in only one adapter module behind a vendor-neutral seam.
  - **Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine MUST produce identical features, state, and confidence; classification MUST NOT depend on wall-clock time or randomness.
  - **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the tape. *(critical)*

## GOAL

On real (historical and live) data the recent-trades list shows a **resolved buy/sell side for the large majority of prints** — applying the quote rule first and a Lee-Ready **tick-test fallback** when no quote is in effect or the print is strictly mid-spread — so historical recent-trades is no longer dominated by `unknown`, while a genuinely undecidable print (no quote **and** no prior trade) still honestly reads `unknown`.

## BACKGROUND

The original must-have set J-01–J-15 reached **GOAL_ACHIEVED** at iter-4. `docs/goal.md` was then expanded (commit `9c1537b`) with five new must-have journeys — **J-16–J-20** (side-classification fix, prediction chart, pause/resume, local-time windows) — which are not yet in `journey-history.json` and, per direct codebase reconnaissance, are **unbuilt**. This iteration takes the **foundational, engine-isolated first slice: J-16**, because a resolved aggressor side is the substrate the prediction chart (J-17/J-18) and every real-data read depend on. Today `app/engine/aggressor.py::classify_aggressor(trade, quote)` only knows the current quote: it returns `UNKNOWN` whenever there is no quote yet or the print lands strictly between bid and ask — so real (free IEX) historical recent-trades is dominated by `unknown`. Depth is **full** because this changes a core engine module and the engine **data model** (the classifier must now carry prior-trade price + last-tick-direction state), it must be re-proven not to regress the 15 already-passing journeys (the evaluator can no longer rely on `aggressor.py` being a 0-line diff to assert the sim path is unchanged), and the no-fabrication / determinism / single-source guarantees need real unit coverage beyond a browser smoke. Subsequent iterations take J-17+J-18 (chart) together, then J-19 (pause/resume), then J-20 (local-time picker) — each its own slice.

**Re-baseline note:** J-16–J-20 have never been scored by the evaluator. Rather than spend a separate verify-only iteration, this `Mode: next` slice has its reconnaissance folded in: the codebase was inspected directly (aggressor classifier is quote-rule-only; no `/history`, no `/pause`/`/resume`, no `paused` status, no chart/charting lib, no local-time picker), so J-16–J-20 are confirmed unbuilt. The evaluator will admit J-16–J-20 into `journey-history.json` when it scores this iteration (J-16 from this slice's result; J-17–J-20 as still-failing/to-build), alongside the J-01–J-15 regression sweep this spec requires.

**Lessons carried in (from `lessons.md`):**
- *iter-2:* Real-data verification of J-16's acceptance needs a **credentialed historical replay** of a liquid name. Reuse the **capture-once committed real-Alpaca fixture** pattern (VCR-style, real epochs + prices, self-documented `note: REAL … not synthesized`) so the `unknown`-fraction reduction is deterministic and offline-reproducible *in-loop* — do **not** depend on live creds being present in QA, and never synthesize trades. Existing fixtures under `apps/backend/tests/fixtures/` are the model; if a richer mid-spread/pre-quote case is needed, **capture it from the vendor** (do not hand-author prices).
- *iter-2:* The free IEX top-of-book is **wide/noisy** for high-priced names; the tick test is exactly what rescues mid-spread prints there. The `unknown`-reduction proof should use a **liquid regular-hours window** where many prints land at/inside a moving quote.
- *iter-3/iter-4:* QA MUST build the frontend in an **isolated `.next`** (never the harness's shared one) and MUST NOT `git checkout` a file carrying uncommitted iter edits. (Lower risk here — this iteration is backend-only — but the harness frontend must stay up for the regression sweep.)
- *iter-4:* Engine determinism is load-bearing; the tick test MUST be a pure function of the ordered stream (prior trade price + carried last-non-zero direction), with **no wall-clock and no randomness**.

## IN SCOPE

### Backend
- [ ] Extend the aggressor classification in `app/engine/aggressor.py` to a **two-stage** rule: (1) **quote rule** unchanged and taking precedence — `price >= ask ⇒ BUY`, `price <= bid ⇒ SELL` using the quote in effect at the trade's timestamp; (2) **tick-test fallback**, applied only when stage 1 yields no decision (no quote in effect **or** price strictly between bid and ask): compare to the **prior trade price** — uptick (`price > prior`) ⇒ BUY, downtick (`price < prior`) ⇒ SELL, zero-tick (`price == prior`) ⇒ carry the **last non-zero tick direction**; if there is **no quote and no prior trade**, return `UNKNOWN`. Keep the function pure and deterministic.
- [ ] Carry the small additional engine state the tick test needs — the **prior trade price** and the **last non-zero tick direction** — in the engine's existing per-ticker state (prefer extending `app/engine/market_state.py`, which already holds the last trade, and/or `TapeEngine`); do **not** add a new parallel store. Wire it at the existing call site `app/engine/tape_engine.py:60` (classify BEFORE `update_trade`, so `MarketState.last` is the prior trade price at classification time — **preserve this ordering**).
- [ ] Update `classify_aggressor`'s signature as needed (e.g. accept `prior_trade_price: float | None` and `last_tick_dir: Side | None`, or an equivalent small carrier) and all internal callers; keep it provider-agnostic — it operates on `TradeEvent`/`QuoteEvent`/`Side` only, never a vendor type.
- [ ] No magic numbers: the tick test is a pure rule with no numeric cutoff. If a price-equality tolerance or any tie-break constant is introduced, it MUST be added to `app/config.py` and read from the `Config` instance — never inlined in engine/classifier code.
- [ ] Confirm the resolved side flows through the **existing single path only**: `recent_trades` rows + `FeatureEngine.add_trade(..., side)` (which feeds `aggressive_buy_ratio` / `aggressive_sell_ratio` / `net_aggressive_volume`). Do **not** add a second side computation anywhere (serializers, API, providers, or a new module). The displayed side and the feature side MUST be the one value (Data Contract row 4).

### Frontend (if applicable)
- None. The recent-trades panel already renders `side` from the snapshot (buy/sell/unknown, color-coded); a more-resolved side appears automatically with no frontend change. Do **not** recompute side in the UI.

### New user-facing capability
On real historical replay (and live), the recent-trades list now shows **buy/sell for most prints** instead of a wall of `unknown`, so the directional read of the tape — and the aggressive-ratio / net-aggressive-volume features that depend on it — is materially more truthful on real data.

### New information displayed
No new field or panel. The **same** `side` value in the recent-trades panel and the same aggressive-ratio features become **more frequently resolved** (fewer `unknown`). Per the goal, this is an intended fidelity gain, not a regression.

### New user actions
None.

### UI surface changes
None (the recent-trades panel is unchanged; it renders the already-existing `side`).

### Product surface delta
Real-data tape reads become honest about direction: where the quote-only rule left mid-spread / pre-quote prints `unknown`, the tick test now resolves them, so historical recent-trades is no longer dominated by `unknown` and the live read sharpens too — without inventing any quote or trade.

### Blueprint conformance
No new surface. This iteration lives entirely under the existing **`/` — Watch (the tape cockpit) — HOME**, in the **recent-trades panel** (the registered canonical home for J-16). It modifies the canonical owner of **Data Contract row 4 (Recent trades / side)** — the aggressor classifier — which `blueprint.md` already clarifies to be "quote rule **then** a tick-test fallback." No second computing owner, no second endpoint, no nav change.

### Data-contract additions
None. J-16 is **folded into the existing row 4** (Recent trades → side), whose canonical owner is the aggressor classifier and whose canonical endpoint stays `GET /tape/{ticker}/events` (re-exposed by `WS /stream`). The tick-test fallback is a clarification of that one owner, already recorded in `blueprint.md`. **Do not** introduce any second way to compute or serve trade side.

## OUT OF SCOPE

- The price/candlestick chart and tape-state markers (J-17/J-18) — next slice; `GET /tape/{ticker}/history` and the engine history buffer are NOT built here.
- Pause/resume (J-19) and the `POST /watch/{ticker}/pause|resume` endpoints / `paused` state — separate slice.
- Local-time historical-window picker + US-session quick-picks (J-20) — separate slice.
- Any change to the **quote-rule precedence** or the existing classifier thresholds — the quote rule still wins when a quote is in effect; the tick test only fills the gap it previously left as `unknown`.
- Any change to the tape-state classifier gates, feature formulas, or confidence boundaries (the resolved side flows into existing features unchanged; do **not** retune thresholds to chase a different state).
- Adding a second vendor or touching `app/providers/adapters/alpaca.py` beyond what a real-data verification fixture/run requires (the seam stays vendor-confined).
- Live-socket / streaming behavior changes (J-12/J-15 stay as-is; this is an engine-classification change that benefits live for free, not a feeder change).

## DEFINITION OF DONE

- [ ] Target journey **J-16** passes via browser-qa-agent: on a real liquid regular-hours historical replay (credentials configured, or a committed real-vendor fixture replayed in-loop), the recent-trades list shows **buy/sell for the large majority of prints**; at/above-ask reads buy and at/below-bid reads sell where a quote is in effect; mid-spread / pre-quote prints are resolved by the tick test; only a genuinely undecidable print (no quote **and** no prior trade) remains `unknown`; the resolved `unknown` fraction is **far lower** than the quote-only rule produced — and the side shown agrees with `GET /tape/{ticker}/events` for that same window (single source of truth).
- [ ] **Required-still-passing journeys remain green: J-01–J-15.** In particular the sim scenarios MUST be re-verified because `aggressor.py` is no longer a 0-line diff — `SIM-BUYER → buyer_control`, `SIM-SELLER → seller_control`, `SIM-BIDABS → bid_absorption`, `SIM-ASKABS → ask_absorption`, `SIM-CHOP → unclear` must all still resolve at confidence ≥ threshold, and J-08 (REST==WS==UI) must still hold.
- [ ] No anti-goal violation introduced — especially: no fabricated side (no quote **and** no prior trade still ⇒ `unknown`); the engine stays deterministic (pure function of the ordered stream); single source of truth preserved (one side value, no UI/API recomputation); the classifier stays provider-agnostic (no vendor type).
- [ ] Unit tests pass; no regressions. The full backend suite (currently **128 passed / 1 skipped (gated)**) is green, exit 0, with new tick-test tests added (test count strictly increases).
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich-iter-5-dev.md`.

## TESTING REQUIREMENTS

- **Browser (browser-qa-agent):**
  - **J-16** — Historical mode, a liquid symbol (e.g. `AAPL`) over a past **regular-hours** window, Watch; let it replay and read the recent-trades list. Assert the large majority of rows show **buy/sell** (not `unknown`), the `unknown` fraction is far lower than quote-only, and the displayed side agrees with `GET /tape/{ticker}/events` for that window (single source of truth). *(Run with credentials configured, OR against the committed real-vendor fixture replayed in-loop — never synthesized data.)*
  - **Regression sweep (must stay green):** J-01/J-02 (`SIM-BUYER → buyer_control`), J-03 (`SIM-SELLER → seller_control`), J-04 (`SIM-BIDABS → bid_absorption`), J-05 (`SIM-ASKABS → ask_absorption`), J-06 (`SIM-CHOP → unclear`), J-07 (transition messages), J-08 (REST==WS==UI), J-09 (Stop→idle), J-10 (mode reveal), J-11 (historical replay populates), J-13 (symbol search), J-14 (honest non-cockpit states). J-12/J-15 (live/stale) re-confirmed at least via the existing hermetic/gated tests if a live socket is not exercisable when QA runs.
- **Unit/integration (pytest):**
  - Extend `apps/backend/tests/test_aggressor.py`: all existing quote-rule cases still pass (quote-rule precedence). Add tick-test cases: **no quote + uptick ⇒ BUY**; **no quote + downtick ⇒ SELL**; **no quote + zero-tick ⇒ carries last non-zero direction**; **strictly-mid-spread (quote present) + uptick ⇒ BUY** (fallback fires inside the spread); **strictly-mid-spread + downtick ⇒ SELL**; **no quote AND no prior trade ⇒ UNKNOWN** (the one honest-undecidable case — assert no fabrication); **zero-tick before any non-zero tick ⇒ UNKNOWN** (no direction to carry yet).
  - A **determinism** test: replaying the same ordered event stream twice yields identical `recent_trades` sides AND identical `aggressive_buy_ratio` / `aggressive_sell_ratio` / `net_aggressive_volume` (no wall-clock/randomness).
  - A **real-data fidelity** test (extend `test_historical_provider.py` or add one): replaying the committed real liquid-window fixture through the engine yields an `unknown` side fraction **below a stated bound** and **strictly lower** than the quote-only rule on the same fixture — proving the J-16 acceptance offline. Any new fixture MUST be **captured from the vendor** (real epochs/prices, self-documented provenance), never hand-authored.
  - A **single-source** check: for a replayed window, the side shown in `recent_trades` for each print equals the side the `FeatureEngine` counted (no divergence between the displayed side and the feature side).
- **Error cases / honesty:**
  - A trade with **no quote in effect and no prior trade** MUST classify `UNKNOWN` (never BUY/SELL) — fabrication guard.
  - The tick test MUST NOT invent or mutate a quote or trade; it reads only the prior trade price + carried direction.
  - An empty/silent stream MUST NOT produce any fabricated side (no trades ⇒ no sides).

## NOTES

- **Why full depth:** core engine module change + engine data-model change (carried prior-trade price / last-tick-direction) + the evaluator can no longer lean on a 0-line `aggressor.py` diff to assert the sim path is unchanged, so the sim scenarios must be explicitly re-proven, and the no-fabrication/determinism/single-source guarantees need real unit coverage. This satisfies the goal-decomposer rule that an engine/data-model change crossing the "must not regress the passing set" boundary runs the full pipeline.
- **Quote-rule precedence is load-bearing:** the tick test is a *fallback only*. When a quote is in effect and the print is at/through it, the quote rule decides — do not let the tick test override a clean quote-rule classification. This keeps J-04/J-05 (absorption: aggressive sells at/below bid, aggressive buys at/above ask) intact.
- **Determinism boundary:** the carried "last non-zero tick direction" is per-ticker engine state seeded empty at watch start; a fresh watch (or re-watch after Stop) starts with no carried direction, so the very first zero-tick-before-any-direction print is honestly `UNKNOWN`. This is the deterministic, reproducible behavior the anti-goal requires.
- **Verification-strategy decision (decide up front, per the iter-2 lesson):** prefer the **committed real-vendor fixture replayed in-loop** as the authoritative J-16 proof (deterministic, offline, no creds needed in QA), and treat a live/credentialed historical replay as confirmatory if creds are present when QA runs. Either way: **never synthesize trades** to manufacture a low `unknown` fraction — that would itself be a critical anti-goal violation.
- **Goal-scope note (no creep):** J-16 is squarely within `docs/goal.md` Key Capability #3 (trade aggressor classification: quote rule + tick-test fallback) and the Success Criterion "Resolved aggressor side" — required must-have scope, not an embellishment.
- This is the first of the J-16–J-20 extension; `blueprint.md` was updated **additively** (rows 10–12 registered for the later slices; row 4 clarified for this one; per-journey IA homes for J-16–J-20 added, all on the existing `/` HOME) with **no nav-skeleton change**, so **no blueprint re-approval is requested** for this iteration.
- iter-4 verdict was GOAL_ACHIEVED for the *old* scope and its coherence was COHERENCE-PASS — there is no open COHERENCE-FAIL to consolidate, so this iteration may add the new scope directly.
