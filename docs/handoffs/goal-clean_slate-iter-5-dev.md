# goal-clean_slate-iter-5 Dev Handoff

**Phase:** goal-clean_slate-iter-5
**Date:** 2026-07-24
**Agent:** developer
**Status:** complete

## What Was Built

J-05 ("the kept product stands: regression sentinel") — the interlude's closing journey. Per the
plan, this iteration's only literal PRODUCT change is one UI-gate flip + one reinstated sentence;
everything else is verification/evidence that J-01–J-04's already-`passing` demolition genuinely
holds under the new fingerprint epoch, with zero backend source edits.

- **Restored Case Studies visibility on `/structure`**: flipped `SHOW_CASE_STUDIES`
  (`apps/frontend/app/structure/page.tsx:335`) from `false` to `true`. The conditional/gate
  structure itself (`{SHOW_CASE_STUDIES && (...)}`) is untouched — only the literal value changed,
  per the plan's explicit instruction and the carried-forward assumption-ledger decision
  (`runs/goal-session-clean_slate/state/assumptions.md`, `## iter-5 — goal-decomposer`: RESTORE,
  not rescope). All Case Studies state/handlers/data-fetch were already live since era 5B/5C —
  confirmed by reading the section (`~2336-2430`): it reads pre-existing `setupsResult`/
  `setupsEvents`/`filteredSetupsEvents`/`SetupRow` state with no new wiring needed.
- **Reinstated the one sentence commit `e60f6a7` dropped** from the `data-testid="structure-framing"`
  paragraph (`~line 2031-2039`): inserted "Case Studies lists every band-touch event with its
  reaction, forward returns, and — once recorded — its tape timeline; " immediately before the
  existing "Edge Report compares v1, structure_tape, and structure_tape_map..." sentence. No other
  text in that paragraph changed.
- **Full backend regression sentinel (TC-1/TC-2) — zero backend source changed**: fresh
  `pytest tests/` run reports **1167 passed, 7 skipped, 0 failed, 0 errors**, exit 0 — identical
  counts to iter-4's baseline (expected, since no backend file was touched this iteration). Live
  `Config().config_fingerprint()` confirmed `08e471b10130e1e2`. The 7 named guard/chart-guard
  suites (`test_no_execution_path.py`, `test_no_credential_in_artifacts.py`,
  `test_backtests.py::test_structure_tape_map_reads_tradability_never_recomputes_levels_or_zones`,
  `test_backtests.py::test_structure_tape_reads_levels_from_the_one_canonical_compute_levels_owner`,
  `test_setups.py::test_compute_setups_itself_never_touches_the_dataset_store`,
  `test_setups.py::test_scan_cache_publish_is_a_single_atomic_rebind_never_two_separate_writes`,
  `test_cockpit_chart_upgrade.py`, `test_structure_chart_viewport.py`,
  `test_price_chart_confluence.py`) all pass in isolation (47 passed) AND `git diff` confirms every
  one of those files is byte-unmodified vs HEAD.
