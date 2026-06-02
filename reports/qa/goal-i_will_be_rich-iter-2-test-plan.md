# goal-i_will_be_rich-iter-2 Functional Test Plan

**Phase:** goal-i_will_be_rich-iter-2
**Date:** 2026-06-02
**Frontend Present:** yes

## Phase Goal

Browser-prove the already-built `SIM-BUYER` tape cockpit (J-01/J-02/J-08) with real screenshots — the UI's tape state / confidence / features must match the REST endpoints exactly — while applying two behavior-preserving backend cleanups (`tape_engine.py:54` spread single-producer; `config.py:11` dead `field` import) with zero regression.

## Preconditions (apply to all browser tests — run is INVALID otherwise)

- Backend running on the QA-harness offset port (e.g. `:8650`).
- `rm -rf apps/frontend/.next` performed, then the managed frontend dev server (re)started with `NEXT_PUBLIC_API_URL` pointed at the running backend.
- Frontend returns **HTTP 200** (not 500) before any UI interaction — verify with `curl -s -o /dev/null -w "%{http_code}" http://localhost:<frontend-port>`.

## Test Cases

### TC-01 — Backend suite stays green after both cleanups

**Type:** api (test-suite)
**Preconditions:** Both cleanups applied (`tape_engine.py:54` → `self._market.spread`; `config.py:11` drops `field`).

**Steps:**
1. `cd apps/backend && .venv/bin/python -m pytest tests/ -v`

**Expected outcome:** All existing backend tests pass (24 expected); no errors or new skips.
**Pass criteria:** Exit code 0; pytest reports `24 passed` (or current full count) with 0 failed.

---

### TC-02 — Determinism preserved (spread cleanup is behavior-preserving)

**Type:** api (test-suite)
**Preconditions:** `tape_engine.py:54` cleanup applied.

**Steps:**
1. Run the run-twice-identical / determinism test in the suite.

**Expected outcome:** Same ordered event stream produces identical features, state, and confidence before and after the cleanup.
**Pass criteria:** Determinism test PASSES; `average_spread` input unchanged (value identical to `event.ask - event.bid`).

---

### TC-03 — SIM-BUYER scenario still resolves to buyer_control

**Type:** api (test-suite)
**Preconditions:** Backend running.

**Steps:**
1. Run the SIM-BUYER scenario test.

**Expected outcome:** Engine resolves `SIM-BUYER` to `buyer_control` with reasonable confidence.
**Pass criteria:** Scenario test PASSES; state == `buyer_control`.

---

### TC-04 — Price-impact guard still enforced (not relaxed)

**Type:** api (test-suite)
**Preconditions:** Backend running.

**Steps:**
1. Run the price-impact-guard test (buyer_control requires positive `buy_price_impact`).

**Expected outcome:** A tape with high one-sided aggression but no positive price impact does NOT resolve to buyer_control.
**Pass criteria:** Guard test PASSES unchanged; assertion thresholds not weakened.

---

### TC-05 — No new magic numbers introduced

**Type:** artifact
**Preconditions:** Both cleanups applied.

**Steps:**
1. Inspect the diff of `tape_engine.py` and `config.py`.
2. Confirm no numeric literal (window length, threshold, cutoff, confidence boundary) was added or relocated into engine/classifier code.

**Expected outcome:** Cleanups only remove a duplicate computation and a dead import.
**Pass criteria:** Zero new numeric literals in changed engine/classifier files; all tunables still sourced from config.

---

### TC-06 — Error cases unchanged (regression guard)

**Type:** api
**Preconditions:** Backend running on `:<backend-port>`.

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:<backend-port>/watch/NOPE_UNKNOWN`
2. `curl -s -o /dev/null -w "%{http_code}" http://localhost:<backend-port>/tape/NOTWATCHED/state`

**Expected outcome:** Unknown-ticker watch rejected; read of not-watched ticker not found.
**Pass criteria:** Step 1 returns `400`; step 2 returns `404`. No fabricated read returned.

---

### TC-07 — Frontend serves HTTP 200 after `.next` clear (precondition gate)

