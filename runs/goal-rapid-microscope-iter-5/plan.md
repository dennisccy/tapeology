# goal-rapid-microscope-iter-5 Execution Plan

Session: `rapid-microscope` · Era: "The Rapid Microscope" · Target journey: **J-05** (the
chronological walk-forward engine) · Required-still-passing: J-01, J-02, J-03, J-04, J-10 (widened
because iteration-4's evaluator verdict was ESCALATE).

Canonical sources (read from, never re-derive): `docs/rapid-validation-spec.md` §6 (walk-forward,
lines 299-390), §1 (constants, lines 65-109), §0 (seed/evidence-class conventions), §9 (trap
table, lines 525-554); phase spec `docs/phases/goal-rapid-microscope-iter-5.md` carries its own
full DEFINITION OF DONE (TC-1…TC-29) — this plan condenses it, it does not replace it. This
iteration's scope and file list were checked against the real tree (below), not assumed.

## Alignment check

Tightly scoped to `docs/goal.md`'s J-05 and the era's "validation that replays the research
process" pillar. No drift found: defers vault/recorder (J-06), graduation (J-07), UI rendering
(J-08), pilot studies (J-09) exactly as the phase spec's OUT OF SCOPE says; touches no frozen
foundation (engine, referee, playbook detectors, fingerprint). Nothing to flag to the owner.

## What to Build

Backend only (`apps/backend/app/research/`):

1. **`micro_accessor.py`** (new) — origin-fenced accessor per spec §6.1: constructed with an
   `origin` session date; any read beyond it raises a typed error (never empty); a sealed shard is
   invisible except as future §7.5 metadata (vault doesn't exist yet — write this path generically,
   nothing to wire it to until J-06); every outcome-data read it serves appends a §6.7 exposure-
   registry entry (surface, window, timestamp) — no unlogged read path.
2. **Re-point both existing direct readers of `micro_snapshots.read_snapshot_rows`** through the
   accessor — confirmed live at `micro_join.py:416` and `scout.py:343` (both grepped against the
   current tree, not assumed from the spec). Both callers' served/ledgered values must stay
   byte-identical (TC-4, TC-5).
3. **TR-3 import-ban guard test** — ast-based source-scan (copy the
   `test_referee_guards.py` bidirectional-import-ban pattern, e.g. its
   `test_no_referee_module_imports_the_detect_module` at line 180) proving no module but
   `micro_accessor.py` imports/calls the raw snapshot-row reader.
4. **`walkforward.py`** (new) + its own hash-chained append-only fold/sequence ledger (mirror the
   `scout.py`/`scout_ledger.py` split, or `desk_playbook_log.py`'s pattern — file split is an
   implementation choice) per spec §6.2-§6.8:
   - Fold spec `{corpus_id, corpus_manifest_hash, geometry, clustering_unit, floors, registered_at,
     geometry_hash}`, frozen at registration; `clustering_unit` always `session_date`; `step ≥ test`
     enforced; a second geometry on an already-fold-1'd corpus refused without a recorded voiding
     event, which then clears every survivor state of that corpus-era (TR-13).
   - Purge exact-by-construction from session-truncated labels (TR-6); per-fold-spec derived
     embargo, `E=0` legitimate with derivation recorded; the diagnostic run's own fold spec pins
     `embargo_sessions=5` as ITS predeclared choice only, never a universal default.
   - Mode A: frozen fitting RULE (not the realized value) is the sequence identity (TR-14); spec
     hash recorded before the validation window is revealed (freeze-order visible in the ledger).
   - Mode B: human-authored spec registered first; evaluation against a window already exposed
     before `registered_at` auto-classes `historical_exposed_diagnostic` (TR-22) — structurally the
     ONLY possible outcome this iteration, since every window in play (playbook corpus + 12 legacy
     tick days) is r2-pre-marked exposed; that is the expected honest state, not a defect.
   - §6.7 exposure registry: hash-chained, r2-initialized with every window of the 155-session
     playbook corpus and all 12 legacy tick symbol-days pre-marked exposed.
   - §6.8 process labels: `rule_process` vs `operator_process`; a post-reveal selection is refused
     at `walkforward_survivor` (TR-21); a pre-reveal registered shortlist keeps `rule_process`.
   - §6.6 decay view (per-fold effect/n/sessions/sign/ToD/symbol breadth/recency line, pooling
     across sequences refused) and the discretion-free **`WF_SURVIVOR_RULE_V1`** predicate (all
     five conditions verbatim — see Key Test Scenarios TC-15).
   - Below-floor folds/sequences serve typed `insufficient`/refusal, never a fabricated verdict; the
     tick family (11 sessions) refuses fold construction outright naming `11 < 105` (TR-15).
5. **`WalkForwardComputeManager`** mirroring `MicroSnapshotComputeManager`/`ScoutComputeManager`
   (single-flight, pollable progress, cooperative cancel, CLI-runnable) plus two lessons carried
   from this era's own audits, applied from day one rather than retrofitted:
   - iteration-2 lesson: terminal-state-only ledger writes — a mid-run exception resolves the run
     log to `"failed"`, never leaves a silently-short ledger.
   - iteration-4 lesson: a **separately-persisted tail anchor** (`{row_count, head_hash}`, written
     AFTER the row it commits to), copied in directly — `scout_ledger.py` needed two later audit
     fixes (B1, B2 below) to get this; don't re-derive the pre-audit chain-only design.
   Wire the already-blueprinted routes into the EXISTING `micro_routes.py` (no new router file),
   following the readiness → snapshots → scout wiring already there (pattern confirmed at
   `micro_routes.py:53, 94, 181`): `GET /research/desk/micro/walkforward`,
   `POST/GET/POST-cancel /research/desk/micro/walkforward/compute`,
   `GET /research/desk/micro/walkforward/runs`.
6. **TR-16 oracle fixtures** (small, keyless, committed): a known-null corpus (zero true effect)
   and a planted-effect corpus (registered sign/magnitude), both run end to end through Scout +
   walk-forward, plus a byte-identical rerun proof.
7. **Traps landing this iteration: TR-3, TR-5, TR-6, TR-13, TR-14, TR-15, TR-16, TR-21, TR-22**
   (9 of the 22; TR-1/7/8/9/10/11/17/18 already landed in J-02/J-03/J-04 — verify, don't re-land;
   TR-2/4/12/19/20 are vault/recorder-scoped, J-06/J-07's job).
8. **The diagnostic acceptance run**: predeclare (ledgered, before any outcome read) a small frozen
   subset of already-shipped playbook setup definitions as the run's candidate rule(s) — the
   specific subset is a build-time implementation choice, disclosed, never invented from outcomes.
   Run the real 155-session playbook bar corpus (2025-06 orphan excluded, disclosed) under
   `DIAGNOSTIC_GEOMETRY` (train=40, embargo=5, test=20, step=20) via the compute manager/CLI —
   **never a blocking pytest recomputation** (iteration-hygiene rail; 13 of 15 referee-era
   iterations tripped step timeouts). Reads the playbook corpus's already-computed forward/MDD
   outcome statistics as each setup occurrence's effect input (Era B2 reuse — `desk_forward.py`'s
   `ForwardStore`/`compute_forward` is the most likely existing owner of those numbers, confirmed
   present in the tree; do not recompute the detector output itself). Produces 5 folds / 100
   validation sessions, every fold/sequence `historical_exposed_diagnostic`.
9. **Counter-tests**: diagnostic-class results and `operator_process` sequences award zero
   graduation-relevant (survivor) credit under `WF_SURVIVOR_RULE_V1`, regardless of statistics.
10. **Frozen-foundation re-checks + full suite**: fingerprint `08e471b10130e1e2`; all 6
    `referee_*.py` SHA-256 hashes match the iteration-0 listing; `app/engine/`/`desk_playbook.py`/
    `desk_playbook_context.py` empty diff; the 18 real-corpus snapshot files' row total unchanged
    at `3,815,933`; full suite via `pytest tests/` (no extra `-q` — iteration-0 lesson, the
    addopts already applies `-q` and swallows the summary line otherwise) ≥ **2,949 pass / 8 skip**
    (iteration-4's post-audit baseline), 0 new failures.

## Agents Required

- backend-data: yes -- implements items 1-10 above (`micro_accessor.py`, `walkforward.py` + ledger,
  compute manager + routes, the two re-points, TR-16 fixtures, the 9 traps, the diagnostic run, and
  every TC-1…TC-28 test).
- frontend-ux: no -- zero `.tsx`/UI files touch this iteration. The Walk-Forward section's
  rendering is explicitly J-08's scope (already the canonical home in `blueprint.md`'s IA table,
  re-confirmed accurate this iteration, no edit needed). Verify with a grep for touched frontend
  files at review time — it should return nothing, mirroring iteration-4's own F1 finding.

## Frontend Present

Frontend Present: no

## MANDATORY browser regression — read before skipping anything

Iteration-4's evaluator verdict was ESCALATE **specifically because** `Frontend Present: no` was
misread as "skip the whole browser lane" — browser-qa recorded a blanket SKIP, so J-10's 13-step
kept-product sentinel never ran at all, and the audit (E1) flagged it as an unclosed IMPORTANT gap.
This lesson is logged twice in the phase spec and is binding here:

- `Frontend Present: no` describes THIS iteration's own delta (J-05 has no dedicated UI surface —
  an honest SKIP is correct for J-05 alone).
