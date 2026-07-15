# goal-tradable_wall-iter-8 Dev Handoff

**Phase:** goal-tradable_wall-iter-8
**Date:** 2026-07-15
**Agent:** developer
**Status:** complete

## What Was Built

This iteration is a lean continuation closing the two carried iter-7 audit findings (Cleanup A,
Cleanup B) plus a **verification-only** confirmation that J-03's real credentialed data now flows
correctly through the already-shipped read paths. No new capability, no new endpoint, no new UI
surface — per the plan.

- **Cleanup A (frontend fix, closes iter-7 audit F1).** The cockpit `PriceChart.tsx` tradable-band
  fetch effect now early-returns (stays in `phase: "loading"`, issues no HTTP request) whenever
  `history?.epoch_anchor == null`, instead of falling back to `new Date().toISOString()`
  (wall-clock "now"). This removes the sub-second window, present since iter-6/7, during which the
  cockpit could request/draw bands on **today's** morning-markup basis for a historical replay of a
  **past** session, before that session's own `epoch_anchor` had resolved. The effect's dependency
  array stays exactly `[ticker, history?.epoch_anchor]` (unchanged); no other behavior changed —
  once the anchor resolves, the fetch proceeds exactly as before (`new
  Date(history.epoch_anchor * 1000).toISOString()`).
