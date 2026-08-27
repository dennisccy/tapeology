# Iteration 4 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The one Foundry screen the last two verdicts asked for is now real, and I checked it myself rather
than trusting the reports. Two journeys moved from partly done to done: J-03 "Generic interpretation
preserves timing, direction and Scout decisions" and J-04 "Foundry owns the denominator, ledger,
freeze barrier and lock". Two stay partly done for concrete, named reasons: J-02 "Sources compile
into auditable CandidateSpecs" is missing three fields its own checklist asks the screen to show, and
its last check needs a report that only a later stage can write; J-05 "The complete factory passes
hermetic oracles" never shows the kill-type mapping its own checklist names. I escalate because a
plain recommendation to use the deeper review pipeline has now been overruled twice by the engine's
budget rule, and the next stage is the one irreversible step of this whole era.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The Foundry opens as a new finite era | passing | passing | reports/qa/goal-hypothesis-foundry-iter-4-evidence/J-01-verify.png (golden replay UT-J-01 PASS; script asserts the frozen fingerprint `08e471b10130e1e2` is on screen) |
| J-02 Sources compile into auditable CandidateSpecs | partial | partial | reports/qa/goal-hypothesis-foundry-iter-4-evidence/UT-J-02-result.png |
| J-03 Generic interpretation preserves Scout decisions | partial | **passing** | reports/qa/goal-hypothesis-foundry-iter-4-evidence/UT-J-03-result.png |
| J-04 Foundry owns the denominator, ledger, freeze and lock | partial | **passing** | reports/qa/goal-hypothesis-foundry-iter-4-evidence/UT-J-04-result.png |
| J-05 The complete factory passes hermetic oracles | partial | partial | reports/qa/goal-hypothesis-foundry-iter-4-evidence/UT-J-05-result.png |
| J-06 One complete real epoch is generated and committed | failing | failing | not targeted; blocked by the goal's own required order until the read surface is complete |
| J-07 Goal Mode exhausts the frozen real epoch | failing | failing | not targeted; blocked by the same required order |
| J-08 The operator sees the final Foundry truth | failing | failing | not targeted; blocked by the same required order |

### What I verified myself, per changed journey

**J-03 → passing.** The Interpreter Fixtures block in `UT-J-03-result.png` shows all five named
scenarios with the amber "HERMETIC FIXTURE — NOT THE REAL EPOCH" banner: scalar equivalence
`screens_equal: true`; conjunction; deferred refill with `unresolved excluded: 6` and both sides
sharing `outcome_start = max_conditioning_available_at`; the mirrored pair with predeclared sidedness
`support/long = long · resistance/short = short`; and the typed block `BLOCKED_UNSUPPORTED_RELATION`.
Two of the five steps prove themselves inside a collapsed "Screen detail" drill-in, so I did not take
the report's word for them — I re-ran `foundry_interpreter.interpreter_hermetic_fixture_view()`
myself and reproduced exactly the reported numbers: conjunction `n_candidate=16 / n_comparator=32`
with `feature_name`/`transform`/`params` all `None` at the Scout boundary (only boolean membership
crosses), and the mirrored pair returning `decision=killed_direction` (effect `-79.905625` bps) for
the long side against `decision=survive` for the short side — a real direction gate, not two static
labels.

**J-04 → passing.** Every one of its six steps is rendered and legible in `UT-J-04-result.png`:
the four-row family table (single 1 / multiple 5 / at_cap 24 / over_cap 25) with denominator visible
on all four and only the over-cap row blocked whole and highlighted; `Late insertion refused: true`;
generation replay `identical rerun verified: true · drifted rerun refused: true`; the freeze record
labelled "fixture-scoped; not yet the real committed file" naming
`docs/hypothesis-foundry/freeze-set.json` with hash `ea01e6eb3293…` and transitive coverage true;
first-read lock all three outcomes true; replay all three outcomes true. I re-ran
`foundry_freeze.freeze_integrity_hermetic_fixture_view()` and got the same values.

**J-02 stays partial — three named reasons.** Its step 3 asks the screen to show, for every record,
"source refs, an exact quoted source span + precise location, operative formula refs, superseded
fields, alternatives, threshold provenance, direction derivation, alias/lineage, and exactly one
disposition". The card renders the source ref, quoted span with location, direction, threshold
provenance, alternatives and disposition — but **not** operative formula refs, superseded fields, or
alias/lineage. Those values are in the backend payload; nothing puts them on screen. Second, the
"two explicitly-frozen legal variants" archetype shows only one of its two records (the sibling
appears only as an id inside `Alternatives`) — disclosed honestly by the developer and the reviewer.
Third, step 5's second half asks the operator to inspect a committed audit report that a later stage
has not written yet; the iteration spec predicted this exact outcome. The half that could be built
is genuinely proven: I re-ran the compiler view and reproduced the identical hash
`0892112d8ba6b1f79ab5cddda4263c852cc1bebdf79b4a4660cd0995359a6e1e` from the two very different
injected effect/p/n sets shown side by side on screen.