- It does **not** excuse the browser-qa-agent step from running the required-still-passing
  regression set. That step MUST execute, with screenshots on record:
  - **J-01** — Microscope Readiness panel, shared-panel re-verify.
  - **J-02, J-03, J-04** — no dedicated UI surface of their own; re-verified via the same
    shared-panel check J-01 covers (iteration-2/3/4 precedent). Honest SKIP recorded for their OWN
    acceptance is fine; a SKIP of the shared-panel re-check is not.
  - **J-10** — the full `journey-scripts/J-10.json` 13-step kept-product sentinel, already repaired
    in iteration 3, re-run **unmodified** (Do-Not-Redo item — do not re-point it).
- A blanket SKIP across J-01/J-02/J-03/J-04/J-10 is not an acceptable outcome (TC-29). Only J-05
  itself records a SKIP, and it must be an explicit, individually-recorded one, not a side effect of
  the frontend flag.
- Clean-rebuild discipline still applies if any browser pass runs: `rm -rf apps/frontend/.next` +
  rebuild before evidence (T-9); no screenshot ⇒ `unknown`, never `passing` (T-10).

## Files to Create/Modify

- `apps/backend/app/research/micro_accessor.py` -- NEW: origin-fenced accessor, sole legal door.
- `apps/backend/app/research/micro_join.py` -- MODIFY: re-point line 416's `read_snapshot_rows`
  call through the accessor (byte-identical output).
