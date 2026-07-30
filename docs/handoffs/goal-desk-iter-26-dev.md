# goal-desk-iter-26 Dev Handoff

**Phase:** goal-desk-iter-26
**Date:** 2026-07-30
**Agent:** developer
**Status:** complete

## What Was Built

**J-17 — a top-up asks the vendor only for the bars the frozen store cannot already prove.**

`desk_topup_compute.py` gains `_pair_window(bar_store, symbol, timeframe)`, which derives ONE
pair's fetch window from that pair's OWN frozen content via the canonical
`BarStore.merged_bars(symbol, timeframe)` read (`bars.py:557` — the SAME accessor
`desk_screen.py`'s reference-close/history walk already uses), never `bar_index`'s
`window_end_utc` (which records what an earlier run ASKED for, not what the store can prove).
Three cases, decided by a single ascending `merged_bars` read:

- nothing frozen for the pair -> the byte-identical full `_TOPUP_LOOKBACK_DAYS` window
  `_fetch_window_now()` already asks for today (`window_basis: "full_lookback"`).
- frozen history shorter than the lookback start -> the SAME full window (`"full_lookback"`) —
  short histories keep deepening exactly as they do today.
- frozen history reaching the lookback start -> a tail window `[that pair's own newest frozen
  bar's UTC date, today]` (`"tail"`).

`_run_one_pair` calls `_pair_window` once, internally, to build the actual fetch body sent to
`record_bar_series` (the SAME existing fetch-and-record seam, unmodified). `run_topup` calls
`_pair_window` again, independently, immediately BEFORE `_run_one_pair`, purely to capture the
pre-fetch provenance for that pair's outcome entry — both reads see identical store content
(nothing is written between them), so the two calls always agree.

A new outcome value, `"unchanged"`, is added beside the existing `"reused"`/`"fetched"`/`"failed"`:
`_run_one_pair` now classifies `record_bar_series`'s own 409 (`BarSeriesAlreadyRegistered`,
`routes.py:681`) as `"unchanged"` — a real vendor call ran and returned only bars already frozen —
distinct from `"reused"` (a store-first exact-key hit, zero vendor calls). Every other refusal
keeps its verbatim detail and its `"failed"` label.

Every per-pair outcome entry (from both the manager's worker path and the CLI's `main()`) now
carries four additive fields: `requested_window: {start, end}`, `store_frozen_from: str | null`,
`store_frozen_through: str | null`, `window_basis: "tail" | "full_lookback"`. These are computed
inside `run_topup`/`_run_one_pair` itself (never a downstream enrichment step), which is what keeps
the existing byte-identity test between the manager's persisted record and `run_topup`'s own return
value passing unmodified. `desk_topup_log.py` needed **zero code changes** — it is already a pure,
schema-agnostic passthrough persister (`record()`/`list()` copy whatever keys an outcome dict
carries), so the new fields flow through the SAME single shared writer
(`desk_topup_log.record_topup_run`) with no store-side change; a run recorded before this
iteration keeps its four-key shape exactly as recorded, served verbatim by `GET
/research/desk/topup/runs` (no backfill, ever).

**Frontend** — `/desk`'s already-shipped Top-up Runs section (no new section, no new control, no
new ranked-table column):
- The latest-run counts line extends to `N reused · N fetched · N unchanged · N failed`
  (`topupOutcomeCounts`).
- A new descriptive line (`topupWindowBasisCounts`) states how many pairs asked for a tail window
  vs. the full lookback window — a plain tally of the served payload's own `window_basis` field,
  nothing derived; returns `null` (rendered as the honest `WINDOW_BASIS_NOT_RECORDED` fallback,
  `"window basis not recorded in this run"`) when ANY outcome in the run lacks `window_basis`
  (a legacy, pre-iter-26 run — a single shared writer lands a run's outcomes all at once, so a run
  is either entirely legacy or entirely new, never a mix).
- Each already-rendered failed pair's row additionally shows its own recorded `requested_window`
  (or the same honest fallback text for a legacy run).
