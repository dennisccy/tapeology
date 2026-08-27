# Iteration 8 Evaluation

**Verdict:** STALLED
**Depth Recommendation For Next Iteration:** lean

## Summary

The last journey of the era is finished. The Desk page now has one "Final Summary" panel that shows
the whole real epoch in one place — how the 11 ratified sources were each ruled on, that zero
candidate families were built, that zero survivors exist, that the seal is green — and each source
can be opened to read its full written provenance. I checked this myself instead of trusting the
reports: I asked the running backend for the same page data, compared all 11 source records
character by character against the sealed source file (zero differences), and re-ran the automatic
browser replay of all 8 journeys after the auditor's late fix (8 of 8 passed). All 8 journeys now
pass and nothing regressed.

The era still cannot be declared finished, and the reason is not the product. Two honesty entries in
the anti-goal record are still open, and only the owner can close them: whether the first real batch
that was made and thrown away is accepted, and whether it is acceptable that simply opening the page
writes a small lock file. I checked both again by hand this iteration. The lock file really is still
written (I watched its timestamp move while the real record book stayed untouched), and the only
place it could be fixed is inside a file the era has permanently sealed. Goal Mode has no legal move
left on either one, so the loop stops here and waits for two decisions.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The Foundry opens as a new finite era | passing | passing (replay) | reports/qa/goal-hypothesis-foundry-iter-8-evidence/J-01-verify.png (opened — spot-check) |
| J-02 Sources compile into auditable CandidateSpecs | passing | passing (replay) | reports/qa/goal-hypothesis-foundry-iter-8-evidence/J-02-verify.png |
| J-03 Generic interpretation preserves Scout decisions | passing | passing (replay) | reports/qa/goal-hypothesis-foundry-iter-8-evidence/J-03-verify.png |
| J-04 Foundry owns denominator, ledger, freeze barrier, lock | passing | passing (replay) | reports/qa/goal-hypothesis-foundry-iter-8-evidence/J-04-verify.png |
| J-05 The factory passes the hermetic oracles | passing | passing (replay) | reports/qa/goal-hypothesis-foundry-iter-8-evidence/J-05-verify.png |
| J-06 One complete real epoch generated and committed | passing | passing (replay) | reports/qa/goal-hypothesis-foundry-iter-8-evidence/J-06-verify.png (opened — spot-check; shows "REAL EPOCH — NOT A FIXTURE", epoch:afd19e9c11a6534f) |
| J-07 Goal Mode exhausts the frozen real epoch | passing | passing (replay) | reports/qa/goal-hypothesis-foundry-iter-8-evidence/J-07-verify.png |
| J-08 The operator sees the final Foundry truth | **failing** | **passing** | reports/qa/goal-hypothesis-foundry-iter-8-evidence/J-08-post-audit-fix-evaluator-verify.png (evaluator's own post-fix replay) + J-08-verify.png + UT-01..UT-06 rows in reports/phase-goal-hypothesis-foundry-iter-8-ui-test-results.md |

Merged browser results: **13/13 PASS, 0 skipped**. No `DEFERRED-BUDGET` row, no `browser-infra.json`,
no `journeys-changed.md`, not maintenance isolation. A golden replay script for the target journey was
created this iteration (`runs/goal-session-hypothesis-foundry/journey-scripts/J-08.json`), applying the
iter-7 lesson.

### J-08 evidence walk (the one status change)

- **Screenshot opened.** `J-08-verify.png` shows, on one screen: the disposition counts
  (ALIASED_PROXY_ONLY 2, BLOCKED_DIRECTION 4, BLOCKED_SPEC_GAP 1, ALIASED_VARIANT_VOCABULARY 1,
  EXCLUDED_PREVIOUSLY_KILLED 1, EXCLUDED_PREREQUISITE_UNMET 1, EXCLUDED_GATE_CLOSED 1 = 11), Family
  count 0, Variant count 0, Frozen-ready total 0, Evidence class `historical_exposed_diagnostic`,
  Protected/withheld/sealed reads 0, Freeze integrity `green`, Epoch status `committed`, the explicit
  zero-survivor sentence, the exhaust-complete sentence, and the expanded drill-in for
  `pilot-study-1-range-wall-failed-aggression` with mechanism, audit note, direction derivation,
  comparator derivation, threshold provenance, superseded fields, alternatives, the 64-character
  source hash, and all three quoted spans with their locations.
- **REST body cross-checked by the evaluator (TC-5, first-hand).** `curl` of
  `GET /research/desk/micro/foundry` returns `final_summary` with exactly those values, and all 11
  served source records match the sealed `docs/hypothesis-foundry/source-registry.json` field-by-field
  with **0 mismatches**. None of `p_value`/`p_screen`/`effect_bps`/`forward_return`/
  `observation_count`/`pnl` appears in the served `epoch_manifest` (this independently covers auditor
  gap B3).
- **Post-fix re-replay by the evaluator.** The auditor fixed a real honesty defect (F1) in
  `apps/frontend/app/desk/page.tsx` at 16:25, *after* the browser lane's 16:08 screenshots. I re-ran
  the golden replay myself against the live app: J-08 1/1 PASS and J-01..J-07 7/7 PASS, and captured
  `J-08-post-audit-fix-evaluator-verify.png`, which shows the added caveat
  "(zero FROZEN_READY variants this epoch — an honest, vacuous completion)". So the shipped state, not
  only the pre-fix state, is photographed.
- **Vacuous steps.** J-08 step 2's "one evaluated variant (if any exist)" and step 3's survivor branch
  are vacuous on a zero-candidate epoch; the screen renders explicit honest text rather than a blank,
  matching the precedent this session set for J-06 step 4 (iter-5) and J-07 (iter-6). MCP is
  explicitly non-blocking per `docs/goal.md` and did not ship.

### Evidence gap recorded (does not change any status)

- **Walkthrough recording is defective (`evidence_makeup: true` on J-08).**
  `reports/demo/goal-hypothesis-foundry-iter-8/` is `RECORDED_WITH_NOTES` with all 7 click steps
  failing. Root cause found by the evaluator: the demo script targets testids
  `desk-section-expand-*`, and no such testid exists anywhere in `apps/frontend/app/desk/page.tsx`.
  Step 03 "View the New Final Summary" therefore shows the top of the Desk page, not the Foundry
  panel. This is a demo-script authoring defect, not a product defect — the golden journey scripts use
  different selectors and replay 8/8 green. Re-record as a passenger task, never as an iteration goal.
- **Auditor P1 / P2 (reporting defects, disclosed, not rewritten).** The QA report cites
  `final-summary-section.png` as proof of visibility; I opened that PNG and confirm it is uniformly
  blank. The same claim is carried by the non-blank `demo_runner` captures, which I also opened. The
  QA report also names `foundry_runner.py` (sealed, byte-identical) and `lib/api.ts` (never touched)
  as "modified"; neither appears in the diff, `git status`, or `status.json`. Both belong in the
  closure record.

## Anti-goal Check

Deterministic scan: `runs/goal-session-hypothesis-foundry/iter-8/scan-report.md` — **CLEAN**, no
secret, dependency, or license findings on added lines. Product diff: 7 files
(`micro_routes.py`, 4 test files, `desk/page.tsx`, `lib/types.ts`) — no sealed path.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials committed | OK | scan-report CLEAN; no config/env file in the 7-file diff |
| Paid / external SaaS dependency | OK | no manifest touched (no package.json / requirements / pyproject in the diff) |
| License change | OK | scan-report CLEAN; no LICENSE or license field in the diff |
| Fabricated / substituted data | OK | evaluator diffed all 11 served source records against the sealed registry: 0 mismatches; UI shows the "REAL EPOCH — NOT A FIXTURE" badge and the real `epoch:afd19e9c11a6534f` |
| No browser proof based on fabricated fixture state | OK | the QA rig is store-scoped, but the Foundry artifacts served are the Git-tracked sealed files and the real `.data/foundry` ledger; real vs fixture views stay visibly distinguished |
| Frozen foundations stay frozen | OK | evaluator recomputed all 59 `freeze-set.json` hashes: 0 mismatched, 0 missing, after the audit's fix |
| No science-affecting change after the first-read lock | OK | diff is read-surface + tests + UI only; served values are read verbatim from sealed artifacts (0 drift) |
| Single source of truth | OK | `final_summary` is a pure projection; `diagnostic_survivor_count` has exactly one implementation (`micro_routes.py`); coherence audit agrees |
| Persistence stays scoped (`GET` read-only) | **OPEN — iter-6 entry, MINOR, BLOCKING** | re-verified live: two GETs advanced `foundry_exhaust_runner.lock`'s mtime while `foundry_trial_ledger.jsonl` and its chain-head stayed byte-identical. Operative intent intact; literal words breached. Only repair site (`foundry_runner.py` `SingleFlightLock.acquire`) is sealed and has no skip parameter |
| No second real generation epoch | **OPEN — iter-5 entry, MINOR, BLOCKING** | no new epoch this iteration (`epoch:afd19e9c11a6534f` unchanged); the entry is about the earlier discarded id and needs owner ratification |
| No candidate invented / no late variant insertion / no family splitting | OK | zero families, zero variants; manifest sealed and byte-identical |
| No automatic ranking / selection among survivors | OK | zero survivors; the screen states this explicitly |
| No claim that `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN` is OOS evidence | OK | the survivor branch text reads "not OOS evidence, not Referee-ready, not a confirmed outcome" |
| Opaque pool stays inference-resistant (TR-2) | OK | evaluator re-ran the 16 TR-2 vault inference tests with the new fields present: green |
| No profit claims and no advice | OK | evaluator re-ran `test_copy_discipline.py`: green; new copy is quoted research provenance |
| No Goal Mode workaround editing/deleting/xfailing a scientific guard | OK | the one deleted assertion in `test_foundry_real_epoch_artifacts.py` was replaced with a stricter field-by-field pass-through check plus an enrichment-presence check, with the reason written in the test; residual reach gap recorded as B3 and independently re-verified clean |
| No execution path / no lookahead / immutable registered data | OK | none of these surfaces is touched; store-scope guard CLEAN (11395 protected files byte-identical) |

**Disposition counts** (`anti_goal_disposition.py summary`): **total=4, resolved=2,
unresolved_blocking=2, unresolved_non_blocking=0, unresolved_critical=0.** Both blocking entries are
MINOR and carry no owner disposition — the evaluator may never write one.

**Coherence:** `runs/goal-session-hypothesis-foundry/iter-8/coherence.md` = **COHERENCE-WARN** — no
blocking violations; two advisory notes (the blueprint's Data Contract row still names the sealed
`foundry_runner.py` as owner of `diagnostic_survivor_count` when the real sole owner is
`micro_routes.py`; and a redundant, non-divergent second ledger read per request). Does not veto.

**Pipeline health:** review PASS, QA PASS, audit PASS_WITH_GAPS, closure CLOSURE-PASS. No fail-open.
The UX-regression lane was shed for wall-clock budget (ninth consecutive breach, 10213s vs 3600s); the
defect it would have caught (F1) was caught by the hard auditor instead.

## Next-Step Recommendation

There is no product work left that Goal Mode is allowed to do. Two decisions belong to the owner, and
the era cannot be signed off until both are made:

1. **The first batch that was made and thrown away.** Accept it or reject it. A first real epoch was
   created, an independent check found one written claim unsupported, and the whole batch was rebuilt
   before anything was published and before any result was ever read. Nothing was hidden, and a guard
   now prevents it happening again — but no guard can undo the id that was created.
2. **The lock file written when the page is opened.** Accept it, or approve breaking the era's seal to
   fix it. Opening the Foundry page creates a small empty lock file. Nothing scientific is recorded —
   I watched the real record book stay untouched — but the written rule says these page reads are
   "read-only", and the only place the behaviour lives is inside a file this era permanently sealed.
3. **(Not blocking, but worth writing down.)** The sealed command file keeps a second, permanently
   un-editable copy of one count. Recording it in the closing record as an accepted exception stops
   future work from chasing a fix that is not legal.

The cheapest way to close 1 and 2 is one written owner ruling on each entry in
`runs/goal-session-hypothesis-foundry/state/journey-history.json` (an `owner_disposition` marking them
open-but-not-blocking-this-era), then `--resume`. After that, one short iteration can re-record the
broken walkthrough, correct the blueprint's ownership row, and the era can be certified.

In one sentence: please make those two rulings (accept, or reject and say what to do instead), then
resume — everything the era set out to build is now finished and verified.

## Halt Justification

Halting as **STALLED**, not GOAL_ACHIEVED and not CONTINUE.

Not GOAL_ACHIEVED: two anti-goal entries are unresolved and classified BLOCKING by
`anti_goal_disposition.py`, and `docs/goal.md`'s own Completion section requires "all anti-goals are
clear". My own contract also forbids GOAL_ACHIEVED while any anti-goal violation is unresolved.

Not CONTINUE: every Must-have journey passes, so there is no failing journey to target, and the four
documented gaps (B2, B3, F2, F3) are non-blocking and would not change this outcome. Another iteration
would end in exactly the same place, which is the loop the framework warns about.

STALLED because every unblock path for both live blockers is a human-owned action:

- **"No second real generation epoch" (iter-5, MINOR, blocking).** Unblock options:
  (a) owner ratifies the discarded first `epoch_id` and records an `owner_disposition`;
  (b) owner rejects it, which would require a decision about the whole era's epoch. No code change can
  discharge it — the recurrence guard has already landed and cannot un-mint an id.
- **"Persistence stays scoped" (iter-6, MINOR, blocking).** Unblock options:
  (a) owner records an `owner_disposition` accepting the lock-file write on the literal reading;
  (b) owner sanctions an edit to the sealed `apps/backend/app/research/foundry_runner.py` (an
  irreversible act against the era's own one-way seal). I checked the code myself:
  `read_exhaust_progress` calls `SingleFlightLock.acquire` unconditionally and takes no parameter to
  skip the probe, so no legal non-sealed fix exists — routing around it would create a second
  computation site and re-open the single-source-of-truth violation iter-7 just closed.

Neither option is available to Goal Mode, and I may never write an `owner_disposition` myself. The
loop should stay stopped until one of the options above is chosen; `--resume` afterwards.