- `apps/backend/app/research/scout.py` -- MODIFY: re-point line 343's `read_snapshot_rows` call
  through the accessor (byte-identical output).
- `apps/backend/app/research/walkforward.py` (+ its ledger module, naming per the scout precedent)
  -- NEW: fold spec, purge/embargo, Mode A/B, decay view, `WF_SURVIVOR_RULE_V1`,
  `WalkForwardComputeManager`, CLI entry point.
- `apps/backend/app/research/micro_routes.py` -- MODIFY: wire the 3 walkforward routes alongside
  the existing readiness/snapshots/scout ones (no new router file).
- `apps/backend/tests/test_micro_accessor.py` -- NEW: TC-1, TC-2, TC-3.
- `apps/backend/tests/test_walkforward.py` -- NEW: TC-6 through TC-19, TC-23 through TC-26.
- A dedicated TR-16 oracle test module + two synthetic fixture corpora -- NEW: TC-21, TC-22.
- `apps/backend/tests/test_scout.py`, `test_scout_ledger.py`, `test_micro_join.py` -- MODIFY: prove
  the accessor re-point is byte-identical (TC-4, TC-5).
- `docs/handoffs/goal-rapid-microscope-iter-5-dev.md` -- NEW: dev handoff (required by DoD),
  logging any interpretation calls explicitly (the iteration-4 handoff's own pattern) rather than
  silently deciding them.

Explicitly untouched (Do-Not-Redo / out of scope): `vault.py`, `tick_recorder.py`,
`micro_graduation.py` (none exist yet — not this iteration's job); `scout.py`'s screening logic,
ledger schema, or decisions beyond the one re-pointed call; any `docs/rapid-validation-spec.md` or
`blueprint.md` edit (both re-confirmed accurate for this scope); any §1 constant; any frontend file;
`journey-scripts/J-10.json` (reused unmodified).

## Key Test Scenarios

(Condensed from the phase spec's own TC-1…TC-29 — cross-reference there for exact wording.)

- **Accessor & re-point** — TC-1 origin-T read beyond T raises typed error, never empty/truncated;
  TC-2 a sealed fixture shard yields only opaque metadata/refusal, never rows; TC-3 the ast source-
  scan finds `read_snapshot_rows` imported nowhere but `micro_accessor.py`; TC-4/TC-5 re-pointing
  `micro_join.py`/`scout.py` changes zero served value (`playbook_signal_count==2`,
  `by_setup_id=={"range_trade":2}`; the iteration-4 fixture grid's `spec_hash`/`decision`/`reason`
  all byte-identical).
- **Fold spec & geometry** — TC-6 registered fields frozen verbatim, `clustering_unit` always
  `session_date` regardless of corpus size; TC-7 `step < test` refused; TC-10 a second geometry
  without a voiding event is refused, a voided corpus-era clears every survivor state.
- **Purge & embargo** — TC-8 a label planted across a fold boundary fails with a named
  purge-exactness error; TC-9 `embargo_sessions=0` accepted with derivation recorded when no
  cross-boundary dependency exists; the diagnostic run's own `embargo_sessions=5` recorded as ITS
  predeclared choice, never a universal rule.
- **Mode A/B & rule identity** — TC-11 same fitting-RULE string across origins stays one sequence,
  a changed rule string starts a new one; TC-12 spec-hash-then-reveal freeze order visible in the
  ledger; TC-13 a Mode B spec registered after a logged exposure entry for its window auto-classes
  `historical_exposed_diagnostic`; TC-14 the freshly initialized exposure registry already reads
  every playbook/legacy-tick window as exposed, before any serving act in the run.
- **Survivor rule & floors** — TC-15 `WF_SURVIVOR_RULE_V1` returns `walkforward_survivor` only when
  ALL FIVE conditions hold (≥3 sufficient `historical_oos`/`rule_process` folds; sign agreement
  ≥0.7; pooled effect ≥ econ floor in the registered direction; no sufficient fold survives the
  screen in the opposite direction; zero voiding events) — violate any ONE and it must not; TC-16
  a fold below `WF_FOLD_MIN_OBSERVATIONS`(30)/`WF_FOLD_MIN_SIGNAL_SESSIONS`(8)/`WF_FOLD_MIN_SYMBOLS`
  (2) reads `insufficient` with the failed arithmetic; TC-17 <`WF_MIN_SUFFICIENT_FOLDS`(3) sufficient
  folds refuses a sequence verdict; TC-20 the 11-session tick corpus returns the typed refusal
  naming `11 < 105`, never an empty report.
- **Class/process discipline** — TC-18 pooling a diagnostic fold with an OOS fold is refused, and
  the diagnostic fold independently contributes zero to any survivor tally; TC-19 a post-reveal
  operator selection is refused at `walkforward_survivor` and labeled `operator_process`; a
  pre-reveal registered shortlist keeps `rule_process` and stays eligible.
- **TR-16 oracles** — TC-21 the known-null corpus survives nothing, byte-identical on rerun; TC-22
  the planted-effect corpus recovers the planted sign within tolerance (mid-basis primary),
  byte-identical on rerun.
- **Diagnostic run** — TC-23 the real 155-session corpus under `DIAGNOSTIC_GEOMETRY` produces
  exactly 5 folds / 100 validation sessions, every one `historical_exposed_diagnostic`; TC-24 every
  diagnostic fold/sequence AND a synthetic `operator_process` sequence evaluate to not-a-survivor
  under `WF_SURVIVOR_RULE_V1` regardless of their own statistics.
- **Compute manager & ledger durability** — TC-25 a second `trigger()` while running returns
  `{"state":"refused","reason":"already_running"}`; a mid-run exception resolves to a terminal
  `"failed"` run-log entry, never a partial row; TC-26 deleting the newest committed row(s) directly
  from the JSONL is caught by the tail-anchor mismatch even though the truncated chain still
  verifies in-place.
- **Frozen foundations + suite** — TC-27 fingerprint/referee-hash/engine-byte-freeze/snapshot-row-
  total (`3,815,933`) all re-check clean; TC-28 `pytest tests/` (no extra `-q`) ≥ 2,949 pass / 8
  skip / 0 new failures.
- **Browser regression** — TC-29 J-01/J-02/J-03/J-04's shared-panel check and J-10's full sentinel
  all stay green with screenshots on record; J-05 records an individually-honest SKIP, never a
  blanket one (see MANDATORY browser regression section above).

## Carried-forward / explicitly not this iteration's job

- Two open owner rulings (the `micro_observer.py` one-quote-early `available_at` stamp at
  `micro_observer.py:636/657`; whether Scout's "variants tried" should also count per data-set) —
  human-owned, due before J-06, not invented here. Neither blocks J-05.
- The "approximately None bps" kill-message copy fix and `_PRICE_ARITHMETIC_FIELDS`/copy-discipline
  additions for new micro numerics — explicitly deferred to "before J-08 renders."
- B5 from the iteration-4 audit (whether Scout's `family_id` should include the corpus term) —
  conservative-direction deviation, left for the spec owner, not this iteration's fix.
- The disclosed real-corpus Scout runtime (minutes against the full 18-dataset corpus) — a cost
  question flagged for a possible future perf iteration before J-06's ~150-symbol-day corpus lands,
  not a blocker here.
