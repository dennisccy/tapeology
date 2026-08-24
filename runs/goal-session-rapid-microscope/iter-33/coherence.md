# Iteration 33 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-33
**Date:** 2026-08-24
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

Row audited: **"Feature snapshot metadata + build progress/runs"** — owner `micro_snapshots.py`,
endpoint `GET /research/desk/micro/snapshots` (already registered since era baseline). This
iteration adds two disclosure sub-fields (`withheld_excluded` already anticipated by the iter-10
Disclosure sub-fields table; `stale_excluded` newly registered this iteration in
`runs/goal-session-rapid-microscope/state/blueprint.md` lines 79-85) and gives the row its first
UI and MCP readers.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Feature snapshot listing (`snapshots[]`) | OK — read verbatim from the canonical endpoint | `apps/frontend/lib/api.ts:fetchDeskMicroSnapshots` → `GET /research/desk/micro/snapshots`; served by `apps/backend/app/research/micro_routes.py:176` (`snapshot_meta_report`, owned by `micro_snapshots.py`) |
| `withheld_excluded` (listing route) | OK — pool-derived via the pre-existing shared choke point, not a new/divergent predicate | `apps/backend/app/research/micro_snapshots.py:390` calls `_unresolved_pool_ids(dataset_store, records)`, the SAME function `withheld_dataset_ids_for_store` (line 149-168) and `exclude_withheld` (line 171-193) already use — verified by direct grep, `_unresolved_pool_ids` is pre-existing (not touched by this diff), not a second implementation |
| `stale_excluded` (new sub-field) | OK — genuinely new, matches blueprint's own precedent for sub-field additions, registered in the same edit | `apps/backend/app/research/micro_snapshots.py:391-408` (`snapshot_meta_report`); blueprint row added at `runs/goal-session-rapid-microscope/state/blueprint.md:79-85` |
| `list_snapshot_meta` (pre-existing callers) | OK — refactored to delegate to the new single walk rather than keeping a second, divergent enumeration | `apps/backend/app/research/micro_snapshots.py:356-360` now calls `snapshot_meta_report(...)["snapshots"]` instead of re-walking the directory itself |
| `desk_micro_snapshots` MCP tool | OK — byte-identical GET proxy of the canonical endpoint, no second computation path (matches the file's own iter-15/31 precedent for MCP tools) | `apps/backend/app/mcp/__init__.py:154, 452-465`; proven byte-identical by `apps/backend/tests/test_mcp_server.py:270-318` |
| Run-history `withheld_excluded` (compute/run-log side) | OK — pre-existing served field (registered under the iter-10 Disclosure sub-fields table, "served by the GET/compute routes of the module in the same row"), read verbatim for the first time by the new UI section, not recomputed | `apps/frontend/app/desk/page.tsx` `FeatureSnapshotsSection`'s run-history table renders `run.withheld_excluded` directly from `GET .../snapshots/runs`; no client-side arithmetic (guarded by the widened `_PRICE_ARITHMETIC_FIELDS` in `apps/backend/tests/test_desk_ui_guards.py:342-206`) |

No new function recomputes any registered value independently, and no new UI surface fetches a
registered value from a non-canonical source. All snapshot-row fields rendered by
`FeatureSnapshotsSection` (`dataset_id`, `snapshot_format_version`, `micro_algo_version`,
`config_fingerprint`, `feature_source_hash`, `params_hash`, `quote_size_unit`, `row_count`,
`bytes_on_disk`, `built_utc`) are pass-through renders of the one served `SnapshotMeta` shape —
re-formatting only (e.g. `formatDateTimeET(snapshot.built_utc, ...)`), which is explicitly
permitted (skill Part A rule 3).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Feature Snapshots section on `/desk` | OK — placed in its blueprint-assigned canonical home, no new route, no parallel shell | `apps/frontend/app/desk/page.tsx`: new `<section aria-label="Feature Snapshots">` inserted as the sibling directly below the existing Graduation `<section>`, inside the same `DeskPage` component/shell used by every other Rapid Microscope section; blueprint IA table (`runs/goal-session-rapid-microscope/state/blueprint.md:24-33, 51`) names exactly this home ("`/desk` → Feature Snapshots, rendered BELOW Graduation") |
| Reachability | OK — 1 click to `/desk` (top nav), section already on that page (same collapsible-section pattern as every prior Rapid Microscope section, established and previously audited PASS at J-08/J-11) | `apps/frontend/app/desk/page.tsx` nav is the persistent top nav (unchanged this iteration — `app/meta.py` `UI_ROUTES` untouched per blueprint) |
| J-02 IA row correction | OK — in-place correction of an existing row to its now-built canonical home, not a new/duplicate row | Blueprint `Feature / journey homes` table, J-02 row (`blueprint.md:41`) updated from a loose reference to point at the same new section |
| `desk_micro_snapshots` MCP tool | OK — not part of the nav skeleton by this codebase's own established convention (MCP tools carry no IA row) | Blueprint iter-15/31 notes explicitly document this precedent; `apps/backend/app/mcp/__init__.py:154, 452-465` |

No new top-level route, no second "snapshots" page, no invented layout/shell. The new tool
position (`desk_micro_readiness` → `desk_micro_snapshots` → `desk_scout`) matches the
dependency-order rule and blueprint's stated placement, verified directly:
`grep -n 'name="desk_micro_readiness"\|name="desk_micro_snapshots"\|name="desk_scout"'
apps/backend/app/mcp/__init__.py` → lines 437, 452, 466 in that order.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None of substance. The new section's disclosure-count labels ("Withheld (excluded)" / "Stale
  (excluded)") and the run-history column label ("Withheld (excluded)") are consistent with each
  other and with the phrasing already used elsewhere on `/desk` (e.g. the Microscope Readiness
  section's existing "Joinable corpus — withheld (excluded)" string per the iter-19 note), so no
  labelling-drift note is warranted this round.
