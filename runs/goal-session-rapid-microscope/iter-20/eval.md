# Iteration 20 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This round had one job and it did it. J-07 "Graduation" now has a fresh picture that could
genuinely have failed, so the last piece of machine bookkeeping this era was waiting on is done.
Eight of the ten journeys are green. No code changed at all this round, and I checked that myself
rather than believing it. But I also found something that changes the plan: the reason the last
two rounds gave for not starting J-09 "The pilot studies" does not survive a check against your
own goal text. J-09 looks buildable today, without waiting for you.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing (carried; outside this round's re-check list; product diff EMPTY, spot-checked) | reports/qa/goal-rapid-microscope-iter-19-evidence/J-01-verify.png |
| J-02 The micro observer | passing | passing (carried; outside this round's re-check list; product diff EMPTY) | reports/qa/goal-rapid-microscope-iter-19-evidence/J-02-verify.png |
| J-03 Structure x flow | passing | passing (carried; outside this round's re-check list; product diff EMPTY) | reports/qa/goal-rapid-microscope-iter-19-evidence/J-03-verify.png |
| J-04 The Scout and the ledger | passing | passing (carried; outside this round's re-check list; product diff EMPTY) | reports/qa/goal-rapid-microscope-iter-19-evidence/J-04-verify.png |
| J-05 The walk-forward engine | passing | passing (carried; outside this round's re-check list; product diff EMPTY, spot-checked) | reports/qa/goal-rapid-microscope-iter-19-evidence/J-05-verify.png |
| J-06 The recorder and the Vault | partial | partial (carried; step 4 is an operator act you have not authorised; `vault.py` byte-unchanged) | reports/qa/goal-rapid-microscope-iter-19-evidence/J-06-verify.png |
| J-07 Graduation | passing (`evidence_makeup: true`) | **passing — RE-VERIFIED with a fresh discriminating capture; flag CLEARED** | reports/qa/goal-rapid-microscope-iter-20-evidence/J-07-graduation.png (row UT-J-07 = PASS) |
| J-08 The surface and MCP v6 | passing | passing — stored-script re-verified this round (0 failed steps) | reports/qa/goal-rapid-microscope-iter-20-evidence/J-08-verify.png (row UT-J-08 = PASS) |
| J-09 The pilot studies | failing | failing — never attempted; I confirmed it unbuilt on disk myself | none (no lane; `micro_readiness.py:99-105` names the three study ids and says registering their Scout specs "is J-09's work") |
| J-10 The kept product stands | passing | passing — stored-script re-verified this round (0 failed steps) | reports/qa/goal-rapid-microscope-iter-20-evidence/J-10-verify.png (row UT-J-10 = PASS) |

No row in `reports/phase-goal-rapid-microscope-iter-20-ui-test-results.md` reads
`DEFERRED-BUDGET` this round; the merged file is 3/3 PASS, 0 skipped.

## Anti-goal Check

The product diff this iteration is **empty** — I verified that myself, not from the handoff:
`git diff 437cc67..HEAD -- apps/ scripts/ docs/goal.md` is empty, `git status --porcelain apps/
scripts/` is empty, and `runs/.../journey-scripts/` is byte-untouched. So no anti-goal can have
been *introduced*. Each category is still answered explicitly below.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | `iter-20/scan-report.md` = CLEAN. Plus my own read of the capture and of the scoped rig's `graduation_ledger.jsonl` row: only sha256-shaped commitments (`row_hash`, `rule_hash`, `shard_checksum`, `spec_hash`) appear — no vault secret, satisfying "the vault secret never enters ... a screenshot". |
| Paid / external SaaS | OK | No manifest changed (diff empty); no new runtime dependency. |
| License changes | OK | No LICENSE or license-field change (diff empty). |
| Fabricated / substituted data | OK | The capture served real on-disk content from the QA-scoped rig; the report cites `reports/qa-scoped-backend-store-manifest.md` by path (launch `2026-08-20T15:56:30Z`, port 8301) and says plainly it is NOT the operator's store. `reports/qa/goal-rapid-microscope-iter-20-store-scope-guard.md` = CLEAN: 11275 files before, 11275 after, nothing written into the real store. |
| Frozen foundations (fingerprint, Referee, MCP) | OK — re-proved by me | `Config().config_fingerprint()` prints `08e471b10130e1e2`; all six `referee_*.py` sha256 hashes diff **identical, 6/6**, against the iteration-0 listing in `docs/handoffs/goal-rapid-microscope-iter-0-dev.md`; `len(TOOL_NAMES)` imports as **26**. |
| Hold-out-only promotion | MINOR, OPEN (pre-existing) | `micro_sealed_evaluation.py`'s economic floor is still supplied by the caller. Escalation condition re-tested this round, not assumed: **zero** production callers of `evaluate_sealed_verdict` (only docstrings + one error string), and `apps/backend/.data` still has **no** `micro_graduation` and **no** `micro_vault` directory. Not tripped → stays minor. |
| Evidence honesty (T-10) | ONE ITEM CLOSED, two open | Iteration 19's "J-07 certified but never run" item is **closed** by this round's capture, and `state/golden-gaps` rebuilt itself to `J-07` with no developer edit. Still open: J-10's two dropped Playbook-Evidence assertions (iter-16), and iteration 19's UT-10 capture defect (that lane did not run this round). |
| Deterministic / seeded, no lookahead, immutable data, sealed-shard rails, denominator, accessor-only door, read-only MCP, no execution path | OK | Zero product diff, and I ran the whole suite myself: **3,281 passed / 8 skipped / 0 failed / 0 errors** in 628.91s — identical to iteration 19's baseline, with all 30 traps present (TR-1…TR-30; TR-17 exists only as TR-17a/b/c). |
| Enhancement loop stays in its box | OK | The `AUTO:journeys` block in `docs/goal.md` is still empty; every journey spec hash matches its recorded value (10/10), so no goal text moved. |
| Host-guard caps | OK | No cap was disabled, widened, or bypassed; nothing in the diff touches the host-guard config. |

**No critical violation, introduced or open.** Five minor items remain open (numbers 17, 21, 25,
29, 34 in `journey-history.json`), all decided, none waiting on you except the economic-floor
ruling.

## Next-Step Recommendation

**Build J-09 "The pilot studies" next, as a FULL round with the independent checker.**

The last two rounds said J-09 must wait for your decision about the sealed judge's money floor.
I checked that claim this round instead of inheriting it, and I do not think it holds. Four
things, each of which I confirmed myself:

1. J-09's own acceptance text says, in your words, that **no study output feeds any gate,
   certificate, or promotion**. The judge with the hole grades sealed results. J-09 produces
   none.
2. Nothing in the shipped product calls that judge at all — I grepped again this round and found
   only comments and one error message.
3. The only tape J-09 can read is the old 12 symbol-days, which your own rules mark permanently
   "exploratory". By the "evidence classes never mix" rule, that evidence can never reach the
   sealed judge even in principle.
4. J-09's money column does not come from the broken place. The Scout works out its own floor
   from the real quoted spreads it measured (`scout.py:1016-1021`, a fixed multiple of the
   family's median spread) — nobody hands it a number.

What J-09 would honestly produce today: three pre-declared studies on the record, each screened,
each almost certainly answering "not enough evidence" at the walk-forward stage — and your goal
says plainly that "not enough evidence" and "no survivor" are passing answers. That is the era's
whole point.

If the next round's planner finds a real dependency I have missed, it must **write that down in
the plan** rather than quietly defer J-09 for a ninth round.

Three small jobs to carry as passengers, never a round of their own: (1) put back the two
Playbook-Evidence checks that were dropped from J-10's stored script in round 16; (2) re-take the
picture for the backend-failure check, whose round-19 photograph does not show what its row
describes; (3) build the disclosure and guard the owner ordered back in round 9 for the stale
Referee readiness count — it has been unbuilt for eleven rounds and needs nobody's permission.

Still do NOT record real market tape (J-06 step 4), and still do not touch the sealed judge's
money floor. Both wait on you.

**In one sentence:** approve building the three pilot studies next — they are the last piece of
machine work in this era, and I believe they do not need your decision after all; the only two
things that still do are authorising real tape recording for J-06 and ruling on the sealed
judge's money floor.
