# Iteration 7 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This iteration had one job and it did it. The structural fault that stopped the last iteration —
the same number being worked out in two different places — is now settled by the only legal route,
and I checked that route myself instead of trusting the reports. The change is tiny (two files) and
nothing an operator sees has changed. The seven finished journeys all still work. What went wrong
was not the product but the paperwork: the browser test lane never actually tested this iteration's
own target journey, while the quality report claimed all the required checks were complete, and the
same report denied changing a test script that it had in fact changed. The strict review lane caught
both and fixed them. That is why the next iteration must also run at the deeper review depth.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The Foundry opens as a new finite era | passing | passing (re-verified) | `reports/demo/goal-hypothesis-foundry-iter-7/step-02.png`; evaluator opened `.../step-03.png` and read "Current era: hypothesis-foundry (active)", "Backend suite: 3787 passed · 8 skipped · 0 failed", "Config fingerprint: 08e471b10130e1e2" and the 6-row Referee SHA-256 table; golden replay 6/6 PASS |
| J-02 Sources compile into auditable CandidateSpecs | passing | passing (re-verified) | `reports/demo/goal-hypothesis-foundry-iter-7/step-03.png` — evaluator read both "COMPILED WITH EXTRA A/B" blocks sharing hash `0892112d8ba6b1f7…` and "Hashes match — outcome-blind compilation proven."; golden replay 6/6 PASS |
| J-03 Interpretation preserves timing, direction, Scout decisions | passing | passing (re-verified) | `reports/demo/goal-hypothesis-foundry-iter-7/step-04.png`; evaluator opened `.../step-05.png` and read all five interpreter fixtures incl. "Foundry vs. direct-Scout screens equal: true" and `BLOCKED_UNSUPPORTED_RELATION`; golden replay 6/6 PASS. QA-lane PNG `UT-J-03-result.png` is a blank capture artifact — see Anti-goal / evidence notes |
| J-04 Foundry owns denominator, ledger, freeze barrier, lock | passing | passing (re-verified) | `reports/demo/goal-hypothesis-foundry-iter-7/step-05.png` + `.../step-06.png` — evaluator read the family-denominator table (1/5/24 not blocked, 25 blocked whole), "Late insertion refused: true", "First-read lock — hash drift refused: true", "Replay — idempotent: true"; golden replay 6/6 PASS |
| J-05 Hermetic known-null / planted-effect / leakage / honest-stop oracles | passing | passing (re-verified) | `reports/demo/goal-hypothesis-foundry-iter-7/step-06.png` + `.../step-07.png` — evaluator read all 11 outcome types, the full kill-type mapping, "Best-of-N disclosure: n_variants_tried=7", and five PASS rows; golden replay 6/6 PASS |
| J-06 One real epoch generated and committed, zero outcome reads | passing | passing (re-verified) | `reports/demo/goal-hypothesis-foundry-iter-7/step-07.png` + `reports/qa/goal-hypothesis-foundry-iter-7-evidence/UT-J-07-result.png` — evaluator read "REAL EPOCH — NOT A FIXTURE", `epoch:afd19e9c11a6534f`, `outcome_access_census: 0`, 11 of 11 source dispositions, "Compiled families (0)"; golden replay 6/6 PASS |
| J-07 Goal Mode exhausts the frozen real epoch (TARGET) | passing | passing (re-verified) | `reports/qa/goal-hypothesis-foundry-iter-7-evidence/UT-J-07-result.png` (non-blank, 147 KB, replay-lane) + `.../UT-J-07-runner-checkpoint-dom.txt` ("Checkpoint: 0 of 0 / Runner lock: Idle — lock free / Freeze integrity: green"); `demo_runner --mode verify --journeys J-07` → 1/1 PASS. Evaluator also curled the live endpoint: `frozen_ready_total: 0`, `exhaust_complete: true` |
| J-08 The operator sees the final Foundry truth | failing | failing (carried, NOT re-verified) | none this iteration — explicitly OUT OF SCOPE in `docs/phases/goal-hypothesis-foundry-iter-7.md`. Last evidence remains `reports/qa/goal-hypothesis-foundry-iter-3-evidence/J-01-verify.png` |

No journey changed status this iteration. No journey regressed. No goal text changed
(`goal_gate.py hash-journeys` returns the identical eight hashes already recorded), and no
`journeys-changed.md` exists. No `browser-infra.json`, no `DEFERRED-BUDGET` row, not maintenance
isolation.

## Anti-goal Check

