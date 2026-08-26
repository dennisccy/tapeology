# Iteration 3 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The factory test bench that this iteration was asked to build is real, and I checked it myself
instead of trusting the reports. I ran the new tests: one practice run puts every possible outcome
side by side — a blocked source, an excluded one, a renamed one, and seven live candidates that end
as too-small, no-effect, wrong-direction, one-symbol-driven, not-worth-the-cost, fragile, and one
survivor — and each lands on exactly the right ending, in the right order, with the same
seven-candidate denominator written on every row. The all-blocked run, the all-killed run, the
two-survivor run (neither survivor ranked above the other), the crash-and-restart run and the
"protected data was touched" run all pass. The deep reviewer found two real holes in the proof —
the practice run never once fed a candidate built by the real compiler into the real runner, and
the all-blocked case never actually ran the runner — and fixed both during the review; I confirmed
those two new checks exist and pass. Two small carried repairs also landed. Nothing here is visible
to the operator yet, so no journey could be photographed, and none moved to done.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The Foundry opens as a new finite era | passing | passing | `reports/phase-goal-hypothesis-foundry-iter-3-ui-test-results.md` row UT-J-01 (PASS) + `reports/qa/goal-hypothesis-foundry-iter-3-evidence/J-01-verify.png` — evaluator opened the image: `/desk` with the HYPOTHESIS FOUNDRY panel rendered |
| J-02 Sources compile into auditable CandidateSpecs | partial | partial (blocker resolved) | No browser row and no screenshot — the Sources/Compiler view still does not exist. Backend re-run by the evaluator: `pytest tests/test_foundry_source_registry.py tests/test_foundry_compiler.py` exit 0, incl. TC-10 `source_hash` and TC-11 `alternatives` (`foundry_source_registry.py:189-199`) |
| J-03 Generic interpretation preserves Scout decisions | partial | partial (carried, not re-targeted) | Not targeted this iteration; no new evidence. Carried from `reports/reviews/goal-hypothesis-foundry-iter-2-review.md`. Interpreter module untouched (`git status` clean for `foundry_interpreter.py`) |
| J-04 Foundry owns denominator, ledger, freeze barrier, lock | partial | partial (blocker resolved) | No browser row and no screenshot — the Freeze/Integrity view still does not exist. Evaluator re-ran `tests/test_foundry_runner.py` exit 0 incl. TC-9; fix read at `apps/backend/app/research/foundry_runner.py:94-110` |
| J-05 The complete factory passes hermetic oracles | failing | **partial** | No browser row and no screenshot (no UI shipped by design). Evaluator ran `pytest tests/test_foundry_hermetic_epoch.py` → **10 passed**; read TC-1/TC-2 (`tests/test_foundry_hermetic_epoch.py:223-292`) and TC-8 (`:652-679`) and confirmed they drive the real production modules with exact-value assertions. Audit `docs/handoffs/goal-hypothesis-foundry-iter-3-audit.md` = PASS_WITH_GAPS, findings B1/B2 fixed in-audit (`:343-386`, `:405-432`) |
| J-06 One complete real epoch generated and committed | failing | failing | `docs/hypothesis-foundry/` does not exist (evaluator ran `ls`: "No such file or directory"). Forbidden before steps 4-5 are proven |
| J-07 Goal Mode exhausts the frozen real epoch | failing | failing | No real committed epoch exists, no CLI entry point, no first-read lock. Illegal until the J-06 freeze commit is an ancestor of HEAD |
| J-08 Operator sees the final Foundry truth; rails hold | failing | failing | Rails half re-verified: suite 3842 passed / 8 skipped / 0 failed (`reports/qa/goal-hypothesis-foundry-iter-3-test.log` final line), `tsc --noEmit` 0 errors, `config_fingerprint 08e471b10130e1e2` recomputed by the evaluator and unmoved, frozen rails untouched (`git status` empty for `scout.py`/`micro_features.py`/`referee_*.py`). Truth half absent — nothing to display |