- Copy stays descriptive measurement only — counts and windows, no saving/efficiency/speed/
  recommendation claim.

Zero diff to `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py`,
`levels.py`, `StructureChart.tsx`, `PriceChart.tsx` (verified via `git diff --stat`, all empty).
Zero new `Config` field (`git diff --stat app/config.py` empty); `Config().config_fingerprint()`
still reads `08e471b10130e1e2`. MCP surface still exactly 17 tools (`test_mcp_server.py`'s
`len(TOOL_NAMES) == 17` assertion, unmodified, passes).

## Known Issues

> **SUPERSEDED for the first item below — see "Fix Notes (review FAIL, 2026-07-30)" at the end of
> this handoff.** The disclosed test casualty is now FIXED (one reviewer-directed assertion edit);
> the full backend suite is green. The paragraph immediately below is retained verbatim as the
> record of why the casualty was structurally unavoidable — its "NOT edited / disclosed rather than
> fixed" resolution no longer describes the shipped state.

**One structurally-unavoidable existing-test casualty (disclosed, not fixed, per this iteration's
own OUT-OF-SCOPE text):** `test_desk_topup_compute.py::test_cli_triggered_run_persists_a_record_with_the_identical_shape_as_a_manager_triggered_one`'s
`assert outcome.keys() == {"symbol", "timeframe", "outcome", "detail"}` now fails — the Data
Contract mandates four new keys on every per-pair outcome entry, and there is no implementation of
that mandate under which a REAL run's persisted outcome entries keep exactly four keys. This is
proven structurally, not just observed: the same file's
`test_manager_triggered_runs_persisted_outcomes_are_byte_identical_to_run_topups_own_return`
requires the persisted record's `outcomes` to equal `run_topup`'s own raw return value
byte-for-byte, so the new fields MUST originate inside `run_topup`/`_run_one_pair` itself for that
assertion to keep holding — which means every path (manager- and CLI-triggered alike) produces the
same 8-key entries, unavoidably breaking the other test's 4-key pin. The test's own assertion was
NOT edited (the iteration's OUT-OF-SCOPE text forbids editing existing assertions in this file);
a header comment block was added directly above the new J-17 test section disclosing this exact
casualty. TC-7 ("second run is all-reused with zero vendor calls") and TC-8 (resumability) — the
two scenarios this iteration's OUT-OF-SCOPE text names explicitly — both pass unmodified, verified
by name (`test_second_run_over_the_same_universe_is_all_reused_with_zero_vendor_calls`,
`test_pairs_already_recorded_report_reused_while_the_rest_report_fetched_the_resumability_guarantee`).
`git diff` on `test_desk_topup_compute.py` contains zero deletion lines — the entire diff is
additive, confirming no existing test body was touched.

**TC-6/TC-10 evidence not captured by this dev pass.** The populated, fixture-scoped top-up run
needed for the browser screenshot (four-outcome counts line with `unchanged` > 0, tail-vs-
full-lookback line, a failed pair's `requested_window`) and the `[NEW]`-flagged demo-narrator
walkthrough belong to the browser-qa dispatch per this iteration's own NOTES (the scoped-rig
recipe — a FRESH, fixture-scoped copy of `apps/backend/.data`, never the ambient store). Dev's own
tests (fixture-scoped, injected fake adapter, no network) already prove the underlying behavior
(TC-1 through TC-4); no live evidence capture was attempted here.

**SHA-256 byte-identity listing (DoD item) not produced by this pass.** No test or verification
step in this dev pass wrote to the operator's ambient `apps/backend/.data` store (confirmed: the
dev server was started only to verify startup/no-port-conflicts, and the one live check against it
was a read-only `GET /research/desk/topup/runs` and `GET /desk`); the append-only proof itself is a
browser-qa/audit-lane artifact per the iteration's NOTES.

