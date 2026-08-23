# Iteration State — rapid-microscope

**After iteration:** 26 · **Date:** 2026-08-23 · **Verdict:** CONTINUE

## Journeys

**10 passing (J-01..J-10)** · 0 failing/partial/unknown. iter-26-stamped but J-07 (iter-24, no
golden by design). J-08 has `evidence_makeup` — TC-8's crop missed the Scout Ledger rows.

## Active blockers

- **Era NOT certifiable: 7 minor anti-goal items open** (0 critical; the iter-26 critical was fixed
  in-round). Verbatim text: `state/journey-history.json` → `anti_goal_violations`.
- **Suite unrunnable / non-hermetic (dev) — NEW, root cause of this round's damage. DO FIRST.**
  `test_micro_readiness.py:456-471` + `test_micro_join.py:951,975` walk the real ~26 GB
  `.data/datasets` cold every run; ONE file did not finish in 520s → starved the backend mid-round
  → 6 browser checks + demo came back empty, QA's log dead at 59% yet recording `EXIT_CODE=0`.
  Fix: durable reused cache path or corpus cap.
- **2 make-up captures owed (dev, passenger, NEVER a goal):** Desk readiness figures; Scout Ledger family row + "variants tried" line IN FRAME.
- **Referee disclosure + guard never built (dev).** Owner ruled r5 pt 7 (KEEP THE FREEZE, DISCLOSE)
  2026-08-18; freeze holds (6/6 hashes re-checked). Largest non-owner job left.
- **Framework-owned, NOT product (ask owner if these still count):** QA certifies unchecked work (4th time); `closure_gate.py` ignores the browser verdict;
  `replay-lane.sh:269` can never run a round's own Target goldens (9/9 unreachable, 7/7 ceiling).
- **Owner-owned, blocking nothing:** chain-ledger identity commitment (r8); judge's money floor.

## Last 2 verdicts

- iter 26: CONTINUE — 2 fixes landed and closed 2 open items, but the delivered cache would have
  served a permanent wrong `0`; the auditor caught+fixed it (12th catch) and I re-proved it.
- iter 25: ESCALATE — J-06 green; refused GOAL_ACHIEVED on open minor items.

## Do not redo

- **Band-touch cache DONE** — `MicroBandTouchCache` + `micro_join.py:660-688`; the
  `cacheable = resolver.resolve(...) is not None` guard is LOAD-BEARING (`test_audit_b1_…` pins it).
- **Pilot-selector dedup DONE** — `_pilot_selectors_by_kind` filters `scout._PILOT_GRID_SELECTORS`
  at call time; never re-add a frozen literal. **J-06's Vault golden ran (UT-J-06 PASS).**
- **Do NOT re-record tape, expose/assign a sealed shard, run J-09's studies on the real corpus, edit any `referee_*.py` (6/6 re-verified), or move fingerprint `08e471b10130e1e2`.**
- **`J-08.json` step 3 / `J-10.json` step 12 assert `"variants tried"`; J-07 cannot have a golden**
  (iter-19); readiness serving `80` (whole pool) not `21` is CORRECT (r5 anti-subtraction).