Only J-05 changed status. There is no `journeys-changed.md` and no `browser-infra.json` for this
iteration, so no prior pass is void and nothing is owed by the browser infrastructure. No row in the
merged results table is `DEFERRED-BUDGET`; this iteration did not run under maintenance isolation.
Stable-journey spot-check: J-01 is the only `passing` journey, and it was re-verified mechanically by
the deterministic replay lane (1/1 PASS) — its screenshot agrees with its recorded status.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets/credentials committed | OK | `iter-3/scan-report.md`: CLEAN, no findings on added lines. Diff is 7 files: 2 backend modules, 4 test files, 1 spec doc — no config/env file added |
| Paid/external SaaS dependency | OK | `git status` shows no change to `package.json`, `package-lock.json`, `requirements*.txt`, `pyproject.toml`, `poetry.lock`. Scan-report reports no dependency findings |
| License change | OK | No `LICENSE`/license-field file in the diff; scan-report reports no license findings |
| Fabricated or substituted data | OK | Every fixture lives inside test files and is synthetic; no fixture file entered a production path. The real recorded artifact `apps/backend/.data/foundry/era_open_baseline.json` is untouched (mtime 21:13 = iter-1, before this run's 22:07 start) |
| "A real candidate outcome read before step 7 is a critical anti-goal violation" | OK | `docs/hypothesis-foundry/` does not exist at all (evaluator `ls`). No real-corpus or accessor wiring was added; TC-7 uses a hermetic generator stand-in |
| "No Foundry trial registered into the Scout ledger this era" | OK | Evaluator grep for `scout_ledger`/`ScoutLedger`/`record_screen` across the three files that could do it (`test_foundry_hermetic_epoch.py`, `foundry_runner.py`, `foundry_source_registry.py`): zero hits |
| "Evidence classes never mix; `historical_exposed_diagnostic` rows never pool with `historical_oos`/`live_confirmatory`" | OK | TC-8 (`tests/test_foundry_hermetic_epoch.py:677-679`) asserts the literal on every terminal row across all seven outcome types and asserts it is never one of the other two |
| "No second Foundry statistical decision rail" | OK | The suite calls the existing `scout.screen_candidate` through the existing interpreter; no new production module shipped (`iter-3/coherence.md` Data Contract table; reviewer PASS) |
| "No family-specific post-freeze extractor/evaluator path" | OK | The auditor-added seam test (`:343-386`) compiles real `SourceRecord`s with the generic `fc.compile_sources` and runs them through the generic `fr.run_family`; no per-candidate branch exists |
| "No source record/threshold/direction/family/CandidateSpec chosen because of effect, p-value, n, or prior Scout outcome" | OK | `alternatives` is a declared disclosure tuple; `source_hash` is `sha256(source_excerpt)`, `init=False` (`foundry_source_registry.py:196-199`) — neither takes any outcome input |
| "The accessor/evidence-control seam remains the only legal market-data door" | OK | TC-7 reuses the real `MicroAccessorSealedShardError`/`MicroAccessorOriginFenceError`; `test_tc7_no_new_accessor_abstraction_is_introduced` (`:639`) asserts the exception identities are the real ones. Auditor independently confirmed |
| "No Goal Mode workaround that edits/deletes/xfails a scientific guard merely to pass a journey" | OK — checked closely | Evaluator grep for added `xfail`/`skipif`/`pytest.skip`/`noqa` in the product diff: zero hits. `scout.py` is untouched in the working tree. The one `scout._two_sided_p` patch is inside a test's per-candidate `monkeypatch.context()` (`:257-259`), a verbatim reuse of `test_scout.py:424`'s own technique; the other six candidates screen under real p-values. Auditor verified this (finding T3) |
| "No lookahead" | OK | No timing law changed; `foundry_interpreter.py` and `micro_features.py` untouched this iteration |
| "Single source of truth" | OK | `iter-3/coherence.md`: all five touched Data Contract rows still served by their one registered module; `source_hash` is derived in exactly one place and deliberately excluded from the registry-hash projection to avoid a second echo |
| "Deterministic and seeded" | OK | Every anchor generator takes an explicit seed (`_survive_anchors(41)`, `_null_anchors(42)`, …); the fragile fixture forces a fixed p-value, not a random one |
| "Frozen foundations stay frozen" | OK | Evaluator recomputed `config_fingerprint` = `08e471b10130e1e2`, unmoved. `git status` empty for `scout.py`, `micro_features.py`, `referee_*.py`, `apps/api/` |
| "No browser proof based on fabricated fixture state when a journey claims to show real final state" | OK | The only browser artifact is J-01's replay, which shows the genuine recorded era-open baseline (verified in iter-2 by recomputing all six Referee hashes). No journey claimed real final state this iteration |
| "No active post-`GOAL_ACHIEVED` science proposer" / "No `AUTO:journeys` self-extension" | OK | Not touched this iteration; no proposer or journeys block was added |
| "No execution path, ever" / "No profit claims and no advice" | OK | No brokerage, order, or execution code in the diff; no return claim is emitted anywhere in the new code |

Ledger counts from `scripts/automation/lib/anti_goal_disposition.py summary`:
**total=0 · resolved=0 · unresolved_blocking=0 · unresolved_non_blocking=0 · unresolved_critical=0.**
No anti-goal violation, minor or critical, was found this iteration or is carried from any prior one.

`iter-3/coherence.md` = **COHERENCE-PASS** (no blocking violations; no new page, route, or served value).

## Next-Step Recommendation

Build the one Foundry screen. Every remaining piece of machinery is now proven in the test bench, but
an operator still cannot see any of it, and that is the single reason J-02 "Sources compile into
auditable CandidateSpecs", J-03 "Generic interpretation preserves Scout decisions", J-04 "Foundry
owns the denominator, ledger, freeze barrier and lock" and J-05 "The complete factory passes hermetic
oracles" are all stuck at partly done — twenty-two on-screen checks between them, and zero of those
checks have ever been photographed. This is the next required stage in the goal's own order (step 5,
the read surface showing fixture states while the real epoch stays unopened), and it is the only work
that can turn four journeys green at once.

Carry three small, already-written-down repairs in the same iteration so they are closed before real
sources get authored: (1) add a batch check that refuses a source record naming a sibling that does
not exist or is not in its own family, so a typo cannot enter the frozen registry silently;
(2) extend the restart check to the crash path as well, not only the already-finished path;
(3) correct the QA report's habit of claiming the J-01 screen check was covered by the backend test
run — it was not; it is covered by the browser replay, and the report should cite that artifact.

One thing for the operator to decide, unchanged for four iterations: the session is capped at 60
iterations and the goal document asks for 80. Run the next iteration at full depth, since it ships
the first real Foundry screen and needs the browser and design review lanes.
