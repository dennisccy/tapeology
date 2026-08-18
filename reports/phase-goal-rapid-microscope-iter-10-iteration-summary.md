# Iteration Summary — goal-rapid-microscope-iter-10

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-08-18
**Iteration:** 10

## In plain words

**What you can do now:** On the Desk page, you can see an honest readout of how much tick-by-tick market data is on hand and which research floors are still unmet. Behind the scenes, the product also reads buying and selling pressure event by event, matches chart signals to that activity without peeking at the future, and screens trading ideas with a tamper-evident record of every trial — including the ones that fail. It can honestly refuse to compute a result when there isn't enough history, and it can now walk a promising test idea all the way from "still being explored" to "ready to hand to the judge," carrying every failure and every kill along with it.

**What changed this time:** Behind the scenes, a new "Graduation" process now exists: it tracks a promising idea's complete paper trail — every test passed, every one failed — as it climbs from early exploration to being sealed and ready for the human-supervised Referee. It has no screen of its own yet; today it honestly reports that no candidate has gone through it, because none has.

**What's next:** Next, the team will make sure a newly recorded batch of market data stays fully anonymous as a whole — no more figuring out which pieces are hidden by process of elimination — before any more real data gets recorded.

## Headline

J-07 Graduation ships: fixture candidates climb all four states, nothing laundered out

## Direction

**Signal:** improving
**Why:** J-07 "Graduation — provenance in, nothing laundered out" moved from failing to passing this iteration after the evaluator personally walked its full four-state climb and ran four adversarial refusal probes outside the developer's own tests. J-01 through J-05 all held on independent re-check with zero regressions, and the ESCALATE is driven by two disclosed spec-§8 gaps the developer filled by invention rather than escalating — not by any broken journey. Six of ten journeys now pass, continuing a five-iteration streak with no state-change gaps.

**Trend (last 5 iters):**
- Newly passing this iter: J-07
- Newly passing in last 5 iters total: J-05, J-07
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 9 opened (1 critical — iter-7, introduced and fixed within the same round; 8 minor); 4 of the 8 minor items remain open at iter-10; 0 critical currently open
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** J-07 "Graduation — provenance in, nothing laundered out" is done and I proved it myself: I ran the whole four-step climb against a throwaway store, outside the coder's own tests, and then tried to break it four ways — it refused all four. Nothing else moved, nothing broke, and the frozen parts are still frozen. I am asking for the full pipeline next time for one specific reason: the written spec leaves two things undefined, the coder invented answers for both instead of stopping to ask you, and the next piece of work is the vault's central promise, where the independent checker is the only step that has ever caught this kind of mistake.

## What was done

- Product changes: apps/backend/app/research/micro_graduation.py (new), apps/backend/app/research/micro_routes.py, apps/backend/tests/test_micro_graduation.py, docs/research-directions.md, GET /research/desk/micro/graduation (new route)
- Built micro_graduation.py: the four-state stage vocabulary (exploratory → walkforward_survivor → sealed_survivor → referee_handoff_ready) on a new hash-chained GraduationLedger that reuses the shared HashChainedLedger primitive.
- Added the read-only GET /research/desk/micro/graduation route; confirmed it serves an honest "No candidates ledgered." empty state against the real (currently empty) ledger.
- Added 19 new tests (test_micro_graduation.py, TC-1 through TC-9 plus two extended guards); full suite now 3,185 collected / 3,177 passed / 8 skipped / 0 failed, independently matched by the reviewer and the evaluator.
- Verified 7/7 required-still-passing journeys (J-01..J-06, J-10) via deterministic golden replay this round — none deferred for time, unlike iterations 8 and 9.
- Verified 1 target journey (J-07) passes browser QA: honest empty-state response, real screenshot on disk.
- Re-confirmed frozen foundations: config fingerprint 08e471b10130e1e2 unchanged, all six referee_*.py hashes byte-identical, MCP surface still 22 tools, zero frontend files touched.
- Outside the pipeline, three owner rulings landed as spec revision r5 ("the opaque research pool") — settles the design for closing the vault's membership-leak and recorder-progress-leak gaps; not yet built.
- Disclosed two spec-§8 interpretation gaps (caller-supplied sealed verdict; invented confirmation-boundary formula), independently confirmed as genuine spec gaps by the reviewer and logged as an open anti-goal minor item.

## What's left

