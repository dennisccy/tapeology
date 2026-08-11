# Iteration State — playbook

**After iteration:** 6 · **Date:** 2026-08-11 · **Verdict:** CONTINUE

## Journeys

6 passing (J-01 J-02 J-03 J-04 J-05 J-06) · 3 failing (J-07 J-08 J-09) · 1 partial (J-10) — 10 total

## Active blockers

- **Scoping, before J-07 (dev, urgent).** The QA lane ran an UNSCOPED Run Playbook into the real
  store (`.data/playbook/playbook-2026-08-07-84fcd116ebd7.json`, 57 signals, 45 real members + ledger
  row). Do NOT delete it (append-only). Make `apps/backend/scripts/qa_playbook_iter6_fixture_scoped_backend.sh`
  the ONLY backend entry point for test/browser work — J-07's back-scan mass-writes real sessions.
- **J-07 needs the auditor (full depth).** First mass writer into the operator's store; the auditor
  caught 2 FAIL-level bugs in iter-6's own maths. Do not let a budget-breach demote it to lean.
- Owner rulings (cheap now, expensive once J-07/J-08 pool real numbers): (a) ratify/reject the
  developer-authored §3.7 "degenerate trigger reference" clause (fail-closed, no constant, signature
  unmoved; rejecting = drop `range_trade`); (b) `crossed_midrange` serves only the approach half of
  §3.7's disclosure; (c) `double_top` returns the first valid PAIR, not §3.8's first valley BREAK;
  (d) carried: §3.3's 1.5x gate unreachable; cup rim reads `near_extreme_mbr` vs §3.6.
- J-10 `partial` until J-09 ships (needs 20 MCP tools; there are 18). Passenger: short-side degenerate
  mirror test (`test_desk_playbook_detect.py:1249`); `_assert_scoped` test; re-capture Range Trade row.

## Last 2 verdicts

- iter 6: CONTINUE — J-06 newly passing on POST-FIX evidence only (pre-fix range-trade screenshots
  voided by the auditor); suite 2105/8, pin held, coherence PASS; 3 open minor items.
- iter 5: ESCALATE — J-05 newly passing; a full-planned iteration ran lean again with no auditor.

## Do not redo

- J-06 DONE: `detect_range_trade`/`_range_trade_side`/`_zone_held`, `detect_double_top`/`detect_double_bottom`/
  `_find_double_extreme`, `PLAYBOOK_SETUPS` 9-id tuple, both geometry branches, zero-structural-calls guard.
- CLOSED: register + both `/desk` copy spots name ALL EIGHT families (pinned guard re-derived); spec
  §3.5 `decline_bars`/re-anchoring prose; orphan-ledger cause (audit B5 — log dir falls back off the
  universe dir; nothing deleted); J-05 stored golden script exists.
- Zero diff verified — do not touch `desk_forward.py`, `desk_playbook_features.py`, `mcp/__init__.py`,
  `config.py`, `desk_routes.py`, `levels.py`, `bars.py`, `setups.py`. Pin `08e471b10130e1e2`; MCP stays
  18. Behaviour-only detector fixes do NOT move `playbook_input_signature` — re-seed the rig FRESH.
