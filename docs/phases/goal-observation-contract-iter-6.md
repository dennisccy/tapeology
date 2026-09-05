# Goal Iteration 6 — Guards, regression sentinel, and closing the J-04/J-02 evidence gaps

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** observation-contract
- **Iteration:** 6
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — the iteration-5 evaluator verdict was ESCALATE, which mandates full depth for this iteration with no exception.
- **Frontend Present:** yes — zero frontend files change this iteration; per this era's own `docs/goal.md` Constraints ("if the engine escalates an iteration to full depth, the iteration spec sets `Frontend Present: yes` with the served JSON page as the browser surface and answers the UI-evolution audit 'no user-facing capability introduced'"), the served-JSON page at `/tape/{ticker}/observation` is declared as the browser surface for this iteration's UI-evolution audit, which answers: no user-facing capability introduced.
- **Target journeys:** J-04, J-06
- **Required-still-passing journeys:** J-01, J-02, J-03, J-05
- **Anti-goal reminders:**
  - "No logic of the form `if tape_state == X: trade = True`; no field, token or copy that reads as a trading action, readiness or verdict (READY, NO_TRADE, NO_VERDICT, `trade_allowed`, PENDING_CONDITION or any equivalent) anywhere in the artifact, the module, its tests or the spec's served surface."
  - "No consumer-specific business logic; no import of, or path reference to, Workstation, Trendora or TenSteps under `apps/` or in `docs/observation-contract-spec.md` (guard-enforced; `docs/goal.md`, `docs/phases/`, `docs/goal-archive/` and `project-extensions/host-guard/` are excluded from the scan)."
  - "No non-English identifier, schema name, enum value, field name, test name or persisted value in the contract."
  - "No mandatory journey or test that requires Alpaca, the network, credentials or market hours."
  - "No new UI page, panel, link, component or frontend file change; no new `Config` field; no named MCP tool; no CLI; no WebSocket embedding; no listing endpoint."
  - "No weakening of any existing guard: `test_no_execution_path.py`, `test_feed_basis.py`, `test_copy_discipline.py`, `test_profile_equivalence.py`, `test_fingerprint_epoch_retirement.py`, `test_mcp_server.py`, `test_stream_lifecycle.py`, `test_observer_equivalence.py` and `test_epoch_anchor.py` stay green and unedited except for additive registrations."
  - "No pooling, equating or silent conversion between `sim`, `iex` and `sip`."
  - "No Goal Mode workaround that edits, deletes, skips or xfails a guard merely to pass a journey."
  - "**Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations."
  - "**Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, and archived-era behavior stay byte-identical. New work is additive and versioned beside them, never a mutation of them."

## GOAL

Ship the era's final production surface — the guard suite and whole-product regression sentinel (J-06) — and, in the same full-depth QA pass, close the two browser-evidence gaps iteration 5 left open (J-04's paused-reload identity check and J-02's own numbered steps), so all six Observation Contract v1 journeys are provably, non-vacuously verified.

## BACKGROUND

Iteration 5 landed the route and moved J-01/J-02/J-03/J-05 to passing, but ESCALATEd: J-06 — Binding Execution Order's own final step — was never touched (its row was `DEFERRED-BUDGET`, and `iter-5/budget-breached` records the round ran out of time), and J-04's browser evidence for the paused-reload identity check was never captured because the deterministic replay lane cannot reach a backend-only path (proof: `J-01/J-03/J-04-verify.png` are one byte-identical 404 screenshot). J-04 requires no new code — its deterministic half (`tests/test_tape_observation_path_equivalence.py`, 6/6) has been green since iteration 4; only its served-JSON Acceptance clause is unmet, which is why it remains a formal Target journey (an unmet Acceptance clause of an active journey) rather than a rule-7 evidence-only pick on an already-passing one. Depth is full per the evaluator's binding, ESCALATE-triggered recommendation (Full trigger 3) — no exception applies, and the last coherence audit was COHERENCE-PASS so no consolidation is owed. Bundling J-04 with J-06 does not violate the "never bundle two risky journeys" rule: J-06's guard module is test-only and scans already-frozen code (no data-model change, no cross-cutting refactor), and J-04 carries zero code this round — one contained build plus one zero-code evidence capture, not two risky changes.

