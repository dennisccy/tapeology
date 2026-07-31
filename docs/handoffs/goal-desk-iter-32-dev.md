# goal-desk-iter-32 Dev Handoff

**Phase:** goal-desk-iter-32
**Date:** 2026-07-31
**Agent:** developer
**Status:** complete

## What Was Built

**J-19 — every top-up run records the date each pair's frozen history actually reaches.**

`desk_topup_compute.py`'s `run_topup` (the per-pair loop) now calls `_pair_window(bar_store,
symbol, timeframe)` a SECOND, independent time — the SAME pure, repeat-call-sanctioned accessor
J-17 already calls once, pre-fetch — immediately AFTER `_run_one_pair` returns for a pair, and
copies its `store_frozen_through` value onto that pair's outcome entry as a new key,
`store_frozen_through_after`. No new accessor, no second vendor fetch, no arithmetic over bars,
never `bar_index`'s `window_end_utc`. `_run_one_pair`'s own two-value return contract
(`(symbol, timeframe, bar_store, bar_index, registry) -> (outcome, str | None)`) is byte-unchanged,
so every existing test that monkeypatches it wholesale keeps working unmodified — the new field is
computed entirely inside `run_topup` itself, one level above the fake boundary.

Semantics, proven by five new fixture-scoped tests (`test_desk_topup_compute.py`):
- `"fetched"` (the store genuinely gained a new series between the two reads) — `after` is later
  than the pair's own pre-fetch `store_frozen_through`, byte-identical to the newest bar
  `BarStore.merged_bars` reports for that pair after the walk.
- `"unchanged"` / `"reused"` / `"failed"` (nothing was written between the two reads) — `after`
  equals the pair's own pre-fetch `store_frozen_through` exactly.
- A pair holding nothing before the run whose fetch also fails — `after` is `null` (nothing to
  observe), exactly the shape `store_frozen_through` already uses.

`desk_topup_log.py` needed **zero code changes** — it is already a pure, schema-agnostic
passthrough persister, so the new field flows through the SAME single shared writer
(`desk_topup_log.record_topup_run`) with no store-side change; a run recorded before this
iteration keeps its existing (eight- or four-key, depending on when it predates) shape exactly as
recorded, served verbatim by `GET /research/desk/topup/runs` — no backfill, ever. Two new
round-trip tests in `test_desk_topup_log.py` document this explicitly for the new field, mirroring
the J-17 precedent.

**Frontend** — `/desk`'s already-shipped Top-up Runs section, latest-run detail block only (no new
section, no new control, no new column on either table — J-16's width contract untouched):
- A new helper, `topupLibraryReach`, mirrors `topupWindowBasisCounts`'s shape but computes an
  EXTREME rather than a tally: the newest `store_frozen_through_after` across the run's own pairs,
  how many pairs reach it, and the list of pairs whose own recorded value is earlier (or `null`).
  Returns `null` when ANY outcome in the run lacks `store_frozen_through_after` (a legacy run) —
  a single shared writer lands a run's outcomes all at once, so a run is either entirely legacy or
  entirely new, never a mix.
- Rendered as one new descriptive line (`desk-topup-run-latest-reach`, placed right after the
  existing `desk-topup-run-latest-window-basis` line) plus a short list
  (`desk-topup-run-latest-reach-earlier` / `-earlier-row`, rendered only when non-empty), each row
  showing that pair's `symbol`, `timeframe`, and recorded date verbatim. The `null` case renders the
  shared constant `LIBRARY_REACH_NOT_RECORDED` = `"library reach not recorded in this run"`.
  Copy is plain descriptive measurement (dates and counts only) — no fresh/stale/current/behind/
  recommendation language.
- `apps/frontend/lib/types.ts` — `DeskTopupOutcome` gains `store_frozen_through_after?: string |
  null`, optional/additive, mirroring `store_frozen_through`'s own legacy-absence contract.

Verified byte-for-byte: the golden replay scripts `journey-scripts/J-09.json` /
`journey-scripts/J-17.json` assert `desk-topup-run-latest-counts`,
`desk-topup-run-latest-window-basis`, `desk-topup-run-latest-failed` — none of those three testids
or their surrounding render logic were touched; the new block sits strictly BETWEEN the window-basis
div and the failed-pairs block (proven structurally by
`test_desk_topup_library_reach_guard.py::test_the_reach_line_and_earlier_list_are_present_beside_the_window_basis_line`).

Zero diff to `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py`,
`levels.py`, `routes.py`'s `record_bar_series`, `StructureChart.tsx`, `desk_topup_log.py`, `config.py`
(verified via `git diff --stat`, all empty). Zero new `Config` field; `Config().config_fingerprint()`
still reads `08e471b10130e1e2`. MCP surface still exactly 17 tools (`test_mcp_server.py`, 39
passed, unmodified).

## One disclosed, precedented existing-assertion edit (same carve-out as iter-26, extended)

`test_desk_topup_compute.py::test_cli_triggered_run_persists_a_record_with_the_identical_shape_as_a_manager_triggered_one`'s
`assert outcome.keys() == {...}` — the SAME single assertion goal-desk-iter-26 already extended
from four keys to eight (a reviewer-ratified carve-out, `reports/reviews/goal-desk-iter-26-review.md`)
— is extended again, in place, to the nine-key set now produced by the one shared writer
(`+ store_frozen_through_after`). This is structurally unavoidable for the identical reason the
iter-26 carve-out documented: the SAME file's
`test_manager_triggered_runs_persisted_outcomes_are_byte_identical_to_run_topups_own_return`
requires the persisted record's `outcomes` to equal `run_topup`'s own raw return value
byte-for-byte, so `store_frozen_through_after` MUST originate inside `run_topup` itself for that
assertion to keep holding — which means the CLI path's persisted entries carry nine keys too. The
assertion keeps its exact key-SET-equality form (still fails on cross-path schema drift, the
property its own name claims) — it is extended, never relaxed to a subset/superset check. `git diff
-U0` on `test_desk_topup_compute.py` contains deletion lines ONLY for this one assertion and its
immediately-preceding disclosure comment (rewritten to describe the extension, matching the
already-green pattern the iter-26 comment block established) — every other pre-existing assertion
and test body in the file is untouched (verified: `git diff -U0 ... | grep '^-[^-]'` shows exactly
the six comment lines + the one assertion line). TC-7
(`test_second_run_over_the_same_universe_is_all_reused_with_zero_vendor_calls`) and TC-8
(`test_pairs_already_recorded_report_reused_while_the_rest_report_fetched_the_resumability_guarantee`),
the two the spec names explicitly, pass byte-unmodified.

Because iter-26's carve-out was already reviewer-ratified for this exact test and this exact
structural reason (a Data-Contract field added inside the shared writer necessarily grows the
key-set pin), this iteration applies the identical, already-established resolution directly rather
than shipping red and waiting for a second review cycle to re-derive the same conclusion. The
reviewer/auditor should still confirm this reasoning holds; nothing else in the file was touched to
reach it.

## Files Changed

- `apps/backend/app/research/desk_topup_compute.py` — `run_topup`'s per-pair loop gains a second
  `_pair_window` call after `_run_one_pair` returns, writing `entry["store_frozen_through_after"]`;
  `run_topup`'s own docstring and the module docstring (new "goal-desk-iter-32, J-19" section) both
  updated.
- `apps/backend/tests/test_desk_topup_compute.py` — five new fixture-scoped tests (TC-1..TC-5) for
  the four outcome branches plus the holds-nothing/null case; the disclosure header comment above
  the J-17 section extended with an iter-32 addendum; the one carve-out assertion extended to nine
  keys (see above — the only deletion lines in the diff).
- `apps/backend/tests/test_desk_topup_log.py` — two new round-trip tests (new field verbatim;
  legacy record still lacks it).
- `apps/backend/tests/test_desk_topup_library_reach_guard.py` — new file, the
  `test_desk_topup_window_disclosure_guard.py` source-introspection pattern applied to J-19: single
  shared fallback constant, the new block's position relative to the window-basis/failed-pairs
  blocks, `topupLibraryReach`'s null-on-absence structure, plus a seeded counter-test.
- `apps/frontend/lib/types.ts` — `DeskTopupOutcome` gains `store_frozen_through_after?: string |
  null`.
- `apps/frontend/app/desk/page.tsx` — `topupLibraryReach` (new helper) + `LIBRARY_REACH_NOT_RECORDED`
  (new shared constant); `LatestTopupRunDetail` renders the new reach line + earlier-pairs list.

`desk_topup_log.py` itself carries no diff (see "What Was Built" — the writer needed no change).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1522 collected, 1514 passed, 8 skipped, 0 failed, 0 errors**, exit 0. This install's `-q`
mode prints no final summary line (a known, pre-existing environment quirk, also noted in the
iter-3/iter-31 handoffs — reproduces on a bare `--collect-only -q` with no code changes); counts
independently verified two ways: (1) parsing the progress-character stream (`.`/`s`/`F`/`E`) —
1514 `.` + 8 `s` + zero `F`/`E` = 1522; (2) `pytest --collect-only -q`'s per-file counts summed to
the identical 1522 (92 files).

Targeted: `.venv/bin/python -m pytest tests/test_desk_topup_compute.py tests/test_desk_topup_log.py tests/test_desk_topup_library_reach_guard.py tests/test_desk_topup_window_disclosure_guard.py -q`
→ 66 passed (37 + 19 + 5 + 5).

`.venv/bin/python -m pytest tests/test_copy_discipline.py tests/test_desk_ui_guards.py tests/test_desk_hover_tooltip_guard.py -q` → 47 passed, all three DoD-named guard suites green unmodified.

`.venv/bin/python -m pytest tests/test_mcp_server.py -q` → 39 passed (confirms the exactly-17-tool
contract, unmodified).

`Config().config_fingerprint()` → `08e471b10130e1e2` (unchanged).

`git diff --stat` over `bars.py`/`bar_index.py`/`desk_coverage.py`/`desk_screen.py`/`tradability.py`/
`levels.py`/`routes.py`/`StructureChart.tsx`/`desk_topup_log.py`/`config.py`/`mcp/__init__.py` —
empty (zero diff, as required).

Frontend: `cd apps/frontend && ./node_modules/.bin/tsc --noEmit` → clean, no output.
`rm -rf .next && npx next build` → compiles, lints, and type-checks cleanly; `/desk` route builds
(9.43 kB, 119 kB First Load JS).

Service startup: `scripts/dev.sh` started both backend (`:8301`) and frontend (`:3301`) cleanly;
verified `GET /research/desk/topup/runs` (200, serves the one real ambient run — a legacy record
correctly lacking `store_frozen_through_after` on every outcome, confirming the legacy-absence path
is exercised by real ambient data) and `GET /meta/ui-routes` (200); stopped (`fuser -k -9` on both
ports, confirmed free via `ss -tln`); restarted a second time with no port conflicts, then stopped
again the same way. No stray tapeology `uvicorn`/`next dev`/`next-server` process left running
(checked via `pgrep -fa`; the only matches remaining belong to an unrelated sibling project).

## Known Issues

**Live evidence capture (TC-1/TC-10/TC-14's browser/demo half, and the SHA-256 append-only
listing) not produced by this dev pass — deliberately, per this iteration's own NOTES and the
iter-26 precedent.** This dev pass proves the underlying behavior hermetically (five new
fixture-scoped tests, zero network, covering all four outcome branches plus the null case) and
confirms the ambient store's one real recorded run
(`topup-2026-07-29-5de907c83fc4`) is a genuine legacy run that will exercise the
`LIBRARY_REACH_NOT_RECORDED` fallback path. Triggering the ONE new, real top-up run against the
ambient `:3301`/`:8301` pair that the NOTES recommend (to produce genuinely varied
`store_frozen_through_after` values for the `[NEW]`-flagged demo walkthrough and the TC-10
screenshot), the real-browser screenshot itself, the `[NEW]` demo-narrator walkthrough, and the
SHA-256 byte-identity listing over all 759 bar series files are left to the browser-qa/demo/audit
lanes — this dev pass never wrote to the operator's ambient `apps/backend/.data` store (the only
live calls made were the two read-only GETs above).

**The nine-key carve-out (see above) awaits reviewer/auditor ratification**, exactly as the
identical eight-key carve-out did in iter-26 — a dev agent has no channel to a human sign-off; the
resolution applied is the one the iter-26 review already established as correct for this exact
structural conflict, applied again without a fresh review round-trip. If a reviewer disagrees with
generalizing that precedent, the only consistent alternative remains what iter-26's own review
concluded: amend the spec's own contradiction, never leave the suite red.
