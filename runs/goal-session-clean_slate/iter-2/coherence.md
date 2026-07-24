# Iteration 2 — Coherence Audit

**Iteration:** goal-clean_slate-iter-2
**Date:** 2026-07-24
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Summary

This iteration (J-02, "Frontend + WS demolition — the two-page product") is a **pure subtraction**
against `5f45d1af08440062c07359487b8bea063ca28cc2`: 25 files touched, 6,820 deletions vs. 99
insertions, and every insertion is either a comment/docstring explaining a deletion or the single
trivial constant `NO_PRICE_LINES: ChartPriceLineSpec[] = []` (a stable empty-array placeholder for
an existing prop seam, not a value computation). A full grep of every `+` line in the diff for
`def `/`function `/`const `/`class `/`export function`/`export const` found **zero new
function/const/class definitions** anywhere in the diff — the strongest possible evidence that
this iteration cannot have introduced a duplicate computation, because it introduces no computation
at all. Excluded-path stat (`runs/*`, `reports/*`, lockfiles, images) is harness bookkeeping only —
no dependency-file changes.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Route / nav inventory (`GET /meta/ui-routes`, owner `app/meta.py` ROUTES) | OK — sanctioned shrink | `apps/backend/app/meta.py:26-31` (`UI_ROUTES` trimmed from 6 rows to exactly `{"/","Cockpit"}` + `{"/structure","Structure"}`); this is the ONE contract row the blueprint's own Notes column pre-registers as changing this iteration ("after J-02: exactly Cockpit + Structure") |
| WS frame (`/tape/{ticker}/stream`) | OK — deletion only, no re-derivation | `apps/backend/app/main.py:585-598` (the `frame["thesis"]`/`frame["hint"]` merge lines and the `_thesis_projection`/`_hint_projection` helpers deleted outright; `frame = serialize_stream(engine.snapshot())` is the sole remaining line — the frame stays the engine projection only, no new client- or server-side re-derivation appears anywhere) |
| Research labels (taxonomy) / `feed_basis` block | OK — untouched, single caller preserved | `apps/frontend/lib/api.ts:403` (`fetchTaxonomy` kept verbatim) + `apps/frontend/components/FeedBasisBadge.tsx:4,46` (its only caller, unedited); no second fetch site introduced |
| Bands / Touch events / Edge cells / PnL ledger / Bars / Levels / Strategy registry / Datasets / Backtests / Profiles / `config_fingerprint` | OK — not touched | Diffstat contains none of `tradability.py`, `setups.py`, `edge_report*.py`, `pnl_ledger.py`, `bars.py`, `levels.py`, `strategies.py`, `datasets.py`, `backtests.py`, `profiles.py`, or `config.py` — matches the iter spec's own OUT-OF-SCOPE list |
| Deleted values (active thesis, hints, verdict timeline, stance, checks, grades, excursions, study jobs/results, analytics aggregates) | OK — removed, not relocated | No new page/component reads or re-derives any of these anywhere in the diff; grep for their canonical identifiers (`declareThesis`, `fetchJournal`, `fetchAnalytics`, `createStudy`, etc.) across `apps/frontend/` returns zero source hits (two incidental non-hits: a gitignored, untracked, pre-existing stray cache directory `apps/frontend/home/dennis-chan/.cache/iad/...` unrelated to this diff, and `apps/frontend/app/structure/page.tsx:1305`, a prose comment — `"...intentionally NOT a reuse of StudyResultsView's ... copy"` — not an import, pre-identified as a false-positive in the iter spec's own NOTES) |

No new displayed value is introduced this iteration, so Part A rules 4/5 (duplicate-of-existing /
unregistered-new) have nothing to check.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/` (Cockpit) | OK — canonical home unchanged | `apps/backend/app/meta.py` (nav source of truth); `apps/frontend/components/NavBar.tsx` byte-unedited — it renders `GET /meta/ui-routes` dynamically with no hardcoded list, so it did not need a change |
| `/structure` (Structure) | OK — canonical home unchanged | same; `StructureChart.tsx` verified zero-diff (`git diff <snapshot>..HEAD -- apps/frontend/components/StructureChart.tsx` returns empty) |
| `/journal`, `/journal/[id]`, `/studies`, `/performance` | OK — removed, not relocated, no dangling link | `apps/backend/app/meta.py:26-31` (rows deleted from `UI_ROUTES`, the single nav owner); grep across `apps/frontend/app`+`components` for `href=.*/(journal|studies|performance)` or `<Link ... (journal|studies|performance)` returns zero hits — no kept surface still links to a deleted route |

No new page/route/feature is introduced this iteration, so IA rules 1-4 (no-nav-path,
reachability, duplicate-home, parallel-shell) have nothing new to evaluate — the checks above
instead confirm the removal was executed through the blueprint's single nav owner (`app/meta.py`)
with no orphaned link left pointing at a now-404 route, and that the two kept homes are otherwise
undisturbed.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- A stray, gitignored, untracked build/cache directory (`apps/frontend/home/dennis-chan/.cache/iad/iad.goal-fast_wall-iter-4.*/...`) exists on disk from an apparently unrelated prior session's misconfigured TMPDIR. It is not tracked by git, not touched by this diff, and outside this audit's scope (it predates this iteration and isn't part of the product). Worth a cheap `rm -rf` housekeeping pass whenever convenient — not a coherence defect.
- `apps/structure/page.tsx`'s pre-existing `SHOW_CASE_STUDIES = false` flag (carried forward again per the iter spec's own NOTES, still explicitly out of scope for J-02) remains unresolved. Not a new issue this iteration and not a Data Contract/IA violation — flagged only for continuity with the iter spec's own tracking.
