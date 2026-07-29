# Iteration 19 — Coherence Audit

**Iteration:** goal-desk-iter-19
**Date:** 2026-07-29
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

This iteration touches exactly one registered Data-Contract row: "Screen snapshots, rank rows, skip
rows" (owner `apps/backend/app/research/desk_screen.py`, served by `GET /research/desk/screen`) —
specifically the already-registered `opposite_band` field. The change is a tie-break-order
correction inside `_select_opposite_band` (`desk_screen.py:274-299`), not a new computation path:

- Old: `_select_opposite_band` delegated to `_select_best_band(opposite_side_bands, close)` (class
  rank descending, distance ascending, quality_score descending).
- New: `_select_opposite_band` uses its own local `key()` closure, `(distance_bps ascending, class
  rank descending, quality_score descending)` via `min(..., key=key)` (`desk_screen.py:293-295`),
  reusing the SAME `_distance_bps` helper and the SAME `_CLASS_RANK` table `_select_best_band`
  already uses — no new helper module, no second `compute_tradability` call, no new `BarStore` read.

Grepped the whole tree for `_select_opposite_band`/`opposite_band` outside test files
(`apps/backend/app/`, `apps/frontend/`): the only computation site is `desk_screen.py:444`
(`opposite = _select_opposite_band(result["bands"], close, best["side"])`); the only serving route
is the pre-existing `GET /research/desk/screen`; the frontend (`apps/frontend/app/desk/page.tsx:414-425`,
`apps/frontend/lib/types.ts:816-841`) only re-formats the field it already rendered in iter-18 — zero
frontend diff this iteration (confirmed via `git diff --stat` and the ui-surface-map). `_select_best_band`
(same-side selection, `desk_screen.py:264-271`) and `_row_rank_key` (`desk_screen.py:312`) are
byte-unchanged, matching the spec's OUT-OF-SCOPE list.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `opposite_band` (ranked row) | OK | `apps/backend/app/research/desk_screen.py:274-299,444,461` — corrected in place, sole owner unchanged |
| `bands_by_class` (ranked row) | OK — untouched | not in this diff |
| `desk_screen` MCP proxy / `get_endpoint` `?date=`/`?id=` reads | OK — verbatim proxies, no shape change | `apps/backend/tests/test_mcp_server.py:521-581` (byte-identity assertion, independent of the specific selected band, still valid) |

No new displayed value was introduced this iteration (README's "Nearest opposite-side wall" bullet
is unchanged text from iter-18, only the iter-17→iter-18 currency-number line was bumped and one new
bullet line about the correction target date was NOT added — the README's product-capability prose
for `opposite_band` was already present pre-iteration and needed no edit since the *rendered shape*
is unchanged, only the selected value on divergent rows).

## Information Architecture check

No new page, route, or nav-skeleton change. `git diff --stat` against the pre-iteration snapshot
confirms zero changes to `apps/frontend/` (any file) and zero changes to `apps/backend/app/meta.py`
(`UI_ROUTES`, the single nav owner). The `opposite` column and its home (`/desk`, Desk nav section)
already existed since iter-18; this iteration only corrects the value it displays.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` opposite column | OK — unchanged home, unchanged nav path | `apps/backend/app/meta.py` (`UI_ROUTES`, 3 rows, untouched); `apps/frontend/app/desk/page.tsx` untouched |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The blueprint's Data Contract section was correctly updated in the same commit scope (`runs/goal-session-desk/state/blueprint.md`, "NOTED at iter-19" entry appended, +19/-1 lines) — registering the
  correction under the existing owner/endpoint with no new row, exactly per this era's own
  documentation convention. Good hygiene, noted for completeness rather than as a defect.
- `apps/backend/tests/test_mcp_server.py` was left unmodified (not in the diff) even though the
  iteration spec's IN SCOPE list conditionally called for updating
  `test_desk_screen_opposite_band_and_bands_by_class_fields_proxy_verbatim` "where the fixture's
  opposite-side divergence changes it." Inspection shows that test only asserts byte-identity across
  the three read paths (`GET /research/desk/screen` vs. the `desk_screen` MCP tool vs.
  `get_endpoint`) against whatever `opposite_band` the fixture resolves to — it is agnostic to which
  tie-break rule produced that value, so no update was structurally required. This is a test-scope
  observation, not a Data-Contract or IA violation, so it is advisory only.
- Out of this iteration's product scope but present in the raw diff: ~67 changed files under
  `incredible_auto_dev/` (the vendored framework's own agents/scripts/docs) and
  `project-extensions/host-guard/host-guard.env`. These are framework-maintenance files, not
  Tapeology product surface or Data-Contract entries, and are outside this gate's charter — noted only
  so a future reader of this verdict is not surprised by the diff's total file count (70) vs. the 3
  product files actually reviewed above.
