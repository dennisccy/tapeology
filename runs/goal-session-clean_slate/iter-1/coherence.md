# Iteration 1 — Coherence Audit

**Iteration:** goal-clean_slate-iter-1
**Date:** 2026-07-24
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope note

This is a backend-only demolition iteration (`Frontend Present: no`; `git diff <snapshot> -- apps/frontend/`
is empty — verified). Zero new pages/routes/values were added; the diff is 14 route deletions, 11 whole-module
deletions, two verbatim relocations, one documented payload slim, and ~24 test-file deletions/updates. The
coherence gate's job here reduces almost entirely to Step 1 (Data Contract): did any relocation or deletion
change how a KEPT value is computed or served.

## Data Contract check

Every registered KEPT value's HTTP response was independently verified byte-identical via the iteration's own
I-9 sha256 capture-and-diff artifacts (`runs/goal-session-clean_slate/iter-1/kept-route-baseline.txt` vs
`kept-route-after.txt`, captured before/after the deletions on the same fixtures): of 28 captured routes, 27
are byte-for-byte identical; the ONE diff is `research.taxonomy` (14021 → 304 bytes), which is the blueprint's
own documented, expected slim. I additionally traced each touched canonical module's source diff directly
(not just the hash) to confirm no duplicate/alternate computation path was introduced.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Backtests | OK | `apps/backend/app/research/backtests.py:154-234` — `r_basis` relocated from `marks.py` verbatim (`return abs(reference_price - invalidation_price)`, byte-identical body); `marks.py` deleted whole (git status: deleted) so no duplicate remains; kept-route hash `research.backtests.list`/`.detail.404` unchanged (`kept-route-baseline.txt:4-5` vs `kept-route-after.txt:4-5`) |
| Datasets | OK | `apps/backend/app/research/datasets.py:75-104,450-477` — `SOURCE_REFERENCE`/`SOURCE_HISTORICAL`/`REFERENCE_SOURCE_ID`/`_load_reference_window` relocated verbatim from `studies.py`; `studies.py` deleted whole; `pnl_baseline.py:37-43` re-points its import at `datasets.py`, no second copy; kept-route hashes `research.datasets.list`/`.detail.historical`/`.detail.reference` unchanged |
| Edge cells + not-computed payload | OK | `apps/backend/app/research/edge_report.py` diff is comment-only (updated a cross-reference, no code change); kept-route hash `research.edge_report` unchanged |
| Edge-report compute snapshot | OK | `edge_report_compute.py` not in the changed-file list; kept-route hash `research.edge_report_compute_snapshot` unchanged |
| PnL ledger rows | OK | `pnl_ledger.py` not in the changed-file list; `store.py`'s KEEP methods `append_pnl_ledger_row`/`get_pnl_ledger_row`/`list_pnl_ledger` (store.py:638-707) present and untouched; kept-route hash `research.pnl_ledger` unchanged |
| Bars / candles | OK | `bars.py` not in the changed-file list; kept-route hashes `research.bars.*`/`research.candles.merged.*` unchanged |
| Levels / zones | OK | `levels.py` not in the changed-file list; kept-route hash `research.levels.aapl_pinned` unchanged |
| Strategy registry + champion pointer | OK | `strategies.py` not in the changed-file list; `store.py`'s `get_champion_pointer`/`set_champion_pointer` (store.py:708-742) present, executable body byte-identical (only a dead-caller docstring reference trimmed); kept-route hash `research.strategies` unchanged |
| Bands (tradable map) | OK | `tradability.py` not in the changed-file list; kept-route hash `research.tradability.aapl_pinned` unchanged |
| Touch events / setups | OK | `apps/backend/app/research/setups.py` diff is comment-only (a cross-reference update, no code change); kept-route hash `research.setups.*` unchanged |
| Profiles | OK | `profiles.py` not in the changed-file list; kept-route hash `research.profiles` unchanged |
| Research labels (taxonomy) | OK — EXPECTED SLIM | `apps/backend/app/research/taxonomy.py` (full file, 51 lines): `taxonomy_payload()` now returns exactly `{"feed_basis": {"feeds": [...], "live_disclosure": ...}}` — matches the blueprint's own Data Contract row verbatim ("serves ONLY the feed_basis block... + source labels sim/iex/sip/yahoo"); single function, single owner, unchanged mechanism; hash diff (14021→304 bytes) is the documented, intended shrink, not an unexpected drift |
| Route / nav inventory | OK | `app/meta.py` not in the changed-file list; kept-route hash `meta.ui-routes` unchanged |
| `config_fingerprint` | OK | `apps/backend/app/config.py` not in the changed-file list at all; `git diff <snapshot> -- .` (noise-excluded) contains zero lines with the literal `4d665603569b9dbf` — none of the 13 pinned assertion sites were touched this iteration, consistent with J-04 owning the epoch bump exclusively |

