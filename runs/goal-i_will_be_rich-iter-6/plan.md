# goal-i_will_be_rich-iter-6 Execution Plan

Delivers the **fifth and final MVP tape state — `unclear`** — and the **honest-uncertainty**
critical anti-goal (J-06), plus close-out of the **transition taxonomy** (J-07). Backend-only
code change; browser verification is the gate. Net-new status confirmed by direct inspection:
`SIM-CHOP` is registered in `SIM_SCENARIOS` (`simulated.py:27`) but `stream()` has **no branch**
for it (`simulated.py:63-73`) — it emits zero events today, so the engine sits at cold-start
`unclear` (0.10). This iteration drives it with a genuinely choppy stream that *warms up and
still reads `unclear`* (0.20) by mixed signals.

## What to Build

- **`_chop_stream()` (SIM-CHOP) in `app/providers/simulated.py`**, wired into `stream()` (add the
  `elif self.ticker == "SIM-CHOP"` branch). Deterministic + seedable (`random.Random(self.seed)`,
  logical timestamps only). Emit only `QuoteEvent` / `TradeEvent` with `Side.UNKNOWN` — aggressor
  classification stays in the engine. The choppy shape must, over **every** rolling window
  (10/30/60/180/300s), deny all four gates by **defense in depth** (multiple independent gate
  conditions fail at once):
  - **Mixed two-sided aggression (load-bearing).** Roughly balanced buy/sell prints, **tightly
    interleaved** (not one-sided streaks), so **both** `aggressive_buy_ratio` and
    `aggressive_sell_ratio` stay **below** their `0.60` floors in **every** window — including the
    short, noise-prone **10s** window. Since all four gates require a one-sided ratio at/above its
    floor, sub-floor ratios everywhere make every gate impossible regardless of impact/refresh/spread.
  - **Wide / jittery spread.** The quote spread oscillates and averages **above** `max_stable_spread`
    (0.06) in every window — independently defeats the `spread <= max_stable_spread` condition of all
    four gates.
  - **No clean price impact, no refresh evidence.** Mid jitters up/down with **no sustained
    directional progress** → `buy_price_impact` / `sell_price_impact` near zero; the quote does **not**
    hold at one level (it jitters) → `bid_refresh_score` / `ask_refresh_score` stay **below** their
    `0.55` floors. Include some **mid-spread prints** (price strictly between bid and ask ⇒
    `Side.UNKNOWN`) to further dilute both ratios.
  - **Warms up yet stays unclear.** Deliver enough trades to pass `warmup_min_events` (40) so the read
    is the **warmed-up** `unclear` (`unclear_confidence` = 0.20), not cold-start 0.10 — proving the
    engine processed real choppy data and still honestly declined to call a side.
  - **Chop shape constants are scenario DATA**, placed in `simulated.py` alongside the existing
    `_START_BID` / `_P_MINORITY` shape constants — **NOT** in `app/config.py` and **NOT** inline in
    engine/classifier code (the no-magic-numbers anti-goal binds engine/classifier; simulator shape is data).
- **Backend tests** (below) — the real correctness proof of the enlarged four-gate false-fire surface.

### Explicitly NOT built (red-flag guard)
- **No change to `app/engine/classifier.py` or `app/config.py` is expected.** The `unclear` fallback
  (`classifier.py:154-158`) and the four gate conditions (`classifier.py:76-151`, each requiring a
  one-sided `ratio >= floor` **and** `spread <= max_stable_spread`) already produce `unclear` for a
  genuinely choppy stream. **If the developer finds a classifier/config change is required to make chop
  read unclear, that is a defect** (a mis-specified gate = latent J-01–J-05 risk) — surface it **loudly
  in the handoff**, do not silently patch.
- **No frontend code change.** `unclear` already renders amber via the dynamic
  `stateColor`/`stateBarColor`/`stateLabel` in `lib/format.ts` (proven on silent SIM-CHOP in iter-5);
  the `unclear_chop` scenario label, transition lines, and observations already render. This iteration
  **verifies** the UI against the now-active chop; it does not modify it.
- Out of scope: J-09 (Stop/`DELETE /watch` UI), any gate/confidence/config change, the unbuilt features
  `spread_change`/`liquidity_imbalance`, L2 book, persistence, and all permanent anti-goal areas
  (execution/orders, scanning, news, charting, portfolio).

## Agents Required

- **developer: yes** — backend only: author `_chop_stream()` + wire into `stream()`; add the chop
  scenario/classifier/API tests; update `test_reserved_ticker_known_but_unresolved`. No frontend code.
