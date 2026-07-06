# goal-tape_to_profit_support_resistence-iter-3 Dev Handoff

**Phase:** goal-tape_to_profit_support_resistence-iter-3
**Date:** 2026-07-06
**Agent:** developer
**Status:** complete

## What Was Built

J-03 — confluence zones + A/B/C conviction classes, the classification half of Data Contract row 39
that iter-2 (J-02) deliberately left out of scope. Built entirely INSIDE the existing
`research/levels.py` (the registered row-39 owner) as an additive field on `compute_levels`'s
return dict — no new module, endpoint, or MCP tool, per the plan:

- **`research/levels.py`** — two new functions plus three new constants:
  - **`_cluster_levels(levels, band_bps)`** — pools levels across EVERY timeframe and clusters them
    by price proximity with an ANCHOR-FIXED scan (sorted ascending by price; the first/lowest
    member of a cluster fixes its tolerance window — `anchor * band_bps / 10_000` — and every
    subsequent candidate is compared to that FIXED anchor, never the previous member, so a
    cluster's price span is bounded by one tolerance rather than an unbounded chain of
    near-neighbours). Only clusters with >= 2 members are "qualifying" and returned; a lone level
    has no confluence partner and is silently dropped (never a fabricated one-member "zone").
  - **`_grade_zone(members, config)`** — the A/B/C decision, by DISTINCT-TIMEFRAME breadth alone
    (goal.md's "levels that align across timeframes matter more"), never by score: class A needs
    both a config-owned minimum distinct-timeframe count AND at least one member timeframe in the
    existing `PRIOR_PERIOD_TIMEFRAMES` long-term bucket (reused verbatim — no second "long-term"
    list); class B needs only the (lower) distinct-timeframe floor; a qualifying cluster whose
    members share exactly ONE timeframe grades C — a real, honestly-reported zone of the lowest
    conviction, never suppressed.
  - **`compute_confluence_zones(levels, config)`** — the canonical, exported entry point: clusters
    `levels`, builds each zone (`levels` members, a timeframe-weighted `score` = sum of member
    `strength` values — already timeframe-weighted per level, so never double-weighted — and the
    `class`), sorts zones by an explicit total order (`_zone_sort_key`: lowest member price, then
    member count) for byte-identical served JSON. **A PURE function of the already lookahead-free
    `levels` list** — it touches no store/bar of its own, so it inherits the as-of truncation for
    free (no second truncation surface to get wrong).
  - `CLASS_A = "A"`, `CLASS_B = "B"`, `CLASS_C = "C"` — the three honest grades.
  - `compute_levels` now returns `{"levels": [...], "no_bar_series_for_symbol": bool,
    "confluence_zones": [...]}` — the new field is additive, always `[]` when `levels` is empty
    (whichever honest reason).
- **Config** (`config.py`): `sr_confluence_band_bps` (float, default 20.0 — wider than the existing
  `sr_touch_tolerance_bps` of 5.0 because independent timeframes' own detected extremes rarely land
  on the exact same price the way a single series' own touches do, calibrated against the committed
  PG fixture to produce several distinct, informative zones rather than one degenerate blob),
  `sr_confluence_class_a_min_timeframes` (int, default 3), `sr_confluence_class_b_min_timeframes`
  (int, default 2). All three added to `config_fingerprint()`'s `excluded` set (the identical
  `sr_pivot_lookback` rationale — confluence is a separate research computation never stamped with a
  `config_fingerprint`) — the pinned `default` fingerprint stays `4d665603569b9dbf` (verified).
