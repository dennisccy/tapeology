# goal-observation-contract-iter-6 Execution Plan

Era: Observation Contract v1 (`docs/goal.md`, session `observation-contract`). This is expected to be
the era's final iteration if J-01...J-06 all close clean (see `docs/goal.md` "Completion / Honest Stop").
Full depth is mandatory (evaluator ESCALATEd iteration 5 — Full trigger 3, no exception).

## What to Build

This iteration is **test-only** (Binding Execution Order step 6) plus two **evidence-only** browser
captures. No production module changes.

1. New test module `apps/backend/tests/test_tape_observation_guards.py` containing exactly **five**
   guard mechanisms (Required Trap Coverage items 40-45; item 2 "recompute guard" is intentionally
   NOT a sixth mechanism here — it already lives in iteration 1's `test_tape_observation_projection.py`
   and must not be duplicated):
   1. **Copy-discipline + compound-identifier ban** — reuse the existing `find_violations`
      (`apps/backend/tests/test_copy_discipline.py:114`, confirmed present) over: (a)
      `apps/backend/app/observation_contract.py` source, (b) the five existing
      `test_tape_observation_{lifecycle_feed,path_equivalence,projection,route,time}.py` modules'
      source, and (c) one **live-served** `/tape/{ticker}/observation` artifact instance (real GET
      against a running backend — follow the real-uvicorn-subprocess fixture pattern
      `test_tape_observation_route.py` already established for `test_mcp_get_endpoint_bytes_equal...`,
      do not use TestClient-only for this leg). Strip comments/docstrings, document a `SELF` exclusion.
      Add a fixed-list compound-identifier ban: `should_trade`, `trade_signal`, `entry_price`,
      `stop_loss`, `position_size`, `trade_allowed`, `READY`, `NO_TRADE`, `NO_VERDICT`,
      `PENDING_CONDITION`, `composite_policy`.
   2. **External-system reference guard** — `workstation`/`trendora`/`tensteps` absent, case-insensitive,
      under `apps/` and in `docs/observation-contract-spec.md`; exclude `docs/goal.md`, `docs/phases/`,
      `docs/goal-archive/`, `project-extensions/host-guard/`.
   3. **English-only guard** — over the observation schema's keys, enum values and module identifiers.
   4. **Real-provider isolation guard** — no `test_tape_observation_*` module reaches `AlpacaAdapter`
      except the environment-gated smoke test (skipped by default, its failure never fails the suite).
   5. **Mutator-call-site guard** — every `TapeEngine` mutator call under `app/` is inside a
      `watch_manager.py` method that re-settles the observation pair, or inside `DatasetStore.replay`.

   **Non-negotiable pattern (iter-3 + iter-4 lessons, repeated failure mode):** each mechanism's
   `test_counterexample_*` must perturb the REAL scanned constant/module/artifact (monkeypatch the real
   attribute, or scan a temp-file copy of the real source/artifact) — never compare against a second
   hand-written literal. This file is explicitly named by two prior lessons as the tautological-summary-test
   risk to avoid.

2. Close the J-04 browser-evidence gap (zero code — deterministic half has been green since iteration 4):
   watch `SIM-BIDABS` to `live`, Pause, reload `/tape/SIM-BIDABS/observation` twice, screenshot each
   reload, confirm identical `observation_hash` and differing `generated_at_utc`/`artifact_hash` across
   the two. File both screenshots under J-04's own evidence (iter-5 left this as one byte-identical 404
   screenshot because the deterministic replay lane cannot reach a backend-only path — this round uses
   the LLM browser-qa lane against the backend origin, not replay).

3. Close the J-02 evidence gap: J-02 must be verified via its OWN numbered browser steps this round —
   watch `SIM-BIDABS` to `live`, open the observation JSON, independently read and record
   `observed_at_utc`, `available_at_utc`, `availability_basis`, `timing.settled_at_utc`,
   `generated_at_utc`. Do not reuse a screenshot filed under J-01's test id (open item logged in
   `runs/goal-session-observation-contract/state/assumptions.md`, iter-5).

4. Regression smoke for J-01, J-03, J-05 (LLM browser-qa lane, backend origin, same served-JSON pattern
   as iteration 5) plus the whole-product sentinel: `/`, `/structure`, `/desk` each load with no new
   panel/link/control; full backend suite green; `tsc --noEmit` 0 errors; `config_fingerprint` still
   `08e471b10130e1e2`; MCP contract unchanged (v8, 28 tools); the nine protected guard tests and every
   existing classifier/profile/determinism/observer/epoch-anchor/lifecycle/feed-basis suite green and
   unedited.

5. Dev handoff at `docs/handoffs/goal-observation-contract-iter-6-dev.md` listing every file touched.