**A restart gotcha worth noting for later dispatches:** `scripts/dev.sh`'s own port-clearing logic
(`fuser -k -9 $PORT/tcp`) correctly kills whatever process is bound to the port regardless of its
command-line name. A manual `pkill -f "next dev -p 3301"` does NOT — Next.js's actual listening
process is a child `next-server` binary whose command line does not contain the parent's
invocation string, so it survives a name-pattern kill. Verified directly: `scripts/dev.sh` was
started, stopped (`fuser -k -9` on both ports, confirmed via `ss -tln`), and restarted cleanly a
second time with no port conflicts — both backend (`:8301`) and frontend (`:3301`) came up and
served real responses (`GET /research/desk/topup/runs` returned the one real, pre-iteration
(2026-07-29) ambient top-up run, correctly lacking the four new fields — i.e. the legacy-absence
path is exercised by real ambient data). Both servers were stopped before finishing this task via
`fuser -k -9` on both ports (confirmed via `ss -tln`), not a name-pattern `pkill` alone.

## Files Changed

- `apps/backend/app/research/desk_topup_compute.py` — `_pair_window` (new), `_iso_bar_epoch` (new
  helper), `_run_one_pair`'s 409 -> `"unchanged"` classification, `run_topup`'s per-pair outcome
  entries gain the four new fields, module docstring gains a "goal-desk-iter-26, J-17" section.
- `apps/backend/tests/test_desk_topup_compute.py` — additive only (zero deletions): a
  source-introspection guard (`merged_bars` used, `bar_index.window_end_utc` never attribute-
  accessed) plus its own seeded counter-test; TC-1/TC-2/TC-3 window-selection unit tests against
  `_pair_window` directly; an end-to-end tail-window test against the injected fake adapter's own
  received arguments; TC-4 (`"unchanged"`, not `"failed"`, no second series file written); a header
  comment disclosing the one unavoidable existing-test casualty (see Known Issues).
- `apps/backend/tests/test_desk_topup_log.py` — additive only: two tests proving the store is a
  pure passthrough for the new J-17 outcome shape, and that a legacy (pre-iter-26) run record still
  round-trips exactly as written, with none of the four new fields backfilled.
- `apps/backend/tests/test_desk_topup_window_disclosure_guard.py` — new file, the
  `test_desk_ui_guards.py` source-introspection pattern applied to `/desk`'s page source: proves
  the honest fallback text is a single shared constant (never a second, independently-typed copy),
  the four-outcome counts line is present, and `topupWindowBasisCounts` returns `null` (never a
  guessed/backfilled count) when any outcome lacks `window_basis` — plus a seeded counter-test
  proving the fallback-text guard can actually fail.
- `apps/frontend/lib/types.ts` — `DeskTopupOutcome.outcome` gains `"unchanged"`; the interface
  gains `requested_window?`, `store_frozen_from?`, `store_frozen_through?`, `window_basis?`.
- `apps/frontend/app/desk/page.tsx` — `topupOutcomeCounts` gains an `unchanged` bucket;
  `topupWindowBasisCounts` (new) + `WINDOW_BASIS_NOT_RECORDED` (new shared constant);
  `LatestTopupRunDetail` renders the extended counts line, the new tail-vs-full-lookback line, and
  each failed pair's own `requested_window`.

`desk_topup_log.py` itself carries no diff (see "What Was Built" — the writer needed no change).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1473 passed, 1 failed, 8 skipped** (full suite). The one failure is the disclosed,
structurally-unavoidable casualty described in Known Issues
(`test_cli_triggered_run_persists_a_record_with_the_identical_shape_as_a_manager_triggered_one`).
Independently verified counts by parsing the dot-summary output (1473 `.` + 1 `F` + 8 `s` = 1482
collected).

Targeted: `.venv/bin/python -m pytest tests/test_desk_topup_compute.py tests/test_desk_topup_log.py tests/test_desk_topup_window_disclosure_guard.py -v`
→ 53 passed, 1 failed (54 collected; the same known casualty).

