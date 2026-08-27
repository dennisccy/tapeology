# goal-hypothesis-foundry-iter-8 Frontend Handoff

**Phase:** goal-hypothesis-foundry-iter-8
**Date:** 2026-08-27
**Agent:** developer
**Status:** complete

## What Was Built

- New "Final Summary" subsection inside the already-shipped `/desk` → Hypothesis Foundry panel
  (`FinalSummarySubsection` component, `apps/frontend/app/desk/page.tsx`). Positioned directly
  under the panel's era-identity/era-open-baseline header and above the six existing subsections
  (Sources/Compiler, Interpreter Fixtures, Freeze/Integrity, Hermetic Oracles, Epoch/Manifest,
  Runner/Checkpoint) — its own separate `CollapsibleSection` (`id="foundry-final-summary-section"`,
  title "Final Summary"), NOT nested inside the six-subsection container.
- Renders, verbatim from the backend's new `final_summary` payload: source counts by disposition,
  family count, variant count, frozen-ready total, evidence class, protected/withheld/sealed read
  count, freeze integrity verdict, and epoch status. Diagnostic survivor count renders as an
  explicit sentence (not a bare number) — an honest zero-survivor statement when `0`, or a
  survivor disclosure (labelled `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN` only, with an explicit "not
  OOS evidence, not Referee-ready" caveat) when non-zero. Exhaust-completion state renders as its
  own explicit sentence.
- A per-source detail drill-in: one `<details>` per real source-registry record (all 11 in the
  real epoch), listing `source_id`/`disposition` in the summary line and, once expanded,
  `mechanism_statement`, `audit_note`, `direction_derivation`, `comparator_derivation`,
  `threshold_provenance` (or an explicit "(none)" when absent), `superseded_fields`,
  `alternatives`, `source_hash`, and every `quoted_spans[]` entry's `text`/`location` — same
  `<details>`/`<summary>` convention already used by the panel's other subsections.
- New user action: expand/collapse a source's canonical-provenance `<details>` disclosure. No new
  page, no new nav entry, no new top-level route.

## Data flow

No new network request. `FinalSummarySubsection` receives `foundry.final_summary` and
`foundry.epoch_manifest.source_dispositions` — both already present on the single
`fetchDeskFoundry()` response the panel already fetches (`GET /research/desk/micro/foundry`). No
client-side arithmetic on any served numeric field (enforced by the extended
`test_desk_page_price_arithmetic_guard_catches_foundry_field_arithmetic` guard test).

## Types

`apps/frontend/lib/types.ts`:
- New `FoundryQuotedSpan { text: string; location: number }`.
- Extended `FoundrySourceDisposition` with the eleven new §1.4 provenance fields.
- Extended `FoundryExhaustProgress` with `diagnostic_survivor_count: number`.
- New `FoundryFinalSummary` interface (the ten `final_summary` fields).
- Extended `DeskFoundryResponse` with `final_summary: FoundryFinalSummary`.

## Visual/behavioral conventions followed

- Same monospace/slate-muted numeric styling as `RunnerCheckpointSubsection`/
  `EpochManifestSubsection`.
- Same green/amber freeze-integrity-verdict color convention as `RunnerCheckpointSubsection`.
- Same `<details>` disclosure pattern as `SourcesCompilerSubsection`'s per-source CandidateSpec
  drill-in.
- Design Direction compliance: no promotional/trading-urgency language; the survivor disclosure
  explicitly denies OOS/Referee readiness; copy-discipline lint (`test_copy_discipline.py`) passes
  over the new JSX with zero banned-phrase matches.
- Effect/timer census unchanged: no new `useEffect`/`setInterval`/`setTimeout` — the component
  reuses the page's existing local `openSubsections`/`toggleSubsection` state already used by the
  six sibling subsections.

## Tests Run

- `cd apps/frontend && npx tsc --noEmit` — 0 errors.
- Backend guard tests covering this frontend surface (`test_desk_ui_guards.py`,
  `test_table_sort_guards.py` effect census, `test_copy_discipline.py`, `test_vault.py` TR-2) — all
  passing as part of the full 3930-passed backend suite.
- Live Chrome verification against the real running `:3301` frontend (see dev handoff's "Tests
  Run" section for the exact DOM-vs-JSON matching evidence).

## Known Issues

- No `demo_runner --mode verify` screenshot capture was run this dev pass (that is QA's step per
  the dispatch note, since deep-scroll Chrome-MCP screenshots of Foundry subsections are a known
  blank-PNG environment artifact this session). Functional correctness was instead verified via
  direct DOM query/eval against the live Chrome session, which confirmed byte-for-byte match with
  the served JSON.
