# Iteration 12 — Coherence Audit

**Iteration:** goal-playbook-iter-12
**Date:** 2026-08-12
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Summary

J-11 adds seven served fields (`cells[].signal.n_unmeasured`/`n_sessions`,
`cells[].baseline.n_truncated`/`n_unmeasured`/`n_sessions`, `other_signatures[].n_records`, a new
top-level `basis: {dates, n_records, created_span}`) to the already-registered "Evidence
aggregates" Data Contract row, plus two carried passenger fixes (a CSS border-color fix on the
Playbook Signals date input; a fifth env var on the back-scan module's test-lane-only scoping
guard). I read the full 9-file diff against snapshot `f3469c25d85ef35d3b8656bcaa9b08a5eabf417f`
(`git diff f3469c25... --stat` confirms exactly the 9 files the bounded diff showed; the 26 lines
the bounded diff truncated in `test_desk_playbook_evidence.py` were fetched directly and reviewed)
and independently verified every zero-diff claim the blueprint/spec make (`desk_forward.py`,
`desk_playbook.py`, `desk_playbook_detect.py`, `desk_playbook_features.py`,
`apps/frontend/lib/api.ts`, `apps/backend/app/meta.py`, `apps/frontend/components/NavBar.tsx` all
show empty diffs against the snapshot). No Data Contract or Information Architecture violation
found.

## Data Contract check

All seven new/touched fields extend the single already-registered "Evidence aggregates" row —
computed by `app/research/desk_playbook_evidence.py`, served by
`GET /research/desk/playbook/evidence`. No new owner, no new endpoint, no cache-schema change
(`PlaybookEvidenceCache` class itself is untouched in the diff), no call into `_measure_from`, no
new `Config` field.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `cells[].signal.n_unmeasured` | OK | Computed `desk_playbook_evidence.py:334` (`_n_unmeasured_by_label`, reads already-materialized `event["horizons"][label]["return_pct"]`, never re-derives measurability) + `:355` (`_n_unmeasured_for`) + `:282` (`_signal_cell`); wired once per pool in `_fold_cells` (`:363`); served by the one registered endpoint (`desk_routes.py:1321`, docstring-only diff); rendered as a plain `fmt()` pass-through at `apps/frontend/app/desk/page.tsx:3772-3774` (no client arithmetic — `_PRICE_ARITHMETIC_FIELDS` extended + counter-tested in `test_desk_ui_guards.py`). |
| `cells[].signal.n_sessions` | OK | Same owner/endpoint; computed once per `(setup_id, side)` pool from `projection["session_date"]` (a field the cache already stores) in `_fold_cells`, applied identically to every measure in that pool (verified against TC-4's own assertion in the diff) — `desk_playbook_evidence.py:363` region; rendered `page.tsx:3775-3777`. |
| `cells[].baseline.n_truncated` | OK | Not a new computation — wires through `_collect_measures`'s (existing `desk_forward.py` helper, zero diff) already-returned second tuple element, previously discarded as `_baseline_truncated`; `desk_playbook_evidence.py:296` (`_baseline_cell`); rendered `page.tsx:3787-3789`. |
| `cells[].baseline.n_unmeasured` / `n_sessions` | OK | Same fold, same owner/endpoint, baseline mirror of the signal-side fields above; `desk_playbook_evidence.py:296`, `:363`; rendered `page.tsx:3790-3795`. |
| `other_signatures[].n_records` | OK | Reuses the new shared `_signature_basis` helper (`desk_playbook_evidence.py:459`) — same helper the payload-level `basis` block below uses — no independent second computation. |
| `basis: {dates, n_records, created_span}` | OK | New top-level key, same endpoint; `_signature_basis` (`desk_playbook_evidence.py:459`) called once over `default_projections` in `fold_evidence` (`:491`); route docstring updated (`desk_routes.py:1321`, no functional route diff — the route returns a plain `dict`, no `response_model`); MCP `desk_playbook_evidence` proxy test updated to expect the enriched key set (`test_mcp_server.py`), confirming the byte-identical-proxy invariant holds; rendered via `PlaybookEvidenceBasisLine` (`page.tsx:3932-3940`), a straight pass-through (`{basis.n_records}`, `{basis.dates.join(", ")}`) beside the pre-existing, byte-unchanged "Built from signature:" line. |

One pre-existing detail I traced but did not flag as a violation: `inspect_signature`
(`desk_playbook_evidence.py:525`, untouched by this diff) independently computes
`dates`/`created_span` for a signature via a fresh `PlaybookStore.get` read, while the new
`_signature_basis` helper computes the same conceptual shape from the evidence cache's already-
stored projections. This dual-path pattern predates this iteration (J-08's original
`_fold_other_signatures` already had its own inline version of the cache-based half); this
iteration's diff *reduces* duplication (extracts that inline logic into one shared
`_signature_basis` helper now reused by `other_signatures[]` and the new `basis` block) and adds a
regression test (`test_iter12_tc5_basis_matches_inspect_signature_for_the_same_signature`) that
cross-checks the two paths agree for the default signature. Not a new drift introduced by this
iteration — see Advisory notes.

## Information Architecture check

No new page, route, or nav entry this iteration. Every new field lands inside the existing `/desk`
Playbook Evidence section (`PlaybookEvidenceSection`/`PlaybookEvidenceCellRow`/
`PlaybookEvidenceCellsTable`, all pre-existing components) — the blueprint's own J-11 IA row names
this as the canonical home ("same as J-08: `/desk` (Playbook Evidence section) — no new home") and
the diff matches it exactly. The passenger CSS fix touches only the existing Playbook Signals
date input in place.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| J-11 (Evidence basis + per-cell exclusion counts) | OK | No new route/page; `git diff <snapshot> --stat -- apps/backend/app/meta.py apps/frontend/components/NavBar.tsx` is empty (both untouched) — nav skeleton unchanged, confirming the fields render inside the already-reachable `/desk` → Playbook Evidence home. Only `apps/frontend/app/desk/page.tsx` among the three `page.tsx` files in the repo references playbook/evidence (`grep -rl` over `apps/frontend/app`), ruling out a second/parallel surface. |
| Playbook Signals date-input border fix (passenger) | OK | Same existing `/desk` Playbook Signals section, same input (`data-testid="desk-playbook-date-input"`); scoped to one `className` expression only, verified by `test_desk_playbook_date_input_amber_border_fix_is_scoped_to_itself_only` (asserts the other 2 Refresh-Data call sites and 4 bare `ASOF_INPUT_CLASS` call sites stay byte-unchanged). |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `inspect_signature` (`desk_playbook_evidence.py:525`, fresh `PlaybookStore` read) and the new
  `_signature_basis` helper (`:459`, cache-projection read) are two code paths to the same
  conceptual value ("dates + created_span for a signature") living in the same registered module.
  This predates iteration 12 and is not worsened by it — if anything this diff reduces the
  duplication by giving `other_signatures[]` and the new `basis` block one shared helper instead of
  two inline copies — and TC-5 now regression-tests the two paths agree for the default signature.
  No action required this iteration; worth a passing mention if a future iteration ever touches
  either function, so a maintainer knows to keep them in sync.
- `PlaybookEvidenceCellsTable`'s data columns grew from 11 to 16 (Signal 6→8, Baseline 5→8;
  `min-w-[900px]` → `min-w-[1180px]`, `page.tsx:3862` region) inside its existing
  `overflow-x-auto` wrapper. Purely a visual-density increase in an already-scrollable table, not a
  coherence violation.
