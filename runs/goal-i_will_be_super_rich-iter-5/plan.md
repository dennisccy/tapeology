# goal-i_will_be_super_rich-iter-5 Execution Plan

> **STALE-ARTIFACT WARNING (read first).** The `status.json` and dev handoff already present in
> this run dir describe iter-5 as a *verify-only re-baseline* (`mode: baseline`, `depth: lean`,
> `code_changed: false`, "Nothing — this is a verify-only re-baseline"). That contradicts the
> **authoritative phase spec** (`docs/phases/goal-i_will_be_super_rich-iter-5.md`), which defines
> iter-5 as **Mode: next, Depth: full** — a real engine change that **builds J-16** (quote rule +
> Lee-Ready tick-test fallback). Those pre-existing artifacts are from a superseded/aborted decompose
> and MUST be ignored/overwritten. This plan follows the **spec** (build J-16). The developer will
> overwrite `status.json` and the iter-5 dev handoff with the real-build record.

## What to Build

- Extend `app/engine/aggressor.py::classify_aggressor` from a quote-rule-only classifier to a
  **two-stage** rule. **Stage 1 (quote rule, unchanged, takes precedence):** with a quote in effect,
  `price >= ask ⇒ BUY`, `price <= bid ⇒ SELL`. **Stage 2 (tick-test fallback, fires only when stage 1
  yields no decision** — no quote in effect **or** price strictly between bid and ask): compare to the
  **prior trade price** — uptick (`price > prior`) ⇒ BUY, downtick (`price < prior`) ⇒ SELL,
  zero-tick (`price == prior`) ⇒ carry the **last non-zero tick direction**. If there is **no quote
  and no prior trade** (or a zero-tick before any non-zero direction exists) ⇒ `UNKNOWN`. Keep the
  function pure and deterministic.
- Carry the small extra engine state the tick test needs — **prior trade price** and **last non-zero
  tick direction** — in the **existing** per-ticker state (extend `app/engine/market_state.py`, which
  already holds the last trade, and/or hold the carried direction in `TapeEngine`). Do **not** add a
  new parallel store.
- Wire it at the existing call site in `app/engine/tape_engine.py` (currently line ~60): classify
  **before** `self._market.update_trade(event)` so `MarketState.last` is still the **prior** trade
  price at classification time. **Preserve this quote-before-trade / classify-before-update ordering.**
- Update `classify_aggressor`'s signature minimally (e.g. add `prior_trade_price: float | None` and
  `last_tick_dir: Side | None`, or an equivalent small carrier) and update its internal callers. Keep
  it provider-agnostic — it operates only on `TradeEvent` / `QuoteEvent` / `Side`, never a vendor type.
- Confirm the resolved side flows through the **existing single path only**: `recent_trades` rows +
  `FeatureEngine.add_trade(ts, price, size, side)` (which feeds `aggressive_buy_ratio` /
  `aggressive_sell_ratio` / `net_aggressive_volume`). Do **not** add a second side computation anywhere
  (serializers, API, providers, UI, or a new module). The displayed side and the feature side are the
  one value (Data Contract row 4 / single source of truth).
- Add unit + determinism + real-data-fidelity + single-source tests (see Key Test Scenarios).
- Write the dev handoff to `docs/handoffs/goal-i_will_be_super_rich-iter-5-dev.md` (overwriting the
  stale verify-only one).

## Agents Required

- developer: **yes** — backend engine change only (aggressor classifier + carried engine state + the
  single call-site wiring) plus pytest coverage. No frontend code.

## Frontend Present

no

> Rationale for `no`: this is an **engine-classification** change. The recent-trades panel already
> renders `side` (buy/sell/unknown, color-coded) from the snapshot; a more-resolved side appears
> automatically with **zero** frontend change, and the spec's "Frontend (if applicable): None" and
> machine-readable `Frontend Present: no` confirm it. The user-visible *effect* (fewer `unknown`
> rows on real historical replay) is real, but it is delivered through the unchanged UI surface.
> The J-16 acceptance is proven authoritatively by the **in-loop real-fixture pytest** (deterministic,
> offline, no creds) per the iter-2 lesson; a credentialed browser replay is confirmatory only.

## Files to Create/Modify

