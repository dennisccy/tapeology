# goal-referee-iter-13 Dev Handoff

**Phase:** goal-referee-iter-13 (Era 6 "The Referee", J-12 — the readiness fold gets its reader)
**Date:** 2026-08-16
**Agent:** developer
**Status:** complete

## What Was Built

J-12 gives `GET /research/desk/referee/evidence` (owner `app/research/referee_evidence.py`,
registered since J-01/iteration-1) its first-ever direct UI reader. It is a **frontend-only**
iteration — zero backend production diff, zero new Data Contract row, zero new field, zero new
MCP tool. Every value the new UI renders is a straight pass-through of the already-served body.

- **`apps/frontend/lib/api.ts`** — new `fetchRefereeEvidence()`, `GET
  ${API_BASE}/research/desk/referee/evidence`, mirroring `fetchRefereeShortlist`/
  `fetchRefereeRegistry`'s exact `{ok, data, error?}` shape, `detail`-surfacing fallback, and
  `"Backend unreachable — is the API running?"` catch-branch message verbatim.

- **`apps/frontend/lib/types.ts`** — new `RefereeEvidenceResponse` (+ `RefereePlaybookOccurrenceReadiness`,
  `RefereeStrategyTradeReadiness`, `RefereeEvidencePerSetupSideCell`, `RefereeEvidenceStaleBasisDate`),
  matching `referee_evidence()`'s served shape field-for-field. One deliberate correction against
  the iter spec's own Data-Contract shorthand: `integrity_errors` on this endpoint is **not**
  `[string, ...]` as the spec's paraphrase stated — tracing `referee_evidence()` →
  `playbook_occurrence_readiness()`/`strategy_trade_readiness()` → `PlaybookStore.list()`/
  `DatasetStore.list()` in the live source shows both `errors` lists are actually
  `[{"file": str, "error": str}, ...]` (unchanged, passed straight through with no
  transformation). Typed as the plain `{ file: string; error: string }[]` shape this codebase
  already uses at 9+ other single-store call sites (`DeskTopupRunsListResult` et al.) — not the
  registry/adjudications' `RefereeIntegrityError[]`, which carries an extra `store` label because
  those endpoints aggregate errors across four stores; `referee_evidence()`'s two blocks each read
  exactly one store, so no disambiguator is needed.

