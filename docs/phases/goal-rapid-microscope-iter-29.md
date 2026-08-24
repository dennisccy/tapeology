# Goal Iteration 29 — Re-verify J-07 "Graduation" and clear the mechanical DEFERRED-BUDGET block

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 29
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — this iteration's regression/audit scope spans ≥3 recently-changed
  test/cache modules (`test_micro_snapshots.py`, `test_micro_readiness.py`, `test_micro_join.py`,
  `conftest.py`, `tests/real_corpus_cache.py`, `test_real_corpus_cache_scope.py`) whose interaction
  with the live backend's own cache-path resolution is not covered by any single journey's own
  tests; the evaluator's binding recommendation for this iteration is independently `full`.
- **Frontend Present:** no
- **Target journeys:** J-07
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-08, J-09, J-10
- **Anti-goal reminders:**
  - Frozen foundations — the `v1` strategy, the `default` profile, the tape engine's five states
    and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
    surface's behaviour stay byte-identical. New work is additive and versioned beside them,
    never a mutation of them. *(critical)*
  - Single source of truth — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - Immutable data — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*
  - Deterministic and seeded — every random draw uses a recorded named seed via per-row streams;
    identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in
    any research artifact. *(critical)*
  - Referee modules are byte-untouched this era — `referee_handoff_ready` never implies
    current-Referee registrability of a flow predicate; that awaits a future named revision of
    the referee spec. *(critical)*
  - **Host-guard caps are law.** This host (GEEKOM A7 Max mini-PC) hard-reset five times between
    2026-07-20 and 2026-07-28 under unconfined goal-mode load — instant power/VRM transient
    trips with nothing in the journal; resets #3–#5 struck while tapeology's goal mode ran
    UNGUARDED beside trendora's. When `project-extensions/host-guard/host-guard.env` declares
    ceilings (CPU mask `4-7,12-15` — the complement of trendora's — plus BLAS thread caps and
    memory/task bounds), every heavy path respects them: headless engine runs self-wrap under
    the mask, and interactive pump sessions are auto-confined in place by the engine
    (`host-guard-adopt.sh`; `scripts/automation/host-guard-exec.sh claude` is the optional
    from-birth wrapper) — the engine pauses `AWAITING_HOST_GUARD` (resumable) only when
    confinement cannot be established. Never disable, widen, or bypass these caps to make a run
    faster or a pause go away; widening the mask follows the verification ladder in
    `trendora/project-extensions/host-guard/README.md`. *(critical)*

## GOAL

Formally re-verify J-07 "Graduation" through its own backend fixture suite inside this iteration's
dispatched pipeline (not an out-of-band manual read), so its stamp moves off the stale iter-24
carry-forward and the DEFERRED-BUDGET cell that mechanically bars `GOAL_ACHIEVED` clears — while
confirming, independently rather than by inheritance, that the owner's direct maintenance commits
since iteration 28 introduced zero production-code diff.

## BACKGROUND

Iteration 28 ended `STALLED`: all ten journeys were green, but J-07 was shed for time
(`DEFERRED-BUDGET`) and the evaluator's own next-step named exactly two remaining machine-buildable
jobs — "give the third slow test file the same one-line fix that worked twice today, and re-check
J-07 so the finishing gate stops blocking." Between iteration 28 and this dispatch, the owner ruled
on that recommendation directly and landed two commits *outside* the goal loop: `f08f46ee`
("tasks A1 + A2" — `test_micro_snapshots.py` now uses the durable `index_db_path=` index, 27:31.86
→ 2.55s, and all three real-corpus test files now use dedicated test-owned caches under
`.data/test-cache/` instead of the operator's live `.data/dataset_index.db` /
`.data/micro_readiness_cache.db`, closing iter-28 audit finding B1) and `f2b292f4` ("task B" — the
`closure_gate.py` `backend-only` substring false-positive). The owner's own verification report
(`reports/qa/goal-rapid-microscope-maint-2026-08-24-verification.md`) measured the full backend
suite at 3,491 passed / 8 skipped / 0 failed in 6:34 (was 33:43) with the live cache DBs
byte-identical before/after and the referee family 6/6 byte-identical.