- **Route** (`research/routes.py`): no route-BODY change — the route already spreads
  `compute_levels`'s dict verbatim (`**result`), so `confluence_zones` flows through automatically.
  Updated the comment block above the route (previously marked `classes` "deliberately ABSENT
  this iteration") and the route's own docstring to describe the new field.
- **MCP** (`mcp/__init__.py`): no dispatch-logic change — the `levels` tool is a byte-for-byte HTTP
  proxy of the REST response body, so any new field flows through automatically. Updated the tool's
  `description` text to mention confluence zones/classes for doc parity.

## Design decisions (beyond the plan's explicit direction)

- **Field name**: `confluence_zones` (not the placeholder `classes` name used in the iter-2
  "deliberately ABSENT" comments) — clearer, since each zone itself carries a `class`; the plan
  explicitly left the exact name as the developer's call.
- **Zone shape**: exactly three keys per zone — `levels` (member level dicts, unchanged shape, each
  already carrying its own `timeframe`), `score`, `class`. No redundant `timeframes` convenience
  field was added (a consumer can derive distinct timeframes from `levels[].timeframe` trivially) —
  keeping the additive contract minimal, per the simplicity bar.
- **A qualifying cluster needs >= 2 members, of ANY timeframe(s)** — not >= 2 DISTINCT timeframes.
  A same-timeframe cluster (e.g. two nearby swing pivots on one 1h series) IS a real, reportable
  zone — just graded C (the lowest conviction), never suppressed. This reads "a symbol with levels
  but no qualifying cluster returns an explicit empty zones list" as "no qualifying cluster" meaning
  "no 2+ levels close in price at all," with the A/B/C grade separately answering "how many
  independent timeframes agree" — cleanly separating the CLUSTERING concern (price-based) from the
  GRADING concern (timeframe-diversity-based). Verified on the real committed PG fixture: 5 of its 6
  real zones are same-timeframe (1d-only) C-grade zones.
- **Class A requires BOTH a distinct-timeframe-count floor AND a long-term member** — not count
  alone. A direct unit test
  (`test_confluence_class_a_requires_a_long_term_member_not_just_timeframe_count`) proves a
  3-distinct-timeframe cluster with NO long-term member (1h+4h+8h) grades B, not A — the two
  conditions are independently enforced.
- **Anchor-fixed clustering, not chained-to-previous-member** — documented and directly tested
  (`test_confluence_clustering_is_anchor_fixed_not_chained_to_the_previous_member`) to prevent the
  classic clustering defect where a chain of pairwise-close levels lets a cluster's price span drift
  unbounded.
- **Corrupt-sole-series seam (plan's explicit ask to decide + document, not fix)**: confirmed by
  inspection that `compute_confluence_zones` takes ONLY the already-derived `levels` list as input —
  it never touches `store` or `BarStore.list()`'s `integrity_errors` half. A symbol whose sole bar
  series is corrupted therefore still aliases to `no_bar_series_for_symbol: true` with an empty
  `confluence_zones` list, exactly as it aliased before confluence existed (iter-2's B1 finding,
  unchanged). The distinct corrupt-series honest state remains owned by `GET /research/bars`. J-03
  introduces no new fabricated or aliased state at the levels endpoint.

## Files Changed

- `apps/backend/app/config.py` -- `sr_confluence_band_bps`, `sr_confluence_class_a_min_timeframes`,
  `sr_confluence_class_b_min_timeframes`; all three excluded from `config_fingerprint`
- `apps/backend/app/research/levels.py` -- `_cluster_levels`, `_grade_zone`, `_confluence_zone`,
  `_zone_sort_key`, `compute_confluence_zones`, `CLASS_A`/`CLASS_B`/`CLASS_C`; `compute_levels`
  wires `confluence_zones` into its return dict; module + function docstrings updated (confluence
  classes are now in scope, no longer "J-03, out of scope here")
- `apps/backend/app/research/routes.py` -- updated the comment block above `GET /research/levels`
  (previously "classes deliberately ABSENT") and the route's own docstring; no route-body change
- `apps/backend/app/mcp/__init__.py` -- updated the `levels` tool's `description` text; no
  dispatch-logic change (already a byte-identical proxy that forwards any new field)
- `apps/backend/tests/test_levels.py` -- extended: 11 new test functions (8 direct
  `compute_confluence_zones` unit tests covering clustering/scoring/A/B/C grading/anchor-fixed
  behaviour/sorting/empty cases; a new 3-timeframe synthetic bar fixture (`_confluence_fixture`,
  symbol `SYN-CONFLUENCE`) proving a real bar-derived class A zone through `compute_levels` end to
  end; an exact-value test on the committed PG fixture; an honest-empty-zones test reusing the
  existing J-02 swing fixture) plus in-place extensions to 6 existing tests (the lookahead-free
  test now asserts zones/class are unaffected by a later bar too; the determinism test asserts a
  non-vacuous zone; the three honest-state tests assert `confluence_zones: []`; the no-magic-numbers
  and fingerprint-exclusion tests cover the three new config fields)
- `apps/backend/tests/test_levels_api.py` -- extended the happy-path test to assert
  `confluence_zones == []` on its single-timeframe fixture; extended the three honest-state tests
  the same way; added one new route-level test that seeds the real committed PG fixture pair
  directly into the temp bar dir (mirroring `test_mcp_server.py`'s technique) and asserts the exact
  zones shape through the REAL route
- `apps/backend/tests/test_mcp_server.py` -- extended the existing `levels` byte-identity test with
  a `confluence_zones` non-empty assertion (the byte-for-byte proxy check already covered the field
  structurally; this makes the coverage intent explicit and non-vacuous)

`git diff -- apps/frontend/` is **empty** — confirmed no frontend file was touched.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q --junit-xml=/tmp/junit.xml`
Result (JUnit XML totals): **1107 passed, 1 skipped, 1108 collected, 0 failed, 0 errors**, 362.28s.
The single skip is the same pre-existing gated live-socket test noted in every prior iteration's
handoff. Up from iter-2's baseline of 1095 passed / 1096 collected — **+12 new tests** (11 in
`test_levels.py`, 1 in `test_levels_api.py`), **zero regressions**.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py tests/test_profile_equivalence.py tests/test_real_data_gate.py -v`
Result: **57 passed** (7 + 15 + 35 — identical counts to iter-1/iter-2's handoffs; the J-07
byte-identical-`default` guard, the pinned-fingerprint test, and the vendor-confinement gate are all
unaffected).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_levels.py tests/test_levels_api.py tests/test_mcp_server.py -v`
Result: **57 passed** (26 + 10 + 21).

Command: `cd apps/backend && .venv/bin/python -c "from app.config import CONFIG; assert CONFIG.config_fingerprint() == '4d665603569b9dbf'"`
Result: passes — the pinned `default` fingerprint is confirmed unchanged despite three new
`Config` fields.

Command: `git diff --stat -- apps/frontend/`
Result: empty (no output) — confirmed.

Command: `grep -rn "structure_tape\|research/strategies\|research\.strategies" apps/backend/app/`
Result: no matches — confirmed J-04–J-06 remain unbuilt, no scope creep.

## Pre-Handoff Verification

- **Service startup**: ran `bash scripts/dev.sh`, confirmed backend (uvicorn on :8301) and frontend
  (Next.js on :3301) started cleanly with no errors. Force-stopped every backend/frontend PID
  (including the `next-server`/`next dev` grandchild worker processes noted in iter-2's handoff —
  `pkill -f "next dev"` alone did not catch them this run either; killed by explicit PID), confirmed
  both ports free via `lsof`, then ran `dev.sh` a second time — both services bound cleanly with no
  port conflicts.
- **Live smoke test** (against the real `dev.sh`-started backend, not just the test suite): seeded
  the committed PG fixture pair into `apps/backend/.data/bars/`, then hit
  `GET /research/levels?symbol=PG&as_of=2026-06-09T21:00:00Z` over real HTTP and called the MCP
  `levels` tool against that same live backend via `TAPEOLOGY_API_BASE` — both returned
  `confluence_zones` with the identical 6-zone (5×C, 1×B) result verified in the test suite. Also
  checked live: a missing `as_of` (422), a malformed `as_of` (422), and an unrecorded symbol
  (`no_bar_series_for_symbol: true`, `confluence_zones: []`). Seeded fixture files were removed from
  the dev data directory after the check; no test data was left behind.
- **No new external integration or native dependency** this iteration (a pure derived-computation
  layer over the existing bar store) — the corresponding pre-handoff checklist items are N/A.

## Known Issues

- **`sr_confluence_band_bps` (20.0 bps default) is a documented research starting point, not a
  validated edge** — same "RESEARCH DEFAULT, calibrated against the sims/fixtures, never a
  validated edge" discipline the existing `sr_pivot_lookback` etc. already use. Calibrated so the
  committed PG fixture (2 timeframes) forms several distinct, informative zones rather than one
  degenerate blob spanning the whole price range — verified by direct computation, not
  hand-derived, and asserted exactly in `test_levels.py`.
- **`sr_confluence_class_a_min_timeframes` / `sr_confluence_class_b_min_timeframes` are single
  global values**, matching the plan's own precedent (`sr_pivot_lookback` /
  `sr_touch_tolerance_bps` are likewise single global values, not per-timeframe or per-symbol).
- **The committed real PG fixture can never produce a class A zone** (it stores only 1h + 1d — two
  timeframes; class A needs three) — an honest, documented consequence of the committed data's own
  breadth (flagged in the plan's own "Known Consideration"), not a defect. Class A is proven
  reachable through the real bar-driven `compute_levels` path on a dedicated synthetic 3-timeframe
  fixture (`SYN-CONFLUENCE`, `test_synthetic_three_timeframe_fixture_produces_exact_a_b_c_zones_through_compute_levels`)
  and directly on the pure `compute_confluence_zones` function
  (`test_confluence_clustering_joins_within_band_across_timeframes_and_grades_class_a`).
- **No support-vs-resistance "kind" labelling of a zone** — correctly out of scope per the phase
  spec (a J-04 tape-confirmation concern); a zone is a horizontal price cluster only.
- **J-04–J-06 remain unbuilt, as scoped** — no `structure_tape` strategy, strategy registry, or
  named-strategy comparison exists yet; `GET /research/strategies` still 404s (grep-confirmed no
  such route/module exists).
- **No frontend/UI surface** — machine-only (REST + MCP), as scoped; no page, panel, or nav change.
  Confirmed via `git diff -- apps/frontend/` (empty).
- **The corrupt-sole-series seam decision (iter-2 B1, revisited)**: unchanged from iter-2 — a
  corrupted sole bar series still aliases to `no_bar_series_for_symbol: true` rather than a distinct
  integrity-error state at the levels endpoint. See "Design decisions" above; this is a deliberate,
  documented scope reading (the phase spec explicitly asks to decide-and-document, not fix), not a
  gap discovered mid-implementation.
- **`.claude/project-template.md` is still the generic unfilled template** (carried over from every
  prior iteration, not this iteration's scope) — this developer again used `docs/goal.md`'s
  Constraints section, `scripts/dev.sh`, and the venv at `apps/backend/.venv/` as the actual stack
  source of truth. The backend venv runs Python 3.14.4.