**Priority if time is tight (iter-5 lesson — that round hit `budget-breached` before ever reaching J-06):
build the guard module and get the whole-suite regression green FIRST. The J-04/J-02 evidence capture is
real required work but must not crowd out J-06.**

## Agents Required

- backend-data: yes -- write `apps/backend/tests/test_tape_observation_guards.py` (new test module, all
  five mechanisms + five `test_counterexample_*`), run the full backend suite + the new module in
  isolation, confirm `tsc --noEmit` and `config_fingerprint` unaffected, write the dev handoff. No
  production module is touched (`observation_contract.py`, `watch_manager.py`, `main.py`, `config.py`,
  `app/engine/*`, `mcp/__init__.py` all stay byte-identical this iteration — confirm via inspection, not
  just intent).
- frontend-ux: no -- zero frontend files change this era (Constraint, restated in this iteration's
  Anti-goal reminders). The J-04/J-02 evidence work is browser-QA evidence capture against already-shipped
  served JSON, not frontend development.

## Frontend Present
Frontend Present: yes

Rationale (per this iteration's own Goal Mode Metadata and `docs/goal.md` Constraints): zero frontend
files change, but because this iteration is escalated to full depth, the served-JSON page at
`/tape/{ticker}/observation` (backend origin, not the Next.js frontend) is declared as the browser
surface for the UI-evolution audit. The audit answer is fixed: **no user-facing capability introduced.**
Browser QA this iteration means the LLM browser-qa lane opening backend-served JSON URLs directly
(`http://localhost:8301/tape/SIM-BIDABS/observation` per the repo's deterministic port convention) plus
spot-checking `/`, `/structure`, `/desk` on the frontend for "unchanged" — not exercising any new UI
component.

## Files to Create/Modify

- `apps/backend/tests/test_tape_observation_guards.py` -- new, the five guard mechanisms + counter-tests.
- `docs/handoffs/goal-observation-contract-iter-6-dev.md` -- new, dev handoff.
- No other file under `apps/backend/app/` or `apps/frontend/` should change. If implementation genuinely
  requires touching one of the nine protected guard files, it must be additive registration only (e.g.
  registering a new fixture path), never an edit to existing assertions.
- Do NOT modify: `apps/backend/app/observation_contract.py`, `watch_manager.py`, `main.py`, `config.py`,
  `app/engine/*`, `mcp/__init__.py`, or any of the nine protected guard files (`test_no_execution_path.py`,
  `test_feed_basis.py`, `test_copy_discipline.py`, `test_profile_equivalence.py`,
  `test_fingerprint_epoch_retirement.py`, `test_mcp_server.py`, `test_stream_lifecycle.py`,
  `test_observer_equivalence.py`, `test_epoch_anchor.py`).
- Do NOT reimplement the copy-discipline lexicon scanner — import/reuse `find_violations` from
  `test_copy_discipline.py`; a second scanner is itself a single-source-of-truth violation.

## UI Evolution (Frontend Present: yes)

- New user-facing capability: **none.** `/`, `/structure`, `/desk` render exactly as before.
- New information displayed: **none.** All `TapeObservation` v1 fields were already registered and
  marked served as of iteration 5.
- New user actions: **none.**
- UI surface changes: **none** — only re-verification (regression), never modification.
- Navigation changes: **none.**
- This iteration's only "browser surface" is the pre-existing served JSON at
  `/tape/{ticker}/observation` on the backend origin, being re-read for evidence purposes (J-04 identity
  check, J-02 own-steps reading), not a product surface change.

## Visual Requirements (Frontend Present: yes)

Not applicable in the normal design sense. There is no component, layout or visual-effect work this
iteration: the "surface" being verified is raw served JSON text on the backend origin, and the three
existing frontend pages (`/`, `/structure`, `/desk`) are checked only for "renders exactly as before, no
new panel/link/control" — no new component library usage, no new layout, no new states (loading/empty/
error) to design. Browser QA should screenshot the raw JSON responses as evidence, not a styled page.

## Key Test Scenarios

- All five guard mechanisms in `test_tape_observation_guards.py` pass, and each has a
  `test_counterexample_*` that demonstrably fails when the mechanism is disabled/bypassed — proven
  against the real scanned artifact, never a second literal.
- Mechanism 1's `find_violations` scan runs against a REAL live-served artifact (real GET against a
  running backend), not just static source.
- Mechanism 4's counter-test shows a `test_tape_observation_*`-named module reaching `AlpacaAdapter`
  outside the gated smoke test is detected.
- Mechanism 5's counter-test shows a `TapeEngine` mutator call placed outside `watch_manager.py`'s
  re-settling methods and outside `DatasetStore.replay` is detected.
