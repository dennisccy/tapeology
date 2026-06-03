# goal-i_will_be_rich-iter-6 Dev Handoff

**Phase:** goal-i_will_be_rich-iter-6
**Date:** 2026-06-03
**Agent:** developer
**Status:** complete

## What Was Built

The **fifth and final MVP tape state — `unclear` (J-06)** — proven against a genuinely
**driven** choppy stream, and the **honest-uncertainty** critical anti-goal demonstrated
positively. The cockpit now reads `unclear` at low confidence when the tape is genuinely
ambiguous, refusing to manufacture a directional or absorption call. This completes the
five-state taxonomy on driven data: `buyer_control` / `seller_control` / `bid_absorption` /
`ask_absorption` / **`unclear`**.

**Backend (the only product code change — `apps/backend/app/providers/simulated.py`):**
- **`_chop_stream()` (SIM-CHOP)**, wired into `SimulatedProvider.stream()` via a new
  `elif self.ticker == "SIM-CHOP"` branch. Before this iteration `stream()` had **no branch**
  for SIM-CHOP, so it emitted **zero** events and the engine sat at a cold-start `unclear`
  (0.10). It now emits a genuinely choppy, deterministic, seedable stream that **warms up and
  still reads `unclear`** (0.20).
- **The choppy shape (defense in depth).** Every rolling window (10/30/60/180/300s) denies all
  four resolved-state gates **at once**, so no single window's noise can trip one:
  - **Balanced two-sided aggression (load-bearing).** The aggressive side strictly **alternates**
    (a deterministic toggle, not the RNG) at a **constant size**, so `aggressive_buy_ratio` and
    `aggressive_sell_ratio` both stay ~0.50 — below their 0.60 floors — in every window, including
    the noise-prone 10s. Since every gate requires a one-sided ratio at/above floor, sub-floor
    ratios everywhere make every gate unreachable.
  - **Wide / jittery spread.** Every quote's spread is `uniform(0.10, 0.20)` — always above
    `max_stable_spread` (0.06) — so every window's average spread is wide, independently defeating
    the `spread <= max_stable_spread` condition of all four gates.
  - **No refresh evidence.** The quote's **near side jitters** (the ask backs off below the center
    on buy ticks, the bid above it on sell ticks), so on the matching prints the bid keeps dropping
    below its prior high and the ask rising above its prior low — both refresh scores stay below
    0.55 (so no absorption can be fabricated).
  - **No price progress.** **Every** aggressive print lands at exactly the center price (100.00):
    the buy lifts an ask placed at/under the center, the sell hits a bid placed at/over it. Because
    successive prints are at the **same** price, `buy_price_impact` and `sell_price_impact` are
    **exactly 0.0** in every window — past neither control cutoff.
  - **Warms up yet stays unclear.** The stream delivers well past `warmup_min_events` (40), so the
    read is the **warmed-up** `unclear` (`unclear_confidence` = 0.20), not the cold-start 0.10 —
    proving the engine processed real choppy data and still declined to call a side.
  - **Chop shape constants are scenario DATA** (`_CHOP_CENTER`, `_CHOP_QUOTE_JITTER`,
    `_CHOP_SPREAD_MIN/MAX`, `_CHOP_SIZE`, `_CHOP_P_MID_PRINT`, `_CHOP_DT`), placed in
    `simulated.py` alongside the existing `_START_BID` / `_P_MINORITY` shape constants — **NOT** in
    `app/config.py` and **NOT** inline in engine/classifier code.
- A **mid-spread minority** (~8% of prints) prints at the center inside a wide quote straddling it
  ⇒ `Side.UNKNOWN` (no clean aggressor), reflecting honest two-sided ambiguity without adding any
  price impact (the mid print is also at the center).

## NO classifier or config change was needed (red-flag guard — explicit)

**Per the spec's DoD and the red-flag guard: NO change was made to `app/engine/classifier.py`
or `app/config.py`, and none was needed.** I verified by direct inspection that the existing
`unclear` fallback (`classifier.py:154-158`) and the four gate conditions
(`classifier.py:76-151`, each requiring a one-sided `ratio >= floor` **and** `spread <=
max_stable_spread`) already produce `unclear` for a genuinely choppy stream. The chop reads
`unclear` purely through the **existing** logic. The `git diff` confirms only `simulated.py`
(+ tests) changed; `classifier.py` and `config.py` are byte-identical. No latent gate defect
was found — the four control/absorption states are unperturbed (regression guards green).

## A note on price impact (the one non-obvious design decision)

The spec asked for `buy_price_impact` / `sell_price_impact` to "stay near zero (past neither
control cutoff)". A first design (trades alternating at the bid/ask across a wide spread) made
the **per-side** impact accumulate to ±1–3+ — *larger* than a real directional tape (SIM-BUYER's
30s `buy_price_impact` is ~+0.43) — because each opposite-side switch adds ~one spread to the
cumulative same-side delta. That would have looked **more** decisive than the decisive case and
contradicted the honest-no-progress claim. The final design fixes this completely: by pinning
**every** aggressive print to the exact center while putting all the variation in the quote's
near side, successive prints are at one price, so **per-side impact is exactly 0.0 in every
window** — genuinely "no clean price impact", and smaller than any directional read. This is
purely simulator shape; the impact **metric** and engine are untouched.

## Files Changed