**J-05 stays partial — its step 3 has no home on screen at all.** The step asks to confirm that a
too-small sample maps only to `EVALUATED_INSUFFICIENT`, every other kill maps to `EVALUATED_KILLED`,
and only a survivor maps to `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN`. The code does enforce this — I ran
the composite epoch myself and confirmed all seven rows land on exactly the right state — but the
Hermetic Oracles panel carries no per-row state at all, so an operator cannot see the mapping. Step
4's "best-of-N disclosure" half is likewise unrendered (only the denominator half is). Separately,
the "Outcome types present" line an operator reads as proof is built from a hard-coded label
dictionary rather than read back off each row (`foundry_hermetic_summary.py:303-318`); the reviewer
and the coherence auditor each caught this independently. I checked whether it is currently telling
the truth — it is, all seven labels match the real returned state — but the panel claims to prove
something it does not actually read.

### Stable-journey spot-checks

J-01 is the only stable passing journey and is in the Required-still-passing set; its golden replay
ran and passed (`regression-replay-results.md`, 1/1). I opened `J-01-verify.png` and confirmed the
`/desk` page with the Hypothesis Foundry panel expanded, and the replay script itself asserts the
frozen configuration fingerprint `08e471b10130e1e2` is on screen — which also re-proves the
"frozen foundations stay frozen" rail. With fewer than two other stable journeys available, I widened
instead to re-running the four Foundry backend test modules myself: **75 passed, 0 failed**.

## Anti-goal Check

Worked from `iter-4/scan-report.md` (**CLEAN** — no secret, dependency or license findings on added
lines; 2 untracked files scanned) plus `iter-4/iter-diff.md` (13 files) and my own reads of the
implicated hunks.

**Disposition counts (`anti_goal_disposition.py summary`): total=1 · resolved=0 ·
unresolved_blocking=1 · unresolved_non_blocking=0 · unresolved_critical=0.**

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | scan-report CLEAN. No new config/env file in the 13-file diff. The new payload carries only fixture ids and SHA-256 file digests; no secret appears in any screenshot. |
| Paid / external SaaS | OK | scan-report reports no dependency findings; no manifest (`requirements.txt`, `pyproject.toml`, `package.json`) is in the changed-file list. |
| License changes | OK | scan-report CLEAN; no LICENSE or license field in the diff. |
| Fabricated / substituted data | OK | Every new value is hermetic fixture data computed by the real modules. I re-ran three of the four builders and reproduced the on-screen numbers exactly (compiler hash, interpreter decisions, freeze table). Store-scope guard **CLEAN**: 11395 protected files byte-identical, nothing written to the operator's real data folder. |
| "No browser proof based on fabricated fixture state…; fixture and real views must be visibly distinguished" | OK | All four new subsections carry the amber "HERMETIC FIXTURE — NOT THE REAL EPOCH" banner, visibly distinct from the header's real era-open baseline block. Verified in all four screenshots and in `page.tsx` (four `HermeticFixtureBanner` mounts). |
| "`GET /research/desk/micro/foundry` … read-only and never compute/evaluate a candidate or trigger the exhaust runner" | OK | The four views are built once at module import and served verbatim (`micro_routes.py:764-800`). Three route tests prove the handler never invokes a builder per request and that two responses are the same cached object. The hermetic fixtures that run at import use temporary directories and touch no market data. |
| "Frozen foundations stay frozen … never silently mutated" | **MINOR VIOLATION (unresolved, blocking)** | `foundry_hermetic_summary.py:75-82` and `:183-188` — production code reassigns the frozen Scout internal `scout._two_sided_p` and restores it in a `finally`. This runs inside the backend server process at import time. The matching test code uses `monkeypatch.setattr`, which restores automatically; the production copy has no such protection. Nothing persists and no research result changed (I re-ran the epoch and every outcome was correct), so this is MINOR, not critical. Recorded in the ledger rather than waved away, per this goal's own rule that anti-goal findings "are not dismissed in prose". |
| "Single source of truth … REST/UI/MCP never independently recompute" | OK | `coherence.md` = **COHERENCE-PASS**; one computing module per key; the UI renders payload verbatim (I grepped the frontend diff for arithmetic — none). One advisory: the outcome-type label is not read back off the row it describes (see J-05 above) — a fidelity gap inside the single owner, not a second owner. |
| "No source record, threshold, direction, family partition, or CandidateSpec chosen because of effect, p-value, sample density, or prior Scout outcome" | OK | Directly disproved on screen and independently by me: two very different injected effect/p/n sets produce the identical `candidate_spec_hash`. |
| "No family splitting to evade the 24-variant cap" | OK | The 25-variant family is blocked whole; the 24-variant family is not. Visible in the family table. |
| "No second Foundry statistical decision rail" | OK | The summary drives the real compiler/family/ledger/runner path; the mirrored short side reuses the existing `killed_direction` gate. No new verdict logic. |
| "No Foundry trial registered into the Scout ledger this era" | OK | All fixture runs write to a `FoundryLedger` inside a temporary directory. |
| "Evidence classes never mix; `historical_exposed_diagnostic` rows never pool with `historical_oos`/`live_confirmatory`" | OK | I re-ran the composite epoch: every row's evidence class is `historical_exposed_diagnostic`; the panel's immutability oracle passes. |
| "No exploratory read of a sealed shard; no Vault secret in repo/log/payload/screenshot" | OK | No accessor/corpus wiring in this diff; the payload contains only fixture ids and module digests. |
| "A real candidate outcome read before step 7 is a critical anti-goal violation" | OK | No real dataset is read anywhere in the diff; the store-scope guard confirms nothing in the protected store was touched. |
| "No Goal Mode workaround that edits/deletes/xfails a scientific guard merely to pass a journey" | OK | I grepped the diff for `xfail`, `pytest.skip`, `skip` markers and `noqa` — zero added lines. Both carried repairs make guards **stricter**, not looser. |
| "No claim that `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN` is OOS evidence" | OK | No such claim in the new UI text. |
| "No active post-`GOAL_ACHIEVED` science proposer" / "No `AUTO:journeys` self-extension" | OK | Untouched this iteration. |