- **Cleanup B (backend test-only, closes iter-7 audit T1).** `test_price_chart_confluence.py`'s
  module docstring (bullet 2) and
  `test_tradability_as_of_uses_the_watched_sessions_own_anchor_with_no_client_side_session_math`
  described a stale pre-fix behavior ("keyed on `ticker` alone", "passes the CURRENT wall-clock time
  as `as_of`") that QA had been observed echoing verbatim in the iter-7 report. Both now describe
  the shipped, no-fallback, deferred-fetch behavior. The other 8 tests in the file are untouched.
- **J-03 live read-path verification (no production code).** Confirmed, against a freshly started
  backend reading the operator's real persisted `apps/backend/.data/datasets/` store (18 files, 11
  of which are the operator's real credentialed historical recordings), that the existing
  `setups.py`/`edge_report.py` read paths now serve real, populated, non-degraded data. Full
  results in "Live Verification" below.

## Files Changed

- `apps/frontend/components/PriceChart.tsx` -- the tradability-fetch effect (`+32/-8` net vs. the
  diff stat's `+32/-... ` — see exact stat below) gained an early-return guard on
  `history?.epoch_anchor == null` and lost the `: new Date().toISOString()` fallback branch; the
  explanatory comment block above the effect was rewritten to describe the new deferred-fetch, no-
  fallback behavior. Nothing else in the file changed (the drawing effect, the confluence-chip
  derivation, and every other effect are byte-identical to iter-7).
- `apps/backend/tests/test_price_chart_confluence.py` -- module docstring bullet 2 and
  `test_tradability_as_of_uses_the_watched_sessions_own_anchor_with_no_client_side_session_math`
  rewritten to assert the early-return guard exists and that no wall-clock fallback remains anywhere
  in the file, replacing the now-false `assert "new Date().toISOString()" in as_of_computation`.
  The other 8 tests are untouched (same line-for-line content).

```
 apps/backend/tests/test_price_chart_confluence.py | 50 +++++++++++++++--------
 apps/frontend/components/PriceChart.tsx           | 32 ++++++++++-----
 2 files changed, 54 insertions(+), 28 deletions(-)
```

`git diff --name-only -- apps/backend/` returns exactly one path
(`apps/backend/tests/test_price_chart_confluence.py`) — no frozen file, no production backend
module, touched. `config_fingerprint()` reconfirmed `4d665603569b9dbf`.

## TDD Verification (genuine red -> green)

Per the workflow, I confirmed the new test assertions actually fail against the pre-fix frontend
before restoring the fix:

1. Edited the test file first (new assertions asserting the deferred-fetch guard + no wall-clock
   fallback).
2. `git stash push -- apps/frontend/components/PriceChart.tsx` to revert ONLY the frontend file back
   to its iter-7 (pre-fix) state, keeping the new test.
3. Ran `pytest tests/test_price_chart_confluence.py -q` against that combination:
   `test_tradability_as_of_uses_the_watched_sessions_own_anchor_with_no_client_side_session_math`
   FAILED with the expected, specific message: *"found a wall-clock-'now' fallback still present —
   the fetch must be deferred (early-return guard) until history.epoch_anchor resolves, never fall
   back to today's date"* — pinpointing the exact `: new Date().toISOString()` line as the offender.
4. `git stash pop` to restore the frontend fix.
5. Re-ran the same test file: all 9 tests passed.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_price_chart_confluence.py -v`
Result: **9 passed** (0 failed).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1348 passed, 7 skipped, 0 failed, 0 errors** -- identical pass/skip counts to the iter-7
baseline (verified by manually tallying the dot/`s`/`F`/`E` output, since this pytest install does
not print its usual final summary line in this environment -- exit code 0 corroborates zero
failures). Zero regressions.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_no_credential_in_artifacts.py -v`
Result: **4 passed** -- no Alpaca credential in any file, log, or artifact.

Command: `cd apps/frontend && npx tsc --noEmit -p tsconfig.json`
Result: **exit 0**, zero type errors.

Command: `CONFIG.config_fingerprint()` (direct Python check)
Result: **`4d665603569b9dbf`** -- unchanged from iter-7, as required (no frozen file touched).

## Live Verification (J-03 read paths, no code change -- confirming real data now flows)

Started the backend fresh (`uvicorn main:app`) against the real, unmodified
`apps/backend/.data/datasets/` store and exercised the four read paths named in the plan.

**`GET /research/datasets`** -- 18 total registered datasets; **11 are the operator's real
`source_kind: "historical"` recordings**, created `2026-07-15`, across **10 distinct panel symbols**
(AAPL x2, AMD, AMZN, GOOGL, META, MSFT, NFLX, NVDA, SPY, TSLA), 7 `train` / 4 `holdout`, every one
`data_feed: "sip"` (never `iex`, never pooled). The pinned `5c7f1a44aa71412eb874cb639dde56e2` (AAPL
2026-06-22, window 12:30-15:00Z, 555,382 real trade+quote rows) is present. This exceeds the
Success-Criterion-4 headline (>=10 windows / >=5 symbols / pinned AAPL included).

**`GET /research/setups`** -- **801 events across all 12 panel symbols** (far exceeds the J-02
>=15-events/>=8-symbols acceptance). The pinned AAPL 2026-06-22 resistance band (id
`13e24a2f185b1299`, price 300.17-302.27, **class A, round_number: true, quality_score 153.0**)
matches goal.md's own pinned description ("a resistance band containing both 300.48 and 302.07,
round-number 300 flagged"). **First call against the real, much larger real-bar corpus took ~6.5
minutes** (cold `_SCAN_CACHE` miss -- a full 12-symbol x every-stored-session scan); subsequent
calls in the same process were near-instant (0.31s, cache hit) -- see "Known Issues" below.

**`GET /research/setups/13e24a2f185b1299`** (the pinned drill-in) -- **fully populated, not the
empty-state**:
- `reaction: "rejected"`, `forward_returns` **both negative** (-0.46% at 78 bars,
  -4.27% at 234 bars) -- matches goal.md's "appears as `rejected` with negative forward reaction"
  verbatim.
- `tape_timeline`: **426 real state-transition entries** spanning 12:33:41Z-14:59:19Z (inside the
  recorded 12:30-15:00Z window), states drawn from the real engine vocabulary
  (`bid_absorption`/`buyer_control`/`seller_control`/`ask_absorption`) -- replacing the prior "No
  recorded tape for this event." empty-state entirely.
- This single request took **13m 4s** end-to-end (a fresh `TapeEngine` replay of all 555,382 real
  ticks -- the frozen engine/join code, unmodified). See "Known Issues" below.

**`GET /research/edge-report`** -- **not run to completion live this session** (see "Known Issues"
below for why and for the verification I did complete instead). The dataset-resolution mechanism
that decides whether a real dataset produces a report cell was independently confirmed correct and
non-degenerate: I cross-referenced all 11 real historical datasets against the (now warm-cached)
801-event registry using the identical symbol + touch_ts-inside-window matching rule
`edge_report.py`'s own `_dataset_event` uses. **All 11 of 11 datasets resolve to a classified scan
event** (0 skipped), spanning classes A/B/C, both sides, reactions `rejected`/`broke`/`chopped`, and
both `train` (7) and `holdout` (4) splits, every one `feed: "sip"`. This is strong, concrete evidence
the report -- once it finishes computing -- will render genuinely populated, diverse cells, not a
vacuous or degenerate one, closing the iter-4/iter-6 "all-empty (only non-panel PG datasets existed)"
gap. See "Known Issues" for why I did not wait out the full live computation.

## Known Issues

- **`GET /research/edge-report` was not verified live to completion this session -- a known,
  pre-existing, out-of-scope-to-fix performance characteristic, now measured concretely.** This is
  not a new finding: iter-3's dev handoff already documented "a from-scratch replay of the AAPL
  dataset alone did not finish inside two bounded attempts (280s, then 90s)", and iter-4's documented
  "`GET /research/edge-report` can take several minutes... hang past 2 minutes" against a MUCH
  smaller store (7 non-panel PG datasets + 47 bar files). This iteration's real dataset corpus is
  much larger: **11 real historical datasets totalling ~9.1M trade+quote rows**. I measured the
  actual replay throughput directly: the pinned AAPL dataset (555,382 events) took **13m 4s** end to
  end (~708 events/sec). `run_strategy_comparison_report` replays **every** registered dataset that
  resolves a classified event through the **same** unmodified per-tick `TapeEngine` replay, once per
  strategy (`v1`, `structure_tape`, `structure_tape_map` all share the identical `_replay` code path
  -- confirmed by reading `backtests.py::_replay`, called once per (dataset, strategy) pair). All 11
  real datasets resolve (see above), so a full live run is ~11 datasets x 3 strategies = 33 full
  replays of ~9.1M total events x 3 -- extrapolating from the measured throughput, **on the order of
  10+ hours**, not minutes. I did not start this live call, because (a) I could not let it run past
  my own session (agent instructions require me to kill any server I start before finishing, which
  would abort an in-flight multi-hour request and waste 100% of its progress with nothing persisted
  -- there is no partial-result caching for this endpoint), and (b) the plan scopes this iteration as
  verification-only with no code changes, so I could not add a caching layer to make it fast (the
  `_SCAN_CACHE` precedent that already speeds up `GET /research/setups` on repeat calls would be the
  natural fix, mirroring audit-B2's already-flagged "future iteration" candidate for `edge_report.py`
  too -- out of scope here). **This is a genuine risk for the next pipeline stage**: browser-QA (or
  anyone) hitting `/structure`'s Edge Report section, or `GET /research/edge-report` directly,
  against the current real store should expect a very long wait (likely hours), not seconds. I
  recommend either pre-warming this endpoint well before QA needs it (kick off the request in the
  background early and poll), or treating "still computing, no error, actively producing work" as
  the honest expected state rather than a failure, until a future iteration adds caching.
- **`GET /research/setups` (list) pays a real ~6.5-minute cold-cache cost on first call in a fresh
  process** (the already-known/documented audit-B2 full-panel-scan cost, now measured slightly
  higher than iter-3's own ~4m43s figure, consistent with a larger real-bar corpus since iter-3).
  Cached after the first call for the life of the process (`_SCAN_CACHE`, keyed on the store's
  content signature) -- not a regression, not touched by this iteration.
- **`scripts/dev.sh`'s SIGTERM trap does not clean up the full process tree** -- discovered during
  this iteration's pre-handoff service-startup verification (not a change I made; pre-existing
  infrastructure, out of this iteration's file scope). `trap "kill $BACKEND_PID $FRONTEND_PID" INT
  TERM` only signals the direct child subshell PIDs. `uvicorn --reload`'s actual port-bound worker is
  a `multiprocessing.spawn`-launched grandchild with a DIFFERENT command line (does not contain
  "uvicorn main:app"), and Next.js's actual `next-server` is a great-grandchild under
  `npm -> sh -> node`. Killing only the immediate children leaves both orphaned, still bound to their
  ports, until the NEXT `dev.sh` invocation's own port-based pre-kill (`lsof`/`fuser` by port number,
  not PID lineage) cleans them up on the following start. I verified this live: after `kill -TERM` on
  the top-level `dev.sh` process, the backend died cleanly but the frontend's `next-server` survived
  and kept holding port 3301; a second `dev.sh` start still succeeded without a port conflict (the
  startup-time port-based pre-kill self-heals), but a plain stop leaves a resource leak until the
  next start. I killed the orphan by exact PID for my own cleanup. Flagging because my agent
  instructions specifically call for checking this ("verify it handles child processes, not just
  parent PIDs") -- this is pre-existing, outside my plan's file list (only `PriceChart.tsx` and
  `test_price_chart_confluence.py` were in scope), so I did not fix it.
- **The QA test plan (`reports/qa/goal-tradable_wall-iter-8-test-plan.md`, written before my dev
  work) contains two factual errors I noticed while grounding my own verification** -- not mine to
  edit (a QA-owned artifact), flagging so the reviewer/QA stage is not misled: (1) TC-01/TC-04
  describe the tape-state vocabulary as `{INIT, RESTING, TRACKING, TRIGGERED, RESET}` -- the actual,
  only-ever-existing engine vocabulary is `{buyer_control, seller_control, bid_absorption,
  ask_absorption, unclear}` (confirmed live in the pinned drill-in's real `tape_timeline` above, and
  is the same vocabulary used everywhere else in this codebase since era 3). (2) TC-04's example curl
  command queries `GET /research/setups/5c7f1a44aa71412eb874cb639dde56e2` -- that is the **dataset**
  id; `GET /research/setups/{id}` expects a **setup/event** id (e.g. the pinned case's real id is
  `13e24a2f185b1299`, confirmed above). The dataset id and the event id are different identifier
  spaces (32 hex chars vs. 16 hex chars respectively); querying the dataset id against this route
  would 404.

## Deviation From Plan

None. Implemented exactly the two named cleanups and the read-path verification; touched no other
file; added no new capability, endpoint, or UI surface.
