# Iteration 26 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** evidence

## Summary

The Desk's top-up now says honestly what it asked the data supplier for and what came back. I opened
the picture myself and then proved every number in it against the run's own saved record on disk:
the counts, the tail-versus-full-window split, and each failed pair's own requested dates all match
character for character, and all three cases the goal file describes really happened on a real run.
Nothing of the owner's data was created, changed or removed. I did not call the goal finished, for
one reason: the goal file also asks for a short guided film over a populated run, the plan for this
run asked for the fuller pipeline that records one, and the machine downgraded the run to the shorter
one that records none.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Universe ingestion | passing | passing | `reports/phase-goal-desk-iter-26-ui-test-results.md` UT-J-01 PASS (golden replay) + `reports/qa/goal-desk-iter-26-evidence/J-01-verify.png` |
| J-02 Coverage + top-up | passing | passing | UT-J-02 PASS + `reports/qa/goal-desk-iter-26-evidence/J-02-verify.png` |
| J-03 The screen | passing | passing | UT-J-03 PASS + `reports/qa/goal-desk-iter-26-evidence/J-03-verify.png` |
| J-04 The /desk briefing page | passing | passing | UT-J-04 PASS + `reports/qa/goal-desk-iter-26-evidence/J-04-verify.png` |
| J-05 Ledger history + drill-in | passing | passing | UT-J-05 PASS + `reports/qa/goal-desk-iter-26-evidence/J-05-verify.png` — **spot-check I opened**: `/structure` prefilled to AAPL / `2026-06-22T23:59:59Z` after drill-in |
| J-06 MCP contract v3 — 17 tools | passing | passing | UT-J-06 PASS (LLM lane; no browser surface exists for this journey). **My own re-run**: `len(app.mcp.TOOL_NAMES) == 17`, all 17 names enumerated |
| J-07 Regression sentinel | passing | passing | UT-J-07 PASS + `reports/qa/goal-desk-iter-26-evidence/J-07-verify.png` |
| J-08 Basis bar named | passing | passing | UT-J-08 PASS + `reports/qa/goal-desk-iter-26-evidence/J-08-verify.png` |
| J-09 Top-up run record | passing | passing | UT-J-09 PASS + `reports/qa/goal-desk-iter-26-evidence/J-09-verify.png` |
| J-10 Coverage the store can prove | passing | passing | UT-J-10 PASS + `reports/qa/goal-desk-iter-26-evidence/J-10-verify.png` |
| J-11 History depth stated | passing | passing | UT-J-11 PASS + `reports/qa/goal-desk-iter-26-evidence/J-11-verify.png` |
| J-12 Snapshots addressable by id | passing | passing | UT-J-12 PASS + `reports/qa/goal-desk-iter-26-evidence/J-12-verify.png` |
| J-13 Band price + close | passing | passing | UT-J-13 PASS + `reports/qa/goal-desk-iter-26-evidence/J-13-verify.png` — **spot-check I opened**: real ambient data, `band 495.45–497.18 · close 497.18` on rank 1 |
| J-14 Opposite wall | passing | passing | UT-J-14 PASS + `reports/qa/goal-desk-iter-26-evidence/J-14-verify.png`; also read `opposite resistance A 497.20–500.67 · 0.40 bps` in J-13-verify.png |
| J-15 What the wall is made of | passing | passing | UT-J-15 PASS + `reports/qa/goal-desk-iter-26-evidence/J-15-verify.png`; also read `155 · 1d 68 · 1h 57 · 1w 11 · 4h 19` in J-13-verify.png |
| J-16 The briefing fits the page | passing | passing | UT-J-16 PASS + `reports/qa/goal-desk-iter-26-evidence/J-16-verify.png`; re-confirmed in this run's own `J-17-ranked-table-regression-check.png` — all 13 columns in one 1440×900 frame, no sideways scroll |
| **J-17 Top-up asks only for what the store cannot prove** | *(new journey)* | **passing** (`evidence_makeup: true`) | UT-J-17 PASS + `reports/qa/goal-desk-iter-26-evidence/J-17-topup-window-disclosure.png` (+ `J-17-ranked-table-regression-check.png`); numbers re-derived by me from `desk-iter26-scoped-qa/data/topup_runs/topup-2026-07-30-f87fec15b167.json` |

No journey was deferred for budget this run (zero `DEFERRED-BUDGET` cells). No `journeys-changed.md`
and no `browser-infra.json` exist for this iteration; all 17 `spec_hash` values were recomputed from
the current `docs/goal.md` and recorded.

### What I verified myself for J-17, rather than accepting a report

- **The picture.** `J-17-topup-window-disclosure.png` shows, in one frame at 1440×900 with nothing cut
  off: `0 reused · 6 fetched · 2 unchanged · 4 failed`;
  `2 pairs asked for a tail window · 10 pairs asked for the full lookback window`; and four failed
  `ZZZINVALIDXYZ` rows each carrying `requested 2024-07-30 → 2026-07-30`.
