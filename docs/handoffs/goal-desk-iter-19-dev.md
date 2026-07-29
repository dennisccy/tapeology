# goal-desk-iter-19 Dev Handoff

**Phase:** goal-desk-iter-19
**Date:** 2026-07-29
**Agent:** developer
**Status:** complete

## What Was Built

A one-key selection-rule correction to `_select_opposite_band`, no new fields, no new endpoints,
no UI code:

- `_select_opposite_band` (`apps/backend/app/research/desk_screen.py:274`) now uses its OWN local
  tie-break key — `(distance_bps ascending, class rank DESCENDING via `_CLASS_RANK`, quality_score
  descending)` — instead of delegating to `_select_best_band`'s class-first key (`(-class_rank,
  distance_bps, -quality_score)`). This implements `docs/goal.md` J-14 step 1 verbatim: "distance
  ascending, then class rank descending (`_CLASS_RANK` — an unclassified band ranks lowest, never
  highest), then `band_score` descending, resolved by `min`'s first-of-tie stability over
  `compute_tradability`'s own served order." It corrects iter-18's shipped selector, which silently
  restated the rule as class-first and diverged from goal.md on 2 of 63 real screen rows (HONA,
  META — the iter-18 evaluator's own finding).
- `_select_best_band` (the row's own same-side selection, `desk_screen.py:263`) and
  `_row_rank_key` (cross-symbol rank order) are byte-unchanged — confirmed via `git diff` showing
  zero touch to either function's body, and via TC-7/TC-9 re-runs below.
- The module docstring's "Opposite-band disclosure" section (`desk_screen.py:90`) is corrected to
  describe the distance-first order and tagged "tie-break corrected goal-desk-iter-19" per the
  module's own per-iteration docstring convention.

## Files Changed

- `apps/backend/app/research/desk_screen.py` — `_select_opposite_band` gets its own local `key()`
  closure (distance-first) instead of delegating to `_select_best_band`; module docstring's
  Opposite-band disclosure section corrected and tagged goal-desk-iter-19.
- `apps/backend/tests/test_desk_screen.py` — flipped and renamed
  `test_select_opposite_band_prefers_higher_class_over_closer_distance` →
  `test_select_opposite_band_prefers_closer_distance_over_higher_class` (TC-1: now asserts the
  close-but-lower-class band wins). All other opposite-band tests in the file were re-run, not
  assumed — see "Re-verification of existing tests" below; none needed a value change.
- `apps/backend/tests/test_mcp_server.py` — re-run, no change needed (it seeds `ScreenStore.record`
  directly, bypassing `_select_opposite_band`, so it only tests byte-identical proxying).

No changes to `apps/frontend/app/desk/page.tsx`, `apps/frontend/lib/types.ts`, `tradability.py`,
`levels.py`, `bars.py`, `bar_index.py`, `StructureChart.tsx`, `desk_coverage.py`, `config.py`, or
any `Config` field/MCP tool — confirmed via `git diff --stat` against every one of those paths
(empty in every case).

## Re-verification of existing tests (per plan's explicit instruction to re-verify, not assume)

- `test_select_opposite_band_returns_the_nearest_band_on_the_other_side` — both candidates already
  share class `"B"`, so the two rules agree; passes unmodified.
- `test_select_opposite_band_exact_tie_keeps_the_served_order_first_item` — both tied bands share
  class `"B"` and quality `5.0`; distance-first and class-first agree on an exact tie; passes
  unmodified.
- `test_opposite_band_golden_near_far_and_null_class_rows` (ABBV/ACN/ADBE, TC-1/TC-2/TC-3/TC-4) —
  each symbol's monkeypatched `compute_tradability` result carries exactly ONE opposite-side band,
  so there is no competing candidate for either rule to disagree on; all three fixture rows'
  expected values are unchanged; passes unmodified.
- `test_opposite_band_stays_byte_identical_on_a_recompute_under_identical_pins` (AAPL) —
  shape-only assertion (second compute equals first); passes unmodified.
- `test_a_legacy_row_recorded_without_opposite_band_fields_serves_them_absent_never_backfilled` —
  shape-only (key absence); passes unmodified.
- `test_aapl_row_cross_checks_byte_identical_to_the_real_tradability_route` — derives its expected
  `opposite_band` dynamically from the live `GET /research/tradability` response rather than
  hardcoding a selection, so it needed no change; re-run to confirm, passes.
- `test_desk_screen_opposite_band_and_bands_by_class_fields_proxy_verbatim`
  (`test_mcp_server.py`) — seeds a raw `ScreenStore.record(...)` call directly, bypassing
  `_select_opposite_band` entirely, so it tests byte-identical proxying only; re-run to confirm,
  passes unmodified.
- `_select_best_band`'s own full unit-test suite (TC-7) — re-run in isolation
  (`-k select_best_band`), all pass unmodified.

## Real-data verification (TC-6: reproducing the HONA/META divergence)

Per the spec's explicit instruction, this was verified against REAL data on a read-only rig, never
by writing to `apps/backend/.data`.

**What was tried first and why it didn't work:** copying HONA's/META's already-recorded 1d bar
series into a fresh scoped `BarStore` via `.record()` (the normal fixture-scoped-rig pattern). This
was refused for HONA: the real recorded series contains one already-registered bar with a
non-finite (NaN) price — a pre-existing data-quality issue predating the write-time "priceless bar"
guard in `bars.py` (`NonFiniteBarPriceError`). The read side (`merged_bars`) already excludes that
one bad row from the merged view, but `.record()` validates the whole window atomically, so
re-recording the identical window into a new store isn't possible without already having the
read-side exclusion.

**What was actually run (read-only against the ambient store, zero writes):** a standalone script
instantiated `BarStore` pointed at the real, already-populated `apps/backend/.data/bars` directory
and called `compute_tradability(store, "HONA"/"META", as_of_epoch, CONFIG)` directly — the exact
same read path `compute_screen` uses, with zero calls to `ScreenStore.record`, `UniverseStore.record`,
or `BarStore.record` (confirmed after the fact: `find apps/backend/.data/bars
apps/backend/.data/screen apps/backend/.data/universe -newermt "5 minutes ago"` returned nothing —
only the derived, non-immutable `tradability_cache.db` was touched). `as_of` was pinned to
`2026-07-29T23:59:59Z`, matching the iter-18 evaluator's own cited measurement window.

Result — exact reproduction of the iter-18 evaluator's own cited figures, confirming both that the
divergence is real and that the fix resolves it correctly:

| Symbol | Best band (unchanged, same-side) | OLD rule (class-first, pre-fix) opposite | NEW rule (distance-first, this fix) opposite |
|---|---|---|---|
| HONA | support / class A / 0.00 bps | class A / **336.96 bps** | class B / **153.67 bps** |
| META | resistance / class A / 78.37 bps | class A / **232.58 bps** | class C / **92.05 bps** |

Both rows: old and new rules pick a genuinely different band, byte-different `price_low`/
`price_high`. The numbers are byte-identical to iter-18's own evaluator measurement (`336.96`/
`153.67` for HONA, `232.58`/`92.05` for META), confirming the underlying bar data has not changed
(append-only immutability holds) and the fix produces exactly the corrected behavior the spec's
TC-6 names. This is NOT a surprising-zero-divergence result — the divergence is real and the fix
closes it, as expected.

## Tests Run

Command (exact, established convention): `cd apps/backend && .venv/bin/python -m pytest tests/ -q`

Result: full backend suite green — verified independently via `--junit-xml`:
`tests="1456" errors="0" failures="0" skipped="8"` (1448 passed, 8 skipped, 0 failed, 0 errors).

Targeted re-runs, all green:
- `pytest tests/test_desk_screen.py -q` — 72 tests pass, including all opposite-band tests.
- `pytest tests/test_mcp_server.py -q -k opposite_band` — passes.
- `pytest tests/test_copy_discipline.py -q` — passes unmodified (30 tests).
- `pytest tests/test_desk_screen.py -q -k select_best_band` — TC-7, passes unmodified.
- `python -c "from app.config import CONFIG; print(CONFIG.config_fingerprint())"` →
  `08e471b10130e1e2` (unchanged, TC-11).
- `git diff --stat` against `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`,
  `StructureChart.tsx`, `desk_coverage.py`, `config.py`, `app/desk/page.tsx`, `lib/types.ts` — empty
  for every path (TC-12).

## Known Issues

- None found during this fix. The corrected rule reproduces the exact real-data divergence the
  iter-18 evaluator measured and resolves it in the direction goal.md specifies.
- Pre-existing (not introduced by this change, not in scope to fix): the real, already-recorded
  HONA 1d bar series in `apps/backend/.data/bars` contains one bar with a non-finite (NaN) price,
  predating the write-time `NonFiniteBarPriceError` guard. `merged_bars`/`compute_tradability`
  already exclude it correctly on read (per `bars.py`'s own documented read-side exclusion), so it
  does not affect this iteration's correctness — flagging only because it blocked the
  scoped-rig-via-copy verification approach and had to be worked around with a direct read-only
  recompute instead (documented above).
- The `[NEW]`-flagged demo-narrator walkthrough over populated `/desk` rows (DoD item, TC-14) and
  the browser-QA screenshot evidence (TC-13) are downstream steps per this project's pipeline
  (browser-qa-agent / demo-narrator lanes), not part of the developer agent's own scope this
  iteration — no `page.tsx` code changed, so there is nothing for those lanes to render differently
  beyond the corrected `opposite_band` values a freshly computed screen will now carry.
