# Iteration 2 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

Real progress. The first journey of this era now passes: the Desk page's Hypothesis Foundry panel
shows the true recorded era-open numbers instead of "not recorded yet", and I checked myself that
those numbers are real, not invented for the test rig. Five new back-end modules also landed and
work — I re-ran all 71 Foundry tests myself and they pass — so J-03 "Generic interpretation keeps
timing, population, direction and Scout decisions the same" and J-04 "The Foundry owns the
denominator, the record, the freeze and the lock" moved from not-working to partly-done. They cannot
be called done, because everything those two journeys ask a person to look at on screen was
deliberately left for a later iteration.

I am escalating for one reason only, and it is not a failure. The iteration's own plan said this
work needed the deeper review pipeline because it is the piece the whole era rests on, but the
engine's budget rule downgraded it to the lighter one (engine log, 21:47). So the heart of the
science shipped with a code review and a coherence check but no independent audit — and the code
review already found a real hole in the restart path. The next stage is the hermetic proof suite,
which is exactly the work that deserves the deeper pipeline.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The Foundry opens as a new finite era | partial | **passing** | `reports/qa/goal-hypothesis-foundry-iter-2-evidence/J-01-result.png` (results row UT-J-01 = PASS); values re-verified by the evaluator against `apps/backend/.data/foundry/era_open_baseline.json` and by recomputing all six `referee_*.py` SHA-256 hashes |
| J-02 Sources compile into auditable CandidateSpecs | partial | partial (unchanged) | no results row this iteration; back-end layer re-run green by the evaluator; prior screenshot `reports/qa/goal-hypothesis-foundry-iter-1-evidence/J-02-fail.png` |
| J-03 Generic interpretation preserves timing/direction/decisions | failing | **partial** | results row UT-J-03 = SKIP (no UI by design); substance re-verified by the evaluator: `apps/backend/tests/test_foundry_interpreter.py:83` (TC-4 whole-dict equivalence vs the direct Scout path), 71 Foundry tests exit 0; `reports/reviews/goal-hypothesis-foundry-iter-2-review.md` |
| J-04 Foundry owns denominator, ledger, freeze, integrity lock | failing | **partial** | results row UT-J-04 = SKIP (no UI by design); `apps/backend/app/research/foundry_family.py`, `foundry_freeze.py`, `foundry_ledger.py`, `foundry_runner.py` + their tests re-run by the evaluator; open defect at `foundry_runner.py:89` |
| J-05 Complete factory passes hermetic oracles | failing | failing (unchanged) | out of scope this iteration; `docs/phases/goal-hypothesis-foundry-iter-2.md` OUT OF SCOPE |
| J-06 One complete real epoch generated and committed | failing | failing (unchanged) | evaluator re-confirmed `docs/hypothesis-foundry/` absent (TC-20) |
| J-07 Goal Mode exhausts the frozen real epoch | failing | failing (unchanged) | illegal before the J-06 freeze commit; no CLI/manager wired |
| J-08 Operator sees the final Foundry truth; rails hold | failing | failing (unchanged) | rails half re-verified (suite 3825/8/0, fingerprint `08e471b10130e1e2`, store-scope guard CLEAN); truth half absent |

No journey is `unknown`; no journey regressed. Stable-journey spot-check: not applicable — zero
journeys held `passing`/`already_passing` before this iteration, and the Required-still-passing set
for this iteration was explicitly empty.

## Anti-goal Check