Lessons applied from `lessons.md` (see NOTES for the full list): the guard module named here (`test_tape_observation_guards.py`) is the exact file the iter-3 and iter-4 lessons both name as the tautological-summary-test risk to watch for; the iter-1 lesson on guard-forbidden imports applies if any of the five mechanisms below needs to cross-check an engine-owned vocabulary; and the iter-5 lessons on the replay-lane base-url bug and the two-browser-qa-dispatch evidence clobber both apply directly to this iteration's QA execution.

## IN SCOPE

### Backend
- [ ] New test module `apps/backend/tests/test_tape_observation_guards.py` (Binding Execution Order step 6), containing exactly five guard mechanisms, each shipping its own `test_counterexample_*` that perturbs the REAL scanned constant/module/artifact (never a second hand-written literal — see iter-3/iter-4 lessons):
  1. **Copy-discipline lexicon + compound-identifier ban** — reuse the EXISTING `find_violations` from `apps/backend/tests/test_copy_discipline.py:114` (do not reimplement or duplicate the lexicon scanner) over `apps/backend/app/observation_contract.py`'s source, the five existing `test_tape_observation_*.py` modules' source, and one live-served artifact instance (a real GET against a running backend, following the pattern already used in `test_tape_observation_route.py`), with comments/docstrings stripped and a documented `SELF` exclusion; plus a compound-identifier ban over the fixed list: `should_trade`, `trade_signal`, `entry_price`, `stop_loss`, `position_size`, `trade_allowed`, `READY`, `NO_TRADE`, `NO_VERDICT`, `PENDING_CONDITION`, `composite_policy`.
  2. **External-system reference guard** — `workstation` / `trendora` / `tensteps` absent, case-insensitive, under `apps/` and in `docs/observation-contract-spec.md`, excluding `docs/goal.md`, `docs/phases/`, `docs/goal-archive/`, `project-extensions/host-guard/`.
  3. **English-only guard** — over the observation schema's keys, enum values and module identifiers.
  4. **Real-provider isolation guard** — no `test_tape_observation_*` module reaches `AlpacaAdapter` except the environment-gated smoke test (skipped by default; its failure never fails the suite).
  5. **Mutator-call-site guard** — every `TapeEngine` mutator call under `app/` lives inside a `watch_manager.py` method that re-settles the observation pair, or inside `DatasetStore.replay`.
  (Required Trap Coverage items 40-45. Item 2 / "recompute guard" is NOT duplicated here — it already exists in iteration 1's `test_tape_observation_projection.py`; see the assumption logged this iteration.)
- [ ] No changes to any existing production module: `observation_contract.py`, `watch_manager.py`, `main.py`, `config.py`, `app/engine/*`, `mcp/__init__.py` all stay byte-identical (this iteration is test-only).
- [ ] No changes to any of the nine protected guard test files.

### Frontend
None. Zero frontend files change this era (era Constraint, restated in Anti-goal reminders above).

### New user-facing capability
None. Per this era's Design Direction, "no visual change this era" — Cockpit `/`, `/structure` and `/desk` render exactly as before. This iteration's browser surface (declared for the UI-evolution audit per Frontend Present above) is the already-shipped served JSON at `/tape/{ticker}/observation`; the audit answer is "no user-facing capability introduced."

### New information displayed
None. All four `TapeObservation` v1 field groups were already registered in the Data Contract and marked served as of iteration 5.

### New user actions
None. No new button, form or control anywhere.

### UI surface changes
None. `/`, `/structure` and `/desk` are only re-verified (regression), never modified.

### Product surface delta
None beyond what iteration 5 already shipped. This iteration adds proof (guards + whole-product regression) and closes two evidence gaps; it introduces no new externally observable behavior.

### Blueprint conformance
No new surfaces. All four Data Contract rows (machine observation semantics; provenance/source/lifecycle metadata; explanatory metadata; integrity) and the Information Architecture's one machine-only route were already registered and marked served at iteration 5 (`runs/goal-session-observation-contract/state/blueprint.md`). This iteration adds guards and regression proof over that same, unchanged surface — no blueprint edit is needed this round.

### Data-contract additions
None.

## OUT OF SCOPE

- Any change to `apps/frontend/` (zero files; era Constraint).
- Any change to `apps/backend/app/engine/`, `config.py`, `observation_contract.py`, `watch_manager.py`, `main.py`, or `mcp/__init__.py` — all complete and frozen since iteration 5 ("Do not redo").
- Any change to the nine protected guard files beyond additive registration (none is anticipated this round).
- Reimplementing the copy-discipline lexicon scanner — reuse the existing `find_violations` (`apps/backend/tests/test_copy_discipline.py:114`); a second scanner would itself be a single-source-of-truth violation.
- Fixing `scripts/automation/lib/demo_runner.py`'s `normalize_url` / `scripts/automation/lib/replay-lane.sh`'s `--base-url` wiring for backend-only paths. This is test-harness/framework tooling, not an `apps/backend` or `apps/frontend` change, and it is outside `docs/goal.md` Key Capabilities (flagged as scope creep, excluded). The standing workaround already proven correct at iteration 5 — the mass-false-FAIL breaker voids the replay lane's false failures, and the LLM browser-qa lane covers the real check — is used again this round (see TESTING REQUIREMENTS). Left as a human/framework-maintenance follow-up outside this session.
- Regenerating deterministic golden-replay scripts for J-01/J-03/J-04/J-05 while the harness still resolves every `goto` onto the frontend origin — a golden script for a path the tool cannot reach is worse than none (iter-5 lesson). `state/goldens-regen-pending` and `state/golden-gaps` stay queued, not actioned, this iteration.
- Any new `Config` field, named MCP tool, CLI, WebSocket embedding, or listing endpoint.
- Any real-provider (Alpaca) network call in a mandatory test.
- Widening any gate, sample-size minimum, or hold-out rule (not touched by this iteration's surface; restated for completeness per the immutable rails).

## DEFINITION OF DONE

- [ ] J-06 passes via browser-qa-agent + deterministic suite: `apps/backend/tests/test_tape_observation_guards.py` exists with all five guard mechanisms green, each with a non-vacuous `test_counterexample_*`; full backend suite green (0 failed); `apps/frontend` `tsc --noEmit` reports 0 errors; `config_fingerprint` reads `08e471b10130e1e2`; `/`, `/structure` and `/desk` each render with no new panel, link or control.
- [ ] J-04 passes via browser-qa-agent: two reloads of the paused `/tape/SIM-BIDABS/observation` show an identical `observation_hash` and differing `generated_at_utc` / `artifact_hash` values, each reload screenshotted.
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-05 remain green — verified via the LLM browser-qa lane against the backend origin (deterministic replay cannot reach `/tape/*`; its expected false-FAILs on these four are voided by the same mass-false-FAIL breaker iteration 5 validated, never treated as a real regression). J-02 is verified via its OWN numbered browser steps this round, not a screenshot borrowed from J-01's test id (closes the open item in `state/assumptions.md`, iter-5).
- [ ] No anti-goal violation introduced: ledger stays at 0 total / 0 resolved / 0 unresolved_blocking / 0 unresolved_non_blocking / 0 unresolved_critical; none of the nine protected guard files modified; zero files under `apps/frontend/`; no new `Config` field.
- [ ] Unit tests pass; no regressions: full backend suite reports 0 failed, 8 skipped, and a pass count equal to the prior 4044 plus the number of new tests in `test_tape_observation_guards.py`.
- [ ] Dev handoff written at `docs/handoffs/goal-observation-contract-iter-6-dev.md`.

## TESTING REQUIREMENTS

- Browser (LLM browser-qa lane against the backend origin — NOT deterministic replay, which cannot reach these paths):
  - J-06: watch `SIM-BIDABS` from `/` to `live`, confirm `/tape/SIM-BIDABS/observation` serves the JSON, then visit `/structure` and `/desk` and confirm each renders with no new panel/link/control.
  - J-04: watch `SIM-BIDABS` to `live`, press Pause, reload `/tape/SIM-BIDABS/observation` twice, screenshot each reload, compare `observation_hash` / `generated_at_utc` / `artifact_hash` across the two.
  - J-02 (own steps, not borrowed evidence): watch `SIM-BIDABS` to `live`, open `/tape/SIM-BIDABS/observation`, independently read and record `observed_at_utc`, `available_at_utc`, `availability_basis`, `timing.settled_at_utc` and `generated_at_utc`.
  - Regression smoke: J-01, J-03, J-05 same lane, same served-JSON pattern as iteration 5.
- Unit/integration:
  - `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_guards.py -q` (new — record the pass count; this venv's pytest prints no final summary line, so tally `-q` progress or per-file collect counts, per the iter-0 lesson).
  - `cd apps/backend && .venv/bin/python -m pytest tests/ -q` (full suite; if the historically-flaky `test_tr31_format_cli_progress_line_serves_only_the_whitelisted_aggregates` fails, re-run once before treating it as a regression — iter-2 lesson).
  - `cd apps/frontend && npx tsc --noEmit`.
- Error cases:
  - Each of the five guard mechanisms' `test_counterexample_*` must perturb the REAL scanned constant/module/artifact instance (not a second hand-written literal) and prove the scan/guard reports the violation.
  - The real-provider isolation guard's counter-test must demonstrate detection of a test module that reaches `AlpacaAdapter` outside the gated smoke test.
  - The mutator-call-site guard's counter-test must demonstrate detection of a `TapeEngine` mutator call placed outside `watch_manager.py`'s re-settling methods and outside `DatasetStore.replay`.

Test-first contract:

- TC-1: given `apps/backend/app/observation_contract.py`'s source, the five existing `test_tape_observation_*.py` modules' source, and one live-served `/tape/{ticker}/observation` artifact instance, when `test_tape_observation_guards.py`'s copy-discipline + compound-identifier check runs (`find_violations` reused from `test_copy_discipline.py`, comments/docstrings stripped, `SELF` excluded), then it reports zero violations across all three scanned texts.
- TC-2: given the same scanned texts, when a `test_counterexample_*` injects one banned compound identifier (e.g. `trade_allowed`) into a temporary copy of one of them, then the same scan reports at least one violation.
- TC-3: given `apps/` and `docs/observation-contract-spec.md` (excluding `docs/goal.md`, `docs/phases/`, `docs/goal-archive/`, `project-extensions/host-guard/`), when the external-system reference guard scans them case-insensitively for `workstation`, `trendora`, `tensteps`, then it reports zero matches.
- TC-4: given the same scan, when a `test_counterexample_*` inserts one of those tokens into a temporary copy of a scanned file, then the scan reports at least one match.
- TC-5: given the observation schema's keys, enum values and module identifiers, when the English-only guard scans them, then it reports zero non-English/non-ASCII matches.
- TC-6: given the same scan, when a `test_counterexample_*` injects one non-English character into a temporary copy of a scanned value, then the scan reports at least one match.
- TC-7: given every test module named `test_tape_observation_*`, when the real-provider isolation guard scans their import/call graph for `AlpacaAdapter`, then it reports zero reachable references outside the environment-gated smoke test.
- TC-8: given the same scan, when a `test_counterexample_*` adds a reference to `AlpacaAdapter` inside a temporary copy of a non-gated `test_tape_observation_*` module, then the scan reports it as a violation.
- TC-9: given every `TapeEngine` mutator call site under `app/`, when the mutator-call-site guard scans them, then it reports each one as located inside a `watch_manager.py` re-settling method or `DatasetStore.replay`, with zero call sites elsewhere.
- TC-10: given the same scan, when a `test_counterexample_*` places a mutator call in a temporary module outside those two locations, then the scan reports it as a violation.
- TC-11: given `SIM-BIDABS` watched to `live` from `/`, when the browser opens `/tape/SIM-BIDABS/observation`, then the page renders the full JSON artifact body (not a "Not Found" or 404 body).
- TC-12: given `SIM-BIDABS` watched and then paused, when the browser reloads `/tape/SIM-BIDABS/observation` twice in succession, then both loads show an identical `observation_hash` value while `generated_at_utc` and `artifact_hash` differ between the two loads.
- TC-13: given `SIM-BIDABS` watched to `live`, when the browser opens `/tape/SIM-BIDABS/observation` and reads it for J-02's own numbered steps, then `observed_at_utc`, `available_at_utc`, `availability_basis`, `timing.settled_at_utc` and `generated_at_utc` are each independently legible and recorded under J-02's own evidence, not a screenshot filed under another journey's test id.
- TC-14: given `SIM-BIDABS` watched to `live`, when the browser visits `/structure` then `/desk`, then each page renders its pre-era content with no new panel, link or control.
- TC-15: given the full backend suite (`cd apps/backend && .venv/bin/python -m pytest tests/ -q`), when it completes, then it reports 0 failed, 8 skipped, and a pass count equal to 4044 plus the new guard-module test count, exit code 0.
- TC-16: given the frontend compile check (`cd apps/frontend && npx tsc --noEmit`), when it completes, then it reports 0 errors.
- TC-17: given the backend process, when `Config.config_fingerprint()` is read, then it equals `08e471b10130e1e2`.
- TC-18: given the full iteration diff, when the nine protected guard files and `apps/frontend/` are inspected, then none of the nine is modified and zero files under `apps/frontend/` appear, and no field is added to `apps/backend/app/config.py`.
- TC-19: given the iteration completes, when `docs/handoffs/goal-observation-contract-iter-6-dev.md` is read, then it exists and lists every file this iteration touched.

## NOTES

Lessons applied from `runs/goal-session-observation-contract/state/lessons.md`:
- (iter-3, iter-4) `test_tape_observation_guards.py` is the file both lessons name directly as the tautological-summary-test risk: every one of the five mechanisms' non-vacuous proof depends on its counter-test perturbing the REAL scanned constant/module/artifact, never a second hand-written copy. Reflected in TC-2/4/6/8/10 above and the IN SCOPE bullet's parenthetical.
- (iter-1) If any of the five mechanisms needs to cross-check an engine-owned vocabulary or enum that a recompute-style guard forbids `observation_contract.py` from importing directly, put that cross-check in the TEST module (unrestricted), not by weakening the guard or importing anyway.
- (iter-0) This venv's pytest (9.1.1) prints no final "N passed" summary line; tally `-q` progress or per-file `--collect-only -q` counts instead of grepping for a summary line that never appears.
- (iter-2) `test_tr31_format_cli_progress_line_serves_only_the_whitelisted_aggregates` is a known time-dependent flake; a single failure there is not a regression signal on its own — re-run before treating it as one.
- (iter-5, tooling) The deterministic replay lane cannot reach a backend-only URL (`normalize_url` rewrites even absolute `:8301` URLs onto the frontend origin). Expect false-FAILs on J-01/J-03/J-05's (and now J-04's) replay rows this round too; they should be voided by the same mass-false-FAIL breaker iteration 5 validated, with the LLM browser-qa lane carrying the real verification. Do not treat those false-FAILs as product regressions.
- (iter-5, process) If more than one browser-qa dispatch runs this iteration, check for a `.canary.md` sibling before trusting a merged `ui-test-results.md` that shows unexpected SKIPs — a second dispatch can silently overwrite the first's evidence file.
- (iter-5, budget) `runs/goal-session-observation-contract/iter-5/budget-breached` is set — that round ran out of time before reaching J-06 at all. Prioritize the guard module and whole-product recheck (the substantive, currently-unbuilt work) first; the J-04/J-02 evidence capture is real but secondary work that should not crowd out J-06 if time is again tight.

This is expected to be the era's final iteration if all six journeys close clean: `docs/goal.md`'s Completion / Honest Stop section lists no further required work beyond J-01…J-06 passing, `config_fingerprint` pinned, the MCP contract unchanged, and zero open anti-goal dispositions — all of which this iteration's Definition of Done directly targets.