**Type:** browser
**Preconditions:** `.next` removed; dev server restarted with `NEXT_PUBLIC_API_URL` set.

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" http://localhost:<frontend-port>/`

**Expected outcome:** Cockpit page loads without the iter-1 HTTP 500.
**Pass criteria:** Returns `200`. (If 500/unreachable after restart, the browser run is INVALID — do not record SKIP as success.)

---

### TC-08 — J-01: Cockpit renders live values and updates over WebSocket

**Type:** browser
**Preconditions:** TC-07 passed.

**Steps:**
1. Navigate to `/`.
2. Watch `SIM-BUYER`; wait for stream to connect.
3. Observe all six panels: Quote (bid/ask/spread/last), Recent Trades, Features, Tape State + confidence, Observations, Event Log.
4. Wait a few seconds WITHOUT reloading; observe values change.
5. Screenshot the populated cockpit → `reports/qa/goal-i_will_be_rich-iter-2-evidence/TC-08-cockpit-live.png`.

**Expected outcome:** Every panel shows real numeric values; spread == ask − bid; recent trades show price/size/side; values update live over WS.
**Pass criteria:** All six panels populated with non-placeholder values; spread equals ask − bid; at least one value updates without a page reload; end-state screenshot saved (not a failure shot).

---

### TC-09 — J-02: Tape state settles on buyer_control with correct evidence

**Type:** browser
**Preconditions:** TC-08 in progress; stream stabilized.

**Steps:**
1. Let the stream stabilize.
2. Read the Tape State panel (state + confidence) and Features panel (`aggressive_buy_ratio`, `buy_price_impact`).
3. Read the Event Log.
4. Screenshot the tape-state panel + event log → `.../TC-09-buyer-control.png`.

**Expected outcome:** State = `buyer_control` at confidence ≥ configured threshold; `aggressive_buy_ratio` high; `buy_price_impact` positive; event log contains "Tape state changed to buyer_control".
**Pass criteria:** Tape state reads `buyer_control`; confidence ≥ threshold; `buy_price_impact` > 0; the buyer_control log line present; screenshot saved.

---

### TC-10 — J-08: UI values match REST endpoints exactly (single source of truth)

**Type:** browser + api
**Preconditions:** TC-09 reached buyer_control.

**Steps:**
1. With the cockpit showing `SIM-BUYER`, `curl http://localhost:<backend-port>/tape/SIM-BUYER/state` and `.../tape/SIM-BUYER/features`.
2. Compare tape state, confidence, and each feature readout against the UI panels for the same ticker.
3. Screenshot the UI panel and the REST JSON → `.../TC-10-ui-vs-rest.png`.

**Expected outcome:** UI and REST agree on every metric — one engine value per metric, no divergence between views.
**Pass criteria:** State, confidence, and all compared feature values are identical (within display rounding) between UI and both REST endpoints; screenshot of both saved.

---

### TC-11 — UI Evolution / no regression of existing states

**Type:** browser
**Preconditions:** Frontend serving 200.

**Steps:**
1. Confirm idle/empty, connecting/warm-up, and live states render.
2. Confirm color semantics (emerald = buy/positive, rose = sell/negative, amber = absorption/unclear) and monospaced numerics.
3. Confirm the "Descriptive only — not trading advice" disclaimer is still present (no regression).

**Expected outcome:** Existing states and visual semantics render correctly; no new surfaces added.
**Pass criteria:** Idle + live states render; disclaimer present; no new panel/route/control introduced.

---

## Summary

Total test cases: 11
- API / test-suite: 6 (TC-01, TC-02, TC-03, TC-04, TC-06, plus the REST half of TC-10)
- Browser: 5 (TC-07, TC-08, TC-09, TC-10, TC-11)
- Artifact: 1 (TC-05)

**Heart of the iteration:** TC-08 (J-01), TC-09 (J-02), TC-10 (J-08) — each must RUN (not SKIP) and produce an end-state screenshot. TC-07 is the mandatory precondition gate; if it fails the browser run is invalid.
