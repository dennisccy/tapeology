# goal-i_will_be_rich-iter-6 Functional Test Plan

**Phase:** goal-i_will_be_rich-iter-6
**Date:** 2026-06-03
**Frontend Present:** yes

## Phase Goal

Deliver the fifth and final MVP tape state — `unclear` — by driving `SIM-CHOP` with a
genuinely choppy stream that warms up yet honestly declines to call a side (J-06,
honest-uncertainty anti-goal), and close out the transition taxonomy by capturing live
cold-start "Tape state changed to …" announcements on ≥2 resolving scenarios (J-07) — all
with **no classifier/config/frontend change** (backend provider + tests only).

## Test Cases

### TC-01 — SIM-CHOP settles on warmed-up `unclear` through the real engine

**Type:** artifact (backend unit test)
**Preconditions:** `_chop_stream()` authored and wired into `stream()`; backend venv present.

**Steps:**
1. `cd apps/backend && .venv/bin/python -m pytest tests/test_scenario.py::test_sim_chop_settles_on_unclear -v`

**Expected outcome:** Running `SIM-CHOP` to completion yields a final snapshot with
`tape_state == STATE_UNCLEAR`, `warm is True`, `event_count >= CONFIG.warmup_min_events` (40),
and `confidence == CONFIG.unclear_confidence` (0.20, strictly `< CONFIG.reasonable_confidence`).
**Pass criteria:** Test passes — unclear by *mixed signals* (warmed) not cold-start silence (0.10).

---

### TC-02 — No-false-fire: step-through state guard (critical)

**Type:** artifact (backend unit test)
**Preconditions:** chop stream wired.

**Steps:**
1. Run the step-through guard test that processes the `SIM-CHOP` stream event-by-event and
   inspects the tape state at every tick.

**Expected outcome:** At **no** tick does the state become `buyer_control`, `seller_control`,
`bid_absorption`, or `ask_absorption`; it is `unclear` at every tick (cold-start and warmed).
**Pass criteria:** Test passes — the classified state never transiently misfires across the
entire stream (proves the enlarged four-gate false-fire surface stays closed).

---

### TC-03 — No-false-fire: all-windows feature guard (defense in depth)

**Type:** artifact (backend unit test)
**Preconditions:** chop stream wired; warmed end-state snapshot available.

**Steps:**
1. Run the all-windows feature guard test against the warmed end-state snapshot.

**Expected outcome:** For **every** window label in `snap.features` (10s/30s/60s/180s/300s):
`aggressive_buy_ratio < CONFIG.min_aggressive_buy_ratio` **and**
`aggressive_sell_ratio < CONFIG.min_aggressive_sell_ratio` (both 0.60), **and**
`average_spread > CONFIG.max_stable_spread` (0.06), **and**
`bid_refresh_score < CONFIG.min_bid_refresh_score` **and** `ask_refresh_score < CONFIG.min_ask_refresh_score` (0.55).
**Pass criteria:** Test passes for all five windows, with explicit attention to the noise-prone
**10s** window — no gate is even reachable in any window.

---

### TC-04 — SIM-CHOP is deterministic (same seed ⇒ identical snapshot)

**Type:** artifact (backend unit test)
**Preconditions:** chop stream seeded with `random.Random(self.seed)`.

**Steps:**
1. Run `test_sim_chop_is_deterministic` — build two SIM-CHOP runs with the same seed and compare.

**Expected outcome:** The two resulting snapshots are equal (`a == b`).
**Pass criteria:** Test passes — classification depends only on the ordered event stream + seed,
no wall-clock / randomness leakage.

---

### TC-05 — Reserved-ticker contract updated (known vs unknown)

**Type:** artifact (backend unit test)
**Preconditions:** `test_reserved_ticker_known_but_unresolved` updated for the now-driven SIM-CHOP.

**Steps:**
1. Run the reserved-ticker contract test.

**Expected outcome:** `build_provider("SIM-CHOP") is not None` and `build_provider("NOPE123") is None`;
the test's comment/intent no longer implies SIM-CHOP emits zero events (all five reserved sim
tickers are now driven).
**Pass criteria:** Test passes; comment/intent reflects driven SIM-CHOP.

---

### TC-06 — Classifier unit mirror: synthetic chop ⇒ `STATE_UNCLEAR`

**Type:** artifact (backend unit test)
**Preconditions:** `test_classifier.py` updated.

**Steps:**
1. Run the classifier chop test: a synthetic feature dict (both ratios ≈ 0.50, wide
   `average_spread` ≈ 0.20, near-zero `buy/sell_price_impact`, refresh scores 0.0, `trade_count=60`).

**Expected outcome:** Classifies as `STATE_UNCLEAR` and explicitly **not** any of the four resolved
states. (Optional companion: balanced ratios + *narrow* spread still ⇒ unclear, pinning that
mixed two-sided aggression alone denies every gate.)
**Pass criteria:** Test passes — no classifier/config change was needed to reach unclear.

---

### TC-07 — API single-source-of-truth on the unclear read (J-08 extension)

**Type:** api (backend integration test + live curl)
**Preconditions:** backend running on the harness port; SIM-CHOP watched.

**Steps:**
1. `curl -s -X POST http://localhost:8000/watch/SIM-CHOP` → expect 200.
2. Allow the stream to warm, then:
   `curl -s http://localhost:8000/tape/SIM-CHOP/state`
3. `curl -s http://localhost:8000/tape/SIM-CHOP/features`
4. `curl -s http://localhost:8000/tape/SIM-CHOP/summary`
5. Compare `tape_state` + `confidence` + feature readouts across `/state`, `/features`,
   `/summary`, and the `WS /tape/SIM-CHOP/stream` payload.

