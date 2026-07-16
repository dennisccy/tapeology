# Iteration 10 — Coherence Audit

**Iteration:** goal-tradable_wall-iter-10
**Date:** 2026-07-16
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->
<!-- COHERENCE-WARN: only advisory issues; does NOT block GOAL_ACHIEVED -->
<!-- COHERENCE-FAIL: ≥1 objective violation; blocks GOAL_ACHIEVED, forces a consolidation iteration -->

---

## Scope of this iteration

Diff since snapshot `bde5f04a` touches exactly 4 files: `README.md` (prose only), `apps/backend/app/research/pnl_ledger.py`, `apps/backend/tests/test_pnl_ledger.py`, `apps/backend/tests/test_pnl_history.py` — confirmed via the bounded diff, a full `git diff <snapshot>` re-run, and the excluded-path `--stat` (only `runs/`/`reports/` harness bookkeeping there, no lockfiles, no dependency changes). Zero `apps/frontend/**` files changed. `runs/goal-session-tradable_wall/state/blueprint.md` gained one additive row ("PnL-ledger register") in the "Existing owners" Data Contract table, made prior to the dev turn (confirmed untouched by dev's own `git status`) — this closes iter-9's coherence-WARN advisory (a). No `reports/phase-goal-tradable_wall-iter-10-ui-surface-map.md` exists, consistent with zero UI surface change this iteration (browser-QA re-verified existing surfaces; it did not create new ones).

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| PnL-ledger register / `reports/pnl/pnl-history.md` (3-way `strategy_comparison` row's band-level column, `cell["band_side"]`) | OK | `apps/backend/app/research/pnl_ledger.py:368` (header text `side`→`band side`), `:377` (cell composition — reads `cell["band_side"]` verbatim, unchanged) |

The rename touches only `_render_strategy_comparison_row_lines`'s markdown header string and its docstring, inside `pnl_ledger.py` — the exact module the blueprint registers as this value's single owner. Line 377 confirms the underlying field is still read verbatim from the cell dict composed from `edge_report.py`'s already-computed cells (`ledger_projection`/`append_strategy_comparison_row`, both untouched this iteration per `git status` and the dev handoff) — no second computation, no new endpoint, no client-side recomputation. This is the skill's explicitly-allowed "re-format for display" case (Part A.3), not a violation. `edge_report.py`, `edge_report_cache.py`, `levels.py`, `setups.py`, `tradability.py`, `backtests.py`, `strategies.py`, `config.py` all confirmed untouched (dev handoff "Not touched" list, cross-checked against the diff `--stat`).

No new displayed value/entity was introduced this iteration (iter spec "Data-contract additions: None," confirmed by the diff — only a header string and a docstring changed).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | OK | n/a — zero `apps/frontend/**` diff; nav stays frozen per anti-goal "No new nav entry" |

No new surface to place. `/structure`'s Edge Report section (existing home, per blueprint IA) is unchanged code; this iteration's actual deliverable (provisioning a scoped-keyless backend so browser-QA can observe the already-shipped warm-cache render) is a verification-harness action documented in `docs/handoffs/goal-tradable_wall-iter-10-dev.md`, not a product surface change.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Cross-surface label drift for the same field (`band_side`).** This iteration renames the 3-way table's band-level column from `side` to `band side` in `pnl_ledger.py`'s rendered markdown (`apps/backend/app/research/pnl_ledger.py:368`, feeding the committed `reports/pnl/pnl-history.md` — itself a blueprint-registered served artifact). The live browser rendering of the identical field — `/structure`'s Edge Report cell tables — still labels the column `side` (`apps/frontend/app/structure/page.tsx:655` and `:717`, both reading `cell.band_side`). Both readings are verbatim off the same canonical `band_side` field (no duplicate computation, so this is not a Data Contract violation), and the two renderers don't currently collide in any single view — the pnl-history.md rename was specifically to resolve an in-document collision with that file's *other*, pre-existing two-way `side` column (baseline/candidate), a collision that does not exist on `/structure` (the iter-10 spec's OUT OF SCOPE explicitly defers giving the 3-way row a `/structure` render path, so both labels are never shown together today). Still, the same concept now reads "side" in one human-facing surface and "band side" in another. Low stakes, but worth a look next time either surface's edge-report labelling is touched — e.g. when the deferred `/structure` render path for the `strategy_comparison` row kind is eventually built, its column should be reconciled with whichever label is chosen as canonical (or the blueprint's Data Contract could note the two are intentionally distinct terms for distinct contexts, if that's the intended resolution).
- No other advisory observations. The docstring correction (previously falsely claimed the table was built "WITHOUT a `side` column," now accurately describes the emitted `band side` column) is a documentation fix, not a new drift.