- **`apps/frontend/app/desk/page.tsx`**
  - New `refereeEvidenceResult` state, mirroring `refereeShortlistResult`/`refereeRegistryResult`.
  - `toggleSection`'s existing `"refereeRegistry"` branch gains a third call,
    `fetchRefereeEvidence().then(setRefereeEvidenceResult)` — no new branch, no new `useEffect`
    (`test_desk_refresh_chain_guard.py::_EXPECTED_EFFECT_COUNT` stays `21`, confirmed unedited and
    passing).
  - `RefereeRegistrySection` gains an `evidenceResult` prop, passed through from the call site,
    and renders a new `RefereeEvidenceReadinessSection` directly below the shipped Registered
    Hypotheses table.
  - New `RefereeEvidenceReadinessSection` component: its own Loading/Unavailable states
    (independent of `shortlistResult`/`registryResult` — the `RefereeAdjudicationsSection`
    precedent, so a slow/failed evidence fetch never blocks the already-shipped shortlist/
    hypotheses tables from rendering). Two dense text/table blocks, no cards/gauges:
    - **Playbook Family** (`data-testid="referee-evidence-playbook-block"`): `records`,
      `distinct_sessions`, `signals_at_current_basis` in a table; `detector_basis` +
      `config_fingerprint` identity line; `stale_basis_dates` list (or the shipped `EmptyState`
      component, "No stale basis dates."); `integrity_errors` list (or `EmptyState`, "No
      integrity errors.").
    - **Strategy Family** (`data-testid="referee-evidence-strategy-block"`): `dataset_count`,
      `per_split_counts.train`/`.holdout`, `trade_count` in a table; `tick_gate_statement`
      rendered verbatim; every `basis_caveats` entry rendered verbatim (today the one Card-6.4
      forming-bar caveat); `integrity_errors` list (or `EmptyState`).
    - All new headings ("Evidence Readiness", "Playbook Family", "Strategy Family") and
      `data-testid`s — confirmed unique via grep against the whole frontend tree before use; none
      reuse a shipped heading or testid (T-11).

- **`runs/goal-session-referee/journey-scripts/J-12.json`** — new deterministic replay script,
  same minimal schema as `J-11.json` (`schema_version`/`journey`/`name`/`default_timeout_ms`/
  `steps` with `goto`/`click`/`expect` only): `goto /desk` → `click`
  `desk-section-expand-refereeRegistry` → `expect` "Strategy Family" (a new, non-shipped heading
  unique to this iteration, matching TC-17's literal wording and the J-11 precedent of expecting a
  stable static heading rather than a dynamic served value). This one file satisfies both Frontend
  scope bullets (the "demo-narrator walkthrough step list" and the "journey-scripts/J-12.json for
  future deterministic regression replay") — the demo-narrator agent's own richer schema (`title`/
  `narration`/`point_out`/`section`/`new`/`verified` fields, per
  `incredible_auto_dev/agents/demo-narrator/body.md`) is a separate artifact this lean-depth
  iteration does not dispatch (per Out of Scope: "Lean depth dispatches no demo step"); J-11.json
  itself never carried that richer schema either, confirming this minimal shape is what "modeled
  on J-11.json's shape" asked for.

- **Backend (tests only — zero production diff)**
  - `tests/test_desk_ui_guards.py`: `_PRICE_ARITHMETIC_FIELDS` widened with
    `evidence.playbook_occurrence.(records|distinct_sessions|signals_at_current_basis)`,
    `evidence.strategy_trade.(dataset_count|trade_count)`, and
    `evidence.strategy_trade.per_split_counts.(train|holdout)` — the exact binding names the new
    component uses. New counter-test
    `test_desk_page_price_arithmetic_guard_catches_referee_evidence_arithmetic` seeds four
    violations (one per new field group) and proves the widened pattern catches all of them.
  - `tests/test_referee_evidence.py`: two new proofs (placed here rather than
    `test_referee_registry.py` — this file already imports `REFEREE_FORMING_BAR_BASIS_CAVEAT` and
    already tests `tick_gate_statement`'s copy-discipline, so it already "owns this shape"):
    1. `test_referee_evidence_served_body_matches_the_pinned_golden_fixture` — a byte-identity
       check: plants one playbook record, one dataset, one backtest through each store's own
       public write path, then asserts the **full** `GET /research/desk/referee/evidence` response
       dict against a hand-computed literal (every key, both blocks). Only `tick_gate_statement`
       is derived through the module's own `_tick_gate_state()` helper rather than hand-retyped
       (its exact wording is already locked down by two other existing tests); everything else is
       a hardcoded expectation, so any future accidental edit to `referee_evidence.py` breaks this
       test immediately.
    2. `test_tick_gate_statement_and_forming_bar_caveat_are_unowned_frontend_literals` +
       its counter-test — mirrors the iteration-9 `REFEREE_STARTER_FAMILY_ID`/`_Q` unowned-literal
       guard (`test_referee_registry.py` TC-17): greps every `apps/frontend/{components,app}/**/*.tsx`,
       `**/*.ts`, `lib/**/*.ts` file (the same root/glob set `test_copy_discipline.py`'s own
       frontend scan uses) for the tick-gate statement's invariant substring
       ("Era-6 tick-corpus gate", present in both the met/unmet branches) and for
       `REFEREE_FORMING_BAR_BASIS_CAVEAT`'s full text. Both are absent — confirmed by running this
       guard against the real, now-modified frontend tree.
  - Confirmed, not edited: `test_desk_refresh_chain_guard.py::_EXPECTED_EFFECT_COUNT` stays `21`;
    `test_copy_discipline.py` stays green with the new copy included (it already globs
    `app/**/*.tsx`/`lib/**/*.ts`); `test_mcp_server.py::EXPECTED_TOOLS` stays exactly 22 names.

## Files Changed

- `apps/frontend/lib/api.ts` -- `fetchRefereeEvidence()`.
- `apps/frontend/lib/types.ts` -- `RefereeEvidenceResponse` + 4 nested interfaces.
- `apps/frontend/app/desk/page.tsx` -- `refereeEvidenceResult` state; `toggleSection` extension;
  `RefereeRegistrySection` gains `evidenceResult` prop + call-site wiring; new
  `RefereeEvidenceReadinessSection` component.
- `apps/backend/tests/test_desk_ui_guards.py` -- `_PRICE_ARITHMETIC_FIELDS` widened + 1 new
  counter-test.
- `apps/backend/tests/test_referee_evidence.py` -- 1 golden byte-identity test + 1 unowned-literal
  guard test + its counter-test (3 new tests).
- `runs/goal-session-referee/journey-scripts/J-12.json` -- new deterministic replay script.
- `runs/goal-referee-iter-13/status.json` -- new, `current_step: dev_complete`.

Not touched (verified byte-identical, see Tests Run): every `app/research/referee_*.py` module,
`desk_playbook*.py`, `desk_forward.py`, `levels.py`, `tradability.py`, `pnl_scan.py` (`git diff
--stat` on all of them together is empty). `runs/goal-session-referee/state/blueprint.md` and
`state/assumptions.md` already carried the correct iter-13 entries from the goal-decomposer's own
iteration authoring (verified accurate against the implementation) and were left as-is, matching
the iter-12 precedent.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest` (pyproject.toml's own `addopts = "-q"`;
do not pass an extra `-q` or the summary line disappears)

Result, full suite: **2691 passed, 8 skipped** (2699 collected). Iteration-12 baseline was 2695
collected / 2687 passed / 8 skipped; this iteration added exactly 4 new tests (1 in
`test_desk_ui_guards.py`, 3 in `test_referee_evidence.py`), 0 regressions, 0 skip-count change, 0
failures.

Targeted verification alongside the full suite (219 tests, all pass):
- `tests/test_desk_ui_guards.py` — including the new counter-test, run against the REAL modified
  `page.tsx` (proves zero client-side arithmetic actually crept in, not just that the regex
  compiles).
- `tests/test_referee_evidence.py` — including the golden byte-identity test and the
  unowned-literal guard, the latter run against the REAL modified frontend tree (proves neither
  disclosure string was hardcoded anywhere).
- `tests/test_copy_discipline.py` — all pass, no lexicon change needed; the new copy ("Evidence
  Readiness", "Playbook Family", "Strategy Family", "No stale basis dates.", "No integrity
  errors.", table labels) is purely descriptive.
- `tests/test_desk_refresh_chain_guard.py` — `_EXPECTED_EFFECT_COUNT == 21` still passes unedited.
- `tests/test_mcp_server.py` — still exactly 22 tools.

TypeScript: `apps/frontend && node_modules/.bin/tsc --noEmit` — zero errors.

Frozen-foundation checks (this iteration is read-only/frontend-only, so there is no
before/after diff to take within this session beyond proving zero touch):
- `Config().config_fingerprint()` == `08e471b10130e1e2` (current state; confirmed both by direct
  Python invocation and by the live `GET /research/desk/referee/evidence` response body).
- `git diff --stat` over every `app/research/referee_*.py` module, `desk_playbook*.py`,
  `desk_forward.py`, `levels.py`, `tradability.py`, `pnl_scan.py` together: empty output — zero
  diff.
- No write endpoint was ever called during dev or verification (confirmed by the backend access
  log during live verification below: only `GET /research/desk/referee/evidence` and `GET /desk`
  requests, never a POST) — the PnL ledger and champion pointer are therefore untouched by
  construction, not just by spot-check; no Referee write control (Confirm Registration / Build
  Null / Evaluate) was ever clicked.

Live verification against the operator's real corpus (read-only GET, via `scripts/start-backend.sh`/
`scripts/start-frontend.sh` on the deterministic ports :8301/:3301 — see Pre-handoff verification
below): `GET /research/desk/referee/evidence` served `records=210, distinct_sessions=156,
signals_at_current_basis=3222` (matches `docs/goal.md`'s own "Corpus reality at authoring" note
exactly) and `dataset_count=18, trade_count=873, tick_gate_met=false`. A real Chrome session
navigated to `/desk`, expanded "Referee Registry", and the extracted DOM text of the new section
matched the raw endpoint body **string-for-string** on every field, including the full
`tick_gate_statement` sentence and the complete Card-6.4 `basis_caveats` paragraph. Zero console
errors or warnings (only the standard React DevTools notice).

## Pre-handoff verification

- **Service startup**: `scripts/start-backend.sh` and `scripts/start-frontend.sh` (T-9: `.next`
  removed first) both started cleanly on ports :8301/:3301, served `GET
  /research/desk/referee/evidence` (200) and `GET /desk` (200, clean Next.js compile, 610-624
  modules, no errors). Stopped by exact PID / exact process-group signal (never pattern-based
  `pkill` — this host is shared with other projects), ports confirmed free via `ss`, started again
  cleanly with no port conflicts, stopped again. No server processes left running (`ps` confirms
  empty after each stop).
- **External integrations**: N/A — this iteration adds no adapter, scraper, or external API call
  (a pure frontend reader of an already-existing, already-tested backend endpoint).
- **Native dependency binaries**: N/A — no new dependency of any kind.
- **Informal browser check** (not a substitute for the browser-qa-agent's formal two-state pass):
  one live Chrome session against the real corpus, described above under Tests Run. A blank
  full-viewport screenshot was observed on the first two capture attempts even after
  `scrollIntoView` — the exact iter-12-carried lesson ("a screenshot taken at a deep scroll offset
  on /desk can come back blank even when the target is laid out and visible"). Since `document.body
  .scrollHeight` (8443px) exceeds this tool's 4320px viewport-height cap, the `set_viewport`-to-
  scrollHeight technique iter-12 used isn't directly available in this session; I relied on
  `extract()` (exact DOM text match, reproduced above) instead of a screenshot for my own
  confidence. This is flagged, not fixed — resolving the capture technique for a page this tall is
  the browser-qa-agent's job downstream (T-10: no screenshot ⇒ `unknown`, never `passing`; it will
  need its own working technique for the formal two-state QA pass this DoD requires).

## Known Issues

None found in this iteration's own scope.

One thing worth flagging for the browser-qa-agent: the empty-corpus state (TC-9's SEPARATE
clean/zero backend) was not exercised by this agent — the pre-handoff verification above ran only
against the operator's real, non-empty corpus (deliberately, to avoid spinning up a second throwaway
backend instance during dev). The all-zero rendering path was reasoned through by inspection (every
new field is a plain, unconditional pass-through of served values — a served `0` renders as `"0"` in
JSX, not blank; `stale_basis_dates`/`integrity_errors` empty lists already render through the shipped
`EmptyState` component regardless of corpus size; `tick_gate_statement`/`basis_caveats` are always
non-empty strings the backend computes even from an empty corpus, per `referee_evidence()`'s own
"never 404/500 on an empty corpus" docstring guarantee) but was not visually confirmed by this agent.
QA needs its own isolated empty-corpus backend instance and its own distinct screenshot per the DoD
(iter-10 lesson: two clauses that demand different on-screen states must not share one screenshot).

Browser QA (the formal two-state screenshot pass, and the sweep of every other shipped `/desk`
section in the same pass per TC-13) was NOT run by this agent — that is the browser-qa-agent's job
downstream. Grep-confirmed against `J-05.json`, `J-07.json`, `J-09.json`, `J-10.json`, `J-11.json`
(every other valid golden replay script in `runs/goal-session-referee/journey-scripts/` —
`J-01.json.invalid`/`J-02.json.invalid` are the pre-existing keyless/backend-only journeys, already
disabled) that none of their `testid`/`text` expectations collide with this iteration's new
headings/testids.
