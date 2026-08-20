# goal-rapid-microscope-iter-17 Execution Plan

Full-depth round (Full trigger 3: iteration-16 verdict was ESCALATE — mandatory independent
auditor, per this era's own iteration-8/12 precedent that a "full depth" recommended only in
evaluator prose, not the verdict line, silently lost the auditor). Target journey: J-10.
Required-still-passing: J-01, J-04, J-05, J-07, J-08 (narrower than iter-16's own full sweep —
this round's surface doesn't touch J-02/J-03/J-06, see phase spec BACKGROUND).

## Scope note — this is not a small round

This is materially more than "add two trap tests." `micro_sealed_evaluation.py` is a genuinely
new module (confirmed absent from the tree this round, along with its test file). It takes over
the sealed verdict from `micro_graduation.py`'s caller-supplied `passed: bool` per the owner's r6
§8.1 ruling. `SEALED_PASS_RULE_V1` introduces no new numeric constant (reuses the §1 per-fold
floors + the family's own pre-registered economic floor). TR-24 replaces a naive
single-sequence `_proposed_confirmation_boundary` with the lineage-wide r6 §8.2 derivation — the
owner explicitly rejected the naive "latest timestamp on surviving evidence rows" formula that is
literally what today's code does. Budget and review attention accordingly; this is not a
passenger-sized diff even though it also carries four small passengers.

## What to Build

- **TR-23** — new module `apps/backend/app/research/micro_sealed_evaluation.py`, the sole
  scientific owner of the sealed-shard evaluation verdict. Implements spec §8.1's 7-step mandatory
  sequence verbatim: (1) require an ASSIGNED shard + a candidate spec frozen before assignment;
  (2) verify spec_hash/family_root_id/outcome basis/sidedness/economic floor/sample+breadth floors
  against the candidate's registered Scout spec; (3) obtain the shard only through
  `micro_accessor.MicroAccessor` + `vault.build_vault_state` (existing, unmodified) to confirm
  genuine `exposed` binding to this exact `family_root_id`; (4) RECOMPUTE the outcome from
  canonical machinery — reuse `walkforward.summarize_fold_observations` (L382) and/or the
  `evaluate_mode_b_fold` shape (L581), never a second independently-valued implementation, never
  trust a caller-computed effect; (5) derive the verdict from `SEALED_PASS_RULE_V1`'s five
  conditions; (6) persist an immutable evaluation artifact through the ALREADY-EXISTING
  `GraduationLedger`/`ROW_KIND_SEALED_EVALUATION` machinery (already in `__all__` — reuse, do not
  add a new row kind); (7) return only that artifact's id+hash to the transition.
- `micro_graduation.py`: retire `record_sealed_evaluation`'s caller-supplied `passed: bool` — the
  function (or its replacement call site) must call into the new module's computed verdict.
  `evaluate_sealed_survivor_transition` and `build_export_bundle` read the new artifact shape.
  Rewrite the module docstring's "disclosed T-1 interpretation call" paragraph (today's lines
  31-48, confirmed unchanged from the phase spec's own anchor) to describe the shipped behavior.
- **TR-24** — rewrite `_proposed_confirmation_boundary` (today's lines 475-491, confirmed: it
  currently reads only `validation_revealed_at`/`registered_at` off fold rows plus
  `evaluated_at` off sealed evaluations for the ONE caller-supplied sequence — exactly the naive
  formula the owner rejected) into the r6 §8.2 lineage-wide formula: `lineage_data_frontier` =
  max of every evidence item's own already-recorded timestamp field across the WHOLE
  `family_root_id` lineage (survivors, killed/superseded siblings — `build_export_bundle` already
  computes `scout_trials` filtered to this exact `family_root_id`, kills included — thread it in,
  no new ledger join; folds of ANY verdict/class/process-label, not just `_eligible_folds`; sealed
  evaluations of any verdict incl. FAIL/`insufficient`) → `evidence_safe_boundary` = frontier +
  the applicable embargo → `proposed_confirmation_boundary` = first eligible boundary strictly
  after `max(evidence_safe_boundary, handoff_created_at)`. Rewrite this function's own stale
  docstring. `build_export_bundle` persists the full derivation (`lineage_data_frontier`,
  contributing evidence ids, `frontier_observed_through`, embargo rule id+value,
  `evidence_safe_boundary`, `handoff_created_at`, `proposed_confirmation_boundary`).
- `micro_accessor.py`: docstring-only correction (today's "Two callers, two disciplines"
  paragraph, lines 23-37, confirmed present at that anchor) — state plainly that no current
  production caller constructs an origin-fenced read. **No behavior change.** (Decided by the
  decomposer, logged in `state/assumptions.md`; do not wire a live fence — see Do Not Touch.)
- Two GAP-closing discriminating fixtures: **B3** in `test_micro_accessor.py` (an
  exposure/viewing entry logged at EXACTLY the same instant a validation window is registered —
  proves `is_exposed_before`'s strict `<`, confirmed at accessor.py:158-166) and **B4** in
  `test_micro_observer.py` (a session whose LAST event is a TRADE, not a quote — proves
  `finalize()`'s session-end stamp equals the trade's own timestamp, numerically different from
  what it would be had the session ended on a quote).
- New `apps/backend/tests/test_micro_sealed_evaluation.py` (TR-23) and additions to
  `apps/backend/tests/test_micro_graduation.py` (TR-24) — see "Governing acceptance rule" below,
  this is the round's central risk, not a formality.
- Run `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` through the deterministic
  replay harness for real, for the first time this era (see Passengers §1).
- Trap suite reaches 29/29 (TR-1…TR-29 all present); J-10 stays `partial` by design (step 2, the
  byte-identical rerun check, stays out of scope — not a shortfall).

## Agents Required

- backend-data: yes — all work above is `apps/backend/**` Python: one new module, one existing
  module's two sub-computations rewritten, four test files touched, one replay script re-run.
- frontend-ux: no — zero `apps/frontend/**` source changes this round (see Frontend Present below
  for why browser QA still runs anyway).

## Frontend Present

Frontend Present: yes

No frontend source file changes this round — the served endpoint shape gains fields inside its
existing payload but is not rendered by any `/desk` section or consumed by any MCP tool (grep
confirms zero hits for "graduation" in `page.tsx` or `app/mcp/*.py`). Frontend Present is still
`yes` because J-10's own acceptance text requires a browser-verified kept-product sentinel this
round (cockpit, `/structure`, every shipped `/desk` section), and the required-still-passing set
(J-01, J-04, J-05, J-08) needs its deterministic-replay checks dispatched. QA is verifying
existing, already-shipped UI for regressions — not new UI construction.

## Files to Create/Modify

- `apps/backend/app/research/micro_sealed_evaluation.py` — NEW. Sole owner of `SEALED_PASS_RULE_V1`
  and the 7-step evaluation sequence (spec §8.1).
- `apps/backend/app/research/micro_graduation.py` — retire caller-supplied `passed: bool`; rewrite
  `_proposed_confirmation_boundary` to the lineage-wide formula; `build_export_bundle` persists the
  full derivation; two stale-docstring rewrites (module docstring L31-48, boundary function
  docstring).
- `apps/backend/app/research/micro_accessor.py` — docstring-only fix, L23-37. No behavior change.
- `apps/backend/tests/test_micro_sealed_evaluation.py` — NEW. TR-23 (TC-1…TC-9).
- `apps/backend/tests/test_micro_graduation.py` — additions. TR-24 (TC-10…TC-14) + TC-15
  (docstring-vs-code check for both rewritten docstrings).
- `apps/backend/tests/test_micro_accessor.py` — add GAP B3 fixture (TC-16).
- `apps/backend/tests/test_micro_observer.py` — add GAP B4 fixture (TC-17).
- `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` — run through replay; conditionally
  restore 2 dropped assertions (Passengers §1).
- `docs/handoffs/goal-rapid-microscope-iter-17-dev.md` — dev handoff (required), naming the
  `observed_through` open question's resolution (or its drop, per T-1) explicitly.

## Do Not Touch — already done or explicitly frozen this round

- `runs/goal-session-rapid-microscope/state/blueprint.md` — **already updated by the decomposer.**
  Confirmed by direct read: the Data Contract "Graduation states + export bundles" row already
  names `micro_sealed_evaluation.py` as sub-owner, and an "iter-17 note" (matching the iter-3/
  iter-11 sub-owner-edit precedent) is already present. Nothing left here for the developer.
- `vault.py`, `micro_chain_ledger.py`, `referee_*.py` (all six modules) — byte-untouched; re-verify
  SHA-256 against the iteration-0 baseline (TC-20). `record_sealed_evaluation` today already calls
  `vault.build_vault_state` unmodified for its exposed-binding check (L379) — TR-23's step 3 reuses
  the identical call, adds no new vault function.
- `walkforward_ledger.py`'s persisted fold-row shape — no new `family_root_id` field on fold rows.
  Thread the already-computed `scout_trials`/`fold_results` through the new boundary function
  instead (the module's own "two identity spaces this era has never joined" precedent stays).
- `scout.py`, `scout_ledger.py`, `micro_readiness.py`, `tick_recorder.py`, `micro_routes.py`'s route
  shape, any Playbook detector, the engine, `Config` (zero new fields), the fingerprint
  (`08e471b10130e1e2` must still print).
- Wiring `micro_accessor.py`'s origin fence into a live production caller — the alternative to the
  docstring fix, explicitly not chosen (decision logged in `state/assumptions.md`).
- J-10 step 2 (byte-identical deterministic-rerun check), J-09 start — both explicitly deferred by
  the phase spec's own OUT OF SCOPE, not oversights.

## The governing acceptance rule for TR-23 and TR-24 — read this before writing either test

Two consecutive prior rounds shipped a brand-new trap that was **structurally unable to fail**,
each caught only by the independent auditor: iteration 15's opaque-pool sweep (sealed under an
unregistered universe, so the leak branch never ran) and iteration 16's TR-26 magnitude clause (a
fixture whose revealing quote coincidentally carried the same size the run already held — survived
a genuine dev TDD proof AND a reviewer mutation of production source before the auditor caught it).
This round is the highest-risk instance yet because TR-23/TR-24 are more structurally complex than
either prior trap. For **both** TR-23 (TC-8/TC-9) and TR-24 (TC-13/TC-14), require both halves,
not just one:

1. **Mutation evidence.** A committed non-vacuity test that installs a deliberately-corrupted
   version of the real logic, asserts the SPECIFIC named wrong value it produces, then restores and
   asserts the correct value returns. The established, already-praised pattern to mirror exactly
   (do not re-derive a different style) is `test_micro_observer.py`'s TR-26 fix,
   `test_tc12_tr26_reverting_the_fix_makes_the_corrected_assertion_fail_restoring_it_passes`
   (L543): `monkeypatch.setattr` installs the exact pre-fix method, asserts the exact wrong value
   (`== 2.0`) AND `!= 3.0` (naming both), then `monkeypatch.undo()` and asserts the correct value
   returns. In addition to this committed test, the developer's own TDD process should perform a
   real on-disk edit of the shipped module, run the specific new test, watch it fail naming the
   wrong value, then revert byte-identical (`git diff` empty) — document this act in the dev
   handoff, mirroring iteration 16's own praised dev practice.
2. **Fixture discrimination (the specific, separate lesson of iteration 16 — the easy one to
   omit).** The correct and corrupted computed paths must yield **numerically different** values,
   never values that happen to coincide. Reference pattern:
   `test_tc10_quote_depletion_resolves_at_a_price_change_attached_to_the_next_trade_row` uses
   deliberately distinct numbers throughout (`anchor_at == 0.0`, `observed_through == 3.0`,
   `value == 200.0`) — never two fixture values that could match by chance. For TR-23: the
   correctly-recomputed effect and a deliberately-corrupted computed effect must be different
   numbers. For TR-24: the killed sibling's own timestamp and the survivor's own frontier must be
   set to deliberately different calendar instants — never coincidentally equal.

**Reviewer and auditor must each independently re-verify both halves**, not just read the tests.
The reviewer performs its own mutation of the real production source (an actual on-disk edit, not
only monkeypatch) for TR-23 and TR-24, runs the new tests, confirms FAIL naming the wrong value,
reverts byte-identical, and documents this in the review report — mirroring iteration 16's
reviewer act ("the reviewer proved it by breaking the real program himself"). The auditor repeats
this independently with its own mutations and is specifically tasked with hunting for any fixture
whose correct-vs-corrupted values could coincide — this is the auditor's single highest-priority
check this round, the exact failure mode that escaped two prior rounds' dev+review passes.

## Open question carried to the developer

No ledger row anywhere is named `observed_through` (confirmed this round by direct source read:
Mode A fold rows carry `validation_revealed_at`, Mode B fold rows and Scout trial rows carry
`registered_at` — `walkforward.py` L531/L552/L577/L612). TR-24's lineage frontier must derive
"this evidence item's own observed_through" from whichever field that row TYPE already carries
(survivors/siblings → their own registration/reveal timestamp; folds of any verdict → their own;
sealed evaluations → their own `evaluated_at`). If a specific evidence-item type genuinely has no
usable own-timestamp field to stand in for "evidence consumed," **drop that item's inclusion, name
the exact gap in the dev handoff, and flag it for an owner ruling under spec rule T-1** — never
invent a field or substitute `anchor_at`/a wall-clock read in its place.

## Passengers (four small named jobs — never a round of their own)

1. **Run J-10's replay script for real, for the first time this era.** Confirmed by direct diff
   read (`git show dd4d439`): iteration 16 REPLACED two Playbook Evidence steps — step 9
   (`click testid=desk-section-expand-playbookEvidence`, expect text `"Built from signature:"`)
   and step 10 (`fill testid=desk-playbook-date-input` = `"2026-06-22"`, expect text
   `"recorded signals, none hidden"`) — with the four new Rapid-Microscope section-expand steps,
   dropping Playbook Evidence coverage entirely, and the script was never actually executed after
   editing. If the current committed script passes through the deterministic replay harness,
   re-insert those exact two steps (text above) and re-run to confirm still green. If it does not
   pass, record the finding in the dev handoff rather than dropping anything further.
2. `micro_accessor.py`'s docstring fix — already covered above under What to Build / Do Not Touch.
3. GAP B3 (`test_micro_accessor.py`) — already covered above under What to Build.
4. GAP B4 (`test_micro_observer.py`) — already covered above under What to Build.

## Fixture & environment discipline

- The real store's Scout ledger, Walk-Forward sequences, and Vault are all genuinely empty, and
  the QA fixture rig has never been seeded with any of them. **All TR-23/TR-24 fixtures must be
  self-contained, hermetic, and committed** (synthetic candidate specs, synthetic assigned/exposed
  vault shard state via the existing vault fixture helpers, synthetic ledger rows) — never
  dependent on live data. Do not seed the real store with a live Scout/Walk-Forward/Vault family.
- **Do not record real tape. Do not seed, mutate, or expose real Vault data — sealed exposure is
  family-level and single-shot, permanent, and this round must not consume it.**
- No acceptance criterion may depend on a live Scout compute completing (one ran past 25 minutes
  without finishing a single candidate recently) — TR-23/TR-24 work is fixture-only.
- Before running tests or anything that writes temp files, export:
  `TMPDIR=/home/dennis-chan/.cache/iad/iad.goal-rapid-m-d1ead7e7.3015052` (same for `TMP`/`TEMP`).
- QA note: the `/desk` "Screen Comparison" and "Provenance" sections named in some earlier test
  plans only render after a screen has been computed and do not exist in the DOM today — do not
  add a browser assertion against them this round.

## UI Evolution

None. No new user-facing capability, no new information rendered anywhere (the endpoint's payload
gains internal fields but nothing on `/desk` reads them), no new user actions, no UI surface or
navigation change. This section is deliberately empty by design, not an oversight — the phase spec
itself states the product surface is unchanged this round.

## Visual Requirements

N/A for new construction — this round ships no new visual surface. QA's browser pass is a
**regression check of already-shipped surfaces**, per the phase spec's TESTING REQUIREMENTS:
- `rm -rf apps/frontend/.next`, clean rebuild, restart before any browser evidence (T-9).
- J-10 sentinel (full): cockpit `/` live tape + chart; `/structure` load + Tradable Map; every
  shipped `/desk` section including the three Referee sections and all four Rapid-Microscope
  sections; via the store-scoped rig (:8301/:3301).
- J-01, J-04, J-05, J-08: deterministic replay (golden scripts).
- J-07: LLM fallback, direct-endpoint navigation to `GET /research/desk/micro/graduation` — no
  golden script exists for it by design (carried from iteration 15).
- No screenshot ⇒ `unknown`, never `passing` (T-10); below-the-fold sections need element captures.

## Key Test Scenarios

- TR-23 (TC-1…TC-9): a caller-supplied `passed: bool` is structurally impossible/refused; the new
  evaluator runs the full 7-step sequence and derives a deterministic tri-state verdict
  (PASS/FAIL/`insufficient`, never coerced to boolean) from `SEALED_PASS_RULE_V1`; a rule changed
  after assignment fails closed; re-running on identical inputs is byte-identical; a second
  evaluation of the same (family_root_id, shard) is refused; a failed verdict travels in every
  later export bundle permanently; mutation evidence + fixture discrimination both proven (TC-8/9).
- TR-24 (TC-10…TC-14): a killed sibling's later `observed_through` pushes the boundary past it,
  not just the survivor's own evidence; a deferred feature's `observed_through` (never its earlier
  `anchor_at`) moves the frontier; the final boundary is never earlier than either the proposed or
  the Referee registration boundary; mutation evidence + fixture discrimination both proven
  (TC-13/14).
- TC-15: corrected docstrings match shipped code exactly (zero origin-fenced production callers;
  neither graduation docstring still describes the retired behavior).
- TC-16 (GAP B3), TC-17 (GAP B4): as described above.
- TC-18: J-10 replay genuinely run; conditional restoration of the two dropped assertions.
- TC-19: exactly 29 distinct TR- labels present (TR-1…TR-29, TR-17/TR-21's sub-parts deduplicated).
- TC-20: full suite 0 failures, passed ≥ 3238; fingerprint `08e471b10130e1e2`; six `referee_*.py` +
  `micro_chain_ledger.py` SHA-256 match iteration-0; MCP tool count = 26; `tsc --noEmit` clean.
- TC-21: J-01/J-04/J-05/J-08 golden replay + J-07 LLM-fallback direct-endpoint check, zero
  regressions.
- Full acceptance text is in `docs/phases/goal-rapid-microscope-iter-17.md` DEFINITION OF DONE and
  TESTING REQUIREMENTS — this plan routes to it rather than re-transcribing it; implement from the
  spec (`docs/rapid-validation-spec.md` §8.1/§8.2/§9) and the phase spec verbatim, not from
  paraphrase.