Source: `runs/goal-session-hypothesis-foundry/iter-2/scan-report.md` (CLEAN) +
`iter-2/iter-diff.md` (11 files, 0 deleted lines) + my own greps.
Disposition counts (`anti_goal_disposition.py summary`): total=0 · resolved=0 ·
unresolved_blocking=0 · unresolved_non_blocking=0 · unresolved_critical=0.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets/credentials | OK | scan-report CLEAN; no config/env file in the 11-file diff |
| Paid/external SaaS dependency | OK | scan-report CLEAN; no manifest touched (no `pyproject.toml`/`requirements*.txt`/`package.json` in the diff) |
| License changes | OK | scan-report CLEAN; no LICENSE file in the diff |
| Fabricated/substituted data | OK | The one risk point is the QA-rig fix. `qa_playbook_iter7_fixture_scoped_backend.sh` copies the genuine recorded artifact and falls back to an honest `null` if none exists; served values match `apps/backend/.data/foundry/era_open_baseline.json` byte-for-byte; all six Referee hashes recomputed and matched; real artifact mtime 21:13 predates the 21:47 iteration start |
| 1. No execution path, ever | OK | Five new research modules + tests + one QA shell script; no broker/order/execution code anywhere in the diff |
| 2. No profit claims / advice | OK | No UI copy shipped (zero `apps/frontend/**` files in the diff) |
| 3. Frozen foundations stay frozen | OK | `git diff <snapshot>..HEAD -- scout.py micro_features.py micro_routes.py` is empty; suite 3825/8/0 with no regressions |
| 4. Hold-out / confirmatory promotion gated | OK | No champion/promotion/graduation/Referee code touched; new modules import nothing from those areas |
| 5. No lookahead | OK | `foundry_interpreter.py` computes `outcome_start` by calling the existing `micro_features.resolve_outcome_start` helper (no second timing law); TC-6 asserts symmetric timing and both-cell exclusion of unresolved anchors |
| 6. Single source of truth | OK | `coherence.md` = COHERENCE-PASS, rows 3-8 verified; `foundry_family.py:19` imports `SCOUT_MAX_VARIANTS_PER_FAMILY` from `.scout`; no second decision function |
| 7. Deterministic and seeded | OK | Only seeded `Random(...)` appears, and only in test files; `recorded_at` timestamps are excluded from the ledger identity comparison (`foundry_ledger.py:150-156`), so wall clock never changes a result |
| 8. Read-only MCP | OK | No MCP file in the diff |
| 9. Immutable registered data | OK | Store-scope guard CLEAN — 11395 protected files byte-identical (`reports/qa/goal-hypothesis-foundry-iter-2-store-scope-guard.md`) |
| 10. Persistence stays scoped | OK | No route file touched; the new modules do no dataset, store or network I/O (import list is stdlib + sibling Foundry modules + `scout`/`micro_features`/`micro_chain_ledger`) |
| No second Foundry statistical decision rail | OK | `interpret_candidate` calls `scout.screen_candidate` directly; coherence audit found no second decision function |
| No Foundry trial in the Scout ledger | OK | grep: `scout_ledger` appears only in docstrings of `foundry_ledger.py` — never imported |
| No unsided candidate; no family splitting; no late insertion | OK | Sidedness is predeclared in `CandidateSpec` (TC-7); over-cap blocks the whole family (TC-9); late insertion always refuses (TC-10) |
| No second real generation epoch | OK | `ManifestDriftRefused` on changed inputs (TC-11); no real epoch exists at all |
| A real candidate outcome read before step 7 (critical) | OK | `docs/hypothesis-foundry/` absent; every fixture is in-test Python data; no dataset/network access in any new module |
| No guard edited/deleted/xfailed to pass a journey | OK | The diff has **zero** deleted lines and adds no `skip`/`xfail`/`noqa` marker |
| No browser proof on fabricated fixture state | OK | See "Fabricated/substituted data" above — the rig serves the real recorded artifact |
| No weakening of `host-guard.env` | OK | Not in the diff file list |

**Result: no anti-goal violation, critical or minor.**

Open defects that are NOT anti-goal violations (all developer-disclosed and evaluator-confirmed):
`foundry_runner.py:89` already-terminal fast path skips the identity re-check; the freeze-set
scanner only follows same-directory imports; resume verifies only the economic-floor identity;
`SourceRecord` still lacks `alternatives`/`source_hash`; `BLOCKED_UNIT_CONTRACT` still unreachable;
no runner CLI yet.

## Next-Step Recommendation

Run the next iteration at **full depth** (this is the point of the ESCALATE verdict — a depth
*recommendation* alone was already overridden by the budget rule last time).

Target J-05 "The complete factory passes hermetic known-null, planted-effect, leakage and
honest-stop oracles" — Binding Execution Order step 4, the only legal next stage. That means one
mixed practice run containing every outcome type at once (compiled, blocked, too-few-samples, null,
wrong-direction, the three kill types, and a survivor), plus an all-blocked run and an all-killed
run, plus the protected-data trip tests that must fail shut.

Two small repairs should ride along in the same iteration, before any real work depends on them:
fix the restart path so a resumed candidate whose inputs have changed is refused instead of quietly
handed the old stored result (`apps/backend/app/research/foundry_runner.py:89`), and add the two
missing record fields `alternatives` and `source_hash` that the written method document already
promises.

In one sentence: approve one more iteration, run it with the deeper review pipeline, and have it
build the hermetic proof suite while fixing the restart-check hole and the two missing record
fields.