- `apps/backend/app/engine/aggressor.py` -- add the two-stage rule (quote rule precedence + tick-test
  fallback); update signature/docstring.
- `apps/backend/app/engine/market_state.py` -- expose the **prior** trade price for the classifier
  (it already stores `_last_trade`; add the small accessor the tick test needs) and/or carry the
  last non-zero tick direction. Keep `spread`/`bid`/`ask`/`last` single-source as-is.
- `apps/backend/app/engine/tape_engine.py` -- pass prior-trade price + carried last-tick direction
  into `classify_aggressor` at the existing call site (classify BEFORE `update_trade`), and update the
  carried direction after each non-zero tick. Seed carried direction empty at construction (fresh
  watch / re-watch after Stop starts with no carried direction).
- `apps/backend/app/config.py` -- **only if** a price-equality tolerance or tie-break constant is
  introduced (e.g. exact-equality vs epsilon for zero-tick). If so, add it to `Config` and read it
  from the instance — **never inline a literal** in engine/classifier code. If exact `==` is used,
  no config change is needed (preferred — the tick test is a pure rule with no numeric cutoff).
- `apps/backend/tests/test_aggressor.py` -- keep all existing quote-rule cases green; add the
  tick-test cases (see Key Test Scenarios). Test count must strictly increase.
- `apps/backend/tests/test_historical_provider.py` (or a sibling) -- add the **real-data fidelity**
  test: replay the committed Ford fixture through the engine and assert the resolved `unknown`
  fraction is **below a stated bound** AND **strictly lower** than the quote-only rule on the same
  fixture; add the **single-source** check (per-print `recent_trades` side == the side `FeatureEngine`
  counted) and a **determinism** check (replay twice ⇒ identical sides + identical
  `aggressive_buy_ratio` / `aggressive_sell_ratio` / `net_aggressive_volume`).
- `docs/handoffs/goal-i_will_be_super_rich-iter-5-dev.md` -- overwrite the stale verify-only handoff
  with the real J-16 build record (what was built, files changed, exact test counts, known issues).
- `runs/goal-i_will_be_super_rich-iter-5/status.json` -- overwrite stale `mode/depth/code_changed`
  with the real build state.

## Grounding notes for the developer (verified against the working tree)

- **Existing real fixture is sufficient for the J-16 proof — no new capture strictly required.**
  `apps/backend/tests/fixtures/alpaca/F_20260602_150000_20260602_150200.json` (Ford, IEX, self-doc
  `note: REAL captured market data — not synthesized`) has **65 trades / 1772 quotes** and contains
  **mid-spread prints**: with the prevailing penny quote `bid=16.56 / ask=16.57`, trades print at
  `16.565 / 16.555 / 16.545 / 16.585 / 16.595` (half-cent prints strictly inside the spread). Under
  the quote-only rule these are `unknown`; the tick test resolves them — exactly the fidelity gain
  J-16 exists to show. Loader: `tests/fakes.py::load_fixture_window()`. If a richer pre-quote
  (no-quote-yet) case is wanted, capture it with `apps/backend/scripts/capture_alpaca_fixture.py` —
  **never hand-author prices.**
- **The blueprint already registers this.** `blueprint.md` Data Contract **row 4** already reads
  "quote rule … **then a tick-test fallback** (no quote yet **or** strictly mid-spread ⇒
  uptick=buy / downtick=sell / zero-tick carries last non-zero dir; no quote **and** no prior trade ⇒
  `unknown`)". Canonical owner = the aggressor classifier; canonical endpoint stays
  `GET /tape/{ticker}/events` (re-exposed by `WS /stream`). **No new endpoint, no nav change, no
  blueprint re-approval** (additive clarification only).
- **Ordering is load-bearing.** `tape_engine.process_event` already classifies with `self._market.quote`
  *before* `self._market.update_trade(event)`. Keep that; the prior-trade price must be read in the
  same window (before the current trade overwrites `last`).

## Out-of-Scope (flag — exclude; do NOT build)

- The price/candlestick chart + tape-state markers and `GET /tape/{ticker}/history` / engine history
  buffer (**J-17 / J-18**) — next slice.