`.venv/bin/python -m pytest "tests/test_desk_topup_compute.py::test_second_run_over_the_same_universe_is_all_reused_with_zero_vendor_calls" "tests/test_desk_topup_compute.py::test_pairs_already_recorded_report_reused_while_the_rest_report_fetched_the_resumability_guarantee" -v`
→ 2 passed (TC-7/TC-8, the two scenarios this iteration's OUT-OF-SCOPE text names explicitly).

`.venv/bin/python -m pytest tests/test_mcp_server.py -q` → 38 passed (confirms the exactly-17-tool
contract, unmodified).

`Config().config_fingerprint()` → `08e471b10130e1e2` (unchanged; `git diff --stat app/config.py`
is empty — zero new Config fields).

`git diff --stat` over `bars.py`/`bar_index.py`/`desk_coverage.py`/`desk_screen.py`/
`tradability.py`/`levels.py`/`StructureChart.tsx`/`PriceChart.tsx` — empty (zero diff, as required).

`git diff` over `test_desk_topup_compute.py` — zero deletion lines (purely additive).

Frontend: `cd apps/frontend && ./node_modules/.bin/tsc --noEmit` → clean, no output.
`rm -rf .next && npx next build` → compiles, lints, and type-checks cleanly; `/desk` route builds
(8.44 kB, 118 kB First Load JS).

Service startup: `scripts/dev.sh` started both backend (`:8301`) and frontend (`:3301`) cleanly;
stopped (port-based `fuser -k -9`, confirmed free via `ss -tln`); restarted a second time with no
port conflicts. Both servers stopped before finishing this task.

## Fix Notes (review FAIL, 2026-07-30)

Fix pass against `reports/reviews/goal-desk-iter-26-review.md` (verdict FAIL). Both of the
report's entries are addressed below; nothing else in the tree was touched.

### CRITICAL — `test_desk_topup_compute.py:1081`, the four-key outcome pin (FIXED)

The reviewer independently reproduced the disclosed failure and ruled that the iteration spec's
own "disclose rather than edit" exception does not reach this test, because that exception covers
only tests that "genuinely pin the shipped window for a pair whose frozen history already reaches
the lookback start" — this one pins the outcome dict's key SET, not a window — while the
DEFINITION OF DONE's *unqualified* "Full backend suite green with zero regressions" does bind.
The reviewer's own `fix_task` names the resolution: extend this one assertion with the four new
keys, since (as the reviewer explicitly accepted) the structural proof that it cannot coexist with
the mandated Data-Contract fields is sound.

Applied exactly that, and nothing more:

- `apps/backend/tests/test_desk_topup_compute.py` — the single line
  `assert outcome.keys() == {"symbol", "timeframe", "outcome", "detail"}` is EXTENDED to the eight
  keys the shared writer now produces (`+ requested_window, store_frozen_from,
  store_frozen_through, window_basis`), with an inline comment naming it as the carve-out. The
  assertion keeps its exact key-SET-equality form, so it still fails on any cross-path schema
  drift — which is the property the test's own name claims ("identical shape as a
  manager-triggered one"). It is not relaxed to a subset/superset check.
- Same file — the J-17 section header comment, which previously read "KNOWN, DISCLOSED,
  UNAVOIDABLE existing-test casualty (not fixed here…)", is rewritten to describe the carve-out
  as applied. Leaving prose asserting a red test in a green tree would have been dishonest.

**Scope of the edit — the honest accounting.** `git diff -U0` on
`test_desk_topup_compute.py` now contains **exactly one deletion line**: that assertion. No other
pre-existing assertion, body, or fixture in the file was touched. TC-7
(`test_second_run_over_the_same_universe_is_all_reused_with_zero_vendor_calls`) and TC-8
(`test_pairs_already_recorded_report_reused_while_the_rest_report_fetched_the_resumability_guarantee`)
— the two the spec names explicitly — remain byte-identical and pass.

**Sign-off status — READ THIS.** The reviewer's fix task asked for explicit product/spec sign-off
*before* the edit, or a formally recorded carve-out. A dev agent has no channel to a human, so the
edit was applied and is recorded here as a **carve-out awaiting ratification**, not as a granted
approval. The spec is genuinely self-contradictory on this point — it mandates four additive
fields on every per-pair outcome entry AND forbids editing a test pinning that entry's key set to
four — and one of the two had to give. The DoD gate ("full backend suite green", unqualified) was
treated as the binding one; the alternative (ship red) fails an explicit DoD line and stalls the
review loop indefinitely with no path to green. **The auditor/evaluator should ratify or reject
this carve-out explicitly.** If rejected, the only other consistent resolution is to amend the
spec's OUT-OF-SCOPE clause, not to change the code — no implementation of the mandated contract
leaves a real run's outcome entries at four keys.

### NOTE — `desk_topup_compute.py:172`, `_pair_window` called twice per pair (NOT changed, deliberate)

Left as is. The reviewer marked it `optional` ("if profiling ever shows it matters"), and it is
not a defect: `_run_one_pair`'s `(symbol, timeframe, bar_store, bar_index, registry)` signature is
deliberately unchanged so the existing tests that monkeypatch it *wholesale* keep working
unmodified — threading the window in as a parameter would break exactly the class of existing
test this iteration is under orders not to disturb. The second read is a pure `merged_bars` read
against unchanged store state. Fix-mode discipline also forbids unlisted changes.

### Verification after the fix

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **exit 0 — 1474 passed, 0 failed, 8 skipped** (1482 collected). Counts re-derived by
parsing the progress characters (`1474` × `.`, `8` × `s`, zero `F`/`E`), and `grep -c '^FAILED|^ERROR'`
returns 0. This is the previously-red suite now green with the one fixed test moving from `F` to `.`
(1473+1 → 1474 passed).

Targeted: `pytest tests/test_desk_topup_compute.py tests/test_desk_topup_log.py tests/test_desk_topup_window_disclosure_guard.py -q` → exit 0, 54 passed.

Re-verified unchanged after the fix (the fix touches only a test file, but the zero-diff
constraints are law, so they were re-checked rather than assumed):

- `Config().config_fingerprint()` → `08e471b10130e1e2`.
- `git diff --stat` over `app/research/bars.py`, `app/research/bar_index.py`, `desk_coverage.py`,
  `desk_screen.py`, `tradability.py`, `levels.py`, `StructureChart.tsx`, `PriceChart.tsx`,
  `config.py`, `desk_topup_log.py` → **empty** (each path confirmed to exist first, so the empty
  output is a real zero-diff and not a stale pathspec).
- No production-code file changed in this fix pass — `desk_topup_compute.py`, `page.tsx`, and
  `types.ts` carry the same diffs the reviewer already verified as correct.

Still outstanding from the original pass, unchanged by this fix and *not* review findings: the
TC-6/TC-10 scoped-rig populated run + browser screenshot + `[NEW]` demo walkthrough (browser-qa
lane), and the SHA-256 append-only byte-identity listing (audit lane).

## Pre-existing-state note

This exact implementation (all files listed above) was already present, uncommitted, in the
working tree when this dev dispatch began — `runs/goal-desk-iter-26/status.json` recorded an
identical prior dev pass (`current_step: dev_complete`) plus downstream evidence artifacts
(`reports/qa/goal-desk-iter-26-evidence/`, a regression-replay report) from what appears to be a
prior review/QA cycle on this same iteration, though `docs/handoffs/goal-desk-iter-26-dev.md` and
`reports/reviews/goal-desk-iter-26-review.md` were both absent at dispatch time. Rather than
re-implementing from scratch (which would risk diverging from already-verified-correct code with
no benefit), this pass independently re-verified every DoD/OUT-OF-SCOPE/acceptance claim against
the actual code and a fresh full test run (see "Tests Run" above — every number was re-derived
directly, not copied from the prior state file) before writing this handoff, which did not exist
until now.
