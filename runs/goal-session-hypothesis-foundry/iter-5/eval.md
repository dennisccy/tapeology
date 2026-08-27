# Iteration 5 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The Foundry now has its one real, frozen epoch, and I checked the artifacts myself rather than
trusting the reports. Three journeys turned green: J-06 "One complete real epoch is generated and
committed", J-02 "Sources compile into auditable CandidateSpecs", and J-05 "The complete factory
passes hermetic oracles". The real epoch honestly produced **zero** candidates — all eleven ratified
ideas were blocked, excluded, or renamed under the owner's own "block unresolved science" rule —
which the goal itself lists as a valid successful ending, not a failure. I am escalating because the
next stage writes the one-way lock that ends this era's freedom to change any science file, and
three real integrity problems with that lock are still open.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The Foundry opens as a new finite era | passing | passing (replayed) | reports/qa/goal-hypothesis-foundry-iter-5-evidence/J-01-verify.png (UT-J-01) |
| J-02 Sources compile into auditable CandidateSpecs | partial | **passing** | reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-03-result.png (UT-03) |
| J-03 Generic interpretation preserves Scout decisions | passing | passing (replayed, spot-checked) | reports/qa/goal-hypothesis-foundry-iter-5-evidence/J-03-verify.png (UT-J-03) |
| J-04 Foundry owns denominator, ledger, freeze barrier, lock | passing | passing (replayed, spot-checked) | reports/qa/goal-hypothesis-foundry-iter-5-evidence/J-04-verify.png (UT-J-04) |
| J-05 The complete factory passes hermetic oracles | partial | **passing** | reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-04-result.png (UT-04) |
| J-06 One complete real epoch, zero outcome reads | failing | **passing** | reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-02-result.png (UT-02); commit `dff64eaa`; docs/hypothesis-foundry/*.json; reports/hypothesis-foundry/source-registry-audit.md |
| J-07 Goal Mode exhausts the frozen real epoch | failing | failing (not targeted; now unblocked) | no results row — the exhaust runner does not exist yet |
| J-08 The operator sees the final Foundry truth | failing | failing (not targeted; depends on J-07) | no results row |

What I personally opened or re-ran, rather than accepting from a report:

- **J-06's screen**: read the emerald "REAL EPOCH — NOT A FIXTURE" banner, "Status: Committed —
  Git-visible pre-outcome barrier crossed", `epoch_id: epoch:afd19e9c11a6534f`, six non-empty
  identity hashes, `outcome_access_census: 0`, exactly eleven source rows, and
  "Compiled families (0) — Zero compiled candidates this epoch" off the screenshot.
- **J-06's artifacts**: `git show --name-only dff64eaa` lists exactly the five tracked files in one
  commit; `git merge-base --is-ancestor dff64eaa HEAD` exits 0; `apps/backend/.data/foundry/` holds
  only `era_open_baseline.json`, so no candidate result was ever recorded; no exhaust-runner
  entrypoint exists anywhere; the generator's outcome tripwire is a real `sys.settrace` call tracer
  over seventeen forbidden modules, not an import check.
- **J-06's honesty**: re-read Card 9.3 and Card 9.1 in `docs/research-directions.md` against their
  registry excerpts — the quoted text is genuine, transcribed into plain ASCII.
- **J-02's screen**: eight fixture rows including both `fixture-variant-a` and `fixture-variant-b`
  naming each other; every row showing operative formula refs, superseded fields and
  aliases/lineage ids; the outcome-blind pair (effect 12 / p 0.5 / n 40 versus effect 99 / p 0.0001
  / n 500) producing one identical hash with "Hashes match"; the committed audit-report reference.
- **J-05's screen**: all seven kill-type rows, the best-of-N line
  (`n_variants_tried=7 · threshold_bps=0.1569542572940126`), and five named oracles all PASS.
- **Tests**: re-ran `tests/test_foundry_real_epoch_artifacts.py` (14 passed) and
  `test_foundry_hermetic_epoch.py` + `test_foundry_route_hermetic_views.py` +
  `test_foundry_route.py` (43 passed).

## Anti-goal Check

Deterministic scan: `runs/goal-session-hypothesis-foundry/iter-5/scan-report.md` — **CLEAN**, no
secret, dependency or license findings on added lines (2 untracked files scanned).
Coherence: `iter-5/coherence.md` — **COHERENCE-PASS**.
Disposition counts (`anti_goal_disposition.py summary`): **total=2 / resolved=1 /
unresolved_blocking=1 / unresolved_non_blocking=0 / unresolved_critical=0**.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | scan-report CLEAN; no config/env file in the 14-file diff (only .py/.json/.tsx/.ts/.md) |
| Paid / external SaaS | OK | scan-report CLEAN; no package.json / requirements / pyproject change in the diff file list |
| License changes | OK | scan-report CLEAN; no LICENSE or license-field diff |
| Fabricated / substituted data | OK | Registry excerpts independently traced: I re-read Card 9.3 (research-directions.md:1196-1200) and Card 9.1 (:1157-1160) and the committed excerpts are faithful ASCII transcriptions of the real text. Auditor B3 confirms the same for all 11, with two named notational transliterations. No data invented. |
| Fixture vs real views visibly distinguished | OK | Verified on screenshots: amber "HERMETIC FIXTURE — NOT THE REAL EPOCH" on all four fixture subsections, emerald "REAL EPOCH — NOT A FIXTURE" on Epoch/Manifest |
| "Frozen foundations stay frozen" | **RESOLVED** | The iter-4 MINOR is genuinely closed: `grep -rn "scout\._two_sided_p\s*="` over `apps/backend` returns one hit, a docstring in the guard test; zero assignments outside `tests/`. The fragility case now reaches `killed_fragile` under the real, unmodified function — I read `fragile → EVALUATED_KILLED` and `fragility_killed` off UT-04-result.png. |
| "No second real generation epoch" | **VIOLATED — MINOR, unresolved, blocking** | Two real `epoch_id`s existed: the audit report's own header (`source-registry-audit.md:9-40`) records `ded18b8b…` regenerated to `ed40dbc2…` after the independent audit proved one `direction_derivation` value unsupported. Scored MINOR because nothing was committed under the discarded hash (one commit, `dff64eaa`), no trial ledger and no candidate outcome ever existed, §7.3 expressly allows repair before the first outcome read, and the whole sequence is disclosed in the committed report. Recorded, not dismissed in prose. Auditor B5 asks for owner ratification. |
| "No real candidate outcome read before step 7" (critical class) | OK | `outcome_access_census = 0` in the artifact and on the served view; no Foundry trial ledger exists; no exhaust-runner entrypoint exists; a test asserts no outcome-shaped key appears in the manifest |
| "No runtime LLM interpretation in the real manifest-generation command" | OK | `generate_hypothesis_foundry_real_epoch.py` has no LLM/network import; its only subprocess calls are read-only `git rev-parse` / `git cat-file -e` |
| "No source record / threshold / direction / family chosen because of effect, p-value, sample density or prior outcome" | OK | Census 0 via dynamic call tracing over 17 forbidden modules; the fixture screen proves compilation is outcome-blind (identical hash under wildly different injected statistics) |
| "No candidate invented after the real manifest freezes" / "no late variant insertion" / "no family splitting to evade the 24-variant cap" | OK | Zero compiled candidates and zero families; nothing added after `dff64eaa` |
| "Single source of truth" | OK | `source_registry_hash` / `source_registry_status` now read from the same `_EPOCH_MANIFEST_VIEW`; coherence audit confirms one computation path and a dedicated test |
| "GET never computes / page loads never record" | OK | `_EPOCH_MANIFEST_VIEW` is built once at module import; `get_foundry()` returns frozen dicts and calls no compiler/runner function |
| "No Goal Mode workaround that edits/deletes/xfails a scientific guard" | OK | The one changed assertion (fixture count 7→8) grew a fixture set rather than weakening a check, was directed by two consecutive evaluator verdicts, and is disclosed in the assumption ledger; skip count unchanged at 8; suite grew 3879→3901 with 0 failures |

## Next-Step Recommendation

Build J-07 "Goal Mode exhausts the frozen real epoch" next, at full depth. Because the frozen epoch
contains zero candidates, there is no result to read at all — the real work is the restartable
single-flight runner, the epoch-opening record, the proof that an empty ready-list still reaches a
valid finished state, and the count of protected, Vault and Referee actions that must all be zero.

Carry these repairs in the same iteration, because after the lock is written no science file may
change again:

1. The frozen file list (`docs/hypothesis-foundry/freeze-set.json`) records full machine-specific
   folder paths, so the safety check only works in this one copy of the project. Store paths
   relative to the project root instead.
2. The commit the freeze record points at does not actually contain the frozen code, because those
   edits were still unsaved when the freeze was taken. Commit this iteration's code changes and
   re-point the record.
3. The frozen file list is missing four files the rules require by name (the three tracked Foundry
   JSON files and the generation script), and the freeze record is missing the era-open
   evidence-class contract. I confirmed that missing field myself.
4. Make the generation command refuse when its saved state file has simply been deleted, so "only
   one real epoch" is enforced by the machine and not by a file's presence.

Two decisions belong to the operator and should be made before the lock is written:

- **Ratify (or reject) the discarded first epoch.** A first real epoch was created and thrown away
  before anything was committed, after an independent review proved one field wrong. Nothing was
  published and no result was ever read, but the era's rule says only one real epoch may exist.
- **Approve amending the already-committed frozen files** for repairs 1-3 above. They are frozen
  artefacts, so changing them is the operator's call, not an agent's.

One process point, now in its sixth iteration: every iteration has overrun its one-hour budget (this
one took just over three hours). That is why a plain "continue" would have forced the next iteration
into the lighter pipeline, and it is the main reason this verdict is an escalation.

In one sentence: next, build and run the empty-epoch exhaust pass at full depth, and please decide
whether the discarded first epoch is accepted and whether the frozen files may be corrected first.