Both repairs the last verdict asked for are genuinely closed and I read them: the record lint now
refuses a sibling that does not exist, sits in another family, or is the record itself
(`foundry_source_registry.py`, `lint_alternatives`, called before any spec is built); and the restart
check now also refuses a candidate whose manifest identity drifted on the crash path
(`foundry_runner.py:114-121`). The third carried repair is also closed: the browser report now cites
J-01's evidence as the replay results file, not the backend test run.

## Next-Step Recommendation

Move to the goal's own next required stage: J-06 "One complete real epoch is generated and committed
with zero Foundry outcome reads" — write the real source registry, run the fresh-context audit, and
generate the candidate manifest, with no candidate results read anywhere. Carry four small, named
repairs alongside it, all of which are already written down above:

1. Put the three missing fields on the Sources screen — operative formula refs, superseded fields,
   and alias/lineage — and show both records of the two-variant family. With J-06's committed audit
   report also in place, J-02 can then be photographed complete.
2. Show the kill-type mapping on the Hermetic Oracles screen (too-small sample versus other kills
   versus survivor) and the best-of-N disclosure, so J-05's own checklist can be seen rather than
   inferred. Also make the "outcome types present" line read each row's real result instead of a
   fixed label list.
3. Remove the temporary change to the frozen scoring function from the running backend
   (`foundry_hermetic_summary.py:75-82`, `:183-188`) — build that fixture from data that genuinely
   produces the low value, or compute the summary outside the serving process.
4. Optionally add the manifest/source/spec/configuration identities to the freeze-record view; the
   backend already pins them.

Run this at full depth, and note two operator decisions: every iteration so far has overrun the
one-hour budget (this one took over two hours), which is exactly why the deeper pipeline keeps being
downgraded — so either raise that budget or accept that only an escalation forces the deeper review.
The session cap of 60 iterations may also still want raising to 80.

## Halt Justification (if halting)

Not halting. This verdict escalates rather than stops: the loop continues, and the next iteration
must run the full pipeline.

Why escalate rather than simply continue. The iteration plan itself asked for the deeper review
pipeline; the engine's budget rule downgraded it to the lighter one, exactly as it did two iterations
ago (engine log 00:47:55: "spec asked FULL but the deterministic ladder demotes it to LEAN"). The
engine grants the deeper pipeline only after an escalation verdict, never on a recommendation. The
lighter pass then left real things uncaught: no independent auditor ran, and I found three separate
places where a screen claims a proof it does not actually show (J-02's three missing fields, J-05's
missing mapping, J-04's missing identities) plus a change to a frozen scoring function inside the
running backend that no lane flagged. The next stage is the one irreversible act of this whole era —
writing and freezing the real candidate manifest, after which the goal forbids inventing or inserting
any candidate. That step should not be reviewed by the lighter pipeline.