- Full backend suite (`cd apps/backend && .venv/bin/python -m pytest tests/ -q`): 0 failed, 8 skipped,
  pass count = 4044 (iter-5 baseline) + new guard-module test count. (This venv's pytest prints no final
  summary line — tally `-q` progress characters or `--collect-only -q` per-file counts, per the iter-0
  lesson. If `test_tr31_format_cli_progress_line_serves_only_the_whitelisted_aggregates` fails, re-run
  once before treating it as a regression — known iter-2 flake.)
- `cd apps/frontend && npx tsc --noEmit` -- 0 errors.
- `Config.config_fingerprint()` reads `08e471b10130e1e2`.
- Browser (LLM lane against the backend origin, NOT deterministic replay):
  - J-06: watch `SIM-BIDABS` to `live`, confirm the observation JSON serves, then visit `/structure` and
    `/desk` and confirm each renders with no new panel/link/control.
  - J-04: watch to `live`, Pause, reload the observation JSON twice, screenshot both, confirm identical
    `observation_hash` and different `generated_at_utc`/`artifact_hash`.
  - J-02 (own steps): watch to `live`, open the observation JSON, independently record
    `observed_at_utc`, `available_at_utc`, `availability_basis`, `timing.settled_at_utc`,
    `generated_at_utc`.
  - Regression smoke: J-01, J-03, J-05 same lane, same served-JSON pattern as iteration 5.
- Anti-goal ledger stays at 0/0/0/0 (total/resolved/unresolved_blocking/unresolved_non_blocking); zero
  files under `apps/frontend/`; no new `Config` field; none of the nine protected guard files modified.
- Dev handoff exists at `docs/handoffs/goal-observation-contract-iter-6-dev.md` and lists every file
  touched.

## Notes / Lessons Carried Forward (do not relearn these)

- **Tautological-summary-test risk** (iter-3, iter-4): this exact file is named by both lessons. Every
  counter-test must perturb the real scanned subject, never a hand-written duplicate.
- **No final pytest summary line** (iter-0): this venv's pytest (9.1.1) prints none; tally progress
  characters or `--collect-only -q`.
- **Known flake** (iter-2): `test_tr31_format_cli_progress_line_serves_only_the_whitelisted_aggregates`
  — re-run once before calling it a regression.
- **Deterministic replay lane cannot reach `/tape/*`** (iter-5, tooling): `normalize_url` rewrites even
  absolute `:8301` URLs onto the frontend origin. Expect false-FAILs on J-01/J-03/J-04/J-05 replay rows;
  they are voided by the same mass-false-FAIL breaker iteration 5 validated. The LLM browser-qa lane
  against the backend origin is the real verification — do not treat replay false-FAILs as product
  regressions, and do not attempt to fix `demo_runner.py`/`replay-lane.sh` (explicitly out of scope —
  framework tooling, not `apps/backend` or `apps/frontend`).
- **Evidence-clobber risk** (iter-5, process): if more than one browser-qa dispatch runs this iteration,
  check for a `.canary.md` sibling before trusting a merged `ui-test-results.md` that shows unexpected
  SKIPs — a second dispatch can silently overwrite the first's evidence file.
- **Cross-check an engine-owned vocabulary from the TEST module, not the guard module** (iter-1): if any
  mechanism needs to reference an engine-owned enum/vocabulary that a recompute-style guard forbids
  `observation_contract.py` from importing directly, put that cross-check in the test module (tests are
  unrestricted), never weaken the guard or import anyway.

## Scope Guardrails (explicitly out of scope this iteration)

- Any change to `apps/frontend/`.
- Any change to `apps/backend/app/engine/`, `config.py`, `observation_contract.py`, `watch_manager.py`,
  `main.py`, `mcp/__init__.py` -- complete and frozen since iteration 5.
- Any edit to the nine protected guard files beyond additive registration.
- Reimplementing the copy-discipline lexicon scanner.
- Fixing `demo_runner.py`'s `normalize_url` or `replay-lane.sh`'s `--base-url` wiring for backend-only
  paths -- framework tooling, not in `docs/goal.md` Key Capabilities; the iter-5 mass-false-FAIL-breaker
  workaround is used again this round.
- Regenerating deterministic golden-replay scripts for J-01/J-03/J-04/J-05 while the harness still
  resolves every `goto` onto the frontend origin.
- Any new `Config` field, named MCP tool, CLI, WebSocket embedding, or listing endpoint.
- Any real-provider (Alpaca) network call in a mandatory test.
- Widening any gate, sample-size minimum, or hold-out rule.

No drift from `docs/goal.md` was found: this iteration directly implements Key Capability 8 ("Guard
suite") and Required Trap Coverage items 40-45, and closes two already-defined J-04/J-02 Acceptance
clauses with evidence rather than new contract surface. If all six journeys close clean this round, no
further work is defined beyond J-01...J-06 passing per the goal's own "Completion / Honest Stop" section.