**Expected outcome:** `/state` returns `tape_state == "unclear"` with low confidence (≈0.20,
`< reasonable_confidence`); `/state`, `/features`, `/summary`, and `WS /stream` agree on state,
confidence, and feature values (no recomputation, no divergence).
**Pass criteria:** `test_api.py` SIM-CHOP cases pass AND the live curls return matching values
across all four projections.

---

### TC-08 — Error cases unchanged (no fabricated data)

**Type:** api
**Preconditions:** backend running.

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/watch/NOPE123` → expect **400**.
2. `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/tape/SIM-SELLER/state` (not watched) → expect **404**.

**Expected outcome:** Unknown ticker ⇒ 400; not-watched read ⇒ 404 — never a synthesized snapshot.
**Pass criteria:** Status codes are exactly 400 and 404 respectively.

---

### TC-09 — Full backend suite stays green (no regressions)

**Type:** artifact (backend test suite)
**Preconditions:** all iter-6 changes in place.

**Steps:**
1. `cd apps/backend && .venv/bin/python -m pytest tests/ -v`

**Expected outcome:** The 53-test baseline plus the new chop tests (TC-01..TC-08) all pass.
**Pass criteria:** Exit code 0; no failures/errors; new chop tests counted in the total.

---

### TC-10 — J-06 browser: SIM-CHOP reads amber "Unclear" at low confidence, live over WS

**Type:** browser (Chrome MCP)
**Preconditions:** frontend reachable; `NEXT_PUBLIC_API_URL` wired to backend port.

**Steps:**
1. Navigate to `/`. Enter `SIM-CHOP` and click Watch.
2. Observe the Tape-state panel headline + confidence bar as values stream over WebSocket (no reload).
3. Probe the amber render by **base selector** (`.text-amber-400{` / `.bg-amber-500{`, excluding
   `:hover`/variant forms) + `getComputedStyle` on the headline and bar elements.
4. Inspect Quote and Features panels for real, jittery choppy numbers.
5. Save evidence screenshot to `reports/qa/goal-i_will_be_rich-iter-6-evidence/TC-10-sim-chop-unclear.png`.

**Expected outcome:** Headline reads "Unclear"; confidence is low (below `reasonable_confidence`);
the UI asserts **no** buyer/seller control and **no** absorption; amber color confirmed by computed
style (not eyeballed, not grep-substring); values update live over WS; Quote/feature panels show
genuine choppy values (no fabricated decisive numbers).
**Pass criteria:** Computed style of headline ≈ amber-400 and bar ≈ amber-500; state text "Unclear";
confidence `< reasonable_confidence`; live WS update observed without reload.

---

### TC-11 — J-07 browser: cold-start transition announced live on ≥2 resolving scenarios

**Type:** browser (Chrome MCP)
**Preconditions:** **fresh backend** (no prior watch of the target tickers — iter-5 bounded-stream gotcha).

**Steps:**
1. On a fresh backend, navigate to `/`, watch `SIM-BUYER` (FIRST watch of this ticker). Watch the
   Event-log and Observations panels during warm-up.
2. Capture the "Tape state changed to buyer_control" line appearing **live** and observations
   updating (e.g. "Buyer aggression increasing").
3. Repeat the cold-start first-watch on a second distinct state — `SIM-SELLER` → "Tape state
   changed to seller_control" (and/or an absorption scenario → its bid/ask absorption line).
4. Save evidence to `reports/qa/goal-i_will_be_rich-iter-6-evidence/TC-11-cold-transition-*.png`.

**Expected outcome:** For each scenario, a "Tape state changed to <state>" message is appended to
the event log at the transition and observations reflect current evidence — appearing **live** over
WS on the cold first watch. SIM-CHOP correctly produces **no** transition line (cold unclear →
warmed unclear is not a state change — that absence is correct honest behavior).
**Pass criteria:** ≥2 distinct states each show a live cold-start "Tape state changed to <state>"
line + live observation update; SIM-CHOP shows no spurious transition.

---

### TC-12 — Regression guards: J-01..J-05, J-08 still green

**Type:** browser (Chrome MCP)
**Preconditions:** frontend + backend running.

**Steps:**
1. J-01: watch `SIM-BUYER` — confirm all six panels render live.
2. J-02: `SIM-BUYER` ⇒ `buyer_control`, green.
3. J-03: `SIM-SELLER` ⇒ `seller_control`, rose.
4. J-04: `SIM-BIDABS` ⇒ `bid_absorption`, amber.
5. J-05: `SIM-ASKABS` ⇒ `ask_absorption`, amber.
6. J-08: spot-check UI ≡ REST on `SIM-CHOP` — UI `unclear` + confidence == `GET /tape/SIM-CHOP/state`;
   UI feature readouts == `/features`.

**Expected outcome:** All four control/absorption states render unperturbed with correct colors;
UI values match REST on SIM-CHOP.
**Pass criteria:** Each journey renders the expected state + color; no divergence between UI and REST.

---

## Summary

Total test cases: 12

- API tests: 2 (TC-07, TC-08)
- Browser tests: 3 (TC-10, TC-11, TC-12)
- Artifact checks (backend unit/integration): 7 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-09)

**Critical gates:** TC-02 (step-through state guard) + TC-03 (all-windows feature guard) prove the
no-false-fire honest-uncertainty claim; TC-10 (J-06 amber Unclear via computed-style probe) and
TC-11 (J-07 cold-start live transitions) are the real browser gates. If browser-qa SKIPS due to a
frontend HTTP 500 (corrupted `.next`), treat as a verification-closure signal — `rm -rf
apps/frontend/.next`, restart with `NEXT_PUBLIC_API_URL`, re-run; a backend PASS does NOT substitute
for browser verification of J-06/J-07 (iter-1 lesson).