No new displayed value/entity was introduced this iteration (backend-only, zero frontend diff) — the "new
value not in the Data Contract" sub-check (Part A.4/A.5) has nothing to evaluate.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| *(none — no new page/route/feature this iteration)* | N/A | `apps/frontend/` diff is empty; route-decorator diff on `apps/backend/app/research/routes.py` shows only 14 removed `@router.get/post(...)` lines, zero added — confirmed by diffing the full sorted decorator list before vs. after the snapshot SHA |

The 14 deleted routes (`/analytics`, `/thesis*`, `/hints*`, `/journal*`, `/studies*`) are removals, not new
surfaces, so Part B's nav-path/reachability/duplicate-home/parallel-shell checks (which govern where NEW
things live) do not apply to them.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Transient frontend/backend mismatch, already planned and disclosed.** The frontend still renders 5 nav
  items (`/journal`, `/studies`, `/performance`, plus Cockpit/Structure) and those 3 pages will now hit 404
  on their backend calls, since J-01 deleted the routes but frontend deletion is explicitly J-02's job
  (`docs/phases/goal-clean_slate-iter-1.md` "OUT OF SCOPE" and "UI surface changes: None ... that is
  expected, not a regression"). The blueprint itself frames its Information Architecture as the "target
  state after this interlude closes" (a multi-iteration end state), not a per-iteration invariant, and
  goal.md's own hard two-phase ordering constraint (backend before frontend) requires exactly this
  intermediate state for one iteration. Not a coherence violation this iteration; expected to close in
  iteration 2 (J-02). Same reasoning covers the MCP server: three tools (`journal`/`analytics`/`studies`)
  transiently proxy to now-404 routes (`test_mcp_server.py`'s one failing case), explicitly owned by J-03.
- **Relocation scope exceeded the iter-1 spec's literal two-item checklist, but strengthens single-ownership
  rather than weakening it.** Beyond the two named relocations (`r_basis`; the four dataset-source symbols),
  `backtests.py` also absorbed the STATUS_* job-status vocabulary, `_PathPoint`, `_PROGRESS_EVERY`,
  `_control_state`, `_absorption_state`, `_premise_state`, and `_synthetic_invalidation` from `studies.py`
  (`apps/backend/app/research/backtests.py:154-234`). This was necessary — `backtests.py` was `studies.py`'s
  sole surviving runtime consumer of these symbols, and `studies.py` is deleted whole this same iteration —
  and it lands everything inside the already-registered canonical `backtests.py` owner (no new module, no
  duplicate). Not a Data Contract violation; noted only because it is broader than the iteration spec's own
  "Data-contract additions: None... the two relocated helpers" phrasing (a spec-fidelity note for the
  decomposer/reviewer, not a coherence-contract breach — the independent post-QA audit
  (`docs/handoffs/goal-clean_slate-iter-1-audit.md` §Domain Assessment) traced every relocated symbol
  byte-for-byte against the pre-iteration original and confirmed no behavior change).
- **Four `ResearchRegistry` methods kept as permanent `None`-returning stubs.** `projection_for`,
  `hint_projection_for`, `monitor_for`, `_surviving_projection` (`apps/backend/app/research/routes.py:279-308`)
  were not deleted because `apps/backend/app/main.py`'s WS `thesis`/`hint` frame merge — explicitly J-02's job
  to remove — still calls them; deleting them now would raise on every WS frame and break the live cockpit
  tape stream. These project no Data Contract value (the underlying thesis/hint concepts are in the
  blueprint's "Removed entirely this interlude" list with no replacement/home), so this is not a violation.
  Already flagged for J-02 same-commit cleanup in the dev handoff and the post-QA audit (finding B2); repeated
  here only for the next iteration's traceability.