- **backend-data: yes** (provider scenario data + tests)
- **frontend-ux: no** (no frontend code change; browser **verification** only — see Frontend Present)

## Frontend Present: yes

(No frontend code change is expected, but J-06 and J-07 are **browser-verified** user journeys on the
existing `/` cockpit, so Chrome MCP browser checks by the QA/browser-qa agent are **required** — a
backend PASS does NOT substitute for browser verification, per the iter-1 lesson.)

## Files to Create/Modify

- `apps/backend/app/providers/simulated.py` — add `_chop_stream()` + chop shape constants; add the
  `SIM-CHOP` branch to `stream()`. (Only file with non-test product code change.)
- `apps/backend/tests/test_scenario.py` — chop resolution + step-through guard + all-windows feature
  guard + determinism; update `test_reserved_ticker_known_but_unresolved` comment/intent.
- `apps/backend/tests/test_classifier.py` — synthetic "chop" feature-dict unit mirror ⇒ `STATE_UNCLEAR`.
- `apps/backend/tests/test_api.py` — watched `SIM-CHOP`: `/state` / `/features` / `/summary` / `WS /stream`
  agree on the `unclear` read (extends J-08 single-source coverage to the fifth state).
- `runs/goal-session-i_will_be_rich/state/blueprint.md` — already carries the additive iter-6 realization
  note (lines 71-75); no further edit needed. Expect **COHERENCE-PASS** (no new row/route/panel/control).

## UI Evolution (verification-only — no frontend code change)

