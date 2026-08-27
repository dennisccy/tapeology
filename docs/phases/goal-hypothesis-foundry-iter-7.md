# Goal Iteration 7 — Consolidation: legally retire the frozen_ready_total duplicate computation

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** hypothesis-foundry
- **Iteration:** 7
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: consolidating a shared Data-Contract value's sole
  ownership across the serving route module, two non-sealed test files, and the freeze-set/
  store-scope invariant, driven by iter-6's own `COHERENCE-FAIL` veto on `GOAL_ACHIEVED`; matches
  the evaluator's binding `full` depth recommendation for this iteration.
- **Frontend Present:** no
- **Target journeys:** J-07
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06 (full regression — the
  fix touches `apps/backend/app/research/micro_routes.py`, the single shared serving module behind
  EVERY Foundry Data-Contract row, so all six must be reverified unaffected)
- **Anti-goal reminders** (verbatim from `docs/goal.md`):
  - "Single source of truth. Every shared scientific value has one canonical backend owner; REST/UI/MCP
    never independently recompute it."
  - "Persistence stays scoped. Fetching/recording/exposure is always an explicit operator act; page
    loads and Foundry reads never record market data. `GET /research/desk/micro/foundry` and every
    page-load GET are read-only and never compute/evaluate a candidate or trigger the exhaust runner."
  - "No second real generation epoch."
  - "No science-affecting code/spec/manifest change after the first-read lock."
  - "No Goal Mode workaround that edits/deletes/xfails a scientific guard merely to pass a journey."
  - "Anti-goal violations use the existing Goal Mode anti-goal violation state/disposition machinery;
    they are not dismissed in prose."
  - Binding Execution Order: "A real candidate outcome read before step 7 is a critical anti-goal
    violation. A science-affecting edit after step 8 begins is an integrity halt, not an iteration
    opportunity."

## GOAL

Retire iter-6's `COHERENCE-FAIL` (duplicate computation of `exhaust_progress.frozen_ready_total`)
through the one legal route available — consolidating ownership in a non-sealed module plus a
permanent equivalence-pinning test — without editing any of the 59 files the iter-6 first-read lock
has already sealed, and without changing anything an operator sees.

## BACKGROUND

Iter-6 wrote the era's second irreversible act (the §8.5 first-read lock) and J-07 passed, but the
same iteration's own new sealed CLI (`run_hypothesis_foundry_real_exhaust.py`) computed
`frozen_ready_total` independently of the already-canonical `micro_routes.py` path, keyed on a
different manifest field. `iter-6/coherence.md` returned `COHERENCE-FAIL` on this — a structural veto
that blocks any `GOAL_ACHIEVED` call regardless of journey status — and `iter-6/eval.md` confirms the
obvious fix (delete the duplicate line) is illegal: that file is now one of the 59 entries in
`docs/hypothesis-foundry/freeze-set.json`, sealed since `2026-08-27T06:55:51Z`, and editing it would
break the era's own seal. The same eval named a narrower legal route: put the one true owner in a
non-sealed file (`micro_routes.py` already is one) and add a test proving the sealed command's own
line always produces the identical number — "if that is judged not to satisfy the check, stop and ask
the owner rather than breaking the seal."