- Journey J-08 (The surface and MCP v6 — the funnel is visible) failing — no `/desk` UI section or MCP v6 bump yet; explicitly out of scope this iteration.
- Journey J-09 (The pilot studies — three predeclared questions, honest answers) failing — no study spec ledgered yet (`.data/micro_scout` absent); blocked behind J-06/J-08.
- Journey J-06 (The recorder and the Vault — new tape, sealed at birth) partial — steps 4 (real Alpaca recording + sealing) and 5 (tranche-pool disclosure) not built; re-scored against the new r5 wording, which adds unbuilt work to step 3 (one-opaque-pool rule, aggregate-only recorder progress, widened TR-2 inference trap).
- Journey J-10 (The kept product stands — traps armed, sentinel green) partial — trap coverage still 19 of 22 (TR-3, TR-17, TR-22 absent by name); the deterministic-rerun check has still not been run this era.
- The r5 ruling's design is settled but not yet implemented: corpus/vault surfaces still list recordings one-by-one rather than serving aggregate-only pool totals.
- New open anti-goal minor item: the developer invented answers to two undefined spec-§8 questions (who decides a sealed verdict's pass/fail; the confirmation-boundary formula) instead of stopping for an owner ruling — inert today, but needs a ruling before J-06 step 4 runs.
- Two older items still await the owner: whether a damaged vault record should fail-closed (safe) or fail-open (today's behavior), and the one-quote-early depletion timing stamp (waiting since iteration 2).

## Next step

Build your r5 decision — "a recorded batch is one opaque pool" — as the next round, under the full pipeline with the independent checker, and scope it to that one step only. Three concrete things: the corpus page must stop listing recordings one by one on EITHER side while any member of a batch is still unopened; the recording-progress view must show only totals, never a name, a date or an id; and the trap that guards this must be rewritten so that it actively tries to work out which recordings are hidden and fails to. Do NOT let that round record real tape — your ruling settles the design, but none of it is built, and one question of the same family is still open. Please decide three things when you can: (1) should a damaged vault record make everything refuse (safe) or make everything open (what happens today)? (2) who decides whether a sealed recording's test was passed or failed — today the program simply believes whoever calls it; (3) the timing stamp that is one quote too early, waiting since round 2. After r5 lands, the natural order is J-08 "The surface and MCP v6" — the funnel is invisible on screen today — then J-09 "The pilot studies", then a hardening round for the three traps still missing by name (TR-3, TR-17, TR-22) and the byte-identical re-run check that has never been run this era.

## Assumptions made

- iter-10 · goal-evaluator — Ambiguity: whether the developer's two disclosed spec-§8 improvisations (caller-supplied sealed verdict; invented confirmation-boundary formula) block J-07's acceptance, given the era's Constraints say an ambiguous spec procedure must be DROPPED and surfaced for an owner ruling, never improvised. We chose: J-07 passing (all four acceptance clauses independently verified), with the improvisations recorded as a new open minor anti-goal item and an owed owner decision, rather than scoring J-07 partial. Reversible: no in one direction — if a real sealed evaluation is recorded before the owner rules, the invented reading is written into a permanent, hash-chained export bundle.
- iter-10 · goal-evaluator — Ambiguity: goal.md's J-07 has no browser acceptance clause (keyless/automated, browser reveals land in J-08), yet the standing rule says no screenshot ⇒ unknown never passing and unit tests are never journey evidence; nothing states which governs a journey whose acceptance is defined as a fixture walk. We chose: score J-07 passing on the evaluator's own end-to-end four-state walk plus four adversarial refusal probes (run outside the developer's test file), the 19-test suite green inside the full run, and the one screenshot its single servable surface can produce (the honest empty state). Reversible: yes — J-08 renders graduation state on /desk next, giving J-07 a true browser-captured acceptance one iteration later.
- iter-10 · owner (spec revision r5, "the opaque research pool") — Ambiguity: three items escalated from the iter-9 audit (cartesian-subtraction membership leak; recorder-progress per-chunk identity leak; the frozen referee_evidence metric counting withheld shards) needed an owner ruling. We chose: a newly recorded tranche is ONE opaque research pool (aggregates only on both sides while any member is unexposed); recorder progress serves aggregates only with no operator bypass; keep the referee freeze but disclose the metric as seal-unaware with micro_readiness as canonical owner. Reversible: no — r5 is a named revision (re-keys nothing today: zero shards sealed, zero tranches recorded).
- iter-10 · goal-decomposer — Ambiguity: goal.md's J-07 acceptance never says whether GET /research/desk/micro/graduation ships in the same iteration as micro_graduation.py or waits for J-08 to wire it in. We chose: ship the read-only route this iteration alongside the module, matching the precedent iter-9 set for vault.py. Reversible: yes — the route is inert this iteration (no caller, real ledger empty) and J-08 wires it into /desk later with zero route changes.
- iter-9 · goal-evaluator — Ambiguity: the audit carries two CRITICALs (sealed membership recoverable by cartesian closure; recorder-compute route leaking per-chunk identity) plus two more (withholding predicates fail open on a corrupted ledger; a frozen referee file counting withheld shards) — do these force a REGRESSION verdict when no shard is currently sealed? We chose: record all four as OPEN but minor severity, and return CONTINUE rather than REGRESSION, verified myself that no vault ledger file exists and no real tape exists, so nothing is currently breached. Reversible: no in one direction — if J-06 step 4 runs before these are ruled, real tape gets sealed under a guarantee that is demonstrably false.
- iter-9 · goal-evaluator — Ambiguity: whether holding J-02/J-03/J-04/J-05 at passing on the evaluator's own re-derivation alone is enough when their own modules ALL changed in the r4 fix round (so A.6 evidence durability covers none of them). We chose: hold passing for all four, with the deferral and "durability does NOT cover this" caveat stated verbatim in each journey's note; J-04 flagged as the honest weak one since verify_chain() could not be re-run (no real scout ledger exists on disk). Reversible: yes — golden replay scripts for J-01–J-06 and J-10 now exist on disk, restoring true lane-level verification next iteration.
- iter-9 · owner (spec revision r4) — Ambiguity: r3's sealed-shard refusals are route-scoped, but edge_report._all_datasets and pnl_scan._split_datasets each enumerate the whole DatasetStore directly, so a corpus-wide report/sweep could read a sealed shard's events and republish its id/checksum/outcome aggregates. We chose: enumerators EXCLUDE withheld shards and DISCLOSE the exclusion (never abort the whole sweep, never accept the bypass). Reversible: no — r4 is a named revision (re-keys nothing today: zero shards sealed).

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-rapid-microscope-iter-10.md |
| Dev handoff | — | docs/handoffs/goal-rapid-microscope-iter-10-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-rapid-microscope-iter-10-review.md |
| Browser QA | PASS | reports/phase-goal-rapid-microscope-iter-10-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-rapid-microscope/iter-10/eval.md |
| Journey history | — | runs/goal-session-rapid-microscope/state/journey-history.json |
