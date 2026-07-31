# Iteration 35 — Coherence Audit

**Iteration:** goal-desk-iter-35
**Date:** 2026-07-31
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Screen comparison (J-20, new this iteration) | OK | Computed by `apps/backend/app/research/desk_screen_diff.py:664` (`compute_screen_diff`), which imports only `ScreenStore` (`desk_screen_diff.py:516`) and calls `store.list()` exactly once (`desk_screen_diff.py:676`, backed by `test_desk_screen_diff.py`'s `test_module_imports_no_store_or_compute_dependency` + `test_compute_screen_diff_only_calls_screen_store_list`). Served by the one new route `GET /research/desk/screen/compare` (`apps/backend/app/research/desk_routes.py:400-416`). No `BarStore`/`bar_index`/`compute_tradability`/`DatasetStore` import or call anywhere in the new module — matches the blueprint row registered *before* this build (`blueprint.md` line 184, "New rows this era" table) verbatim, including the response shape (`compare`/`base`/`base_resolution`/`rows`/`identical`/`counts`). |
| Screen snapshots, rank rows, skip rows (existing owner `desk_screen.py`) | OK | Diff touches `desk_routes.py` and `desk_screen_diff.py` only for this feature; `desk_screen.py`, `ScreenStore.list()`'s sort order, the five-pin key, and the rank key are untouched (confirmed: `desk_screen.py` does not appear in the diff at all). The new comparison row re-reads (never re-derives) `side`/`band_class`/`distance_bps`/`basis_as_of` off the same recorded rows (`desk_screen_diff.py:521` `_DISCLOSED_FIELDS`, copied verbatim at `:624-625`/`:641-642`). |
| Route / nav inventory (`app/meta.py` `UI_ROUTES`) | OK | `apps/backend/app/meta.py` is untouched by this iteration's diff (confirmed via `git status`/diff — not in the changed-file list); no new nav-skeleton entry was needed since the new section lives on the already-registered `/desk` route. |
| `config_fingerprint` / MCP tool count | OK | Neither `app/config.py` nor `app/mcp/__init__.py` appears in the diff — zero new `Config` field, zero new MCP tool, consistent with the iter-35 spec's "Out of scope" list and the blueprint's new-row note ("no new MCP tool… J-06's exactly-17-tool contract is unaffected"). |
| Frontend re-render of the compare payload | OK (re-format only) | `ScreenCompareRowView`/`ScreenCompareMeta`/`ScreenCompareTable` (`apps/frontend/app/desk/page.tsx:1489-1625` per the bounded diff) render `DeskScreenCompareResult` fields verbatim, applying only display formatting (`fmt()` for distance, literal fallback strings for `null`, `.slice()` for the display cap) — no client-side re-rank, re-score, or second fetch of a registered value from a non-canonical endpoint. `fetchDeskScreenCompare` (`apps/frontend/lib/api.ts` new function) hits the one new canonical endpoint only. |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Screen Comparison section (`/desk`, J-20) | OK | `apps/backend/app/meta.py` (`UI_ROUTES`, lines 31-41) is unchanged — still 3 top-level routes (`/`, `/structure`, `/desk`). The new section is rendered inside the existing `DeskPage` component (`apps/frontend/app/desk/page.tsx`, new `<section aria-label="Screen Comparison">` appended after the existing Screen Runs section, per the bounded diff's final hunk), using the shared `Panel` component already used by every sibling section (Screen History, Top-up Runs, Index Reconciliation, Screen Runs) — no parallel shell, no new layout. `/desk` is already 1 click from the top nav, so the new section requires zero additional clicks. Confirmed not a duplicate home: it discloses a new concept (cross-snapshot diff) that no existing section renders — Screen History lists snapshots, the ranked table shows one snapshot's rows, neither compares two snapshots. This matches the blueprint's J-20 IA row (`blueprint.md` line 141) and the iter-35 spec's "Blueprint conformance" field, both of which registered `/desk` as the canonical home before the build. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `desk_screen_diff._not_found_response()` returns `base_resolution: None` for an unresolved `?id=` (`desk_screen_diff.py:571-582`), a fourth value beyond the three the blueprint's Data Contract row and the iter-35 spec's shape both enumerate (`"explicit" | "default_prior_date" | "none_earlier"`). This is intentional and test-covered (`test_unknown_compare_id_is_an_honest_null` asserts `base_resolution is None`) and does not create a second source of truth or a duplicate computation — it is a minor type-shape documentation gap, not a coherence violation. Worth a one-line addition to the Data Contract's declared enum (`| null`) next time this row is touched, but does not block this iteration.
