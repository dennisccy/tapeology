# Iteration State — rapid-microscope

**After iteration:** 27 · **Date:** 2026-08-23 · **Verdict:** ESCALATE

## Journeys

**10 passing (J-01..J-10)** · 0 failing/partial/unknown. iter-27-stamped except J-07 (iter-24; no screen, no golden — iter-19 ruling). `evidence_makeup` on J-08 + J-10 = captures only.

## Active blockers

- **DEPTH TRAP — read first.** iter-27 ran at `evidence` depth: NO developer, NO reviewer, zero product diff, both planned items unbuilt. With 10/10 green, `run-goal.sh` (~2745-2775) demotes any `lean` dispatch to `evidence`; budget-breach + full-cap demote `full`→`lean`. Only ESCALATE (this verdict) or operator `CHAIN_REQUIRE_FULL_DEPTH` dispatches a developer. Plan for a FULL round.
- **Suite non-hermetic (dev) — DO FIRST, unbuilt.** `test_micro_readiness.py` `real_readiness` still takes `tmp_path_factory` (~:461); `index_db_path` appears NOWHERE in it or `test_micro_join.py`. Both walk the real ~26 GB `.data/datasets` cold every run.
- **Referee r5-pt-7 caveat never built (dev).** `grep -rl seal-unaware apps/frontend/` = nothing. Static copy in `page.tsx` `referee-evidence-strategy-block` (:5152). Freeze holds (6/6 hashes).
- **2 captures owed (dev, passenger, NEVER a goal):** Scout Ledger family row + "variants tried" IN FRAME (J-08); a sentinel ELEMENT capture for J-10 (its full-page stitch duplicates the page top and truncates). Also regenerate demo step 04 — it narrates the unbuilt caveat over a duplicate image.
- **Era NOT certifiable: 8 minor items open** (0 critical); verbatim in `journey-history.json`.
- **ASK THE OWNER (blocks certification, not the loop):** 3 of the 8 are dev-chain, not product — QA certifies unchecked work; `closure_gate.py` ignores the browser verdict; `replay-lane.sh:269` can never run a round's own Target goldens (7/9 again). Owner-owned by this era's own scope rule.
- **Owner-owned, blocking nothing:** chain-ledger identity commitment (r8); judge's money floor.

## Last 2 verdicts

- iter 27: ESCALATE — nothing built (no developer dispatched); 2 lanes published claims their own artifacts contradict; only ESCALATE escapes the depth trap. All 10 journeys re-verified green.
- iter 26: CONTINUE — 2 fixes landed, but the delivered cache would have served a permanent wrong `0`; the auditor caught + fixed it (12th catch).

## Do not redo

- **Band-touch cache DONE** — `MicroBandTouchCache` + `micro_join.py:660-688`; the `cacheable = resolver.resolve(...) is not None` guard is LOAD-BEARING (`test_audit_b1_…` pins it).
- **Pilot-selector dedup DONE** — `_pilot_selectors_by_kind` filters `scout._PILOT_GRID_SELECTORS` at call time; never re-add a frozen literal.
- **`test_micro_no_referee_evidence_guard.py` ALREADY IS the r5-pt-7 source-scan guard** (iter-21, 4/4 green). Only the caveat-SERVING half is unbuilt — do not rebuild the guard.
- **Do NOT re-record tape, expose/assign a sealed shard, run J-09's studies on the real corpus, edit any `referee_*.py` (6/6 re-verified), or move fingerprint `08e471b10130e1e2`.**
- **`J-08.json` step 3 / `J-10.json` step 12 assert `"variants tried"`; J-07 cannot have a golden** (iter-19); readiness serving `80` (whole pool) not `21` is CORRECT (r5 anti-subtraction).