- Pause/resume + `POST /watch/{ticker}/pause|resume` + `paused` stream status (**J-19**) — separate slice.
- Local-time historical-window picker + US-session quick-picks (**J-20**) — separate slice.
- Any change to **quote-rule precedence** or existing classifier thresholds — the quote rule still
  wins when a quote is in effect; the tick test only fills the gap it previously left `unknown`.
- Any retune of tape-state gates, feature formulas, or confidence boundaries (resolved side flows into
  existing features unchanged — do **not** chase a different state).
- A second vendor / touching `app/providers/adapters/alpaca.py` beyond what a verification fixture/run
  needs (the vendor seam stays confined).
- Any live-socket / streaming behavior change (J-12 / J-15 unchanged — this benefits live for free).

## Key Test Scenarios

**Unit — `test_aggressor.py` (all existing quote-rule cases stay green; quote rule precedence):**
- no quote + uptick ⇒ **BUY**
- no quote + downtick ⇒ **SELL**
- no quote + zero-tick ⇒ **carries last non-zero direction**
- strictly-mid-spread (quote present) + uptick ⇒ **BUY** (fallback fires *inside* the spread)
- strictly-mid-spread (quote present) + downtick ⇒ **SELL**
- **no quote AND no prior trade ⇒ UNKNOWN** (the one honest-undecidable case — fabrication guard)
- zero-tick before any non-zero tick exists ⇒ **UNKNOWN** (no direction to carry yet)
- (regression) quote present + at/through quote ⇒ quote rule decides; tick test does **not** override
  a clean quote-rule classification (protects J-04 / J-05 absorption).

**Determinism:** replay the same ordered stream twice ⇒ identical `recent_trades` sides **and**
identical `aggressive_buy_ratio` / `aggressive_sell_ratio` / `net_aggressive_volume` (no
wall-clock/randomness).

**Real-data fidelity (in-loop, the authoritative J-16 proof):** replay the committed Ford fixture
through the engine ⇒ resolved `unknown` fraction is **below a stated bound** and **strictly lower**
than the quote-only rule on the same fixture. Any new fixture is **captured from the vendor**
(real epochs/prices, self-documented provenance), never hand-authored.

**Single source of truth:** for a replayed window, each print's side in `recent_trades` equals the
side `FeatureEngine` counted (no divergence between displayed side and feature side).

**Honesty / error cases:** trade with no quote **and** no prior trade ⇒ `UNKNOWN` (never BUY/SELL);
the tick test never invents/mutates a quote or trade (reads only prior price + carried direction); an
empty/silent stream produces **no** fabricated side (no trades ⇒ no sides).

**Regression sweep — MUST stay green (the spec's required-still-passing set, J-01–J-15):**
- Sim scenarios re-proven (because `aggressor.py` is no longer a 0-line diff): `SIM-BUYER → buyer_control`,
  `SIM-SELLER → seller_control`, `SIM-BIDABS → bid_absorption`, `SIM-ASKABS → ask_absorption`,
  `SIM-CHOP → unclear`, each at confidence ≥ threshold.
- J-07 transitions, J-08 REST==WS==UI single source, J-09 Stop→idle / re-watch fresh, J-10 mode reveal,
  J-11 historical replay populates, J-13 symbol search, J-14 honest non-cockpit states.
- J-12 / J-15 (live / stale) re-confirmed via the existing hermetic/gated tests if a live socket
  isn't exercisable when QA runs.

**Suite gate:** the full backend suite (currently **128 passed / 1 skipped-gated**) is green, exit 0,
with new tick-test tests added so the **test count strictly increases**.

## Definition of Done (from the spec)

- J-16 satisfied: on the real liquid regular-hours replay (credentialed run **or** the committed
  Ford fixture replayed in-loop) the recent-trades list shows **buy/sell for the large majority of
  prints**; at/above-ask reads buy, at/below-bid reads sell; mid-spread / pre-quote prints resolved by
  the tick test; only a no-quote-**and**-no-prior-trade print stays `unknown`; resolved `unknown`
  fraction **far lower** than quote-only; the side agrees with `GET /tape/{ticker}/events`.
- J-01–J-15 remain green (sim scenarios + J-08 single source re-verified).
- No anti-goal violation: no fabricated side, deterministic pure function, single source preserved,
  classifier stays provider-agnostic, no magic numbers.
- Full backend suite green (exit 0); test count strictly increases.
- Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich-iter-5-dev.md`.