- **New user-facing capability:** watching `SIM-CHOP` now yields an honest **non-call** — a driven choppy
  tape reads **Unclear** at low confidence, the UI explicitly NOT asserting buyer/seller control or
  absorption (the product's honesty surface). Plus: from a cold start, any resolving scenario announces
  its state change live in the event log.
- **New information displayed:** none new in kind. The already-built `unclear` state + low confidence are
  now shown against a *driven* choppy stream (previously only cold-start silence); the already-built
  "Tape state changed to …" transition lines + observations are verified appearing live from a cold start.
- **New user actions:** none. (Stop / `DELETE /watch` UI remains J-09.)
- **UI surface changes:** none. All verification on the existing `/` cockpit (Tape-state, Event-log,
  Observations panels; top-bar scenario indicator).
- **Navigation changes:** none (single `/` route).
- **Product surface delta:** the cockpit now demonstrates the **complete five-state MVP taxonomy** end-to-end
  and browser-verifiable: `buyer_control` / `seller_control` / `bid_absorption` / `ask_absorption` / **`unclear`**.

## Visual Requirements (verification-only)

- **Component patterns:** existing hand-built panels (Tape-state panel, Event-log, Observations, Features,
  Quote). No new components.
- **Layout:** existing single-`/`-screen panel grid (1-col narrow / 2-col md / 3-col lg). Unchanged.
- **Key visual effects:** `unclear` renders **amber** (`amber-400` text / `amber-500` bar) via the dynamic
  `format.ts` mappings — confirm on-screen by **base-selector probe** (`.text-amber-400{` / `.bg-amber-500{`,
  excluding `:hover`/variant forms) + `getComputedStyle`, never a grep-substring or screenshot glance.
  Monospaced numerics for the choppy quote/feature readouts.
- **States to handle:** the live (warmed) `unclear` read streaming over WS; choppy real values in the Quote
  and Features panels (must be genuine jittery numbers, **not** fabricated decisive ones).

## Key Test Scenarios

**Backend unit/integration (`apps/backend/tests/`) — 53-test baseline must stay green, plus:**
- `test_sim_chop_settles_on_unclear` — run `SIM-CHOP` through the real engine: `snap.tape_state ==
  STATE_UNCLEAR`, `snap.warm is True`, `snap.event_count >= CONFIG.warmup_min_events`, and
  `snap.confidence == CONFIG.unclear_confidence` (strictly `< CONFIG.reasonable_confidence`) — unclear by
  *mixed signals*, not cold-start silence.
- **No-false-fire — step-through state guard (critical):** process the `SIM-CHOP` stream event-by-event;
  assert the state is **never** `buyer_control`/`seller_control`/`bid_absorption`/`ask_absorption` at **any**
  tick (always `unclear`). Proves the classified state never transiently misfires across the whole stream.
- **No-false-fire — all-windows feature guard:** on the warmed end-state snapshot, for **every** window in
  `snap.features` (10s/30s/60s/180s/300s) assert both `aggressive_buy_ratio < min_aggressive_buy_ratio` **and**
  `aggressive_sell_ratio < min_aggressive_sell_ratio`, plus `average_spread > max_stable_spread` and both
  refresh scores `< min_bid_refresh_score` / `< min_ask_refresh_score`. Give the **10s** window explicit attention.
- `test_sim_chop_is_deterministic` — same seed ⇒ identical snapshot (`a == b`).
- **Update `test_reserved_ticker_known_but_unresolved`** — keep the known-vs-unknown contract
  (`build_provider("SIM-CHOP") is not None`, `build_provider("NOPE123") is None`); fix the comment/intent so
  it no longer implies SIM-CHOP emits zero events (all five reserved sim tickers are now driven).
- `test_classifier.py` — synthetic "chop" feature dict (both ratios ≈ 0.50, wide `average_spread` ≈ 0.20,
  near-zero `buy/sell_price_impact`, refresh 0.0), `trade_count=60` ⇒ `STATE_UNCLEAR` and explicitly NOT any
  of the four resolved states. (Optional: balanced ratios + *narrow* spread still ⇒ unclear, pinning that
  mixed two-sided aggression alone denies every gate.)
- `test_api.py` — watched `SIM-CHOP`: `/state` reads `unclear` + low confidence and `/state` / `/features` /
  `/summary` / `WS /stream` agree (single-source projection across the fifth state).
- Error cases unchanged: unknown ticker ⇒ 400; not-watched read ⇒ 404.

**Browser (the real gate — Chrome MCP, Frontend Present: yes):**
- **J-06** — `SIM-CHOP` ⇒ **unclear** at low confidence (below `reasonable_confidence`); UI asserts **no**
  side and **no** absorption; amber "Unclear" headline + confidence bar confirmed by **base-selector probe +
  `getComputedStyle`** (not eyeballed, not grep-substring); values stream live over WS without reload;
  Quote/feature panels show real choppy values (no fabricated decisive numbers).
- **J-07** — from a **cold start** (first watch on a fresh backend), a resolving scenario records a **"Tape
  state changed to <state>"** line in the event log and observations update **live** over WS. Capture on
  **≥2 distinct states** (e.g. `SIM-BUYER` → buyer_control and `SIM-SELLER` → seller_control). Capture each on
  the **FIRST** watch of that ticker on a fresh backend (iter-5 bounded-stream gotcha: a re-watch of an
  exhausted sim ticker returns the already-resolved engine, so the live append is only observable cold; the
  message persists in the log thereafter). Note: `SIM-CHOP` itself produces **no** transition line
  (cold-start unclear → warmed unclear is not a state change) — that absence is correct honest behavior.
- **Regression guards (must stay green):** J-01 (six panels live on SIM-BUYER), J-02 (SIM-BUYER buyer_control),
  J-03 (SIM-SELLER seller_control), J-04 (SIM-BIDABS bid_absorption), J-05 (SIM-ASKABS ask_absorption),
  J-08 (UI ≡ REST — spot-check on `SIM-CHOP` too: UI `unclear` + confidence == `GET /tape/SIM-CHOP/state`).
- **If browser-qa SKIPS due to frontend HTTP 500 (corrupted `.next` cache):** treat as a verification-closure
  signal, NOT a pass — `rm -rf apps/frontend/.next`, restart the dev server with `NEXT_PUBLIC_API_URL` set,
  and re-run. A backend PASS is NOT browser verification of J-06/J-07 (iter-1 lesson).

## Scope & Coherence Notes

- **No goal drift / no scope creep.** J-06 + J-07 are Must-have journeys in `docs/goal.md`; `unclear` is the
  fifth MVP state; this is exactly the iter-5 evaluator's recommended next step. Surface is intentionally
  small (provider data + tests); **full depth** is justified by (1) net-new provider code on a **critical**
  anti-goal and (2) the enlarged four-gate false-fire surface that the step-through + all-windows guards close.
- **Anti-goals positively exercised:** honest-uncertainty (demonstrated against a *driven* choppy stream, not
  silence), no fabricated data, single source of truth (holds on the unclear read across all views),
  determinism (seeded), no magic numbers (chop constants are simulator data, gates untouched), and the four
  control/absorption states left **unperturbed** (regression guards above).
- **Coherence:** expect **COHERENCE-PASS** — no new displayed value, route, panel, or control; `unclear` is an
  already-enumerated value of the Tape-state row with one producer (`TapeStateClassifier`) and one canonical
  endpoint (`GET /tape/{ticker}/state`). Blueprint already updated with the additive realization note.
