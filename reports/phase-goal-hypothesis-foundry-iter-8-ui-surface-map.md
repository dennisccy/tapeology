# Phase goal-hypothesis-foundry-iter-8 — UI Surface Map

**Phase:** goal-hypothesis-foundry-iter-8
**Date:** 2026-08-27
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | `FinalSummarySubsection` (`data-testid="foundry-final-summary"`), wrapped in `CollapsibleSection id="foundry-final-summary-section"` title "Final Summary" | New component | J-08: one top-level synthesis of the real epoch's final state | Navigate to `/desk`, click the "Hypothesis Foundry" section header to expand it, then click the "Final Summary" section header (`data-testid="desk-section-expand-foundry-final-summary-section"`); verify the body (`data-testid="desk-section-body-foundry-final-summary-section"`) renders and is positioned above the "Sources/Compiler" subsection in the DOM |
| `/desk` | `foundry-final-summary-source-counts` block | New element | Shows source counts tallied by disposition | Expand Final Summary; verify each disposition string (e.g. `BLOCKED_DIRECTION`, `ALIASED_PROXY_ONLY`) appears with a numeric count next to it, and the counts sum to 11 |
| `/desk` | `foundry-final-summary-family-count` / `-variant-count` / `-frozen-ready-total` / `-evidence-class` / `-protected-read-count` / `-freeze-integrity-verdict` / `-epoch-status` (all inside `foundry-final-summary-counts`) | New elements | Renders `final_summary`'s scalar fields verbatim | Expand Final Summary; verify "Family count: 0", "Variant count: 0", "Frozen-ready total: 0", "Evidence class: historical_exposed_diagnostic", "Protected/withheld/sealed reads: 0" (green text), "Freeze integrity: green" (green text), "Epoch status: committed" all render |
| `/desk` | `foundry-final-summary-zero-survivors` (or `foundry-final-summary-survivors` when non-zero) | New element | Explicit honest zero-survivor statement (avoids a bare "0") | Expand Final Summary; verify the text "Zero diagnostic survivors exist for this epoch (diagnostic_survivor_count = 0) -- no candidate reached DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN this era." renders (not a bare "0") |
| `/desk` | `foundry-final-summary-exhaust-complete` (or `-exhaust-incomplete`) | New element | Explicit exhaust-completion statement | Expand Final Summary; verify the text "Exhaust complete -- every frozen candidate reached a terminal state." renders in emerald-colored text |
| `/desk` | `foundry-final-summary-source-detail-rows` → one `<li>` per source, each with a `<details data-testid="foundry-final-summary-source-detail">` | New feature (expand/collapse) | Per-source canonical-provenance drill-in | Expand Final Summary; locate the row whose `source_id` text reads `pilot-study-1-range-wall-failed-aggression` (badge shows `ALIASED_PROXY_ONLY`); click its "Canonical provenance" `<summary>`; verify the expanded body shows a Mechanism line, an Audit note line, a Direction derivation line reading `BLOCKED_DIRECTION`, a Comparator derivation line reading `complement_within_same_eligible_population`, and at least one quoted-span line starting with `"` and ending with `` @ 0`` (the first `quoted_spans[0].location`) |
| `/desk` | Source detail rows for a source missing `threshold_provenance` | Changed behavior (honest degrade) | A `null` optional field must render explicit absence text, never blank | Inside any expanded source's "Canonical provenance" body, verify the "Threshold provenance:" line shows the literal text `(none)` rather than being empty when the underlying field is `null` |
| `/desk` | Six existing Foundry subsections (Sources/Compiler, Interpreter Fixtures, Freeze/Integrity, Hermetic Oracles, Epoch/Manifest, Runner/Checkpoint) | Unchanged (regression) | Verify insertion of the new subsection did not disturb the existing six | Expand each of the six existing subsection headers below "Final Summary" one at a time; verify each still renders its previously-shipped content with no console errors |
| `/desk` | Top nav bar (`data-testid="app-nav"`, link labeled "Desk") | Unchanged | No navigation change this iteration | From `http://localhost:3301/`, verify the "Desk" nav link is present and unchanged, and clicking it still lands on `/desk` |
| N/A (backend) | `GET /research/desk/micro/foundry` | Backend-API — consumed by frontend | New `final_summary` top-level key; `exhaust_progress.diagnostic_survivor_count` added; `epoch_manifest.source_dispositions[]` entries enriched with §1.4 provenance fields | `curl http://localhost:8301/research/desk/micro/foundry \| python3 -m json.tool`; verify the response has a `final_summary` object with `source_counts_by_disposition` summing to 11, `family_count: 0`, `variant_count: 0`, `frozen_ready_total: 0`, `diagnostic_survivor_count: 0`, `freeze_integrity_verdict: "green"`, `protected_read_count: 0`, `exhaust_complete: true`, `epoch_status: "committed"`; verify `epoch_manifest.source_dispositions[]` entries now include `mechanism_statement`/`quoted_spans`/etc. |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_desk_ui_guards.py` — new
  `test_desk_page_price_arithmetic_guard_catches_foundry_field_arithmetic` regression test — no UI
  surface affected, guards against a future regression only.
- `apps/backend/tests/test_foundry_real_epoch_artifacts.py` — updated one pre-existing assertion
  to reflect the now-enriched `source_dispositions[]` shape — test-only, no UI surface affected.
- `apps/backend/tests/test_foundry_route.py` — 7 new unit tests proving the new backend fields
  read rather than recompute their underlying values — test-only, no UI surface affected.
- `apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py` — docstring-only correction (no
  assertion-logic change) — test-only, no UI surface affected.
- `apps/backend/app/research/micro_routes.py`'s `_compute_diagnostic_survivor_count()` /
  `_enrich_source_dispositions_with_registry_provenance()` internal helpers — these compute the
  values that DO surface in the UI (via `final_summary` and the per-source detail drill-in), but
  the helper functions themselves are not directly observable — only their output is (see the
  backend-API row above).

---

## Summary

- **Frontend surfaces changed:** 1 (the `/desk` → Hypothesis Foundry panel gains one new
  subsection with several sub-elements and a per-source drill-in)
- **New pages/routes:** 0
- **Modified components:** 2 (`apps/frontend/app/desk/page.tsx` — new `FinalSummarySubsection`
  component + insertion point; `apps/frontend/lib/types.ts` — supporting type extensions, not
  independently visible)
- **Navigation changes:** no
- **Backend-only changes:** 4 (all test files, plus the docstring-only correction — see above)
