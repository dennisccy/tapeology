# Iteration 1 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The dead browser lane is alive again. The test copy of the site started cleanly on port 8301 for
the first time this session, and the very first two screenshots of the era were taken. The new
"Hypothesis Foundry" panel is on the Desk page and correctly names the old era as closed and this
era as active. But the panel's second half — the frozen opening numbers the whole era will be
checked against — shows "not recorded yet" in the test copy, so J-01 "The Foundry opens as a new
finite era" did not reach the finish line and stays partly done. J-02 "Sources compile into
auditable CandidateSpecs" also stays partly done: its behind-the-scenes rules are real and were
re-run independently, but none of its five checks can be seen on screen because that screen was
deliberately left for a later step.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The Foundry opens as a new finite era | partial | partial (steps 1-4 hold on screen/repo; step 5 not shown) | `reports/qa/goal-hypothesis-foundry-iter-1-evidence/J-01-fail.png`; results row UT-J-01 in `reports/phase-goal-hypothesis-foundry-iter-1-ui-test-results.md`; artifact `apps/backend/.data/foundry/era_open_baseline.json` (all six referee hashes recomputed by me and matched) |
| J-02 Sources compile into auditable CandidateSpecs | failing | partial (backend rules real and re-run; zero UI steps shown) | `reports/qa/goal-hypothesis-foundry-iter-1-evidence/J-02-fail.png`; results row UT-J-02; reviewer's own re-run of 40/40 Foundry tests in `reports/reviews/goal-hypothesis-foundry-iter-1-review.md` |
| J-03 Generic interpretation preserves Scout decisions | failing | failing (not targeted, unbuilt) | carried from iter-0; `foundry_interpreter.py` absent (iteration spec OUT OF SCOPE) |
| J-04 Foundry owns denominator, freeze barrier, lock | failing | failing (not targeted, unbuilt) | carried from iter-0; `docs/hypothesis-foundry/` still absent (re-checked) |
| J-05 Hermetic oracles | failing | failing (not targeted, unbuilt) | carried from iter-0; the four named oracles do not exist |
| J-06 One real epoch generated and committed | failing | failing (correctly not attempted) | carried from iter-0; no tracked epoch artifacts, forbidden before steps 2-5 |
| J-07 Deterministic exhaust of the frozen epoch | failing | failing (correctly not attempted) | carried from iter-0; no exhaust runner, no trial ledger |
| J-08 Operator sees final Foundry truth; rails hold | failing | failing (route + panel header now exist; the rest absent) | `reports/qa/goal-hypothesis-foundry-iter-1-evidence/J-01-fail.png`; `micro_routes.py` GET route in `runs/goal-session-hypothesis-foundry/iter-1/iter-diff.md:9-75` |

Notes on the two changed rows:

- **J-01 stays `partial`, not `passing`.** The screenshot is the ruling evidence and it shows
  "The era-open baseline has not been recorded yet." The recorded snapshot itself is genuine — I
  recomputed the SHA-256 of all six `referee_*.py` modules and every one matches the file, and its
  suite counts (3787/8/0) are exactly the iter-0 baseline (3747/8/0) plus the 40 new tests — but it
  lives under the operator's real data folder, and the scoped test rig derives its own folder from
  `TAPEOLOGY_DATASET_DIR`, so the rig sees nothing. No one has yet observed the populated panel in a
  browser, so the journey cannot be called passing.
- **J-01 was NOT scored `evidence_makeup`.** Closing this needs a launch/provisioning change by a
  developer, not just a re-photograph, so an evidence-only depth would not fix it.
- **J-02 moves `failing` → `partial`.** All five of its acceptance steps are on-screen inspections
  and none was demonstrated; the screenshot proves no such screen exists. The move to `partial`
  rests only on the backend rules the reviewer re-ran himself (40/40, TC-3..TC-12). This is an
  interpretation call and is logged in `state/assumptions.md`.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials committed | OK | `iter-1/scan-report.md` CLEAN over the product diff (8 untracked files scanned); no new env/config file in the 13-file diff list; no Vault value in payload or in either screenshot |
