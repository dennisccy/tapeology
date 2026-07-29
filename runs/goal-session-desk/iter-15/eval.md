# Iteration 15 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** lean

## Summary

This run added one thing to the Desk page: every ranked row now says how many completed daily
sessions its wall was measured over, and from what date. I opened the picture that carries the
whole run and I proved the numbers myself instead of believing any report. The page shows a
27-session row sitting beside a 500-session row in one image, the numbers match the stored price
files exactly on all 63 rows, older records were not rewritten, and everything that worked before
still works.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Universe ingestion — fetched, registered, honest | passing | passing (carried; outside this run's required set, product code untouched; spot-checked) | reports/qa/goal-desk-iter-14-evidence/J-01-verify.png |
| J-02 Coverage + explicit bar top-up over the universe | passing | passing (carried; outside this run's required set, product code untouched; spot-checked) | reports/qa/goal-desk-iter-14-evidence/J-02-verify.png |
| J-03 The screen — pinned inputs, append-only snapshot, deterministic rank | passing | passing | reports/qa/goal-desk-iter-15-evidence/J-03-verify.png |
| J-04 The /desk briefing page | passing | passing | reports/qa/goal-desk-iter-15-evidence/J-04-verify.png |
| J-05 Ledger history + drill-in to /structure | passing | passing | reports/qa/goal-desk-iter-15-evidence/J-05-verify.png |
| J-06 MCP contract v3 — 17 read-only tools | passing | passing | reports/phase-goal-desk-iter-15-ui-test-results.md row UT-J-06; evaluator's own `len(app.mcp.TOOL_NAMES)` = 17 and the full suite green |
| J-07 The kept product stands — regression sentinel | passing | passing | reports/qa/goal-desk-iter-15-evidence/J-07-verify.png |
| J-08 Every ranked briefing row names the bar its distance was measured from | passing | passing | reports/qa/goal-desk-iter-15-evidence/J-08-verify.png |
| J-09 Every top-up run leaves an append-only record of what it attempted | passing | passing | reports/qa/goal-desk-iter-15-evidence/J-09-verify.png |
| J-10 The coverage the briefing shows is the coverage the frozen store can prove | passing | passing | reports/qa/goal-desk-iter-15-evidence/J-10-verify.png |
| J-11 Every ranked briefing row states how much completed history its wall was measured over | (new) | **passing** | reports/qa/goal-desk-iter-15-evidence/UT-02-result.png (HONA `history 27 sessions · from 2026-06-15` beside BRK-B `history 500 sessions · from 2024-07-25`, one frame) · reports/demo/goal-desk-iter-15/step-09.png ([NEW]-flagged walkthrough, same split) · reports/demo/goal-desk-iter-15/step-06.png (legacy snapshot → "history not recorded in this snapshot" on every row) |

### What I verified myself (not read from a report)

- Opened `UT-02-result.png`, demo `step-06.png` and `step-09.png`; opened the two carried-journey
  spot-check frames `J-01-verify.png` / `J-02-verify.png`.
- Re-derived both new values for **all 63 ranked rows** of
  `apps/backend/.data/screen/screen-2026-07-28-ac07c9581a4f.json` straight from
  `BarStore.merged_bars(symbol, "1d")` — the canonical owner — **0 mismatches**. Range 27…501,
  1 row ≤ 60, 57 rows ≥ 400. Skip rows (38) carry neither key.
- Read the legacy snapshot `screen-2026-07-29-ce0d82b8e9bf.json` (recorded 02:11, before this
  run's code): all 63 ranked rows have both keys **absent**, never `null`. Both snapshot files
  recompute their own stored checksums.
- No lookahead: `history_start <= basis_as_of` on every one of the 63 rows.
- Rank key did not move: the ranked symbol order is identical between the pre-change and
  post-change screens, and every non-history field matches on all 63 rows except `basis_age_days`,
  which differs by exactly 1 because the two screens are one day apart. `_row_rank_key`'s body
  appears only as unchanged context in the diff.
- Re-ran the work: full backend suite **1418 passed / 8 skipped / 0 failed, exit 0**;
  `Config().config_fingerprint()` = `08e471b10130e1e2`; `len(app.mcp.TOOL_NAMES)` = 17.
- Zero working-tree diff on `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`,
  `StructureChart.tsx`, `PriceChart.tsx`, `config.py`, `meta.py`, `mcp/__init__.py`, `app/engine/`,
  `test_copy_discipline.py`, `test_no_execution_path.py`, `test_no_credential_in_artifacts.py`,
  `test_profile_equivalence.py`.
- The one edited guard test (`test_desk_hover_tooltip_guard.py`) was **strengthened**, not weakened:
  it adds `row.history_start` as a required needle.
- Ambient store: 0 of 369 bar-series files modified; no universe file written; no prior screen
  snapshot rewritten; only one appended snapshot plus two rebuildable caches.
- `docs/goal.md`'s only change is 71 added lines **inside** the `AUTO:journeys` markers — the J-11
  block and nothing else.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No execution path, ever *(critical)* | OK | Diff adds a count and a date to a briefing row; no order/broker concept. `test_no_execution_path.py` unmodified and green in my own suite run. |
| No profit claims and no advice *(critical)* | OK | New copy is `history <N> sessions · from <date>` and `history not recorded in this snapshot`. `test_copy_discipline.py` unmodified and green; UT-09 grep for "enough/reliable/confidence/buy/watch this/opportunity" found nothing. |
| Frozen foundations *(critical)* | OK | Zero diff on engine, `v1`, `default`, `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `StructureChart.tsx`, `PriceChart.tsx` (checked by `git status` per file). Kept surfaces re-verified by J-07 replay. |
| Hold-out-only promotion *(critical)* | OK | No strategy, gate, sweep, or champion file in the diff (5 product files only). |
| No lookahead *(critical)* | OK | Verified by me: `history_start <= basis_as_of` on all 63 rows; the walk returns at the basis bar, so the count can never see a later bar. |
| Single source of truth *(critical)* | OK | Verified by me: all 63 rows re-derive from `BarStore.merged_bars` with 0 mismatches. One owner (`desk_screen.py`), one endpoint (`GET /research/desk/screen`), frontend derives nothing. `coherence.md` = COHERENCE-PASS. |
| Deterministic and seeded | OK | Same-pins re-run returns the honest reused response (UT-07: "Reused the snapshot already recorded for this key"); exactly one `screen-2026-07-28-*.json` on disk. Values come from bar timestamps, never a wall clock. |
| Read-only MCP *(critical)* | OK | No diff under `app/mcp/`; `len(TOOL_NAMES)` = 17 printed by me. |
| Immutable data *(critical)* | OK | 0 of 369 bar-series files modified; prior screen snapshots unmodified (mtimes) and checksum-valid; only an appended snapshot and rebuildable caches. |
| Persistence stays scoped *(critical)* | OK | No ambient stream recording; the one write was an explicit `POST` compute. See the process deviation below. |
| Membership is never a signal *(critical)* | OK | Rank key byte-unchanged and reads neither new field; history comes from bars, not membership. |
| Snapshots are append-only and pinned *(critical)* | OK | New snapshot carries all five pins; no legacy row backfilled (63/63 keys absent, verified by me). |
| Every run is an explicit operator act *(critical)* | OK | No scheduler/cron/auto-refresh in the diff; page-load GETs still compute nothing. |
| The briefing describes, never advises *(critical)* | OK | A count and a date; no threshold, no judgement word; copy lint green unmodified. |
| No new statistics, gates, or strategies *(critical)* | OK | Disclosure only — nothing filters, weights, or scores on the new value. |
| The demolition stays demolished *(critical)* | OK | No manual-input write path added; no journal-era machinery. |
| The ledger never holds orders *(critical)* | OK | No size, ticket, entry/exit, or account field anywhere in the new row shape. |
| The suite stays keyless and hermetic *(critical)* | OK | I ran the whole suite with no services and no network: exit 0. New tests synthesize bars on real fixture-universe symbols. |
| The fingerprint pin does not move *(critical)* | OK | `08e471b10130e1e2` printed by me; `app/config.py` absent from the diff; zero new Config fields. |
| The enhancement loop stays inside its box *(critical)* | OK | `docs/goal.md`'s only change is +71 lines inside `AUTO:journeys`; J-11 carries an SSOT acceptance clause and a `[NEW]` walkthrough clause. |
| Host-guard caps are law *(critical)* | OK | `project-extensions/host-guard/` unmodified; my own process affinity is `4-7,12-15`. |
| Deterministic scan | OK | `iter-15/scan-report.md`: CLEAN — no secret, dependency, or license findings. |

**Process deviation (recorded, deliberately NOT scored as an anti-goal violation).** The
development step ran a real screen against the owner's own data folder instead of the throw-away
copy this run's own plan asked for, and the "scoped" test rig on port 8301 turned out to carry no
data-folder override at all, so the browser pictures and the walkthrough were also taken against
the owner's real folder — even though the browser report states the opposite. What actually
happened there is safe and I checked it item by item: not one of the 369 stored price files was
touched, no old record was rewritten, one new record was added, and only two rebuildable caches
changed. It is a breach of this run's own plan and of one report's honesty, not of any project
rule. Full reasoning is in `assumptions.md` under iter-15.

## Next-Step Recommendation

Halt — the goal is achieved. Five follow-ups for the owner, none a defect and none blocking:
(1) a new screen record for 2026-07-28 was written into your own data folder during this run, and
your two rebuildable caches were refreshed; nothing was deleted and no price file was touched, but
it cannot be undone because permanent records are never deleted here; (2) the checking step marked
the "walkthrough exists" item as passed while looking at the wrong file, which let a silently
skipped filming step through — the independent audit caught it and re-filmed properly, and that
single check is worth making a hard stop in future; (3) one small test the plan asked for was not
written (a machine-tool pass-through check) — the property is already proven a stronger way, so
this is tidy-up only; (4) the picture named "tooltip" does not actually show a tooltip, because the
browser never paints that kind of hint into an image — the hint text itself was read out and is
correct; (5) still open by choice: the word "history" here counts daily bars only, while a wall is
built from four time frames, so nobody should later turn that number into a pass/fail rule; the
Desk page is now eight stacked sections and long; two screens saved on the same day cannot be told
apart by a date-only lookup; and keyboard access for the history rows. One sentence for the owner:
the new "history" column works, is honest about older records, and matches the stored price files
exactly on every row — please confirm the finish.

## Halt Justification

All eleven Must-have journeys have positive, opened evidence and none is `failing` or `unknown`.
No anti-goal violation is open: the three older ones stay resolved and I re-checked every category
myself above. The coherence audit for this run is `COHERENCE-PASS`. No journey's goal text changed
without being re-checked — there is no goal-edit drift note for this run, and every recorded text
fingerprint still matches. Nothing is waiting on a person. That is why the loop stops here rather
than continuing.
