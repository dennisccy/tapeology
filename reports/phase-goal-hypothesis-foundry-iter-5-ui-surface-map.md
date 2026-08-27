# Phase goal-hypothesis-foundry-iter-5 — UI Surface Map

**Phase:** goal-hypothesis-foundry-iter-5
**Date:** 2026-08-27
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | `EpochManifestSubsection` (new nested `CollapsibleSection` id `foundry-epoch-manifest-section`, header text "Epoch / Manifest") | New component | J-06: surfaces the era's one real, Git-committed Foundry epoch | Navigate to `/desk`, click the "Hypothesis Foundry" section header, then click the "Epoch / Manifest" row header; verify the panel expands and shows `epoch_id: epoch:afd19e9c11a6534f`, all 11 rows under "Source dispositions (11 of 11 required objects)", and the text "Zero compiled candidates this epoch — every required source disposed non-COMPILED." under "Compiled families (0)" |
| `/desk` | `RealEpochBanner` (`data-testid="foundry-epoch-manifest-real-banner"`) | New component | Distinguishes the real epoch from the four hermetic-fixture demonstrations per DoD/anti-goal requirement | With Epoch / Manifest expanded, verify the banner text reads exactly "Real Epoch — not a fixture" and is styled with an emerald/green border and text color, visibly different from the amber "Hermetic Fixture — not the real epoch" banners on the other four subsections |
| `/desk` | `EpochManifestSubsection` status line (`data-testid="foundry-epoch-status"`) | New display | Shows the freeze-barrier crossing state | With Epoch / Manifest expanded, verify the "Status:" line reads "Committed — Git-visible pre-outcome barrier crossed" in emerald text (not amber) |
| `/desk` | `EpochManifestSubsection` identity block (`data-testid="foundry-epoch-identities"`) | New display | Shows the freeze identity hashes required by TC-7 | With Epoch / Manifest expanded, verify all six lines are present and non-empty: `epoch_id`, `source_registry_hash`, `manifest_hash`, `freeze_set_hash`, `freeze_commit`, `config_fingerprint`, plus a 7th line `outcome_access_census: 0` shown in emerald text |
| `/desk` | `EpochManifestSubsection` source-disposition list (`data-testid="foundry-epoch-source-disposition-rows"`) | New display | Shows the real per-source disposition for all 11 required objects | With Epoch / Manifest expanded, count the `<li>` rows under "Source dispositions" and verify there are exactly 11, including `card-9.6-shuffled-side-persistence` and `card-9.6-run-length-at-touch` as two separate rows and `cards-9.8-9.11-wave2-gate-closed` showing disposition `EXCLUDED_GATE_CLOSED` |
| `/desk` | `EpochManifestSubsection` empty-families state (`data-testid="foundry-epoch-families-empty"`) | New empty state | Honest zero-compiled-candidates outcome must render, not be hidden | With Epoch / Manifest expanded, verify the text "Zero compiled candidates this epoch — every required source disposed non-COMPILED." is visible under the "Compiled families (0)" heading |
| `/desk` | `EpochManifestSubsection` audit reference (`data-testid="foundry-epoch-source-registry-audit"`) | New display | Links the UI to the committed independent audit report | With Epoch / Manifest expanded, verify the line reads "Source-registry audit report: reports/hypothesis-foundry/source-registry-audit.md (committed)" with "(committed)" shown in emerald text |
| `/desk` | `SourcesCompilerSubsection` fixture rows (`data-testid="foundry-source-fixture-rows"`) | Changed behavior (row count 7→8) | Both alias-family sibling records must be independently visible per J-02 | With "Sources / Compiler" expanded, count the `<li>` rows in the fixture list and verify there are exactly 8, with both `fixture-variant-a` and `fixture-variant-b` present as separate rows |
| `/desk` | `SourcesCompilerSubsection` additive fields (`data-testid="foundry-source-operative-formula-refs"`, `foundry-source-superseded-fields`, `foundry-source-aliases-lineage-ids`) | New field rendering | Fields already existed in the API response but were never rendered | With "Sources / Compiler" expanded, on the `fixture-unsupported-stat` row verify "Operative formula refs: (none)" is shown (its `operative_formula_refs` array is empty), and on the `fixture-alias-older` row verify "Superseded fields: event_time_window → docs/rapid-validation-spec.md#feature-windows" is shown |
| `/desk` | `SourcesCompilerSubsection` audit reference (`data-testid="foundry-source-registry-audit-reference"`) | New display | Text reference to the committed audit report | With "Sources / Compiler" expanded, verify the line "Real registry audit report: reports/hypothesis-foundry/source-registry-audit.md (committed alongside the real epoch — see Epoch / Manifest below)." is visible near the top of the subsection |
| `/desk` | `HermeticOraclesSubsection` kill-type mapping (`data-testid="foundry-kill-type-mapping-rows"`) | New field rendering | Per-row kill-type mapping required by J-05/TC-13 | With "Hermetic Oracles" expanded, count the `<li>` rows in the kill-type-mapping list and verify there are exactly 7, including a row reading "fragile → EVALUATED_KILLED" and a row reading "survive → DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN" |
| `/desk` | `HermeticOraclesSubsection` best-of-N line (`data-testid="foundry-best-of-n-disclosure"`) | New field rendering | Best-of-N disclosure required by J-05/TC-13 | With "Hermetic Oracles" expanded, verify the line "Best-of-N disclosure: n_variants_tried=7 · threshold_bps=0.1569542572940126" (or the current live value) is visible below the kill-type-mapping list |
| `/desk` | Hypothesis Foundry panel header (`data-testid="foundry-era-identity"`, "Source registry hash" line) | Changed behavior | Top-level hash line now reads a real value instead of always "not_yet_generated" | With the "Hypothesis Foundry" section expanded (subsections still collapsed), verify the "Source registry hash:" line shows a long hex string (e.g. starting `ed40dbc25e8f...`), not the literal text `not_yet_generated` |