- **The numbers behind the picture.** The run record on disk holds exactly 12 per-pair entries of
  exactly 8 fields each, tallying to those same counts and that same 2 / 10 split. All three window
  cases are exercised on a real run: `AAPL 1d` and `1w` reach past the lookback start → tail windows
  starting `2026-07-30` / `2026-07-27`, each equal to that pair's own newest stored bar's date;
  `AAPL 1h` / `4h` start `2024-07-31`, one day later than the `2024-07-30` lookback start → the
  byte-identical full window; `MSFT` ×4 and `ZZZINVALIDXYZ` ×4 have nothing stored → the same full
  window, equal to the run-level `requested_window`.
- **The `unchanged` outcome wrote nothing.** The scoped bar folder holds exactly 10 series files =
  4 pre-seeded + 6 fetched; the two `unchanged` pairs added none.
- **The fake-adapter half of the acceptance.** `test_run_topup_asks_the_fake_adapter_for_the_derived_tail_window_and_records_it_on_the_outcome`
  asserts on `adapter.fetch_bars_calls` directly, alongside the nothing-frozen, short-history and
  `unchanged` tests and a source-introspection guard (reads `merged_bars`, never `.window_end_utc`)
  with its own seeded-violation counter-test.
- **Re-run by me, not quoted:** full backend suite → exit 0, **1,474 passed / 8 skipped / 0 failed /
  0 errors**; `Config().config_fingerprint()` → `08e471b10130e1e2`; MCP tool count → exactly 17;
  zero diff against this run's own snapshot for `bars.py`, `bar_index.py`, `desk_coverage.py`,
  `desk_screen.py`, `tradability.py`, `levels.py`, `desk_topup_log.py`, `config.py`, `meta.py`,
  `mcp/__init__.py`, `routes.py`, `StructureChart.tsx`, `PriceChart.tsx`, and for
  `test_copy_discipline.py`, `test_desk_ui_guards.py`, `test_desk_hover_tooltip_guard.py`,
  `test_no_execution_path.py`, `test_profile_equivalence.py`.
- **Append-only proof (the audit lane does not run at lean depth, so I produced my own).**
  `find apps/backend/.data -newermt '2026-07-30 15:00'` returns ONLY `bar_index.db-wal` and
  `bar_index.db-shm` — two rebuildable sidecars. Counts unchanged: 759 bar series, 1 universe
  snapshot, 11 screen snapshots, 1 top-up record.

### The one unmet acceptance conjunct