That leaves exactly one machine-buildable item standing between this era and a clean run: J-07 has
never been re-checked *by the pipeline itself* since iteration 24. Per this era's own iter-25
lesson ("re-check the GROUNDS of every carried-forward open item, not just whether the code
changed") and iter-28's own evaluator discipline ("I ran J-07's own fixture suite myself... but
deliberately did not use that to move its stamp, because the lane did not check it"), an owner's
manual maintenance verification does not substitute for a dispatched developer/reviewer/QA lane
actually running the suite this round. J-07 also has no screen and (per an earlier binding ruling)
no stored golden script — it is a backend-only journey whose acceptance mechanism is its own
fixture suite, `apps/backend/tests/test_micro_graduation.py`. Per the iter-28 (second) lesson ("any
journey that has no stored golden and rides the Required-still-passing list — give it a golden, or
route it to the lane that can actually run it, before a round that is likely to overrun"), this
iteration routes J-07 to the one lane that can run it: the dispatched developer/reviewer pipeline's
own test execution, now finishable well inside budget thanks to the owner's fix.

Everything else that was open at iteration 28 stays exactly where it was: three of the four
dev-chain framework findings (a QA lane certifying unchecked work; a closure gate that never reads
the browser lane's verdict; a replay harness that cannot run a round's own target goldens) live in
`agents/**`/`scripts/automation/**`, which `.claude/maintenance-protocol.md` §1 puts outside a
product round's authority — they are not re-planned here, matching rule 6 (do not re-plan a
human-owned blocker). The two owner-deferred items (chain-ledger identity, iter-13; the sealed
judge's money floor, iter-18) stay deferred. No new journey, no new UI surface, and no production
code change is in scope: this is a targeted re-verification round following external maintenance,
matching the priority rubric's "smallest spec wins ties" (rule 4) and the injunction against
manufacturing new scope when the evaluator has already named the concrete remaining work (the same
reading this session's iter-27 assumption-ledger entry established for an analogous situation).

Depth is `full` because the dispatch header states it is binding for this iteration, and
substantively this round's regression surface (re-deriving that two out-of-band commits truly
touched zero production files, plus a full-suite and full-replay sweep across every journey) spans
more than one test/cache module and benefits from the independent audit lane that has caught a
finding in this era 13+ times.

## IN SCOPE

### Backend
- [ ] Execute `apps/backend/tests/test_micro_graduation.py` (J-07's own acceptance suite) via the
      dispatched pipeline; record pass count and wall-clock time.
- [ ] Independently re-derive (not inherit) that commits `f08f46ee` and `f2b292f4` changed zero
      files under `apps/backend/app/` and `apps/frontend/` relative to iteration 28's snapshot SHA
      (`d397ad4bdfcd3850870dfbb1ab7ad7a0c48273c6`).
- [ ] Run the full backend suite (`pytest apps/backend/tests/`) end to end once; record the exit
      code, pass/skip/fail counts, and total wall-clock time.
- [ ] Confirm the two operator-live cache files (`apps/backend/.data/dataset_index.db`,
      `apps/backend/.data/micro_readiness_cache.db`) are byte-unchanged (mtime and checksum) after
      the full suite run, exercising the A2 store-scope guard (`test_real_corpus_cache_scope.py`)
      as a live check rather than trusting its own passing status alone.
- [ ] Re-hash the six `referee_*.py` files against the era's iteration-0 frozen sha256 listing.
- [ ] No production code change anticipated in `apps/backend/app/**`.

### Frontend
- None. J-07 has no screen; no frontend file is expected to change.

### New user-facing capability
None — this iteration re-verifies existing, already-shipped behavior.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None. The product surface is unchanged; only the pipeline's own verification record for J-07
advances from a stale iteration-24 stamp to a fresh iteration-29 one.

### Blueprint conformance
No new surfaces. J-07's canonical home in `blueprint.md`'s Information Architecture table is
unchanged: "keyless/automated; states surface via the Scout Ledger / Walk-Forward / Vault rows
they attach to" (Desk). A housekeeping-only note has been appended to `blueprint.md` documenting
the owner's out-of-band test-cache fix, matching the file's own iter-19/24/25/27/28 harness-only
precedent.

### Data-contract additions
None. No new displayed value, computing module, or serving endpoint. The Graduation row (owner
`micro_graduation.py` / `micro_sealed_evaluation.py`, endpoint `GET /research/desk/micro/graduation`)
is unchanged and re-registered nowhere new.

## OUT OF SCOPE

- The three remaining dev-chain framework findings (QA lane certifying unchecked work; closure
  gate never reading the browser lane's verdict; replay harness unable to run a round's own target
  goldens) — these live in `agents/**`/`scripts/automation/**`, outside a product round's authority
  per `.claude/maintenance-protocol.md` §1; they stay an owner decision, not re-planned here.
- The two owner-deferred items: the chain-ledger identity question (iter-13) and the sealed
  judge's money floor (iter-18).
- Any change to `micro_graduation.py`, `micro_sealed_evaluation.py`, `micro_accessor.py`, or any
  other `research/*` production module.
- Recording more real tape, revealing or assigning any sealed shard, or running the three pilot
  studies against the real recorded corpus.
- Any new `Config` field or fingerprint movement.
- Any UI/frontend change.

## DEFINITION OF DONE

- [ ] J-07 passes: `test_micro_graduation.py` executed and recorded green by this iteration's
      dispatched pipeline (not an out-of-band manual run), replacing its iteration-24 stamp.
- [ ] Required-still-passing journeys (J-01, J-02, J-03, J-04, J-05, J-06, J-08, J-09, J-10) remain
      green via deterministic replay of their stored goldens (mechanically verified).
- [ ] No anti-goal violation introduced — zero production/frontend diff since iteration 28
      independently confirmed; referee family stays byte-identical; live cache files stay
      byte-unchanged.
- [ ] Unit tests pass; no regressions — full backend suite exits 0 with 0 failures, well inside
      the iteration's time budget.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-29-dev.md`.

## TESTING REQUIREMENTS

- Browser: none required for the target journey (J-07 has no screen, per an earlier binding
  ruling). Required-still-passing journeys J-01, J-08, J-10 (and any others without a durable
  golden) route through deterministic replay first, live browser-qa fallback only on a replay
  miss.
- Unit/integration: `apps/backend/tests/test_micro_graduation.py` (J-07's acceptance suite) plus
  the full `apps/backend/tests/` suite.
- Error cases: none new — no new input surface this iteration. The store-scope guard
  (`test_real_corpus_cache_scope.py`) rejecting any test construction against the live cache path
  stays exercised as part of TC-7 below.

- TC-1: given `apps/backend/tests/test_micro_graduation.py` is byte-unchanged since iteration 17
  (per `git diff <iteration-17-commit>..HEAD -- apps/backend/app/research/micro_graduation.py
  apps/backend/app/research/micro_sealed_evaluation.py apps/backend/app/research/micro_accessor.py`
  showing no hunks), when this iteration's pipeline runs
  `pytest apps/backend/tests/test_micro_graduation.py -v`, then all tests report PASS (0 failed)
  and the pass count plus wall-clock time are written into
  `docs/handoffs/goal-rapid-microscope-iter-29-dev.md`.
- TC-2: given `runs/goal-session-rapid-microscope/state/journey-history.json`'s J-07 row currently
  carries `last_passing=goal-rapid-microscope-iter-24` and `iteration-state.md`'s DEFERRED-BUDGET
  note, when TC-1's suite run completes green this iteration, then the evaluator records J-07 with
  a fresh `last_passing=goal-rapid-microscope-iter-29` stamp and the DEFERRED-BUDGET flag is
  cleared.
- TC-3: given commits `f08f46ee` and `f2b292f4` (dated 2026-08-24, both prior to this iteration's
  dispatch), when this iteration's pipeline runs
  `git diff d397ad4bdfcd3850870dfbb1ab7ad7a0c48273c6..HEAD -- apps/backend/app apps/frontend`,
  then the output is empty (zero production/frontend code changed since iteration 28).
- TC-4: given the owner's post-fix verification measured 3,491 passed / 8 skipped / 0 failed in
  6:34, when this iteration's pipeline runs `pytest apps/backend/tests/` end to end, then it exits
  0, reports 0 failed with a pass count >= 3,491, and completes well inside the iteration's time
  budget.
- TC-5: given the 9 journeys with a stored golden on file
  (`runs/goal-session-rapid-microscope/journey-scripts/J-01.json` through `J-10.json` excluding
  J-07), when the deterministic replay harness runs `demo_runner.py --mode verify` against each,
  then every one reports PASS with zero diff from its committed script.
- TC-6: given the six `referee_*.py` files' iteration-0 frozen sha256 listing, when this iteration
  re-hashes them, then every hash matches byte-identical, confirming Foundation invariant 2 held
  through the owner's out-of-band commits.
- TC-7: given `apps/backend/.data/dataset_index.db` and `apps/backend/.data/micro_readiness_cache.db`
  have their mtime and sha256 recorded before this iteration's full-suite run, when the full
  backend suite (including the three real-corpus test files) completes, then those two files'
  mtime and sha256 are unchanged, proving no test wrote to the live cache path.

## NOTES

- Lesson applied (iter-25): "re-check the GROUNDS of every carried-forward open item, not just
  whether the code changed" — the developer/reviewer must independently run TC-3, not cite the
  owner's own verification report as sufficient on its own.
- Lesson applied (iter-28, second): "any journey that has no stored golden and rides the
  Required-still-passing list — give it a golden, or route it to the lane that can actually run
  it" — J-07 cannot get a browser golden (no screen, earlier binding ruling), so this iteration
  routes it to the developer/reviewer/QA lane's own pytest execution instead.
- Lesson applied (iter-26, second): a durable test-owned cache is only as safe as its
  invalidation/scope guard's own assertions — TC-7 checks the *behavior* (live files unchanged),
  not merely that `test_real_corpus_cache_scope.py` itself reports green.
- If this iteration's TC-1/TC-2 land, the era's remaining certification blockers reduce entirely
  to items this iteration explicitly excludes (three dev-chain framework findings + two
  owner-deferred items) — all human-owned per iteration-state.md's own categorization. The
  evaluator, not this spec, decides what that means for the next verdict.
- Reference: owner's out-of-band maintenance verification —
  `reports/qa/goal-rapid-microscope-maint-2026-08-24-verification.md`.
