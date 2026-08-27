# Iteration 4 — Coherence Audit

**Iteration:** goal-hypothesis-foundry-iter-4
**Date:** 2026-08-27
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

All four new top-level response keys were pre-registered in `state/blueprint.md`'s Data Contract
table at exactly this iteration (see the table's `sources_compiler`/`interpreter_fixtures`/
`freeze_integrity`/`hermetic_oracles` rows and the "Iteration note (iter-4)" below it). Verified
against the diff:

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `sources_compiler` | OK | Computed by `foundry_compiler.sources_compiler_hermetic_fixture_view` (new function in the already-registered `apps/backend/app/research/foundry_compiler.py`, no new module), served only via `GET /research/desk/micro/foundry` (`apps/backend/app/research/micro_routes.py:774-800`). UI reads `foundry.sources_compiler` verbatim (`apps/frontend/app/desk/page.tsx:7382` `SourcesCompilerSubsection`) — no second fetch, no client recompute. |
| `interpreter_fixtures` | OK | Computed by `foundry_interpreter.interpreter_hermetic_fixture_view` (new function in the already-registered `apps/backend/app/research/foundry_interpreter.py`), served by the same endpoint. UI reads `foundry.interpreter_fixtures` verbatim (`page.tsx` `InterpreterFixturesSubsection`). |
| `freeze_integrity` | OK | Computed by `foundry_freeze.freeze_integrity_hermetic_fixture_view` (new function in the already-registered `apps/backend/app/research/foundry_freeze.py`; internally calls the canonical `foundry_family`/`foundry_ledger`/`foundry_runner` functions rather than re-implementing family/replay/lock logic), served by the same endpoint. UI reads `foundry.freeze_integrity` verbatim. |
| `hermetic_oracles` | OK | Computed by the NEW module `apps/backend/app/research/foundry_hermetic_summary.py::build_hermetic_oracles_summary` — this module was itself pre-registered in the blueprint's Data Contract table ("NEW: `app/research/foundry_hermetic_summary.py`... introduces no second oracle implementation"), so its newness is not a drift. Internally it drives the real `foundry_compiler`/`foundry_family`/`foundry_ledger`/`foundry_runner` path and `foundry_source_registry.compile_source_disposition` (the same canonical functions rows 2-8 already register) rather than re-deriving disposition/decision logic — confirmed by reading `foundry_hermetic_summary.py:19-333`. Served by the same endpoint; UI reads `foundry.hermetic_oracles` verbatim. |
| `CandidateSpec` full-field rendering | OK | New `foundry_compiler.candidate_spec_view()` is introduced as the *one* canonical dict projection of a `CandidateSpec`, explicitly to avoid each caller hand-rolling its own subset (`foundry_compiler.py:327-333` docstring cites the anti-goal directly). `sources_compiler` is its only caller this iteration. This is a coherence *improvement*, not a new source of truth. |
| Repair 1 (`SourceRecord.alternatives` lint) | OK | `lint_alternatives` added to the already-registered `foundry_source_registry.py`, invoked from the already-registered `compile_sources` in `foundry_compiler.py:255` — no new computing path for source dispositions. |
| Repair 2 (`run_one_candidate` crash-path check) | OK | Added to the existing `foundry_runner.run_one_candidate` (`foundry_runner.py:114-121`), mirrors the already-existing terminal-path check three lines below — same module, same function, no duplicate rail. |

No new endpoint was introduced; the frontend fetch site (`fetchDeskFoundry()` populating
`foundryResult`, `page.tsx:10897`) is unchanged and is the sole call site feeding all five
Hypothesis Foundry subsections (header + 4 new).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| J-02 Sources/Compiler subsection | OK | Nested inside the existing `HypothesisFoundrySection` on `/desk` (`page.tsx:7706` `HypothesisFoundrySection`, mounted once at `page.tsx:13239`), reusing the shared `CollapsibleSection` from `@/components/CollapsibleSection` (`page.tsx:192` import; confirmed no locally-defined competing component). Home matches blueprint IA table row for J-02 exactly (`/desk` → Hypothesis Foundry → Sources/Compiler). No new route, no new top-level nav entry. |
| J-03 Interpreter fixtures subsection | OK | Same container/pattern; matches blueprint IA row for J-03. |
| J-04 Freeze/Integrity subsection | OK | Same container/pattern; matches blueprint IA row for J-04. |
| J-05 Hermetic Oracles subsection | OK | Same container/pattern; matches blueprint IA row for J-05. |

Reachability: `/desk` is an existing top-level nav item (1 click). The Hypothesis Foundry panel
already exists as a section on that page (iter-1); the four new subsections are nested
`CollapsibleSection`s inside that one panel — expand the panel, then expand a subsection. This
nested-subsection design was the blueprint's own explicit IA decision for these four journeys
(`state/blueprint.md`'s IA narrative: "iter-4 additionally ships four fixture-scope subsections
below the header"), so it is not new drift this iteration — it is exactly what was pre-approved,
and the iteration spec's own "Blueprint conformance" section confirms "No IA/nav change; no
`blueprint.reapproval-requested` needed." No duplicate home, no parallel shell — the layout shell
(top nav + `/desk` page) is untouched.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `foundry_hermetic_summary.py`'s `outcome_types_present` list (feeding `hermetic_oracles`) is
  built from a hard-coded `{plan-label: display-string}` dict keyed to which fixture the code
  *intends* to produce a given outcome, rather than reading the actual returned
  `row["foundry_state"]`/decision back off each `foundry_runner.run_one_candidate` call
  (`foundry_hermetic_summary.py` around the `build_hermetic_oracles_summary` outcome-mapping
  block). The iteration's own reviewer already caught this as a MINOR finding, correctly
  identifying it as edging toward the "hand-typed duplicate of these outcomes exist" pattern
  `lessons.md` (iter-3) warns against. This is **not** a Data Contract FAIL under this gate's Part
  A/Step 1 rule: there is still exactly one computing module/function for `hermetic_oracles`, and
  it does genuinely drive the real `foundry_compiler`/`foundry_family`/`foundry_ledger`/
  `foundry_runner` path rather than a second independent implementation — so no second owner of
  the value exists. It is a fidelity gap *within* the one canonical builder (the display label
  isn't verified against the row it describes), which is squarely the reviewer/auditor's territory
  (already flagged) rather than a coherence "two sources of truth" violation. Recommend the next
  touch of this file derive the label from the row's own returned state, as the reviewer suggested.
- `foundry_hermetic_summary.py` imports `tests.test_foundry_hermetic_epoch` at production
  module-import time — unusual layering, but this was the blueprint's own deliberate, pre-approved
  design (the Data Contract row explicitly names this as "a thin summary builder ... over
  `apps/backend/tests/test_foundry_hermetic_epoch.py`'s existing hermetic suite"), and the
  reviewer already logged it as a transparent NOTE. Flagged here only for visibility — not a
  coherence violation (no duplicate/parallel data path is created).
