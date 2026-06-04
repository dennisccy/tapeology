# Iteration 0 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

This is the verify-only **baseline** that establishes the starting line for the expanded goal. The
**simulated half (J-01–J-09) is the green floor** — all nine verified passing in the browser with
evidence I inspected directly, including the two defining anti-goal proofs (absorption over
aggression) and the single-source-of-truth check. The **real-data half (J-10–J-15) is genuinely
unbuilt** — DOM probes, backend 404s, and a clean `git diff` confirm the surfaces are absent, not
merely untested. No source code changed, no anti-goal was violated, and there is no `coherence.md`
to veto (zero-diff baseline). Clear, tractable work remains, so the loop continues.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Watch + live cockpit | (none) | already_passing | `…-evidence/UT-J-01-J-02-SIM-BUYER.png` |
| J-02 buyer_control | (none) | already_passing | `…-evidence/UT-J-01-J-02-SIM-BUYER.png` (conf 0.883, agg_buy 0.946, buy_impact +0.430) |
| J-03 seller_control | (none) | already_passing | `…-evidence/UT-J-03-SIM-SELLER.png` (conf 0.885, sell_impact −0.400) |
| J-04 bid_absorption | (none) | already_passing | `…-evidence/UT-J-04-SIM-BIDABS.png` (agg_sell **1.000**, sell_impact **0.000** → Bid Absorption, NOT seller_control) |
| J-05 ask_absorption | (none) | already_passing | `…-evidence/UT-J-05-SIM-ASKABS.png` (agg_buy **1.000**, buy_impact **0.000** → Ask Absorption, NOT buyer_control) |
| J-06 unclear/chop | (none) | already_passing | `…-evidence/UT-J-06-SIM-CHOP.png` (Unclear, conf 0.200, wide spread 0.16) |
| J-07 transition messages | (none) | already_passing | event logs in `UT-J-01..05` PNGs ("Tape state changed to …") |
| J-08 REST == UI | (none) | already_passing | `…-evidence/UT-J-01-J-02-SIM-BUYER.png` + same-tick capture (ui_conf 0.855 == rest_conf 0.855) |
| J-09 Stop / re-watch | (none) | already_passing | `…-evidence/UT-J-09-stopped-idle.png` (idle empty state; `/state` → 404) |
| J-10 data-source selector | (none) | failing (not built) | `…-evidence/UT-J-10-no-datasource-selector.png` (select_count 0, radio_count 0) |
| J-11 historical replay | (none) | failing (not built) | UT-J-10 + backend probe (no historical provider; `mode` body ignored → 400) |
| J-12 live streaming | (none) | failing (not built) | UT-J-10 + backend probe (`GET /market/clock` → 404; no Live mode) |
| J-13 symbol search | (none) | failing (not built) | UT-J-10 + backend probe (`GET /symbols/search` → 404) |
| J-14 honest real-data edge cases | (none) | failing (not built) | `…-evidence/UT-J-14-unknown-symbol-honest-error.png` (errors honestly, NO fabricated cockpit; but the 4 distinct real-data states absent) |
| J-15 stale → recover | (none) | failing (not built) | UT-J-10 (no Live provider/socket to gap; `stale` dot mapping exists but nothing produces it) |

Baseline classification rationale: J-01–J-09 were built and shipped by the prior session
(`i_will_be_rich`) and are confirmed passing at this baseline → `already_passing` (set only by the
baseline iter, so later iters skip them and only guard against regression). J-10–J-15 have positive
evidence of being unbuilt (absent DOM controls + backend 404s + clean diff), so they are `failing`
(to-build), not `unknown`.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No execution path | OK | No code changed; no order/broker surface anywhere. |
| Stay in scope | OK | No scanner/news/charting/portfolio added. |
| Price impact over raw aggression | OK (proven) | J-04 (agg_sell 1.000, sell_impact 0.000 → bid_absorption) and J-05 (agg_buy 1.000, buy_impact 0.000 → ask_absorption) — absorption beats aggression. |
| Honest uncertainty | OK (proven) | J-06: Unclear at conf 0.200 with wide spread; no forced directional call. |
| No fabricated data | OK (proven) | J-14: unknown symbol → explicit "'AAPL' is not a known simulated ticker", cockpit NOT rendered. |
| Single source of truth | OK (proven) | J-08 same-tick: ui_conf 0.855 == rest_conf 0.855; state/features read identically. |
| No magic numbers | OK | No engine/classifier code changed; config home (`config.py`) intact. |
| Provider-agnostic engine | OK | Only `base.py` + `simulated.py` providers exist; no vendor SDK leak. |
| No secrets in source | OK | No credentials added/committed (verified via clean `git diff`). |
| Deterministic & reproducible | OK | 68 backend tests pass (green floor); no wall-clock/random introduced. |
| No ML in v1 | OK | Classifier remains rule/threshold-based; no model added. |
| No trade/profit claims | OK | Footer renders "Descriptive only — not trading advice." on every cockpit. |

No violations (`anti_goal_violations: []`).

## Next-Step Recommendation

Resume after blueprint approval and begin the **real-data half**. Recommended first slice (conforms
to the drafted blueprint, browser-verifiable **without** a live feed or market hours):

1. **Vendor-agnostic adapter seam + credentials/availability contract** — establish the one adapter
   module (Alpaca, free IEX) behind a vendor-neutral provider interface, and the explicit
   "real-data provider unavailable" state when no credentials are configured. This makes the
   **no-credentials path of J-14** verifiable immediately, and locks in the critical anti-goals
   (no secrets in source, provider-agnostic seam, no fabricated data) before any vendor wiring.
2. Then build outward: `GET /symbols/search` (**J-13**) and `GET /market/clock`; the `{mode,start,end,speed}`
   watch body + historical-replay provider (**J-11**); the live provider + stale/recover
   (**J-12 / J-15**); and the TopBar data-source selector + mode-specific controls (**J-10**).

Every real-data read MUST flow through the existing engine (blueprint rows 1–6) unchanged and MUST
NOT regress J-01–J-09 (now the required-still-passing floor).

**Why `full` depth for iter 1:** the first real-data slice establishes security- and
architecture-critical surfaces — credential handling (*no secrets*), the single vendor-SDK adapter
seam (*provider-agnostic engine*), and a new honest-failure state (*no fabricated data*) — plus the
first new UI control that must not regress the sim cockpit. The full pipeline's audit +
ux-regression + closure gate is worth running to lock the seam in correctly; later, well-bounded
slices can drop back to lean. (If the decomposer scopes a minimal seam-only slice, lean coherence
auditing still runs — but full is recommended for this foundational iteration.)

## Halt Justification (if halting)

N/A — not halting. CONTINUE. Six tractable journeys remain to build (J-10–J-15); the simulated floor
(J-01–J-09) is green and now protected against regression. The one-time human blueprint-approval
pause that `run-goal.sh` enforces after the baseline gates the start of iter 1.
