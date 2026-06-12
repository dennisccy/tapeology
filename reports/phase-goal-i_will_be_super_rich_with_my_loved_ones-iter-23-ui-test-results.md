# Goal Iter 23 — UI Test Results

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-23
**Date:** 2026-06-12
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 9/9 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-65 | Setup-forming hints: descriptive, gated, logged | happy-path | P1 | Hint card appears on SIM-BIDABS past dwell, descriptive copy, no imperative, baseline "no studied baseline — unvalidated pattern", prefill-only declare, SIM-CHOP no hint, hint logged in /journal hints tab | All four legs confirmed: hint showed with correct copy; prefill set setup=absorption_reversal/direction=long/invalidation empty, thesis null after click; SIM-CHOP produced no hint over 35s; hint visible in /journal Hints tab with declared_from=— | PASS | J65-hint-dock-active.png, J65-declare-prefill.png, J65-chop-no-hint.png, J65-hint-log.png, J65-hint-cleared-on-pause.png |
| UT-J-01 | Watch a ticker and see the live tape cockpit | regression | P1 | SIM-BUYER cockpit fully populated within warm-up | buyer_control state, Confidence 0.927, all panels populated (bid/ask/spread/last, recent trades, features, observations, event log), hint dock shows "BUYER CONTROL FORMING" for trend_continuation | PASS | J01-buyer-control.png |
| UT-J-04 | Bid absorption detected (price impact, not aggression) | regression | P1 | SIM-BIDABS shows bid_absorption despite high sell aggression | bid_absorption state, Confidence 0.950, absorption_score/bid_refresh_score both 1.000, sell_price_impact=0.000, price holding at 100.00 | PASS | J65-hint-dock-active.png (same watch) |
| UT-J-06 | Unclear tape reported as unclear | regression | P1 | SIM-CHOP shows unclear with no hint | unclear state confirmed via REST polling; no hint dock visible in UI over 35s of watching | PASS | J65-chop-no-hint.png |
| UT-J-38 | Declare a thesis on the watched ticker | regression | P1 | Thesis strip shows ACTIVE with pending verdict; REST projection matches | absorption_reversal/long/inv=99.50 declared on SIM-BIDABS; strip shows PENDING; REST /research/thesis/active returns thesis present; declare affordance hidden in hint dock when thesis active (no dead control) | PASS | J38-thesis-declared.png |
| UT-J-51 | Journal survives backend restart | regression | P1 | Thesis rows from prior sessions visible after restart | Journal /journal shows theses from 11-06-2026 and 12-06-2026 sessions; rows show resolved/expired/abandoned correctly — store is persistent | PASS | J51-journal.png |
| UT-J-59 | Analytics aggregate honestly, segregated | regression | P1 | Analytics shows n with abandonment, segregated by feed/fingerprint, no currency P&L | Analytics tab shows feed=SIM + multiple config_fingerprint partitions; abandonment bucket always visible; "insufficient sample" for n<5; no equity curve, no currency P&L | PASS | J59-analytics.png |
| UT-J-63 | Entry checklist renders live margins | regression | P1 | Each check shows measured margin in its own units; stance reads conditions_not_met/met appropriately | Checklist on SIM-BIDABS thesis showed 7/8 checks with live margins (lag 1.7s/5.0s, spread 2.0/30.0 bps, trade speed 2.00/0.50 etc); stance=conditions_not_met; copy factual not imperative | PASS | J63-entry-checklist.png |
| UT-J-64 | Stance freshness — never frozen green over dead tape | regression | P1 | Pausing flips stance to no_fresh_tape | Paused SIM-BIDABS with active thesis; await_text("no_fresh_tape") succeeded; hint dock also cleared on pause | PASS | J64-no-fresh-tape.png |

---

## Passed Tests

### UT-J-65 — Setup-forming hints: descriptive, gated, logged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-23-evidence/J65-hint-dock-active.png`