- **Final surface-inventory grep sweep**: T-12 import-grep for all 11 deleted modules
  (`journal_rows`, `monitor`, `hints`, `stance`, `verdict`, `grades`, `marks`, `excursions`,
  `execution_checks`, `analytics`, `studies`) returns zero hits under `apps/`, and the module files
  themselves are confirmed physically gone (no T-2 stub). `app/meta.py`'s `UI_ROUTES` read directly:
  exactly 2 entries (`/` Cockpit, `/structure` Structure). MCP `_STATIC_PATHS`/`_TAPE_PATHS`/
  dedicated-branch registry read directly plus the already-green `test_mcp_server.py::EXPECTED_TOOLS`
  contract test confirm exactly the 15 I-6 tool names (no `journal`/`analytics`/`studies`). Live
  404 sweep against a freshly-started backend: all 14 concretely-enumerated I-1 routes return
  exactly HTTP 404 (see Known Issues re: the "15" vs the table's 14 rows); `GET /research/taxonomy`
  correctly still 200s (SLIM, not DELETE).
- **Final I-9 kept-route byte-comparison recapture** (`runs/goal-session-clean_slate/iter-5/
  kept-route-after.txt`, 28 routes) against iter-4's capture: **0 new diffs** — every one of the 28
  rows (sha256 + body_len + status) is byte-for-byte identical to iter-4's capture, including the
  two previously-sanctioned J-04 diffs (`research.pnl_ledger`, `research.backtests.list`), which
  simply persist unchanged since no new backend mutation happened this iteration.
- **Session-wide diff-vs-inventory cross-check** (`runs/goal-session-clean_slate/iter-5/
  diff-vs-inventory-crosscheck.md`): the cumulative `apps/`-scoped diff from the session baseline
  (`e7865b4`, pre-iter-0) through this iteration's working tree — 91 files (1 added, 51 deleted, 39
  modified) — is fully accounted for against I-1…I-9 + I-8's test dispositions + J-04's landed pin/
  baseline updates, with zero out-of-inventory residue. Chart guard re-verified directly:
  `StructureChart.tsx` shows zero diff across the whole session (T-8); `PriceChart.tsx`'s entire
  107-line diff is scoped exactly to the thesis-geometry-overlay removal (no other change). TC-17
  re-verified against HEAD (not just the session baseline): `docs/goal-archive/`,
  `runs/goal-session-clean_slate/iter-0`–`iter-4`, and `reports/pnl/pnl-history.md`'s pre-iter-5
  content show zero bytes changed. The 14th derived-pin site
  (`test_profile_equivalence.py::test_candidate_resolved_fingerprint_is_distinct_from_default`)
  re-run in isolation by name: 1 passed, pins `16d7c98e4fdca755` (distinct from base
  `08e471b10130e1e2`).
- **Clean rebuild + restart (T-9)**: `rm -rf apps/frontend/.next`, ran `npm run build` (the
  project's frontend test command) — compiled successfully, zero type errors, route table shows
  exactly `/`, `/_not-found`, `/structure` (confirming no journal/studies/performance route
  survives at the build level). Cleaned `.next` again post-build, then started both services twice
  via `scripts/dev.sh` (stop, then start again) to confirm no port conflicts — both boots clean, no
  errors, ports 8301/3301 released and re-bound cleanly each time. Non-Chrome smoke checks on both
  boots: `/`, `/structure` → 200; `/journal`, `/studies`, `/performance` → 404;
  `GET /meta/ui-routes` → the 2 kept routes; the served `/structure` HTML contains "Case Studies"
  and the exact reinstated sentence text; no "journal"/"performance" text survives anywhere on the
  page. Both processes stopped cleanly before finishing (no server left running).

## Files Changed

- `apps/frontend/app/structure/page.tsx` -- flipped `SHOW_CASE_STUDIES` `false`→`true` (line 335);
  inserted the one reinstated sentence into the `structure-framing` paragraph. **The only product
  file touched this iteration** — confirmed via `git diff --stat` (one file). `StructureChart.tsx`
  and `PriceChart.tsx` untouched (T-8).
- `runs/goal-session-clean_slate/iter-5/kept-route-after.txt` -- new: final I-9 byte-comparison
  capture (28 routes), 0 new diffs vs iter-4's capture.
- `runs/goal-session-clean_slate/iter-5/diff-vs-inventory-crosscheck.md` -- new: the session-wide
  diff-vs-inventory cross-check artifact (evidence for TC-15), covering every changed file across
  the whole interlude against I-1…I-9.
- `runs/goal-clean_slate-iter-5/status.json` -- `current_step: dev_complete`.
- No backend source file changed (matches the plan's expectation of zero backend edits this
  iteration — J-01–J-04's own code is only re-verified, not re-implemented).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1167 passed, 7 skipped, 0 failed, 0 errors**, exit 0 (identical to iter-4's baseline —
expected, zero backend files touched).

Additional targeted runs:
- Guard/chart-guard suites in isolation (7 files/functions): **47 passed, 0 failed**; `git diff`
  confirms byte-unmodified.
- `test_profile_equivalence.py::test_candidate_resolved_fingerprint_is_distinct_from_default` in
  isolation: **1 passed**.

Command: `cd apps/frontend && npm run build`
Result: **compiled successfully**, 0 type errors, 3 routes generated (`/`, `/_not-found`,
`/structure`).

Live/manual verification (non-Chrome smoke checks, both `scripts/dev.sh` boots):
- 15-ish route 404 sweep (14 concretely-enumerated I-1 routes): all 404. `research.taxonomy`: 200.
- `/`, `/structure`: 200. `/journal`, `/studies`, `/performance`: 404.
- `GET /meta/ui-routes`: exactly the 2 kept routes.
- `/structure`'s served HTML contains "Case Studies" and the exact reinstated sentence text.

**Not run by this agent**: the full Chrome-driven browser walk with screenshot evidence (sim
cockpit + both charts, `/structure` Load of the pinned AAPL window, Case Studies drill-in, Edge
Report state) is browser-qa-agent's stage in the pipeline (developer → reviewer → ui-impact-analyst
→ ui-test-designer → browser-qa-agent → qa → …), not the developer's. Per T-13, that evidence
remains `unknown` (never `passing`) until browser-qa-agent captures it.

