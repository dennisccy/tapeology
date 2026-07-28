# Iteration 11 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

The new "Top-up Runs" panel on the Desk page is really built and really works. I opened the pictures
myself: the panel says "No top-up runs recorded yet." when nothing has been saved, and after three
test runs it lists each run with how many pairs it tried, how many were reused, freshly fetched or
failed, the failed pair's own words ("AAPL 4h — no data for that window"), and an honest "401 pairs
not reached" line for the run that was stopped early. I also re-did the work myself on a throw-away
copy instead of trusting any report, and everything held. One written promise in `docs/goal.md` is
still not kept: the guided walkthrough for this new feature shows only the empty panel and never
shows a single saved run, so it does not cover the new record "end to end". That is one short
picture-taking run away, with no change to the program.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Universe ingestion — fetched, registered, honest | passing | passing | `reports/phase-goal-desk-iter-11-ui-test-results.md` row UT-J-01 (golden replay) · `reports/qa/goal-desk-iter-11-evidence/J-01-verify.png` |
| J-02 Coverage + explicit bar top-up over the universe | passing | passing | row UT-J-02 · `reports/qa/goal-desk-iter-11-evidence/J-02-verify.png` |
| J-03 The screen — pinned inputs, append-only snapshot, deterministic rank | passing | passing | row UT-J-03 · `reports/qa/goal-desk-iter-11-evidence/J-03-verify.png` |
| J-04 The /desk briefing page | passing | passing | row UT-J-04 · `reports/qa/goal-desk-iter-11-evidence/J-04-verify.png`; regression walk row UT-08 (`UT-08-regression-history-drillthrough-reverted.png`) |
| J-05 Ledger history + drill-in to /structure | passing | passing | row UT-J-05 · `reports/qa/goal-desk-iter-11-evidence/J-05-verify.png` (spot-checked: /structure prefilled AAPL @ 2026-06-22T23:59:59Z with the pinned 300.10/302.20 bands drawn) |
| J-06 MCP contract v3 — 17 read-only tools | passing | passing | row UT-J-06 (`tests/test_mcp_server.py` 35 passed after the audit's added proxy test); evaluator's own live count `len(TOOL_NAMES) == 17` |
| J-07 The kept product stands — regression sentinel | passing | passing | row UT-J-07 · `reports/qa/goal-desk-iter-11-evidence/J-07-verify.png` (spot-checked); evaluator's own suite 1369 pass / 8 skip / 0 fail, pin `08e471b10130e1e2`, zero diff on every frozen file |
| J-08 Every ranked briefing row names the bar its distance was measured from | passing | passing | row UT-J-08 · `reports/qa/goal-desk-iter-11-evidence/J-08-verify.png`; `basis` column re-confirmed live in row UT-08 (8 columns, 63 rows) |
| **J-09 Every top-up run leaves an append-only record of what it attempted** | *(new)* | **partial** | MET: `reports/qa/goal-desk-iter-11-evidence/UT-02-empty-state.png` (honest empty), `UT-05-failed-pair-detail-legible.png` (3 runs, `404 of 404 pairs attempted`, `0 reused · 403 fetched · 1 failed`, `AAPL 4h — no data for that window`), `UT-06-partA-unreached-pairs.png` (`cancelled`, `3 of 404`, `401 pairs not reached`). UNMET: the `[NEW]` walkthrough (`reports/phase-goal-desk-iter-11-demo.json` — one J-09 step, empty state only; `reports/demo/goal-desk-iter-11/step-02.png`) |

### What I verified myself, rather than reading

- Full backend suite, my own run under the host-guard mask: **1369 passed, 8 skipped, 0 failed,
  exit 0** (floor 1346/8) — counted marker-by-marker off the progress output.
- `Config().config_fingerprint()` → `08e471b10130e1e2`; live `TOOL_NAMES` → exactly 17 names.
- Zero diff (committed and working tree) for `tradability.py`, `levels.py`, `bars.py`,
  `StructureChart.tsx`, `PriceChart.tsx`, `config.py`, `app/mcp/__init__.py`, `meta.py`,
  `desk_coverage.py`, `desk_screen.py`, `test_copy_discipline.py`, and all of `app/engine/`.
- Own scoped end-to-end run (temp dirs, zero network): honest-empty `{"runs": [], "latest": null}`
  before any run and the store directory not even created; after a real walk the persisted
  `outcomes` are **byte-identical** to the value the real `run_topup` returned (spy comparison);
  `pairs_attempted == len(outcomes)`; a forced failure records `outcome: "failed"` with
  `detail: "no data for that window"` verbatim while the walk continues; a second run appends and
  the first file's sha256 is unchanged; the store class exposes no update/delete/overwrite method.
- Route level: `GET /research/desk/topup/runs` → HTTP 200 `{"runs": [], "latest": None}`, and three
  repeated GETs left `GET /research/desk/topup/compute` at `null` — a page load starts nothing.
- Owner's real data folder took no write: 369 bar files (newest 2026-07-26), 3 screen records, 1
  universe file, 18 datasets, and **no `topup_runs` directory at all**. The only files touched since
  this iteration began are two rebuildable caches (`setups_scan_cache.db`, `bar_index.db` WAL/SHM).
- `docs/goal.md`'s J-09 addition is `+63/−0`, one hunk at line 564 — entirely inside the
  `AUTO:journeys` block (lines 514–630). Nothing human-authored was edited.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | `iter-11/scan-report.md`: CLEAN (2 untracked files scanned). New module carries no config/env/secret literal. |
| Paid / external SaaS | OK | `git diff` on `requirements.txt`, `pyproject.toml`, `package.json`, `package-lock.json` is empty. No new vendor seam; no network call in any test. |
| License changes | OK | No LICENSE or license-field path in the changed-file list (9 files, all app/test/state). |
| Fabricated / substituted data | OK | Browser QA's three checkpoint runs used a monkeypatched adapter double (synthetic bars, one induced `NoDataForWindow`) — disclosed in `ui-test-results.llm.md` "Test rigs used" and confined to a `cp -a` throw-away copy under `$TMPDIR`. I confirmed the real store gained no bar, screen, universe, dataset or run file. |
| 1 No execution path, ever | OK | Record fields are id / universe snapshot / window / fingerprint / times / state / pair counts / per-pair outcomes. `test_no_execution_path.py` green, unmodified. |
| 2 No profit claims and no advice | OK | Panel text is counts, dates, states and vendor detail only; UT-10 scanned the whole section against an advice/urgency word list — zero hits; `test_copy_discipline.py` green unmodified (file diff empty). |
| 3 Frozen foundations | OK | Zero diff on all four named frozen files plus `PriceChart.tsx` and the engine; the audit AST-compared `run_topup`/`_run_one_pair`/`_fetch_window_now`/`_iso_utc_now` against HEAD — byte-identical. Nothing added to R-1's eight-file inventory. |
| 4 Hold-out-only promotion | OK | No strategy, gate, sweep or champion code touched; `pnl_ledger` untouched. |
| 5 No lookahead | OK | The record persists values an existing computation already produced; it derives no as-of value. |
| 6 Single source of truth | OK | `coherence.md` = COHERENCE-PASS. One owner (`desk_topup_log.py`), one serving route (`GET /research/desk/topup/runs`), one writer — my own grep found exactly two call sites and one `write_text`. Coverage keeps `desk_coverage.py` (zero diff). |
| 7 Deterministic and seeded | OK | No randomness in a served value; the run id's random suffix is an identifier, and the store re-rolls rather than overwriting. Wall-clock start/finish stamps are required by J-09's own step 1. |
| 8 Read-only MCP | OK | `app/mcp/__init__.py` diff empty; live tool count 17; the new path is reached through the existing `/research/` allowlist. The audit added the missing byte-identity proxy test. |
| 9 Immutable data | OK | Append-only proven by my own second-run check (first file sha256 unchanged); no update/delete API; real bar store untouched. |
| 10 Persistence stays scoped | OK | Every write this iteration landed in a throw-away root; the real `.data/` has no `topup_runs` directory. Iteration 9's ambient-write deviation did **not** recur. |
| 11 Membership is never a signal | OK | The record stores the universe snapshot id as provenance only; no rank or computation reads it. |
| 12 Snapshots are append-only and pinned | OK | Each record carries universe snapshot id, requested window, fingerprint, times, state, counts, and its own `file_checksum`; a second run appends a new file. |
| 13 Every run is an explicit operator act | OK | No scheduler/daemon added; only a GET route. My own three repeated GETs left the compute snapshot `null`; browser QA diffed the access log across three reloads — zero POSTs. |
| 14 The briefing describes, never advises | OK | Same evidence as rail 2; the unreached note is a plain count, the failed line is the vendor's own words. |
| 15 No new statistics, gates, or strategies | OK | Counts of attempts only — no probability, expectancy or edge claim anywhere in the panel. |
| 16 The demolition stays demolished | OK | No journal-era machinery; `journal.db` schema untouched; zero manual-input write path — the only new route is a GET. |
| 17 The ledger never holds orders | OK | I dumped a real record's field list myself: no size, ticket, entry/exit or account concept. |
| 18 The suite stays keyless and hermetic | OK | New tests use `FakeAdapter`/monkeypatch; my own full-suite run passed offline. The real ~100-symbol run stayed out of scope, as the spec says. |
| 19 The fingerprint pin does not move | OK | My own `Config().config_fingerprint()` → `08e471b10130e1e2`; `config.py` diff empty; zero new `Config` field (the store dir is an env-var-or-sibling default). |
| 20 The enhancement loop stays inside its box | OK | `docs/goal.md` `+63/−0`, single hunk inside `AUTO:journeys`; J-09 carries a single-source-of-truth acceptance criterion and a `[NEW]` walkthrough requirement. The walkthrough exists and is `[NEW]`-flagged — its *coverage* is the shortfall scored above, not a rail breach. |
| 21 Host-guard caps are law | OK | `project-extensions/host-guard/` untouched (no diff, no working-tree change); this evaluation's own suite run and scripts were wrapped in `taskset -c 4-7,12-15` with BLAS threads capped at 4. |

**Coherence:** `runs/goal-session-desk/iter-11/coherence.md` = **COHERENCE-PASS**. Its one advisory
(the panel sits after the Run Screen / Top-up controls rather than literally beside Screen History)
is a disclosed, reasoned placement call logged in `assumptions.md`, not a violation.

**Violations:** none new. All three older items stay resolved and were re-confirmed by my own checks.

## Next-Step Recommendation

Run iteration 12 at **lean** depth. It is a picture-taking run only — do not change any program code.

1. Bring the throw-away rig back the way this run already did it: copy the real data folder to a
   temporary place, point the backend's four folder settings at the copy, start it on the same port
   the Desk page already talks to, and record three top-up runs into it — one ordinary, one stopped
   early, and one where a single pair is made to fail (`apps/backend/scripts/goal-desk-iter9-scoped-backend.sh`
   plus the recipe written down in `reports/phase-goal-desk-iter-11-ui-test-results.llm.md`).
2. Re-record the guided walkthrough against that rig so it shows **both halves**: first the panel
   saying "No top-up runs recorded yet.", then a saved run with its attempted-of-total count, its
   reused/fetched/failed counts, and the failed pair's own words. Today only the first half exists
   (`reports/phase-goal-desk-iter-11-demo.json` has one J-09 step; `reports/demo/goal-desk-iter-11/step-02.png`
   shows an empty panel), and `docs/goal.md` asks for the disclosure "end to end".
3. State in the walkthrough report which data folder was used — this run did that properly and it
   should stay the habit.
4. Redo nothing else. The panel itself, the saved-run store, the endpoint, the tests, the browser
   pictures and the replay script are all verified done; the real data folder is untouched.

Carry, do not force (all optional, none blocking): the run list does not yet report a damaged file
the way the two sibling lists do (`desk_routes.py:258`); a just-finished run can stay hidden until
you refresh, in a very narrow timing window (`apps/frontend/app/desk/page.tsx:1116-1121`); the run
table has no limit yet; the Desk page is now six stacked sections and long; the saved replay script
for this feature will need its wording updated the first time a real top-up is saved to your own
data folder; and `runs/goal-desk-iter-11/status.json` still says browser checks did not run when
they did.

One sentence for the owner: everything this new feature promised is built, proven and photographed —
the next short run only needs to re-film the guided walkthrough so it shows a saved run, not just an
empty panel.
