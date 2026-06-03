# Phase N — User-Visible Changes

**Phase:** goal-i_will_be_rich-iter-6
**Date:** 2026-06-03
**Written by:** ui-impact-analyst

---

## Classification summary

This iteration changed **one product source file**: `apps/backend/app/providers/simulated.py`
(+ four backend test files). Per `.claude/skills/diff-to-ui-impact.md` this is a **backend-api /
provider-data** change — but a special case: it adds a data stream to a ticker the existing UI
*already consumes*. No frontend file changed (`git diff` shows no `apps/frontend/**`), yet the
behavior the user observes on the existing `/` cockpit **does** change, because the cockpit now
receives a live driven stream for `SIM-CHOP` where it previously received none.

**Net effect for the user:** the last of the five MVP tape states — **`unclear`** — is now
demonstrable end-to-end on a genuinely *driven* choppy tape, completing the visible taxonomy
(`buyer_control` / `seller_control` / `bid_absorption` / `ask_absorption` / **`unclear`**).

---

## What Users Can Now Do

- Users can now watch **`SIM-CHOP`** (type `SIM-CHOP` in the ticker input on `/` and click
  **Watch**) and get a genuine, honest **non-call**: the Tape-state panel warms up and reads
  **"Unclear"** in **amber** at **low confidence (0.20)**, instead of sitting silently at
  cold-start. Before this iteration `SIM-CHOP` emitted zero events, so the cockpit never warmed
  up on it; now it streams a real choppy tape and the engine *still* declines to call a side.
- Users can now **see the product's honesty surface in action**: on `SIM-CHOP` the cockpit
  explicitly does **not** assert buyer control, seller control, or absorption — it shows balanced
  aggressive ratios (~0.50 each), a wide average spread, and **0.0** buy/sell price impact. The
  UI displays real, jittery, non-decisive numbers rather than manufacturing a directional read.
- Users can now observe the **complete five-state taxonomy** on the same cockpit: a decisive,
  price-impact-keyed call when evidence is clean, and an honest "Unclear" when it is not.
- Users watching a **resolving** scenario (e.g. `SIM-BUYER`, `SIM-SELLER`) **from a cold start**
  see the **"Tape state changed to <state>"** line appear **live** in the Event-log panel and the
  Observations panel update in real time over the WebSocket — closing out the transition taxonomy
  (J-07) across the now-reachable states.

---

## What Changed in the Visible UI

No UI components, routes, labels, layouts, or controls were added or modified. The changes are in
what the **existing** surfaces *display* when `SIM-CHOP` is watched:

- The **Tape-state panel** (on `/`) now renders an **amber "Unclear"** headline and an amber
  confidence bar at **0.20** for a driven `SIM-CHOP` stream (via the existing dynamic
  `stateColor`/`stateBarColor`/`stateLabel` mappings in `lib/format.ts` — unchanged code).
- The **Quote** and **Features** panels now show real choppy readouts for `SIM-CHOP`: a wide
  average spread (> 0.06), balanced aggressive buy/sell ratios (both < 0.60), and **0.0** buy/sell
  price impact — honest, non-decisive numbers.
- The **Observations panel** shows the unclear rationale (e.g. "Mixed or weak evidence — no clear
  side in control") for the choppy read.
- The **top-bar scenario indicator** displays the **`unclear_chop`** scenario label for `SIM-CHOP`
  (the label already existed; it is now backed by a driven stream).
- The **Recent Trades panel** shows a constant trade price (every chop trade prints at exactly
  100.00 by design — the "no price progress" signal) with mixed buy/sell/unknown sides.

---

## What Old Behavior Changed

- **Watching `SIM-CHOP`:** previously the cockpit received **zero events** and sat at a silent
  cold-start `unclear` (confidence 0.10) that never warmed up. Now `SIM-CHOP` streams a driven
  choppy tape, the cockpit **warms up** (event_count ≥ warmup), and reads the **warmed** `unclear`
  at **confidence 0.20**. This is the one behavior change testers must re-verify.
- **No regression to the four resolved states.** `SIM-BUYER` (buyer_control / emerald),
  `SIM-SELLER` (seller_control / rose), `SIM-BIDABS` (bid_absorption / amber), `SIM-ASKABS`
  (ask_absorption / amber) are unperturbed — the classifier and config were **not** touched. These
  remain regression guards (J-01–J-05) that must stay green.
- **No spurious transition line for `SIM-CHOP`** — and this is correct. Cold-start `unclear` →
  warmed `unclear` is not a state change, so the Event-log shows **no** "Tape state changed to …"
  message for `SIM-CHOP`. The absence of a fabricated transition is honest behavior, not a bug.

---

## Not Visible Yet

- **Stop / `DELETE /watch` control + return-to-idle / re-watch (J-09)** — backend teardown exists
  conceptually but there is **no UI control** to stop a watch and return to idle. Deferred to the
  next (final) iteration.
- **`stream_status = "stale"`** is enumerated and handled in the contract but is never set (no
  provider-gap detector yet) — no UI path exercises the stale/no-data state. Unchanged from prior
  iterations.
- No other backend capability is hidden — `SIM-CHOP` is fully reachable through the existing
  ticker input + Watch flow.