| Paid / external SaaS dependency | OK | No manifest touched (`package.json`, `requirements*.txt`, `pyproject.toml` absent from the diff file list); scan-report reports no dependency findings |
| License change | OK | scan-report reports no license findings; no LICENSE file in the diff |
| Fabricated / substituted data presented as real | OK | I recomputed all six `referee_*.py` SHA-256 hashes — identical to the recorded baseline; `config_fingerprint` `08e471b10130e1e2` is the pinned era value, unmoved; suite counts reconcile exactly with iter-0 + 40 new tests; `source_registry_hash` renders honestly as `not_yet_generated`, never a placeholder (visible in `J-01-fail.png`) |
| "No Goal Mode workaround that edits/deletes/xfails a scientific guard merely to pass a journey" | OK | `apps/backend/app/research/walkforward.py` is untouched in both `snapshot..HEAD` and the working tree; no `xfail`/`skip` marker appears anywhere in `iter-diff.md`; the fix declares `value_unit` on the fixture using the guard's own constant `wf.WF_OBSERVATION_UNIT` |
| "GET /research/desk/micro/foundry ... read-only, never compute/evaluate a candidate" | OK | Route body reads the persisted snapshot verbatim (`iter-diff.md:9-75`); TC-13/TC-15 verified by the reviewer; store-scope guard CLEAN — 11395 protected files byte-identical after the run (`reports/qa/goal-hypothesis-foundry-iter-1-store-scope-guard.md`) |
| "Single source of truth ... REST/UI/MCP never independently recompute" | OK | Coherence audit verified every displayed field has one canonical backend owner and the page renders verbatim (`iter-1/coherence.md`, COHERENCE-PASS) |
| "No source record, threshold, direction, family partition, or CandidateSpec chosen because of effect, p-value, sample density, or prior Scout outcome" | OK | Compiler never reads `SourceRecord.extra`; TC-11 re-run by the reviewer; no real source authored and no candidate outcome exists to read |
| "No runtime LLM interpretation in the real manifest-generation command" | OK | No manifest-generation command exists yet (J-06, forbidden at this step) |
| Binding Execution Order — no real epoch work before steps 2-5 | OK | `docs/hypothesis-foundry/` does not exist; no `source-registry.json` / `epoch-manifest.json` / `freeze-set.json` / `freeze-record.json` created |
| "No browser proof based on fabricated fixture state" | OK | The browser pass reported the honest empty state instead of dressing it up; no fixture baseline was planted to force a green shot |
| "Frozen foundations stay frozen" (v1 strategy, Scout/Referee behaviour, fingerprint) | OK | Diff touches only the new Foundry modules, an additive route, the QA seed script and frontend files; `referee_*`/`scout` untouched; fingerprint unmoved |
| "No weakening or bypass of host-guard.env" | OK | `project-extensions/` does not appear in the diff or in `git status` |
| No execution path / no profit claim / no annualized metric | OK | Nothing of that kind added; the panel is read-only text |

Ledger counts (`anti_goal_disposition.py summary`): **total=0, resolved=0, unresolved_blocking=0,
unresolved_non_blocking=0, unresolved_critical=0.**

Coherence: **COHERENCE-PASS** (`runs/goal-session-hypothesis-foundry/iter-1/coherence.md`) — no
structural veto.

Open defects that are NOT anti-goal violations (carried, must be fixed before J-06):
`SourceRecord` (`apps/backend/app/research/foundry_source_registry.py:159-188`) is missing the two
§1.4 fields `source_hash` and `alternatives`, although the new spec document says the list is
mirrored "verbatim" — I read the dataclass myself and confirmed the reviewer's finding. J-02 step 3
requires each record to show its `alternatives`, so J-02 can never pass while this is missing.
Two further declared gaps: `BLOCKED_UNIT_CONTRACT` cannot currently be derived from declared fields,
and `CandidateBlueprint` is still a hand-written input to the compiler.

## Next-Step Recommendation

1. Make the test copy of the site show the real recorded opening numbers, so J-01 "The Foundry
   opens as a new finite era" can finally be photographed complete. Point the test rig at the
   already-recorded snapshot (or copy that same real file into the rig before the browser pass).
   The rig must display the REAL recorded values — inventing numbers just to get a green screenshot
   is forbidden by the goal's own rules.
2. Add the two missing record fields (`alternatives` and a source hash) and make the spec document
   and the code agree, before any real source is written against this schema.
3. Then start the next required stage: the general reader that turns a frozen candidate description
   into the existing Scout decision without changing it, plus the family/denominator and freeze
   machinery — J-03 "Generic interpretation preserves timing, population symmetry, direction, and
   exact Scout decisions" and J-04 "Foundry owns the denominator, append-only state, freeze barrier,
   and integrity lock".

Run the next iteration at full depth, because that stage touches the frozen decision rail the whole
project rests on, and because this iteration already found three places where the written spec and
the code disagree — an auditor pass is worth its cost there. Approve continuing, and no operator
action is needed except the still-open choice about raising this session's iteration cap from 60 to
80.

## Halt Justification (if halting)

Not halting.