Per this agent's priority rubric, a `COHERENCE-FAIL` from the last iteration makes this iteration a
consolidation pass with no new scope — so, despite iter-6's own recommendation to also build J-08 in
the same iteration, J-08 is explicitly deferred to iter-8 (disclosed in `state/assumptions.md`,
iter-7). Two other blocking anti-goal findings carried from iter-5/iter-6 ("No second real generation
epoch"; the page-load GET writing a lock file) are OWNER-only per the evaluator's own words ("only the
owner can give it" / "its fix also lives in a sealed file") and stay out of this iteration's scope —
they remain open and undismissed in the anti-goal ledger.

**Lessons applied:** iter-6's own lesson — "run coherence + a duplicate-computation sweep over the
candidate freeze set BEFORE the lock is written, never in the same iteration as the lock... prefer
keeping new CLIs OUT of the freeze set unless the spec truly requires them" — names this iteration
directly ("Applies to: ... specifically iter-7's attempt to resolve this coherence FAIL"); this spec
follows its implied ordering by fixing the non-sealed side only and never touching the sealed CLI.
Iter-6's second lesson (a QA report cited one byte-identical blank image four times as "proof") means
J-07's re-verification this iteration must read screenshots from the `-evidence/` lane, not trust the
QA report's own citation list.

## IN SCOPE

### Backend

- [ ] `apps/backend/app/research/micro_routes.py` (non-sealed): extract the existing inline
      `_FOUNDRY_FROZEN_READY_TOTAL` computation (currently ~line 901) into one clearly named,
      documented function that becomes the SOLE canonical owner of
      `exhaust_progress.frozen_ready_total`. Served value must not change — still `0` against the
      real, frozen `docs/hypothesis-foundry/epoch-manifest.json` (`families: []`).
- [ ] Add one new equivalence-pinning test (extend `apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py`
      and/or `apps/backend/tests/test_foundry_route.py`, both non-sealed) that transcribes the exact
      formula already present at the sealed `apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py:225`
      (do NOT import/refactor that file — it is one of the 59 `freeze-set.json` entries) and asserts
      it equals the new canonical helper's output, both evaluated against the real committed
      `docs/hypothesis-foundry/epoch-manifest.json` — permanently pinning the two formulas'
      agreement for this frozen, unchangeable manifest.
- [ ] No edit to any of the 59 `docs/hypothesis-foundry/freeze-set.json` entries, `epoch_id`,
      `docs/hypothesis-foundry/source-registry.json`, or `docs/hypothesis-foundry/epoch-manifest.json`
      content.
- [ ] If a fresh coherence-auditor pass STILL reports DUPLICATE-COMPUTATION for this row after the
      above, do not force a PASS by editing a sealed file — record the finding plainly in the dev
      handoff and recommend an owner ruling (per iter-6 eval's own explicit fallback), leaving the
      coherence verdict as-is rather than papering over it.

### Frontend

None. The served value is unchanged (`0`); the existing `/desk` → Hypothesis Foundry →
Runner / Checkpoint subsection already renders `frozen_ready_total` verbatim and needs no edit.

### New user-facing capability

None — this is a backend integrity/consolidation repair behind an already-shipped surface.

### New information displayed

None.

### New user actions

None.

### UI surface changes

None.

### Product surface delta

None. Purely an internal single-source-of-truth repair behind the existing J-07 Runner/Checkpoint
subsection; no operator-visible change.

### Blueprint conformance

No new page/route. Lives entirely within the already-registered `/desk` → Hypothesis Foundry →
Runner / Checkpoint home (J-07, registered at baseline) and the already-registered `exhaust_progress`
Data-Contract row. `state/blueprint.md` updated this iteration: the row is split so
`exhaust_progress.frozen_ready_total` is called out with its corrected sole owner.

### Data-contract additions

None (no NEW displayed value). This iteration corrects the registered computing-module ownership of
an EXISTING Data-Contract value, `exhaust_progress.frozen_ready_total`: its sole canonical computing
module becomes one new named helper function in `apps/backend/app/research/micro_routes.py`
(non-sealed), still served by the same single endpoint `GET /research/desk/micro/foundry`
(`exhaust_progress` key). `state/blueprint.md` already updated to record this (see Blueprint
conformance).

## OUT OF SCOPE

- Building J-08 "The operator sees the final Foundry truth." Iter-6's evaluator recommended bundling
  it with this fix, but a `COHERENCE-FAIL` iteration is consolidation-only per this agent's priority
  rubric; J-08 is the natural next iteration (see `state/assumptions.md`, iter-7).
- Fixing "Persistence stays scoped" (page-load GET writes a lock file,
  `apps/backend/app/research/foundry_runner.py:197-201` via `:250-254`) — iter-6 eval states its fix
  "also lives in a sealed file"; no legal route exists without owner sanction to break the seal.
  Stays open, undismissed, in the anti-goal ledger (OWNER-only).
- Ratifying/rejecting the discarded first real epoch, or sanctioning any seal break — OWNER-only per
  iter-6 eval; flagged here as still open, not resolved.
- Folding the advisory (non-blocking) "two owners, same formula" note for `terminal_count`/
  `checkpoint_ordinal` into the same helper — deferred to avoid touching `foundry_ledger.py` (sealed)
  or widening this iteration's risk surface for a non-blocking finding.
- Any edit to `docs/hypothesis-foundry-spec.md`'s freeze-integrity-verdict enum text — that file is
  sealed; the cosmetic drift `iter-6/coherence.md` noted stays undone, recorded here for the closing
  record.
- Any change to `epoch_id`, `docs/hypothesis-foundry/source-registry.json`, or
  `docs/hypothesis-foundry/epoch-manifest.json` content.
- Raising the session `--max-iter` cap — an operator decision, not a spec item.

## DEFINITION OF DONE

- [ ] `apps/backend/app/research/micro_routes.py` has exactly one named function computing
      `exhaust_progress.frozen_ready_total`; the served value is unchanged (`0`).
- [ ] The new equivalence-pinning test passes, proving the sealed CLI's own formula and the new
      canonical helper agree on the real, frozen `docs/hypothesis-foundry/epoch-manifest.json`.
- [ ] A fresh coherence-auditor pass over this iteration's diff reports no DUPLICATE-COMPUTATION
      finding for `exhaust_progress.frozen_ready_total`; if it still does, the dev handoff records
      the finding plainly and recommends an owner ruling instead of a sealed-file edit.
- [ ] J-07 replays passing via browser-qa/deterministic replay, reading proof from the `-evidence/`
      lane (not the QA report's own citation list).
- [ ] Required-still-passing journeys J-01..J-06 remain green (full regression replay, deterministic
      goldens + LLM fallback where no golden exists).
- [ ] Store-scope guard remains CLEAN: all 59 `docs/hypothesis-foundry/freeze-set.json` entries stay
      byte-identical to their pinned sha256 hashes — zero sealed-file edits.
- [ ] No anti-goal violation introduced by this iteration's diff; the two carried OWNER-only findings
      ("Persistence stays scoped," "No second real generation epoch") remain explicitly recorded as
      open, not silently dropped.
- [ ] `state/blueprint.md`'s `exhaust_progress` Data-Contract row reflects the corrected sole owner
      of `frozen_ready_total` (already updated by this spec; verify no further drift).
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-hypothesis-foundry-iter-7-dev.md`.

## TESTING REQUIREMENTS

- Browser: full replay of J-01..J-07 (J-07's Runner/Checkpoint subsection must render unchanged
  values off the `-evidence/` lane).
- Unit/integration: the new canonical `frozen_ready_total` helper; the new equivalence-pinning test
  against the sealed CLI's transcribed formula; the full existing Foundry suite (44+ tests, per
  iter-6's own count) re-run clean.
- Error cases: none new (this is a pure read-aggregation consolidation on an already-frozen,
  zero-family manifest — no new failure mode is introduced).

- TC-1: given the real committed `docs/hypothesis-foundry/epoch-manifest.json` (`families: []`) and
  the refactored `micro_routes.py`, when `GET /research/desk/micro/foundry` is called, then the
  response's `exhaust_progress.frozen_ready_total` field equals `0`, unchanged from iter-6.
- TC-2: given the sealed `run_hypothesis_foundry_real_exhaust.py:225` formula (transcribed, unedited)
  and the new canonical helper function in `micro_routes.py`, when both are evaluated against the
  real `docs/hypothesis-foundry/epoch-manifest.json`, then the new pinning test asserts both return
  the identical integer value and the test passes.
- TC-3: given this iteration's full diff, when the store-scope/freeze-set guard runs, then all 59
  entries in `docs/hypothesis-foundry/freeze-set.json` remain byte-identical to their pinned sha256
  hashes (zero sealed-file edits detected).
- TC-4: given `/desk` → Hypothesis Foundry → Runner / Checkpoint, when browser-qa replays J-07, then
  the on-screen `frozen_ready_total`/checkpoint fields render identically to iter-6's evidence
  ("0 of 0") and the journey is recorded passing, with the screenshot read from the `-evidence/` lane.
- TC-5: given this iteration's diff, when a fresh coherence-auditor pass evaluates the
  `exhaust_progress.frozen_ready_total` Data Contract row, then it reports no DUPLICATE-COMPUTATION
  finding for that row; if it still does, the dev handoff explicitly records the fallback
  recommendation to stop and request an owner ruling, and no sealed file is edited to force a PASS.
- TC-6: given `apps/backend/tests/test_foundry_route.py` and
  `test_run_hypothesis_foundry_real_exhaust.py`, when the full backend test suite runs, then both
  existing assertions (`progress["frozen_ready_total"] == 0` and the `run_real_exhaust` fixture
  assertions at `frozen_ready_total == 0`/`== 1`) still pass unchanged.
- TC-7: given J-01 through J-06's stored golden replay scripts, when this iteration's regression pass
  runs them against the unmodified other Foundry subviews, then all six replay green (no regression
  from the `micro_routes.py` refactor).
- TC-8: given the anti-goal disposition ledger before this iteration (total=4 / resolved=1 /
  blocking=3), when this iteration's diff is scanned, then the two carried OWNER-only findings
  ("Persistence stays scoped," "No second real generation epoch") are still present and unresolved
  (not silently removed), and no new anti-goal finding is recorded beyond the coherence-FAIL fallback
  disposition described in TC-5.
- TC-9: given this iteration's completion, when `docs/handoffs/goal-hypothesis-foundry-iter-7-dev.md`
  is opened, then it exists and states plainly whether the coherence-auditor's re-run PASSED or, per
  the TC-5 fallback, recommends an owner ruling — never silently omitting either outcome.

## NOTES

- Escalation flag: if the legal-route consolidation still leaves the coherence-auditor at FAIL, STOP
  — do not edit any of the 59 sealed `freeze-set.json` entries to force a PASS. Report the finding to
  the owner per iter-6 eval's explicit instruction; this is exactly the kind of self-granted exception
  Goal Mode must not take on its own authority.
- Three owner-only decisions remain open across this era and are NOT this iteration's to resolve:
  (1) ratify/reject the discarded first real epoch; (2) accept this iteration's one-sided
  consolidation as sufficient, or sanction breaking the seal for a stronger fix; (3) accept that a
  page visit writes a small lock file (its only fix sits in the sealed `foundry_runner.py`).
- Two permanently-unfixable gaps carried from iter-6 (no §8.5 runtime-environment metadata on the
  epoch-opening row; nothing re-verifies the ledger chain on the read path) are not addressed here —
  they were already recorded for the era's closing record and this iteration does not reopen them.
- If this consolidation lands clean, iter-8 should build J-08 "The operator sees the final Foundry
  truth" at full depth (per iter-6 eval's own scope description) — it touches no sealed file.