## Known Issues

**Two carried, pre-existing documentation-count observations in goal.md itself (T-14-style;
neither is new, neither blocks, neither needs a code change)** — full detail in
`runs/goal-session-clean_slate/iter-5/diff-vs-inventory-crosscheck.md`:

1. **I-1's prose says "DELETE these 15 route handlers" but its own table enumerates only 14 rows.**
   This was already caught and correctly resolved at iter-1 (that dev handoff explicitly says
   "Deleted 14 route handlers... 404 verified"; iter-1's review says the same). This iteration's
   live 404 sweep re-confirms all 14 enumerated routes return 404 today; there is no 15th route
   anywhere in the current `routes.py` (the file no longer exists to search for a missing one —
   the deletion is the point). Same class of slip as the already-resolved "13→14 pin sites" and
   "48→40 exclusion set" items iter-4's audit flagged elsewhere in goal.md.
2. **I-8's DELETE list is prefixed "~24 files" but names 25** (the tilde already signals
   approximation in the source text) — this iteration's diff shows exactly those 25 named test
   files deleted, name-for-name; not a real discrepancy.

**Seven backend test files show mechanical modifications not itemized by filename in I-8's UPDATE
table, but each is a necessary, correct, directly-traceable consequence of I-2/I-5's
`ResearchRegistry` deletions** (verified by reading every diff line-by-line — full detail in the
cross-check artifact): `test_backtests_api.py`, `test_bars_api.py`, `test_datasets_api.py`,
`test_levels_api.py`, `test_setups_api.py`, `test_tradability_api.py` each drop 2-3 lines calling
the now-deleted `manager.set_on_engine_created(registry.on_engine_created)` /
`registry.study_jobs.join_all(...)` in their own fixture teardown (leaving them would raise
`AttributeError` on every test run); `test_observer_equivalence.py` drops exactly two whole test
functions that imported the now-deleted `ResearchMonitor`/`ThesisRecord` (leaving them would be a
`ModuleNotFoundError` at collection time). This is the same "discovered gap, documented, fixed"
pattern iter-1's own Known Issues already established as sanctioned under T-14 — these are not new
problems, just not individually named in goal.md's file-level table.

**Carried, not this iteration's concern**: none — `SHOW_CASE_STUDIES` (the one item every prior
handoff carried forward) is resolved as of this iteration.

**Deferred to browser-qa-agent**: the actual screenshot-evidenced browser walk (TC-4–TC-11) per the
pipeline's own stage ordering — see Tests Run above.
