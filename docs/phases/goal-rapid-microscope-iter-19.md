# Goal Iteration 19 — J-10's deterministic-rerun check, plus three regression-harness passengers

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 19
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict (iteration 18) was ESCALATE; per this session's own binding
  rule, ESCALATE makes full depth mandatory this iteration, no exceptions.
- **Frontend Present:** yes — DEFINITION OF DONE names `browser-qa-agent` (J-10's kept-product
  sentinel screenshots and the golden-replay lane for J-01–J-08), so the UI chain MUST run even
  though no `.tsx` product behaviour changes this iteration (iter-18's own lesson: `Frontend
  Present: no` silently skips the browser+replay lanes at ANY depth, which is exactly what let
  iteration 18's regression ship unnoticed).
- **Target journeys:** J-10
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08
- **Anti-goal reminders:**
  - **Deterministic and seeded** — every random draw uses a recorded named seed via per-row
    streams; identical requests reproduce byte-identical results; no wall-clock, no unseeded
    randomness in any research artifact. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **The denominator never shrinks.** Every evaluated variant lands in the hash-chained ledger
    with a closed-vocabulary decision; kills are never deleted; the union-N across grid versions
    is served beside every family. *(critical)*
  - **Guard tests are extended, never edited** — new micro modules add their own guards; existing
    guards, traps (TR-1…TR-30, already 30/30), and fixed assertions are never weakened. *(critical
    house rule, not a numbered anti-goal, restated because this iteration touches shared fixture
    scripts)*

## GOAL

Land J-10's last remaining gap — a deterministic-rerun check proving snapshot/scout/walk-forward
outputs are byte-identical when the same computation is re-run over unchanged stored data — so J-10
moves from `partial` to `passing`; carry three small, already-scoped regression-harness fixes as
passengers (never a round of their own), closing three items from iteration 18's evaluator
recommendation.

## BACKGROUND

Iteration 18's evaluator (ESCALATE) named five things "in order" for this round. Item 1 (the
sealed judge's economic floor and evidence-label ownership) explicitly "needs one decision from
[the owner] first" — I checked `docs/rapid-validation-spec.md` for a revision after r9
(2026-08-20) and found none, so per this session's own priority rubric ("don't pick a
human-blocked journey") that work stays out of scope this iteration; J-09 stays out of scope too,
both per the standing instruction and because it would be graded by the still-unringed judge.
Item 2 — J-10's step-2 deterministic-rerun check — is "the ONLY thing left before J-10 passes and
it needs nobody's permission," so it is this iteration's target. Items 3–5 are explicitly framed
as passengers ("never a round of their own"): deepen the four golden replay scripts that iter-16
(second) and iter-18 (third)'s lessons proved cannot fail (J-02–J-05, each currently asserting an
unrelated pre-existing Desk heading); make the QA quality report cite the actual running backend's
data store rather than an assumption; and treat "a round that touches the shared QA rig re-runs the
full replay set" as standing practice (iter-18 first lesson) — which this round's own diff (the
launcher script + four golden scripts) triggers, so the full 8-journey replay set below is not
optional this round.

Last coherence.md verdict (iter-18) was COHERENCE-PASS, so no consolidation-first requirement
applies (priority rubric step 2). No journey regressed (step 1 n/a). This iteration touches no
production computation module — it is test/harness-only — so its blast radius is small even at
mandatory full depth; the full-depth requirement here buys the independent auditor's mutation-proof
lane on the new determinism assertions (iter-15/16's lesson: an equality check between two runs is
exactly the "structurally unable to fail" shape those lessons warn about) and the UI chain that
iteration 18 lost.

## IN SCOPE

### Backend

- [ ] New backend test module (e.g. `apps/backend/tests/test_micro_deterministic_rerun.py`) that,
      over an UNCHANGED fixture dataset/store, re-runs each of the three era computations twice
      and diffs the outputs:
      - `micro_snapshots.run_snapshot_build_and_record` / `build_snapshot_rows` — snapshot rows +
        identity fields.
      - `scout.screen_candidate` / `register_and_screen_candidate` (same registered candidate
        spec, same corpus) — the `screen_result` payload.
      - `walkforward.evaluate_mode_b_fold` (or `register_mode_a_origin` + its fold evaluation,
        whichever the existing walk-forward test fixtures already stand up) — `fold_results`
        (effect, n, n_sessions, sign, evidence_class, process_label) for every fold index.
      Each comparison excludes only fields that are legitimately new per run by the store's own
      append-only design (ledger row id/position, `registered_at`/timestamp, `run_id`,
      `sequence_id`) — every other field must be byte-identical between run 1 and run 2.
- [ ] Mutation-proof for the new determinism assertions themselves (this era's own established
      discipline, iter-15/16's lesson): before finalizing, prove each comparison CAN fail — e.g. by
      deliberately perturbing one field of the second run's result in a scratch call and confirming
      the assertion raises — then confirm the real (unperturbed) rerun passes. Record which fields
      were perturbed to prove discrimination in the test module's own docstring, matching
      `test_micro_sealed_evaluation.py`'s TC-8 precedent.
- [ ] Deepen the four "cannot-fail" golden replay scripts (iter-16(second)/iter-18(third)
      lessons) — `runs/goal-session-rapid-microscope/journey-scripts/J-02.json` through
      `J-05.json` — so each expands its OWN already-registered Rapid-Microscope section
      (`desk-section-expand-microReadiness` / `-scoutLedger` / `-walkForward`) and asserts a real,
      already-registered field from that section rather than an unrelated pre-existing Desk
      heading. Exact target strings (see TESTING REQUIREMENTS TC-5..TC-8) — reuse the existing
      step-1 `goto /desk` + `"Playbook Signals"` pattern already shared by J-01/J-08/J-10 before
      each script's own step 2.
- [ ] Extend `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` IN PLACE (its own
      standing rule — never a new file) so it writes a durable, fixed-path manifest (e.g.
      `reports/qa-scoped-backend-store-manifest.md` or equivalent under `reports/`) recording the
      resolved `TAPEOLOGY_DATASET_DIR` and sibling store-root env vars plus a launch timestamp —
      the same values it already prints to stderr at startup (confirmed present at the script's
      existing `echo … >&2` lines) — so any quality/QA report this iteration or a future one
      produces can CITE that durable file instead of assuming which store a running server used
      (the exact process gap iteration 18's evaluator found: "the quality report states that the
      browser lane used your real data store. It did not.").
- [ ] Reviewer/QA process requirement for THIS iteration's own generated report (not a code
      change): any statement in this iteration's quality/QA report about which data store the
      browser/replay lane used must cite the manifest above (or the script's own stderr line), and
      must not assert "real data store" for any pass launched through the fixture-scoped launcher.

### Frontend (if applicable)

- None — no `.tsx` file changes this iteration. `Frontend Present: yes` is set solely to keep the
  browser-qa-agent and replay lanes running (see Goal Mode Metadata), per iter-18's lesson.

### New user-facing capability

None — this iteration adds no new UI-visible feature. It hardens the REGRESSION HARNESS (four
golden scripts made discriminating) and closes J-10's own acceptance gap (a backend-only
determinism proof), with zero product behavior change.

### New information displayed

None.

### New user actions

None.

### UI surface changes

None — no page, section, or copy changes. The four edited golden scripts click ALREADY-shipped
`desk-section-expand-*` controls and assert ALREADY-served text; nothing new renders.

### Product surface delta

None — the product experience is unchanged; only the automated regression coverage of it changes.

### Blueprint conformance

No new page or section; nothing to place in the Information Architecture. `state/blueprint.md` is
updated with a brief iter-19 documentation note only (no row change) — see Data-contract additions
below.

### Data-contract additions

None. Every field this iteration's deepened golden scripts assert is an ALREADY-registered Data
Contract value read verbatim from its already-registered endpoint:
- "Fallback frac" (per-shard `fallback_frac`) — `micro_readiness.py`, `GET
  /research/desk/micro/readiness` (era-baseline row).
- "Joinable corpus — withheld (excluded)" (`joinable_corpus.withheld_excluded`) — `micro_
  readiness.py` (+ `micro_join.py` sub-owner, iter-3 note), same endpoint; also the iter-10
  "Disclosure sub-fields" `withheld_excluded` row.
- "Ledger chain verification:" (`chain_verification.ok`/`.reason`) for Scout — `scout_ledger.py` +
  `scout.py`, `GET /research/desk/micro/scout` (era-baseline row).
- "Ledger chain verification:" (`chain_verification.ok`/`.reason`) for Walk-Forward — `walkforward.py`
  + its ledger, `GET /research/desk/micro/walkforward` (era-baseline row).
No second computation or second endpoint is introduced for any of these; the deterministic-rerun
test and the QA-launcher manifest are test/tooling artifacts, not served product values, so they
carry no Data Contract row.

## OUT OF SCOPE

- The sealed judge's economic floor / evidence-label ownership fix (iter-18 item 1) — blocked on
  an owner ruling that has not landed (`docs/rapid-validation-spec.md` has no revision after r9 as
  of this iteration). Do not guess a resolution; leave `micro_sealed_evaluation.py`'s `econ_floor`
  handling exactly as-is.
- J-09 "The pilot studies" — explicitly deferred per the standing instruction and blocked on the
  same ruling above (its results would be graded by the still-open-econ-floor judge).
- J-06 step 4 (real Alpaca tranche recording) — operator-owned; do NOT record real tape.
- Any edit to `micro_sealed_evaluation.py`'s TR-30 condition-1 logic, `SEALED_MIN_OBSERVATIONS`,
  or the trap suite (TR-1…TR-30) — all "Do not redo," already 30/30 and mutation-proved.
- Any edit to `J-08.json` / `J-10.json`'s already-refreshed Validation Vault assertions
  (`iter18-qa-universe`) — "Do not redo."
- Any `.tsx` / UI feature change — this iteration is test-and-harness-only.
- Any change to `vault.py`, `tick_recorder.py`, or any frozen/Referee module.

## DEFINITION OF DONE

- [ ] J-10 passes via browser-qa-agent: the kept-product sentinel (`/`, `/structure`, every
      shipped `/desk` section including the three Referee sections) is browser-verified fresh, AND
      the new deterministic-rerun backend test module passes (both are step 2/3 of J-10's own
      acceptance).
- [ ] Required-still-passing journeys J-01–J-08 remain green via the FULL 8-journey golden replay
      set (not a subset) — mandatory this round because the diff touches the shared QA launcher
      script and four of the golden scripts themselves (iter-18's first lesson).
- [ ] No anti-goal violation introduced (see Anti-goal reminders above — determinism and
      single-source-of-truth are the two most at risk this round).
- [ ] Full backend suite passes with a count ≥ the count recorded at the start of this iteration
      (per iter-18's evaluator: 3,271 collected / 3,263 passed / 8 skipped / 0 failures / 0
      errors), 0 regressions.
- [ ] `config_fingerprint()` still prints `08e471b10130e1e2`; the six `referee_*` module SHA-256
      listing still matches the iteration-0 baseline (both already-standing sentinel checks, not
      new work).
- [ ] This iteration's own generated quality/QA report states which backend data store the
      browser/replay lane used, sourced from the new manifest file (or the launcher's existing
      stderr line) — not asserted from the invoking shell's own environment.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-19-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-10 fresh (kept-product sentinel, all three surfaces); J-01, J-02, J-03, J-04, J-05,
  J-06, J-07, J-08 via the full golden-replay set (J-07 has no golden script by design — its
  designated LLM lane covers it, per standing precedent).
- Unit/integration: the new `test_micro_deterministic_rerun.py`-class module (snapshot / scout
  screen / walk-forward fold rerun byte-identity, TC-1..TC-3 below) plus its mutation-proof
  (TC-4); full existing suite unmodified and green.
- Error cases: N/A for new product behavior (none shipped this iteration) — the one negative
  requirement is that the rerun-equality assertions must NOT silently pass when a field differs
  (covered by TC-4's mutation-proof) and the golden-script deepening must NOT silently pass when
  the target section fails to render (covered by TC-5..TC-8's reliance on the section's real
  `UnavailablePanel`/error branch, which renders different text than the asserted string).

Test-first contract:

- TC-1: given a fixture dataset already registered in a scratch `DatasetStore` with no snapshot
  yet built, when `run_snapshot_build_and_record` (or `build_snapshot_rows`) is invoked twice in
  succession against that unchanged dataset, then the second run's snapshot rows and identity
  fields (dataset_checksum, MICRO_ALGO_VERSION, SNAPSHOT_FORMAT_VERSION, feature_source_hash,
  config_fingerprint, params_hash) are byte-identical (equal after canonical JSON serialization)
  to the first run's.
- TC-2: given a scout candidate family already registered and screened once against an unchanged
  fixture corpus, when the same candidate spec is screened a second time via `screen_candidate`
  (or `register_and_screen_candidate`), then the second run's `screen_result` payload (effect,
  p-value, concentration/ToD/fallback-tercile disclosures, economic-relevance column) is
  byte-identical to the first run's, while the ledger records two independent trial rows (never
  overwritten, never deduplicated away).
- TC-3: given a fold spec already evaluated once over an unchanged fixture corpus, when the same
  corpus/rule is evaluated a second time, then every fold index's `fold_results` fields (effect,
  n, n_sessions, sign, evidence_class, process_label) are byte-identical between the two runs,
  while the ledger records a new independent sequence_id.
- TC-4: given TC-1..TC-3's comparison logic, when one field of a scratch second-run result is
  deliberately perturbed before comparison, then the corresponding assertion FAILS (proving the
  check is not vacuous) — and when the perturbation is reverted, the real rerun's assertion PASSES.
- TC-5: given the fixture-scoped `/desk` page is loaded and the Microscope Readiness section is
  expanded (`desk-section-expand-microReadiness`), when `journey-scripts/J-02.json` replays, then
  the page displays the literal column-header text `"Fallback frac"`.
- TC-6: given the same section expanded, when `journey-scripts/J-03.json` replays, then the page
  displays the literal label text `"Joinable corpus — withheld (excluded)"`.
- TC-7: given the fixture-scoped `/desk` page with Scout Ledger expanded
  (`desk-section-expand-scoutLedger`), when `journey-scripts/J-04.json` replays, then the page
  displays the literal text `"Ledger chain verification:"` sourced from `GET
  /research/desk/micro/scout`'s `chain_verification` field.
- TC-8: given the same page with Walk-Forward expanded (`desk-section-expand-walkForward`), when
  `journey-scripts/J-05.json` replays, then the page displays the literal text `"Ledger chain
  verification:"` sourced from `GET /research/desk/micro/walkforward`'s `chain_verification` field.
- TC-9: given the fixture-scoped QA backend launcher script starts a scoped backend instance, when
  startup completes, then a durable manifest file under `reports/` (or the launcher's own already-
  printed stderr line, if the manifest is judged redundant by the developer) records the exact
  resolved `TAPEOLOGY_DATASET_DIR` (and sibling store-root vars) the running server process is
  bound to.
- TC-10: given this iteration's diff touches `apps/backend/scripts/qa_playbook_iter7_fixture_
  scoped_backend.sh` and four files under `runs/goal-session-rapid-microscope/journey-scripts/`,
  when the browser-qa/replay lane runs for this iteration, then all 8 currently-registered golden
  scripts (J-01, J-02, J-03, J-04, J-05, J-06, J-08, J-10) execute and report individually — never
  a subset.
- TC-11: given the full backend suite passed at 3,271 collected / 3,263 passed / 8 skipped / 0
  failures at the start of this iteration, when `pytest` runs against `apps/backend` after this
  iteration's changes, then it exits 0 with a collected/passed count ≥ that baseline and 0
  failures/errors.

## NOTES

- **Applied lesson (iter-15/16):** the new determinism assertions are exactly the "equality check
  between two computed things" shape that produced a structurally-unable-to-fail trap twice before
  in this session (TR-26's coincident fixture numbers, the TR-2 unregistered-universe sweep) — TC-4
  above is non-negotiable, not a nice-to-have.
- **Applied lesson (iter-18, first):** the shared-rig-touch rule (TC-10) is why this round's DoD
  requires the FULL 8-journey replay set rather than a targeted subset, even though only J-10 is
  the target journey.
- **Applied lesson (iter-18, second):** `Frontend Present: yes` is set explicitly despite zero
  `.tsx` changes, because the DoD names `browser-qa-agent`.
- **Escalation flag carried forward, not resolved:** iteration 18's evaluator asked, for the sixth
  time, whether a `full`-depth request expressed only in prose (rather than the verdict line) is
  binding — and separately asked whether the machine can be told the independent-checker lane may
  never be cut for time. Both are questions for the human owner / framework maintainer, not
  something this iteration spec can resolve; carrying them forward here so they stay visible.
- **Item 1 status recorded for the record:** no revision after r9 exists in
  `docs/rapid-validation-spec.md` as of this iteration's authoring — confirmed by grep, not
  assumed. If the owner rules on the econ-floor/evidence-label sourcing question before the next
  iteration is planned, that ruling becomes the next iteration's primary target ahead of any other
  work, per iteration 18's own framing ("nothing else should go first").