Worked from `runs/goal-session-hypothesis-foundry/iter-7/scan-report.md` (CLEAN) plus
`.../iter-diff.md` (2 files, +60/−1). Ledger counts from
`anti_goal_disposition.py summary`: **total=4 · resolved=2 · unresolved_blocking=2 ·
unresolved_non_blocking=0 · unresolved_critical=0.**

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | scan-report CLEAN on added lines; diff adds no config, env, or key file |
| Paid / external SaaS dependency | OK | no manifest touched (`package.json`, `requirements*.txt`, `pyproject.toml` all absent from the 2-file diff) |
| License changes | OK | scan-report CLEAN; no LICENSE or license-field diff |
| Fabricated / substituted data | OK | the served value stays `0` read from the REAL frozen `epoch-manifest.json`; the new test loads that same real committed file. Fixture views are badged "HERMETIC FIXTURE — NOT THE REAL EPOCH" and real views "REAL EPOCH — NOT A FIXTURE" — evaluator saw both badges in the screenshots it opened |
| Rail 1 — No execution path | OK | no broker/order/trading code in the diff |
| Rail 2 — No profit claims / no advice | OK | no new displayed value at all ("Product surface delta: None") |
| Rail 3 — Frozen foundations stay frozen | OK | evaluator recomputed sha256 for all 59 `freeze-set.json` entries: **0 mismatched, 0 missing**. Iter-4's entry stays `resolved: true`, re-confirmed |
| Rail 4 — Hold-out promotion stays gated | OK | no champion/promotion/gate code in the diff |
| Rail 5 — No lookahead | OK | no timing or availability logic changed |
| Rail 6 — Single source of truth | **RESOLVED this iteration, with a permanent disclosed residual** | Evaluator's own repo-wide grep finds exactly ONE non-sealed computing site (`micro_routes.py:901-920`), called once (`:923`), consumed at `:963`; `foundry_runner.read_exhaust_progress` takes it as a parameter and never re-derives it. Test re-run by the evaluator: 21 passed. `iter-7/coherence.md` is COHERENCE-WARN and states "Iter-6's COHERENCE-FAIL on this row is retired". RESIDUAL, carried to the closing record: the sealed CLI `run_hypothesis_foundry_real_exhaust.py:225` still computes it independently and legally cannot be edited. The evaluator reproduced auditor finding B1 by running both formulas itself — real manifest `0/0`, `[{variant_count:25, variants:[]}]` → `25` vs `0`, `[{variants:[a,b]}]` → `KeyError` vs `2`. The formulas are NOT equivalent in general; what makes divergence impossible is that both operands are sha256-pinned, not the test |
| Rail 7 — Deterministic and seeded | OK | no randomness in the diff |
| Rail 8 — Read-only MCP | OK | no MCP surface touched |
| Rail 9 — Immutable registered data | OK | `reports/qa/goal-hypothesis-foundry-iter-7-store-scope-guard.md` CLEAN — 11395 protected files byte-identical before and after |
| Rail 10 — Persistence stays scoped | **OPEN, BLOCKING, OWNER-ONLY** (carried from iter-6, unchanged) | Auditor B4 re-read the path: a page-load GET still creates/truncates a lock file (`foundry_runner.py:197-201` via `:250-254`). Fix site is inside the sealed `foundry_runner.py`. Mitigation re-verified: the lock target is gitignored and outside every store-scope protected path |
| No second real generation epoch | **OPEN, BLOCKING, OWNER-ONLY** (carried from iter-5, unchanged) | Out of scope this iteration; the 2-file diff touches no epoch-generation code; `epoch:afd19e9c11a6534f` unchanged on the live endpoint |
| No science-affecting change after the first-read lock | OK | both edited files are provably NOT in the freeze set (evaluator checked the entry list); the replaced expression body is byte-identical and the served value is still `0` |
| No workaround that edits/deletes/xfails a scientific guard to pass a journey | OK — but a disclosure fault occurred | The one golden edit (`J-01.json` step-2 selector, text → testid) left its `expect` byte-identical; the auditor replayed BOTH versions green, so it was never needed to make J-01 pass. No test was deleted or xfailed; the suite gained one test. The **denial** of the edit in the browser-QA report was false and was retracted by the auditor correction |
| No browser proof based on fabricated fixture state | OK | fixture and real subviews carry distinct on-screen badges; evaluator confirmed visually |

Evidence-lane note (not an anti-goal violation): four QA-lane screenshots
(`UT-J-03/04/05/06-result.png`) are one byte-identical blank image, md5
`5167f380a66763a1219c996433733438`. Unlike iter-6, the browser-QA report **disclosed** this,
documented two recovery attempts, and grounded every PASS in live DOM text; the auditor reproduced
the blank and discarded rather than filed its own. Because non-blank evidence exists in the demo and
replay lanes, no `evidence_makeup` flag was set on any journey.

## Next-Step Recommendation

Build J-08 "The operator sees the final Foundry truth" — the last remaining journey and the era's
closing act. It needs the final on-screen summary, the honest "no survivor exists" statement, the
count of the 80 left-out datasets that today only the command prints, and the full battery of
protective checks. None of that work touches a sealed file, so it is legal to build. Run it at the
deeper review depth: in this session the strict review lane has found a real fault in every single
iteration it ran, including this one.

Carry three things into that iteration. First, replay the **target** journey, not only the older
ones — this iteration's browser lane skipped its own target and the quality report still said the
checklist was complete. Second, take pictures of the Foundry sections through the replay tool, never
through the browser tool's deep-scroll path, which reliably returns blank images. Third, do not
describe the number-agreement test as protection against future drift; it only reads "0 equals 0"
because the frozen list is empty, and what really prevents drift is the seal.

Three decisions belong to the owner and the era cannot be declared finished without them: accept or
reject the first real batch that was made and thrown away; accept that opening the page writes a
small lock file, whose only fix sits inside a sealed file; and — not blocking, but worth writing
down — accept the leftover duplicate calculation inside the sealed command as a permanently allowed
exception, so no future iteration keeps trying to "fully" fix something that cannot legally be
touched. **In one sentence: approve building the final Foundry summary screen next, at full review
depth, and make those three rulings so the era can be closed.**

## Halt Justification

Not halting. Verdict is ESCALATE, which continues the loop at the deeper review depth.