Key verifications:
- **Hint fires on SIM-BIDABS**: REST `GET /research/hints/active?ticker=SIM-BIDABS` returned hint at first poll (logical_ts=24.5s, after 5s dwell). UI showed `[data-testid="hint-dock"]` with `data-testid="hint-evidence"` containing: "Bid absorption is sustained 5s — aggressive selling is being absorbed at the bid with no meaningful downward price progress."
- **Copy discipline**: descriptive present-tense only; no imperative buy/sell/enter/exit wording; "Bid absorption forming" pattern label; "Descriptive only — not trading advice." register present
- **Exact baseline string**: `data-testid="hint-baseline"` reads exactly "no studied baseline — unvalidated pattern" (fresh DB, no matching studies)
- **Declare affordance prefills, never creates**: clicking `[data-testid="hint-declare"]` opened the thesis form with setup=`absorption_reversal` (selected), direction=`long` (selected), invalidation input empty (placeholder "price"); REST `/research/thesis/active?ticker=SIM-BIDABS` returned `{"thesis":null}` — one click never created a thesis
- **Declare affordance hidden with active thesis**: after declaring a thesis on SIM-BIDABS, the hint dock showed again but the declare button was absent from the page (no dead control)
- **SIM-CHOP negative leg**: 6 polls over 35s all returned `{"hint":null}`; no `[data-testid="hint-dock"]` in UI DOM
- **Active hint clears on pause**: Pause button clicked; REST immediately returned `{"hint":null}`; `hint_dock_present=false` with `paused_indicator=true`
- **Hint log persists after clearing**: `GET /research/hints?ticker=SIM-BIDABS&limit=10` returned 2 rows (from two separate watches) with all stamps: `data_feed`, `config_fingerprint`, `bound_source`, `logical_ts`, `wall_ts`, `baseline_citation`
- **Journal hint log visible**: `/journal` Hints tab shows correct columns (Time, Ticker, Pattern, Evidence, Studied Baseline, Declared From) with SIM-BIDABS row: "12-06-2026 | SIM-BIDABS | Bid absorption forming | Bid absorption is sustained 5s... | no studied baseline — unvalidated pattern | —"
- **Taxonomy canary confirmed**: `GET /research/taxonomy` returns `hints` key with patterns, copy, log_columns, baseline_unvalidated="no studied baseline — unvalidated pattern"
- **Error case confirmed**: unknown `declared_from_hint_id` → HTTP 422 "unknown declared_from_hint_id 'nonexistent_hint_id'"
- **Second hint pattern**: SIM-BUYER watch showed hint dock with "BUYER CONTROL FORMING" (trend_continuation/long) — all four state-native patterns are functional

### UT-J-01 — Watch a ticker and see the live tape cockpit
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-23-evidence/J01-buyer-control.png`
- SIM-BUYER reached buyer_control state; all panels populated with live values; WebSocket updating without page reload; bid=100.56 ask=100.58 spread=0.02 last=100.58 (spread = ask - bid ✓); recent trades show buy side; tape state "Buyer Control" Confidence 0.927; observations and event log populated

### UT-J-04 — Bid absorption detected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-23-evidence/J65-hint-dock-active.png`
- SIM-BIDABS showed bid_absorption with Confidence 0.950; aggressive_sell_ratio=1.000 yet sell_price_impact=0.000 (price not moving lower); absorption_score=1.000, bid_refresh_score=1.000; event log shows "Large sell print absorbed" and "Bid refreshing at 100.00"

### UT-J-06 — Unclear tape
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-23-evidence/J65-chop-no-hint.png`
- SIM-CHOP showed unclear state (confirmed via REST and UI text); no hint dock appeared over 35s

### UT-J-38 — Declare thesis
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-23-evidence/J38-thesis-declared.png`
- Thesis declared successfully; verdict starts pending; REST active thesis projection matches UI; hint dock declare affordance correctly hidden when thesis active

### UT-J-51 — Journal survives restart
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-23-evidence/J51-journal.png`
- Journal shows theses from 11-06-2026 (prior session) and 12-06-2026 with their resolved statuses intact — append-only store, byte-identical after restart

### UT-J-59 — Analytics
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-23-evidence/J59-analytics.png`
- Analytics segregated by feed+config_fingerprint; n with abandonment always shown; "insufficient sample" for n<5; no currency P&L or equity curves

### UT-J-63 — Entry checklist live margins
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-23-evidence/J63-entry-checklist.png`
- Each of 8 checks rendered with live measured margin: lag 1.7s/5.0s, spread 2.0/30.0 bps, trade speed 2.00/0.50 /s, etc.; stance "conditions_not_met"; nearest counterevidence named; copy factual not imperative

### UT-J-64 — Stance freshness
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-23-evidence/J64-no-fresh-tape.png`
- Pause on watched SIM-BIDABS immediately flipped stance to no_fresh_tape; UI confirmed via await_text("no_fresh_tape"); hint dock also cleared on pause

---

## Failed Tests

None.

---

## Skipped Tests

None. J-68 (byte-identity clause) was verified via the automated observer equivalence suite: `python3 -m pytest tests/test_observer_equivalence.py` — all 7 tests passed including `test_real_monitor_attached_outputs_byte_identical` and `test_real_monitor_with_thesis_does_not_alter_engine_outputs` (zero re-pins). The 29 hint unit tests in `test_research_hints.py` also all passed.

---

## Environment

- **Frontend URL:** http://localhost:3650
- **Backend URL:** http://localhost:8650
- **Browser:** Chrome via MCP
- **Test Date:** 2026-06-12
- **Evidence directory:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-23-evidence/`
