# Iteration 5 — Coherence Audit

**Iteration:** goal-hypothesis-foundry-iter-5
**Date:** 2026-08-27
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `epoch_manifest` (new key: status/epoch_id/source_registry_hash/manifest_hash/freeze_set_hash/freeze_commit/config_fingerprint/outcome_access_census/source_dispositions/families/source_registry_audit) | OK | Computed by `read_epoch_manifest_view()` in `apps/backend/app/research/micro_routes.py:786-870`, which reuses only already-registered modules (`foundry_source_registry`, `foundry_compiler`, `foundry_freeze` via the untracked `apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py`, no new computing module); served by the one registered endpoint `GET /research/desk/micro/foundry` at `micro_routes.py:900-931`; computed once at module import (`_EPOCH_MANIFEST_VIEW = read_epoch_manifest_view()`, `micro_routes.py:893`), never per-request. Reads the literal repo-relative `docs/hypothesis-foundry/*.json` paths (`_FOUNDRY_TRACKED_DIR`, `micro_routes.py:775-777`) rather than `get_foundry_dir()`/`resolve_foundry_dir()`, matching the blueprint's explicit iter-5 instruction. Frontend `EpochManifestSubsection` (`apps/frontend/app/desk/page.tsx:7706-7823`) renders every field verbatim, no client-side recomputation. |
| `source_registry_hash` / `source_registry_status` (top-level, pre-existing keys) | OK | Previously hard-coded `None`/`"not_yet_generated"`; now sourced from the SAME `_EPOCH_MANIFEST_VIEW` read (`micro_routes.py:922-923`, no second calculation path) — verified by a dedicated new test asserting `body["source_registry_hash"] == body["epoch_manifest"]["source_registry_hash"]` (`apps/backend/tests/test_foundry_route.py::test_iter5_source_registry_hash_and_status_are_sourced_from_the_same_epoch_manifest_read`). |
| `hermetic_oracles.kill_type_mapping` (new field) | OK | Added in `foundry_hermetic_summary.py:311-313`, reading each composite row's own real `foundry_state` off the existing `results` list — same module (`build_hermetic_oracles_summary`), same endpoint (`hermetic_oracles` key), no new oracle path. |
| `hermetic_oracles.best_of_n_disclosure` (new field) | OK | Sourced from the existing `screen_result.screen_result.best_of_n_disclosure` payload already present on each composite row (`foundry_hermetic_summary.py:325-333`) — no new statistical computation, just a read-and-select over already-produced values. |
| `hermetic_oracles.outcome_types_present` (row-derivation repair) | OK | Extracted to `_derive_outcome_types_present()` (`foundry_hermetic_summary.py:301-317`), now reading each row's real `screen_result["decision"]` through a fixed rendering table (`_DECISION_TO_PRESENT_LABEL`) instead of a hard-coded per-fixture-label dict. Same value, same source data, provably row-derived (`test_iter5_outcome_types_present_is_row_derived...`-style test referenced in the spec's TC-14). |
| `sources_compiler` (fixture count 7→8 + `operative_formula_refs`/`superseded_fields`/`aliases_lineage_ids`) | OK | `foundry_compiler.py:411-428` change surfaces the already-existing `variant_b` `SourceRecord` as its own entry — no new record type, no new module; fields were already computed on `FoundrySourceFixture` and are now simply rendered (`apps/frontend/app/desk/page.tsx:7466-7488`) — a pure rendering-only fix, matching the blueprint's own framing of this repair. |
| `scout._two_sided_p` anti-goal (production reassignment removal) | OK (closed) | `grep -rn 'scout\._two_sided_p\s*=' apps/backend` outside `tests/` returns zero matches (verified directly). `foundry_hermetic_summary.py` now uses `_fragile_killed_anchors_natural()` (a re-tuned fixture) instead of monkeypatching a frozen module attribute in the serving process. |

No new displayed value was found unregistered in the blueprint; every new key traces to a Data Contract row that the blueprint.md itself was updated to add at this iteration (`epoch_manifest` row, `hermetic_oracles` field extensions).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` → Hypothesis Foundry → Epoch / Manifest (new subsection) | OK | No new route/page; new `CollapsibleSection id="foundry-epoch-manifest-section"` nested inside the already-registered `HypothesisFoundrySection` on `apps/frontend/app/desk/page.tsx:8060-8069` — exactly the canonical home the blueprint pre-registered for J-06. Reachability confirmed both statically (nested inside the existing panel, no separate router entry) and live via browser-qa: UT-09 in `reports/phase-goal-hypothesis-foundry-iter-5-ui-test-results.md` confirms Epoch/Manifest is reachable 2 clicks from `/desk` (expand Hypothesis Foundry, then expand the Epoch/Manifest row), alongside the four pre-existing sibling subsections in stable order. |
| `/desk` → Hypothesis Foundry → Sources/Compiler, Hermetic Oracles (additive field rendering) | OK | Same existing components (`SourcesCompilerSubsection`, `HermeticOraclesSubsection`), no new component tree, no parallel shell. |

No new top-level nav entry, no duplicate home for any existing entity, no parallel shell introduced.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The auditor's own handoff (`docs/handoffs/goal-hypothesis-foundry-iter-5-audit.md`, verdict PASS_WITH_GAPS) flagged two IMPORTANT integrity gaps in the freeze-set/first-read-lock mechanism (absolute-path portability, `freeze_commit` not guaranteeing science-byte content) — these are correctness/robustness concerns for the future J-07 first-read lock, not coherence violations: they do not create a second computation path, a second endpoint, or a navigation problem. Out of scope for this gate; already tracked by the auditor for J-07.
- `epoch_manifest.families` is `[]` this iteration (every one of the 11 real sources disposed non-COMPILED) — an honest empty state, rendered as an explicit "Zero compiled candidates..." message rather than hidden, consistent with the Data Contract's own sparse-epoch allowance. Not a coherence issue.
