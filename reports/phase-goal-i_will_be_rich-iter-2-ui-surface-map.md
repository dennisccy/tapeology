# Phase goal-i_will_be_rich-iter-2 — UI Surface Map

**Phase:** goal-i_will_be_rich-iter-2
**Date:** 2026-06-02
**Written by:** ui-impact-analyst

> **No UI surface was modified this iteration** (zero frontend code change; the diff is two backend lines).
> This is a **verification-closure** pass: its job is to browser-prove the *existing* iter-1 `SIM-BUYER`
> cockpit (J-01 / J-02 / J-08). The table below therefore lists the **existing surfaces that browser QA must
> exercise and screenshot** to close the verification gap from iter-1 (where all 18 UI tests SKIPPED on an
> HTTP 500). Change Type is "Re-verify (no code change)" for every row — these are not new or modified
> surfaces, but each carries a specific, screenshot-backed action so the run cannot be recorded as a vague
> pass. There are **no rows with an actual code-driven UI change**, because none exists.

---

## Affected UI Surfaces

<!-- Every row is an EXISTING surface to be browser-verified this iteration. No new/modified UI surfaces exist. -->

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|------------:|------------|-------------|
| `/` | Frontend serves HTTP 200 (precondition) | Re-verify (no code change) | iter-1 SKIPPED all UI tests on a cached HTTP 500 from a corrupted `.next`; `.next` is now cleared and `next dev` restarted with `NEXT_PUBLIC_API_URL` set | Load `/` after `rm -rf apps/frontend/.next` + dev-server restart; confirm the page returns **HTTP 200** (not 500) and the cockpit shell renders before any journey test runs |
| `/` | `QuotePanel` | Re-verify (no code change) | J-01: bid/ask/spread/last must render live numerics; spread cleanup must keep `spread = ask − bid` | Watch `SIM-BUYER`; confirm bid, ask, last show monospaced numbers and **spread equals ask − bid** (e.g. ≈ 0.02 = 100.26 − 100.24); confirm values change over WebSocket without reloading the page |
| `/` | `RecentTradesPanel` | Re-verify (no code change) | J-01: trade tape must populate live | Confirm recent trades list shows rows with **price, size, and side** (buy/sell color: emerald/rose); confirm new trades append over WS without a page reload |
| `/` | `FeaturesPanel` | Re-verify (no code change) | J-01/J-02: feature readouts must render live and drive the classification | Confirm `aggressive_buy_ratio` reads **high** (≈ 0.90) and `buy_price_impact` reads **positive** (≈ +0.41); confirm `average_spread` displays (≈ 0.0200) and updates over WS |
| `/` | `TapeStatePanel` | Re-verify (no code change) | J-02: must settle on the buyer_control end state with confidence ≥ threshold | Let the stream stabilize; confirm the tape state reads **buyer_control** with a confidence bar ≥ the configured reasonable threshold (≈ 0.80); screenshot this panel as the J-02 end-state evidence |
| `/` | `ObservationsPanel` | Re-verify (no code change) | J-01: human-readable observations accompany the state | Confirm the observations panel renders non-empty, plain-language descriptors consistent with a buyer-control tape (no placeholder/blank text) |
| `/` | `EventLogPanel` | Re-verify (no code change) | J-02: state transition must be logged | Confirm the event log contains the line **"Tape state changed to buyer_control"**; screenshot the event log alongside the tape-state panel |
| `/` | `TopBar` (stream-status dot + confidence) | Re-verify (no code change) | J-01: connection/warm-up status must reflect a live stream | Confirm the stream-status dot indicates connected/live (not idle/error) once the WebSocket warms; confirm no "not trading advice" disclaimer regression |
| `/` | `Cockpit` ↔ REST cross-check (`GET /tape/SIM-BUYER/state` and `/features`) | Re-verify (no code change) | J-08: single source of truth — UI must match REST exactly | Open `/tape/SIM-BUYER/state` and `/tape/SIM-BUYER/features` in a second tab; confirm the UI's **tape_state, confidence, and each feature readout match the REST JSON exactly** for the same ticker (no divergence); screenshot the UI panel beside the REST JSON |
| `/` | `IdleState` / connecting / watch-error states | Re-verify (no code change) | J-01: pre-stream and error states must still render | Before watching, confirm the idle/empty state renders; trigger a watch on a bad ticker and confirm the watch-error state renders (no crash, no blank screen) |

<!-- No row represents a new or modified surface. All are existing iter-1 surfaces under browser re-verification. -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/tape_engine.py` (line 54) — feeds the rolling `average_spread` from the canonical
  `MarketState.spread` instead of an inline `event.ask - event.bid`. **Behavior-preserving** (identical
  value); consolidates the `ask − bid` subtraction to a single producer. No serializer, endpoint, or response
  shape changed — **no UI surface affected**.
- `apps/backend/app/config.py` (line 11) — removed the unused `field` symbol from the `dataclasses` import.
  Pure dead-code cleanup; no runtime, env-var, or tunable change — **no UI surface affected**.

---

## Summary

- **Frontend surfaces changed:** 0 (zero frontend code change; all surfaces listed are existing iter-1
  surfaces under browser re-verification)
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 2 (both behavior-preserving; neither affects a UI surface)