`docs/goal.md`'s J-17 acceptance also names "a **`[NEW]`-flagged demo-narrator walkthrough** …
narrated over a populated run". No film exists: `runs/goal-session-desk/iter-26/depth-dispatched`
reads `lean` although the spec's metadata asked for `Depth: full`, and the lean path records no
walkthrough — `reports/demo/goal-desk-iter-26/` does not exist. Scored under methodology A.7 as a
capture gap (`evidence_makeup: true`), not a behaviour gap; see `assumptions.md` iter-26.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No execution path, ever *(critical)* | OK | No broker/order/ticket code anywhere in the 6-file product diff, which I read in full; `test_no_execution_path.py` byte-unmodified and green in my own suite run. |
| No profit claims and no advice *(critical)* | OK | The only new copy is `N reused · N fetched · N unchanged · N failed`, `N pairs asked for a tail window · N pairs asked for the full lookback window`, and `requested <date> → <date>` — counts and dates, no saving/efficiency/speed/recommendation claim. `test_copy_discipline.py` byte-unmodified and green. |
| Frozen foundations *(critical)* | OK | Zero diff verified by me for `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py`, `levels.py`, `routes.py`, `config.py`, `meta.py`, `mcp/__init__.py`, `StructureChart.tsx`, `PriceChart.tsx`; engine equivalence and the 13 fingerprint pins green inside the suite. |
| Hold-out-only promotion *(critical)* | OK | No diff to `backtests.py`, `strategies.py`, `pnl_ledger.py` or the champion pointer; no gate, floor or sample-size touched. |
| No lookahead *(critical)* | OK | The change alters only a vendor FETCH window (which bars to request), never an as-of computation; `desk_screen.py`'s as-of clamp takes a zero diff. The screen in `J-17-ranked-table-regression-check.png` still pins `As of 2026-07-30T23:59:59Z`. |
| Single source of truth *(critical)* | OK | `coherence.md` = COHERENCE-PASS. The window comes only from `BarStore.merged_bars` (I read `_pair_window`; a source-introspection guard + counter-test enforce it), `desk_topup_log.record_topup_run` stays the sole writer (zero diff), `GET /research/desk/topup/runs` the sole endpoint, and the frontend tallies already-served fields with no new fetch. |
| Deterministic and seeded | OK | No new randomness and no new wall-clock use; the run's end bound stays the pre-existing `_fetch_window_now()` value. |
| Read-only MCP *(critical)* | OK | `app/mcp/__init__.py` zero diff; I re-ran the tool list — exactly 17, no write tool. |
| Immutable data *(critical)* | OK | Nothing under `apps/backend/.data` created, modified or removed (only two rebuildable sqlite sidecars); the `unchanged` path writes no second series file, proven by the scoped folder's 10-file count and by TC-4. |
| Persistence stays scoped *(critical)* | OK | The top-up remained an explicit POST by the evidence lane on a throwaway copy; no ambient recording, no scheduler. |
| Membership is never a signal *(critical)* | OK | No universe value enters any computation; the diff touches no ranking or feature code. |
| Snapshots are append-only and pinned *(critical)* | OK | Legacy runs are served verbatim and rendered as an honest absence — `topupWindowBasisCounts` returns `null` when any entry lacks `window_basis`, and the page prints `window basis not recorded in this run`; nothing is backfilled or computed at read time. |
| Every run is an explicit operator act *(critical)* | OK | No scheduler, cron, daemon, auto-refresh or retry loop added; page-load GETs unchanged (no new endpoint call in the frontend diff). |
| The briefing describes, never advises *(critical)* | OK | Same evidence as the profit-claims row; copy lint green unmodified. |
| No new statistics, gates, or strategies *(critical)* | OK | No probability/expectancy/edge value added; the new fields are windows, timestamps and a two-value basis label. |
| The demolition stays demolished *(critical)* | OK | No journal machinery, no manual-input write path on desk records. |
| The ledger never holds orders *(critical)* | OK | New fields are `requested_window`, `store_frozen_from`, `store_frozen_through`, `window_basis` — no size, ticket, entry/exit or account concept. |
| The suite stays keyless and hermetic *(critical)* | OK | All new tests use the suite's injected fake adapter (`_inject_adapter`) and planted bars; the real Yahoo calls happened only in the operator-style evidence run on a throwaway store, reported as such and never a CI gate. |
| The fingerprint pin does not move *(critical)* | OK | `08e471b10130e1e2` re-printed by me; `config.py` zero diff, so zero new `Config` fields. |
| The enhancement loop stays inside its box *(critical)* | OK | The J-17 text is a single +125-line insertion ending exactly at the `<!-- /AUTO:journeys -->` marker (hunk `@@ -1278,0 +1279,125 @@`; markers at lines 524 and 1404) — nothing outside the block was edited. J-17 carries an explicit single-source-of-truth acceptance criterion and keeps `default`/`v1` byte-identical. Its `[NEW]`-flagged walkthrough clause is the one item still owed (see above). |
| Host-guard caps are law *(critical)* | OK | The chain widened nothing. The `incredible_auto_dev/` and host-guard changes visible in `iter-diff.md` come from six operator commits dated 2026-07-30 21:39–22:30 (including `884eeaf` "release the CPU mask to the whole machine"), which sit between this run's snapshot and `HEAD` — not this iteration's product work. |
| Secrets / credentials | OK | `scan-report.md` = CLEAN; no new config or env file in the 6-file product diff. |
| Paid / external SaaS | OK | No manifest changed (`package.json`, `requirements*.txt`, `pyproject.toml` all absent from the diff); no new runtime dependency. |
| License changes | OK | `scan-report.md` = CLEAN; no LICENSE or license-field diff. |
| Fabricated / substituted data | OK | The evidence run used real keyless Yahoo calls and a genuinely unknown ticker for the failure case; the honest `unchanged` label distinguishes a real vendor call from `reused`'s zero-call hit, and nothing is recorded as reused that a vendor call served. |

**Unresolved violations: none.** The three historical entries (iters 3 and 4) stay `resolved` and
were re-confirmed by my own append-only check this run.

## Next-Step Recommendation

One more short capture-and-check run, with no code change. Two jobs, in this order.

1. **Rebuild the everyday page first.** Delete `apps/frontend/.next`, rebuild it, and restart both
   everyday processes before anything else. I checked the built files myself: the client bundles now
   contain `localhost:8000` and no longer contain `localhost:8301`, because the evidence step built
   the one shared build folder while pointing at its own throwaway backend, which has since been shut
   down. Until this is fixed the page at port 3301 shows nothing, and all sixteen saved replay
   scripts would fail for a reason that has nothing to do with the product.
2. **Record the guided film for J-17** "A top-up asks the vendor only for the bars the frozen store
   cannot already prove", over a populated run on a throwaway copy of the data and never the owner's
   own. Its frames must show the four-outcome counts line and the tail-versus-full-window line, and
   each step in its script must name ONE row rather than many — and should read the row's text rather
   than click it, which is the fix iteration 25 already identified.

Also worth doing in the same run, because no saved script exists for the new item: check J-17 in a
real browser rather than by replay.

Two things for the owner's own track, neither blocking: iteration 25's optional notes (the film's
wording, and the replay tool saving the same first picture over and over) are still open; and one
line of an existing test was widened this run — from the four fields each record entry used to carry
to the eight it now carries — because the run's own rules both demanded the four new fields and
forbade touching that line. I ratify that as a widening, not a weakening, and it is recorded in the
assumption ledger.

One sentence for the owner: the Desk's top-up now states honestly what it asked the data supplier for
and what came back, proven number by number against the run's own record, and the next short run only
needs to rebuild the page and record the film before the finish can be proposed again.