<!-- Change Type options: New page | New component | Updated layout | Added navigation | Changed behavior | Removed element | New form | New table | New modal -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py` — operator-run CLI that generates and freezes the real epoch; it is a one-time, ahead-of-time generation tool (already run and committed), not something an operator invokes from the UI — no UI surface, and none is expected (goal.md's own Product Shape rules out a mutation page for this era).
- `docs/hypothesis-foundry/{source-registry,epoch-manifest,freeze-set,freeze-record}.json` and `reports/hypothesis-foundry/source-registry-audit.md` — the committed data artifacts themselves; they are consumed by the `epoch_manifest` API key and surfaced through the Epoch / Manifest UI listed above, but the raw files/paths have no direct UI surface of their own (only their content, via the API).
- `apps/backend/app/research/foundry_hermetic_summary.py`'s removal of the two `scout._two_sided_p` production reassignments and the `_derive_outcome_types_present()` refactor — an internal integrity/anti-goal cleanup with no change to any rendered value (the `outcome_types_present` line's displayed text is unchanged; only how it is computed changed) — no new UI surface.
- `apps/backend/app/research/micro_routes.py`'s `read_epoch_manifest_view()`, `_git_rev_parse_head()`, `_git_path_committed_at_head()` helper functions — internal plumbing that feeds the `epoch_manifest` API key already covered by the Epoch / Manifest rows above — no separate UI surface.
- Test-file changes (`test_foundry_hermetic_epoch.py`, `test_foundry_route_hermetic_views.py`, `test_foundry_route.py`) and the standalone drift-refusal verification script — test-only code, no UI impact.

---

## Summary

- **Frontend surfaces changed:** 5 (1 new subsection + 2 new field groups inside Sources/Compiler + 2 new field groups inside Hermetic Oracles, plus the panel-header hash line)
- **New pages/routes:** 0
- **Modified components:** 3 (`SourcesCompilerSubsection`, `HermeticOraclesSubsection`, and the top-level `HypothesisFoundrySection` header line) + 2 new components (`EpochManifestSubsection`, `RealEpochBanner`)
- **Navigation changes:** no
- **Backend-only changes:** 5 (real-epoch generation CLI, 5 committed data artifacts, hermetic-summary integrity cleanup, route helper functions, test-only changes)