**Backend (product)**
- `apps/backend/app/providers/simulated.py` — added the `_CHOP_*` shape constants and
  `_chop_stream()`; added the `SIM-CHOP` branch to `stream()`; updated the module docstring and
  the `SIM_SCENARIOS` comment (all five reserved sim tickers are now driven). **Only** product
  file changed.

**Backend (tests)**
- `apps/backend/tests/test_scenario.py` — `test_sim_chop_settles_on_unclear` (warmed unclear,
  event_count ≥ warmup, confidence == 0.20, no spurious transition line);
  `test_sim_chop_never_misfires_a_resolved_state_step_through` (the critical event-by-event guard
  — state is **never** a resolved state at any tick, cold or warm);
  `test_sim_chop_all_windows_deny_every_gate` (the all-windows feature guard: every window has
  both ratios < 0.60, spread > 0.06, both refresh < 0.55, and impact past neither cutoff);
  `test_sim_chop_is_deterministic` (same seed ⇒ identical snapshot). Renamed
  `test_reserved_ticker_known_but_unresolved` → `test_known_vs_unknown_ticker_contract` and fixed
  its intent (SIM-CHOP is now driven; all five are; the known-vs-unknown contract still holds).
- `apps/backend/tests/test_classifier.py` — synthetic chop unit mirror
  (`test_chop_balanced_two_sided_is_warmed_unclear`) ⇒ `STATE_UNCLEAR` and explicitly none of the
  four resolved states; plus `test_chop_balanced_ratios_alone_deny_every_gate` (mixed two-sided
  aggression denies every gate even with a narrow spread + full refresh — pins the load-bearing
  lever).
- `apps/backend/tests/test_api.py` — `test_chop_views_agree_single_source` (J-08 extended to the
  fifth state: `/state` / `/features` / `/summary` / WS stream agree on the `unclear` read);
  `test_watch_sim_chop_reads_unclear_over_feeder` (live HTTP watch through the real background
  feeder — warms to unclear@0.20, never a resolved state, impacts past neither cutoff, no spurious
  transition line).

**Frontend:** none (verification-only — see the frontend handoff).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **61 passed** (53 baseline + 8 new), stable across repeated runs (ran twice end-to-end;
the live feeder tests are timing-robust — they poll until warm and freeze the feeder before the
single-source comparison).

Command: `cd apps/frontend && npm run build`
Result: **Compiled successfully**, type-check clean, 4 static pages generated (this also
regenerates a clean `.next`, de-risking the browser-QA HTTP-500 lesson).

Live HTTP smoke (real uvicorn on isolated port 8765, `TAPEOLOGY_FEED_PACE=0.02`):
- `POST /watch/SIM-CHOP` → `{"scenario":"unclear_chop","status":"watching"}`; polled `/state` →
  warmed to **`unclear` @ confidence 0.2** (`warm:true`, `stream_status:"live"`) within ~8 polls.
- `/features` 30s window: `aggressive_buy_ratio=0.513`, `aggressive_sell_ratio=0.487`
  (both < 0.60), `average_spread=0.144` (> 0.06), `buy_price_impact=0.0`, `sell_price_impact=0.0`,
  `bid_refresh_score=0.421`, `ask_refresh_score=0.20` (both < 0.55). `/summary` agrees
  (`unclear`, 0.2). Server process killed; none left running.

Empirical tuning (temporary harness, since removed): verified across N = 80…1200 trades that
**every** window holds both ratios < 0.60, spread > 0.06, both refresh < 0.55, impact = 0.0; that
the state is **never** a resolved state at **any** tick over 1200+ trades (0 violations); and that
the worst-case refresh across **all warmed ticks** (not just the end state) stays < 0.55 — i.e.
the all-windows guard holds at every tick, not only the snapshot the test asserts on.

## Known Issues

- **Every SIM-CHOP trade prints at exactly 100.00 by design.** This is what makes the per-side
  price impact exactly zero (the honest "no progress" signal). A consequence is that the Recent
  Trades panel shows a constant price with mixed buy/sell/unknown sides, and the latest quote's
  near side can sit up to `_CHOP_QUOTE_JITTER` (0.10) away from `last` (the variation lives in the
  quote, not the trade price). This is a faithful "price pinned, wide quote churning, nobody
  winning" choppy tape; nothing is fabricated. Documented inline in `simulated.py`.
- **No transition line for SIM-CHOP — and that is correct.** Cold-start `unclear` → warmed
  `unclear` is not a state change, so the engine emits no "Tape state changed to …" message. The
  absence of a spurious transition is honest behavior and is asserted in the tests. (The J-07
  transition-taxonomy verification rides the already-built resolving scenarios — SIM-BUYER /
  SIM-SELLER / absorption — whose transition lines were built and tested in prior iterations and
  are browser-verified this iteration.)
- **`stream_status = "stale"`** remains enumerated/handled but unset (no provider-gap detector
  yet) — unchanged from prior iterations.
- The on-screen **computed-style amber probe** for the `unclear` render is the browser-QA gate;
  `format.ts` already maps `unclear` to amber (`text-amber-400` / `bg-amber-500`) and the base
  utilities are confirmed in the served bundle (iter-3/iter-5). No frontend change this iteration.

## Suggested Next Phase

**J-09** — the Stop / `DELETE /watch` UI control + return-to-idle / re-watch (the next and final
Must-have journey). It needs a net-new UI control and a fresh-backend teardown verification (the
iter-5 bounded-stream gotcha applies); the stream-status-dot groundwork landed in iter-5. With
J-09, the MVP's nine Must-have journeys are complete.
